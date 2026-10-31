"""LLM provider adapter (Appendix 3, configurations A/B/C).

Claude Opus 5.5 through the Anthropic Messages API is the provider (report §5.1.1);
`get_client()` selects by `AI_PROVIDER` (`fake` for local runs). Tests replace the whole
client through `set_client()`, so nothing here runs in the suite.

Runtime fallback model (report §1.4.2, §4.1.1): a transport error, timeout, 429 or 5xx
on the primary model is retried once on `LLM_FALLBACK_MODEL`; if that fails too, the
assistant reports the error. A 4xx auth/validation error is never retried — it means
the request itself is wrong, so a different model would fail the same way. A safety
refusal is rerouted server-side (`fallbacks="default"`); if it still refuses, the call
fails.
"""

import asyncio
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Literal, Protocol

import anthropic
import httpx2
from anthropic.types.beta import BetaTextBlockParam

from app.core.config import get_settings
from app.modules.ai.usage import attempt_context, finish_attempt, start_attempt

logger = logging.getLogger(__name__)

# Thinking counts toward max_tokens; a low-effort SQL answer needs far less, and the cap
# bounds the cost of a runaway reply (NFR-08).
MAX_OUTPUT_TOKENS = 8192
REFUSAL_FALLBACK_BETA = "server-side-fallback-2026-07-01"
# Ends the per-role stable prefix (instructions, schema, examples) of a prompt. The
# hosted client caches everything before it; other clients never see the marker.
CACHE_BREAKPOINT = "\x1e"

Effort = Literal["low", "medium", "high", "xhigh", "max"]


class ProviderRefusal(RuntimeError):
    """The model declined the request; retrying the same prompt would decline again."""


@dataclass(frozen=True)
class GenerationOptions:
    reasoning_effort: Effort | None = None
    fallback: bool = True
    # Routes one call to another model, e.g. the interpretation model (NFR-02).
    model: str | None = None
    # False sends `thinking: disabled`; Opus 5.5 rejects it, so only set it for models
    # that accept it.
    thinking: bool = True


_options: ContextVar[GenerationOptions | None] = ContextVar("ai_generation_options", default=None)


@contextmanager
def generation_options(
    *,
    reasoning_effort: Effort | None = None,
    fallback: bool | None = None,
    model: str | None = None,
    thinking: bool = True,
) -> Iterator[None]:
    previous = _options.get()
    effective_fallback = (
        fallback if fallback is not None else (previous.fallback if previous else True)
    )
    token = _options.set(
        GenerationOptions(reasoning_effort, effective_fallback, model=model, thinking=thinking)
    )
    try:
        yield
    finally:
        _options.reset(token)


def _provider_timeout() -> float:
    settings = get_settings()
    # Reserve time for the fallback-model retry and SQL within the outer deadline.
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


def _content(prompt: str) -> str | list[BetaTextBlockParam]:
    prefix, found, tail = prompt.partition(CACHE_BREAKPOINT)
    if not found:
        return prompt
    return [
        {"type": "text", "text": prefix, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": tail},
    ]


def _is_retryable(exc: anthropic.APIError) -> bool:
    if isinstance(exc, anthropic.APIStatusError):
        return exc.status_code == 429 or exc.status_code >= 500
    # APITimeoutError is a subclass of APIConnectionError.
    return isinstance(exc, anthropic.APIConnectionError)


class CommercialClient:
    """An Anthropic Messages API client (Claude Opus 5.5 by default).

    Opus 5.5 always thinks; `effort` is the only depth control. Thinking blocks are
    never part of the answer — only `text` blocks are the SQL or interpretation.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "",
        fallback_model: str = "",
        reasoning_effort: Effort | None = None,
        transport: httpx2.BaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self.model = model
        self._base_url = base_url.rstrip("/")
        self._fallback_model = fallback_model
        self._reasoning_effort = reasoning_effort
        self._sdk = anthropic.Anthropic(
            # Empty key/URL defer to ANTHROPIC_API_KEY / ANTHROPIC_BASE_URL.
            api_key=api_key or None,
            base_url=self._base_url or None,
            # Retries and fallbacks are owned here so they fit the 8s budget (NFR-02).
            max_retries=0,
            http_client=httpx2.Client(transport=transport) if transport else None,
        )

    def _post(self, model: str, prompt: str) -> str:
        attempt = start_attempt(model)
        options = _options.get()
        effort = (options.reasoning_effort if options else None) or self._reasoning_effort
        response = self._sdk.with_options(timeout=_provider_timeout()).beta.messages.create(
            model=model,
            max_tokens=MAX_OUTPUT_TOKENS,
            messages=[{"role": "user", "content": _content(prompt)}],
            output_config={"effort": effort} if effort else anthropic.omit,
            thinking={"type": "disabled"} if options and not options.thinking else anthropic.omit,
            betas=[REFUSAL_FALLBACK_BETA],
            fallbacks="default",
        )
        finish_attempt(attempt, response.model_dump())
        if response.stop_reason == "refusal":
            raise ProviderRefusal(f"model {response.model} declined the request")
        text = "".join(block.text for block in response.content if block.type == "text")
        return _strip_code_fence(text)

    def complete(self, prompt: str) -> str:
        try:
            result = self._post(self.model, prompt)
        except anthropic.APIError as exc:
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


async def complete_async(client: LlmClient, prompt: str) -> str:
    """Bound each provider attempt by wall time, not HTTP's per-phase timeout.

    A timed-out thread may finish its single HTTP request, but it never starts
    another attempt itself. Cancellation of the outer turn stops the chain.
    """
    timeout = _provider_timeout()
    if not isinstance(client, CommercialClient):
        async with asyncio.timeout(timeout):
            with attempt_context(str(getattr(client, "model", type(client).__name__))):
                return await asyncio.to_thread(
                    client.complete, prompt.replace(CACHE_BREAKPOINT, "")
                )
    options = _options.get()
    models = [(options.model if options else None) or client.model]
    allow_fallback = options is None or options.fallback
    if allow_fallback and client._fallback_model and client._fallback_model != models[0]:
        models.append(client._fallback_model)
    last_error: Exception | None = None
    for model in models:
        try:
            async with asyncio.timeout(timeout):
                with attempt_context(model):
                    return await asyncio.to_thread(client._post, model, prompt)
        except TimeoutError as exc:
            last_error = exc
        except anthropic.APIError as exc:
            if not _is_retryable(exc):
                raise
            last_error = exc
        logger.warning("ai.llm.attempt_failed model=%s", model)
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
    if provider == "fake":
        return FakeClient()
    return CommercialClient(
        api_key=settings.ai_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        fallback_model=settings.llm_fallback_model or settings.ai_config_c_model,
        reasoning_effort=settings.llm_reasoning_effort,
    )


def get_client() -> LlmClient:
    global _client
    if _client is None:
        _client = _build_client()
    return _client
