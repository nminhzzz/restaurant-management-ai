"""Anthropic Messages API client: request shape, fence stripping, refusals and the
runtime fallback model (report §1.4.2, §4.1.1). No real network — every request goes
through `httpx2.MockTransport`.
"""

import json

import anthropic
import httpx2
import pytest

from app.modules.ai.llm import CommercialClient, ProviderRefusal

BASE_URL = "https://api.test"


def _json_response(status_code: int, payload: dict) -> httpx2.Response:
    return httpx2.Response(status_code, json=payload)


def _error(status_code: int, message: str = "boom") -> httpx2.Response:
    return _json_response(
        status_code, {"type": "error", "error": {"type": "api_error", "message": message}}
    )


def _message(
    content: list[dict] | str,
    model: str = "claude-opus-5-5",
    stop_reason: str = "end_turn",
) -> dict:
    blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content
    return {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": blocks,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }


def _client(handler, **kwargs) -> CommercialClient:
    kwargs.setdefault("model", "claude-opus-5-5")
    return CommercialClient(
        api_key=kwargs.pop("api_key", "secret"),
        base_url=BASE_URL,
        transport=httpx2.MockTransport(handler),
        **kwargs,
    )


def test_sends_the_expected_request() -> None:
    captured: dict = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        captured["path"] = request.url.path
        captured["auth"] = request.headers["authorization"]
        captured["beta"] = request.headers["anthropic-beta"]
        captured["json"] = json.loads(request.content)
        return _json_response(200, _message("SELECT 1"))

    result = _client(handler, reasoning_effort="low").complete("hỏi gì đó")

    assert result == "SELECT 1"
    assert captured["path"] == "/v1/messages"
    assert captured["auth"] == "Bearer secret"
    assert captured["beta"] == "server-side-fallback-2026-07-01"
    assert captured["json"] == {
        "model": "claude-opus-5-5",
        "max_tokens": 8192,
        "messages": [{"role": "user", "content": "hỏi gì đó"}],
        "output_config": {"effort": "low"},
        "fallbacks": "default",
    }


def test_no_effort_is_sent_when_none_is_configured() -> None:
    """Opus 5.5 rejects `thinking: disabled` and sampling params; nothing extra is sent."""
    captured: dict = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        captured.update(json.loads(request.content))
        return _json_response(200, _message("SELECT 1"))

    _client(handler).complete("q")

    assert "output_config" not in captured
    assert "thinking" not in captured
    assert "temperature" not in captured


@pytest.mark.parametrize("effort", ["low", "high"])
def test_a_generation_option_overrides_the_configured_effort(effort) -> None:
    from app.modules.ai import llm

    captured: dict = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        captured.update(json.loads(request.content))
        return _json_response(200, _message("SELECT 1"))

    with llm.generation_options(reasoning_effort=effort):
        _client(handler, reasoning_effort="medium").complete("q")

    assert captured["output_config"] == {"effort": effort}


def test_strips_a_code_fence_around_the_sql() -> None:
    def handler(_: httpx2.Request) -> httpx2.Response:
        return _json_response(200, _message("```sql\nSELECT 1\n```"))

    assert _client(handler).complete("q") == "SELECT 1"


def test_only_text_blocks_are_used_never_thinking() -> None:
    def handler(_: httpx2.Request) -> httpx2.Response:
        blocks = [
            {"type": "thinking", "thinking": "vì bảng này...", "signature": "sig"},
            {"type": "text", "text": "SELECT 1"},
        ]
        return _json_response(200, _message(blocks))

    assert _client(handler).complete("q") == "SELECT 1"


def test_a_refusal_raises_instead_of_returning_empty_sql() -> None:
    def handler(_: httpx2.Request) -> httpx2.Response:
        return _json_response(200, _message([], stop_reason="refusal"))

    with pytest.raises(ProviderRefusal):
        _client(handler).complete("q")


@pytest.mark.parametrize(
    "make_response",
    [
        lambda: _error(500),
        lambda: _error(529, "overloaded"),
        lambda: _error(429, "rate limited"),
        lambda: (_ for _ in ()).throw(httpx2.ConnectTimeout("timed out")),
    ],
)
def test_retries_once_on_the_fallback_model_after_a_retryable_error(make_response) -> None:
    calls: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        model = json.loads(request.content)["model"]
        calls.append(model)
        if model == "claude-opus-5-5":
            response = make_response()
            if isinstance(response, httpx2.Response):
                return response
            raise response
        return _json_response(200, _message("SELECT 1", model=model))

    result = _client(handler, fallback_model="claude-sonnet-5-5").complete("q")

    assert result == "SELECT 1"
    assert calls == ["claude-opus-5-5", "claude-sonnet-5-5"]


def test_never_retries_on_a_4xx_auth_or_validation_error() -> None:
    calls: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        calls.append(json.loads(request.content)["model"])
        return _error(401, "invalid api key")

    client = _client(handler, api_key="bad", fallback_model="claude-sonnet-5-5")
    with pytest.raises(anthropic.AuthenticationError):
        client.complete("q")

    assert calls == ["claude-opus-5-5"]


def test_no_fallback_configured_raises_the_original_error() -> None:
    def handler(_: httpx2.Request) -> httpx2.Response:
        return _error(500)

    with pytest.raises(anthropic.InternalServerError):
        _client(handler).complete("q")


def test_fallback_equal_to_primary_model_is_never_retried() -> None:
    calls: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        calls.append(json.loads(request.content)["model"])
        return _error(500)

    with pytest.raises(anthropic.InternalServerError):
        _client(handler, fallback_model="claude-opus-5-5").complete("q")

    assert calls == ["claude-opus-5-5"]


def test_provider_timeout_leaves_time_for_fallback_inside_the_response_budget() -> None:
    """A stalled primary must time out before the assistant's outer deadline."""
    from app.core.config import get_settings

    observed = []

    def handler(request):
        observed.append(request.extensions["timeout"]["read"])
        if json.loads(request.content)["model"] == "primary":
            raise httpx2.ReadTimeout("Primary stalled", request=request)
        return _json_response(200, _message("SELECT 1 FROM vw_ai_kho_ton"))

    client = _client(handler, model="primary", fallback_model="fallback")
    assert client.complete("question") == "SELECT 1 FROM vw_ai_kho_ton"
    # Leave ~2.5s for the interpretation call; a real schema prompt takes ~3s.
    assert observed[0] <= get_settings().ai_response_budget_seconds - 2.0


@pytest.mark.anyio
async def test_async_provider_deadline_reaches_fallback_even_when_primary_thread_stalls(
    monkeypatch,
):
    import asyncio
    import threading

    from app.core.config import get_settings
    from app.modules.ai import llm

    monkeypatch.setenv("AI_LLM_TIMEOUT_SECONDS", "0.05")
    get_settings.cache_clear()
    release = threading.Event()

    client = CommercialClient(
        api_key="test", model="primary", base_url=BASE_URL, fallback_model="fallback"
    )

    def stalled_post(model, prompt):
        if model == "fallback":
            return "SELECT 1 FROM vw_ai_kho_ton"
        release.wait(2)
        return "late primary answer"

    monkeypatch.setattr(client, "_post", stalled_post)
    try:
        result = await asyncio.wait_for(llm.complete_async(client, "question"), timeout=0.5)
        assert result == "SELECT 1 FROM vw_ai_kho_ton"
    finally:
        release.set()


def test_the_stable_prompt_prefix_is_marked_for_the_prompt_cache() -> None:
    from app.modules.ai.llm import CACHE_BREAKPOINT

    captured: dict = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        captured.update(json.loads(request.content))
        return _json_response(200, _message("SELECT 1"))

    _client(handler).complete(f"lược đồ{CACHE_BREAKPOINT}câu hỏi")

    assert captured["messages"] == [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "lược đồ", "cache_control": {"type": "ephemeral"}},
                {"type": "text", "text": "câu hỏi"},
            ],
        }
    ]


@pytest.mark.anyio
async def test_clients_without_a_prompt_cache_never_see_the_breakpoint() -> None:
    from app.modules.ai import llm

    seen: list[str] = []

    class Recorder:
        def complete(self, prompt: str) -> str:
            seen.append(prompt)
            return "SELECT 1"

    await llm.complete_async(Recorder(), f"lược đồ{llm.CACHE_BREAKPOINT}câu hỏi")

    assert seen == ["lược đồcâu hỏi"]


def test_cached_prompt_tokens_are_counted_and_priced_separately() -> None:
    from app.modules.ai.usage import collect_usage

    def handler(_: httpx2.Request) -> httpx2.Response:
        payload = _message("SELECT 1")
        payload["usage"] = {
            "input_tokens": 100,
            "cache_creation_input_tokens": 1000,
            "cache_read_input_tokens": 3000,
            "output_tokens": 200,
        }
        return _json_response(200, payload)

    with collect_usage(
        input_price=4.0, output_price=20.0, cache_write_price=5.0, cache_read_price=0.2
    ) as usage:
        _client(handler).complete("q")

    assert usage.input_tokens == 4100
    assert usage.cost_complete
    # 100*4 + 1000*5 + 3000*0.2 + 200*20 = 10_000 per million
    assert usage.cost_usd == pytest.approx(0.01)
