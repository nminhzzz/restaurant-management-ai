"""LLM provider adapter (Appendix 3, configurations A/B/C).

A commercial chat-completions API is the default and Ollama is the self-hosted
fallback used as configuration C; `get_client()` selects by `AI_PROVIDER`. Tests
replace the whole client through `set_client()`, so nothing here runs in the suite.
"""

from typing import Protocol

import httpx

from app.core.config import get_settings


class LlmClient(Protocol):
    def complete(self, prompt: str) -> str: ...


class CommercialClient:
    def __init__(self, *, api_key: str, model: str, base_url: str) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    def complete(self, prompt: str) -> str:
        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
            },
            timeout=20.0,
        )
        response.raise_for_status()
        payload = response.json()
        return str(payload["choices"][0]["message"]["content"])


class OllamaClient:
    def __init__(self, *, model: str, base_url: str) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")

    def complete(self, prompt: str) -> str:
        response = httpx.post(
            f"{self._base_url}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": False},
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
    return CommercialClient(
        api_key=settings.ai_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url or "https://api.openai.com/v1",
    )


def get_client() -> LlmClient:
    global _client
    if _client is None:
        _client = _build_client()
    return _client
