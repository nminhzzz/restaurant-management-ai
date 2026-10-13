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

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
OPENAI_BASE_URL = "https://api.openai.com/v1"


# USD per million tokens (input, output) at the list price the report budgets with
# (DeepSeek-V4.1-Flash, 09/10/2026, report §4.2). A model absent here has no known price,
# so the turn's cost is left unrecorded instead of guessed.
MODEL_PRICES_USD_PER_MILLION: dict[str, tuple[Decimal, Decimal]] = {
    "deepseek-flash": (Decimal("0.30"), Decimal("1.20")),
}
_TOKENS_PER_PRICE_UNIT = Decimal(1_000_000)


@dataclass
class UsageTally:
    """What one question spent on the model: calls, tokens, models used and cost."""

    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    models: list[str] = field(default_factory=list)
    cost_usd: Decimal = Decimal(0)
    fully_priced: bool = True

    @property
    def model_version(self) -> str | None:
        return "+".join(self.models) if self.models else None

    @property
    def priced_cost(self) -> Decimal | None:
        return self.cost_usd if self.calls and self.fully_priced else None


_tally: ContextVar[UsageTally | None] = ContextVar("ai_usage_tally", default=None)


@contextmanager
def track_usage() -> Iterator[UsageTally]:
    """Collect the usage of every model call made inside the block.

    The tally travels in a context variable, which `asyncio.to_thread` copies into the
    worker thread, so the shared singleton client needs no per-request state.
    """
    tally = UsageTally()
    token = _tally.set(tally)
    try:
        yield tally
    finally:
        _tally.reset(token)


def _record_call(model: str, input_tokens: int, output_tokens: int) -> None:
    tally = _tally.get()
    if tally is None:
        return
    tally.calls += 1
    tally.input_tokens += input_tokens
    tally.output_tokens += output_tokens
    if model not in tally.models:
        tally.models.append(model)
    price = MODEL_PRICES_USD_PER_MILLION.get(model)
    if price is None:
        tally.fully_priced = False
    else:
        tally.cost_usd += (
            Decimal(input_tokens) * price[0] + Decimal(output_tokens) * price[1]
        ) / _TOKENS_PER_PRICE_UNIT


def _count(usage: Any, key: str) -> int:
    value = usage.get(key) if isinstance(usage, dict) else None
    return value if isinstance(value, int) and value >= 0 else 0


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
    ) -> None:
        self._api_key = api_key
        self.model = model
        self._base_url = base_url.rstrip("/")
        self._fallback_model = fallback_model
        self._reasoning_effort = reasoning_effort
        self._transport = transport

    def _post(self, model: str, prompt: str) -> str:
        body: dict[str, object] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }
        # Opt-in: OpenAI-style models reject parameters they do not know.
        if self._reasoning_effort:
            body["reasoning_effort"] = self._reasoning_effort
        with httpx.Client(transport=self._transport, timeout=20.0) as client:
            response = client.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=body,
            )
        response.raise_for_status()
        payload = response.json()
        usage = payload.get("usage")
        _record_call(
            model,
            _count(usage, "prompt_tokens"),
            # Reasoning models bill their chain of thought as completion tokens.
            _count(usage, "completion_tokens"),
        )
        message = payload["choices"][0]["message"]
        return _strip_code_fence(str(message.get("content") or ""))

    def complete(self, prompt: str) -> str:
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
        response = httpx.post(
            f"{self._base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=20.0,
        )
        response.raise_for_status()
        payload = response.json()
        _record_call(
            self.model, _count(payload, "prompt_eval_count"), _count(payload, "eval_count")
        )
        return str(payload.get("response", ""))


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
    )


def get_client() -> LlmClient:
    global _client
    if _client is None:
        _client = _build_client()
    return _client
