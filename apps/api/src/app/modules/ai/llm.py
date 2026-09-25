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
from typing import Protocol

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
OPENAI_BASE_URL = "https://api.openai.com/v1"


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
        return str(response.json().get("response", ""))


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
