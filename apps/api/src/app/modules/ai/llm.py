"""LLM provider adapter (Appendix 3, configurations A/B/C).

DeepSeek's OpenAI-compatible chat-completions API is the default commercial provider
and Ollama is the self-hosted fallback used as configuration C; `get_client()` selects
by `AI_PROVIDER`. Tests replace the whole client through `set_client()`, so nothing
here runs in the suite.

Runtime fallback model (report §1.4.2, §4.1.1): a transport error, timeout, 429 or 5xx
on the primary model is retried once on `LLM_FALLBACK_MODEL` before the call is treated
as failed. A 4xx auth/validation error is never retried — it means the request itself
is wrong, so a different model would fail the same way.
"""

import asyncio
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import get_settings
from app.modules.ai.usage import attempt_context, finish_attempt, start_attempt

logger = logging.getLogger(__name__)

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
OPENAI_BASE_URL = "https://api.openai.com/v1"


@dataclass(frozen=True)
class GenerationOptions:
    thinking: str = "disabled"
    reasoning_effort: str = ""
    fallback: bool = True


_options: ContextVar[GenerationOptions | None] = ContextVar("ai_generation_options", default=None)


@contextmanager
def generation_options(
    *, thinking: str = "disabled", reasoning_effort: str = "", fallback: bool | None = None
) -> Iterator[None]:
    previous = _options.get()
    effective_fallback = (
        fallback if fallback is not None else (previous.fallback if previous else True)
    )
    token = _options.set(GenerationOptions(thinking, reasoning_effort, effective_fallback))
    try:
        yield
    finally:
        _options.reset(token)


def _provider_timeout() -> float:
    settings = get_settings()
    # Reserve time for hosted retry, Ollama and SQL within the outer deadline.
    # Leave room for the interpretation call inside the 8s turn budget.
    return min(
        settings.ai_llm_timeout_seconds,
        max(1.0, settings.ai_response_budget_seconds - 2.5),
    )


class LlmClient(Protocol):
    def complete(self, prompt: str) -> str: ...


def _strip_code_fence(text: str) -> str:
    """The model sometimes wraps SQL in a ```sql ... ``` fence; only the SQL matters."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    lines = lines[1:]  # drop the opening ``` or ```sql line
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _is_retryable(exc: httpx.HTTPError) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return status == 429 or status >= 500
    # httpx.TimeoutException and connection failures are both TransportError subclasses.
    return isinstance(exc, httpx.TransportError)


class CommercialClient:
    """An OpenAI-compatible chat-completions client (DeepSeek by default).

    `deepseek-reasoner`-style reasoning models return their chain of thought in a
    separate `reasoning_content` field; only `content` is ever the SQL answer.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        fallback_model: str = "",
        reasoning_effort: str = "",
        transport: httpx.BaseTransport | None = None,
        fallback_client: "LlmClient | None" = None,
    ) -> None:
        self._api_key = api_key
        self.model = model
        self._base_url = base_url.rstrip("/")
        self._fallback_model = fallback_model
        self._reasoning_effort = reasoning_effort
        self._transport = transport
        self._fallback_client = fallback_client

    def _post(self, model: str, prompt: str) -> str:
        attempt = start_attempt(model)
        body: dict[str, object] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }
        # Opt-in: OpenAI-style models reject parameters they do not know.
        options = _options.get()
        if "deepseek" in self._base_url or options is not None:
            body["thinking"] = {"type": options.thinking if options else "disabled"}
        effort = options.reasoning_effort if options else self._reasoning_effort
        if effort:
            body["reasoning_effort"] = effort
        with httpx.Client(transport=self._transport, timeout=_provider_timeout()) as client:
            response = client.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=body,
            )
        response.raise_for_status()
        payload = response.json()
        finish_attempt(attempt, payload)
        message = payload["choices"][0]["message"]
        return _strip_code_fence(str(message.get("content") or ""))

    def complete(self, prompt: str) -> str:
        try:
            return self._complete_commercial(prompt)
        except httpx.HTTPError as primary_error:
            if self._fallback_client is None or not _is_retryable(primary_error):
                raise
            logger.warning("ai.llm.provider_fallback reason=%s", primary_error)
            try:
                return self._fallback_client.complete(prompt)
            except Exception:
                logger.exception("ai.llm.fallback_provider_failed")
                raise primary_error from None

    def _complete_commercial(self, prompt: str) -> str:
        try:
            result = self._post(self.model, prompt)
        except httpx.HTTPError as exc:
            if (
                not self._fallback_model
                or self._fallback_model == self.model
                or not _is_retryable(exc)
            ):
                logger.error("ai.llm.failed model=%s error=%s", self.model, exc)
                raise
            logger.warning(
                "ai.llm.fallback primary=%s fallback=%s reason=%s",
                self.model,
                self._fallback_model,
                exc,
            )
            result = self._post(self._fallback_model, prompt)
            logger.info("ai.llm.answered model=%s (fallback)", self._fallback_model)
            return result
        logger.info("ai.llm.answered model=%s", self.model)
        return result


class OllamaClient:
    def __init__(self, *, model: str, base_url: str) -> None:
        self.model = model
        self._base_url = base_url.rstrip("/")

    def complete(self, prompt: str) -> str:
        attempt = start_attempt(self.model)
        response = httpx.post(
            f"{self._base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=_provider_timeout(),
        )
        response.raise_for_status()
        payload = response.json()
        finish_attempt(attempt, payload, ollama=True)
        return str(payload.get("response", ""))


async def complete_async(client: LlmClient, prompt: str) -> str:
    """Bound each provider attempt by wall time, not HTTP's per-phase timeout.

    A timed-out thread may finish its single HTTP request, but it never starts
    another provider itself. Cancellation of the outer turn stops the chain.
    """
    timeout = _provider_timeout()
    if not isinstance(client, CommercialClient):
        async with asyncio.timeout(timeout):
            with attempt_context(
                str(getattr(client, "model", type(client).__name__)),
                billable=not isinstance(client, OllamaClient),
            ):
                return await asyncio.to_thread(client.complete, prompt)
    models = [client.model]
    options = _options.get()
    allow_fallback = options is None or options.fallback
    if allow_fallback and client._fallback_model and client._fallback_model != client.model:
        models.append(client._fallback_model)
    last_error: Exception | None = None
    for model in models:
        try:
            async with asyncio.timeout(timeout):
                with attempt_context(model):
                    return await asyncio.to_thread(client._post, model, prompt)
        except TimeoutError as exc:
            last_error = exc
        except httpx.HTTPError as exc:
            if not _is_retryable(exc):
                raise
            last_error = exc
        logger.warning("ai.llm.attempt_failed model=%s", model)
    if allow_fallback and client._fallback_client is not None:
        async with asyncio.timeout(timeout):
            fallback = client._fallback_client
            with attempt_context(
                str(getattr(fallback, "model", type(fallback).__name__)),
                billable=not isinstance(fallback, OllamaClient),
            ):
                return await asyncio.to_thread(fallback.complete, prompt)
    assert last_error is not None
    raise last_error


class FakeClient:
    """A fixed reply, for running locally without any provider configured."""

    def __init__(self, reply: str = "SELECT 1") -> None:
        self.reply = reply

    def complete(self, prompt: str) -> str:
        return self.reply


_client: LlmClient | None = None


def set_client(client: LlmClient | None) -> None:
    global _client
    _client = client


def _build_client() -> LlmClient:
    settings = get_settings()
    provider = settings.ai_provider.lower()
    if provider == "ollama":
        return OllamaClient(model=settings.llm_model, base_url=settings.ai_ollama_base_url)
    if provider == "fake":
        return FakeClient()
    default_base_url = OPENAI_BASE_URL if provider == "openai" else DEEPSEEK_BASE_URL
    return CommercialClient(
        api_key=settings.ai_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url or default_base_url,
        fallback_model=settings.llm_fallback_model or settings.ai_config_c_model,
        reasoning_effort=settings.llm_reasoning_effort if provider == "deepseek" else "",
        # Report §1.4.2: a commercial outage falls back to the self-hosted model,
        # not merely to another hosted model name.
        fallback_client=(
            OllamaClient(
                model=settings.ai_ollama_model,
                base_url=settings.ai_ollama_base_url,
            )
            if settings.ai_ollama_fallback
            else None
        ),
    )


def get_client() -> LlmClient:
    global _client
    if _client is None:
        _client = _build_client()
    return _client
