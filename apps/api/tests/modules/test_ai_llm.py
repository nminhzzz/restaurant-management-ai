"""DeepSeek-compatible commercial client: request shape, fence stripping, and the
runtime fallback model (report §1.4.2, §4.1.1). No real network — every request goes
through `httpx.MockTransport`.
"""

import json

import httpx
import pytest

from app.modules.ai.llm import CommercialClient


def _json_response(status_code: int, payload: dict) -> httpx.Response:
    return httpx.Response(status_code, json=payload)


def _completion(content: str, model: str = "deepseek-flash") -> dict:
    return {
        "id": "1",
        "object": "chat.completion",
        "model": model,
        "choices": [{"message": {"role": "assistant", "content": content}}],
    }


def test_sends_the_expected_request_body() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers["authorization"]
        captured["json"] = json.loads(request.content)
        return _json_response(200, _completion("SELECT 1"))

    client = CommercialClient(
        api_key="secret",
        model="deepseek-flash",
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    )

    result = client.complete("hỏi gì đó")

    assert result == "SELECT 1"
    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["auth"] == "Bearer secret"
    assert captured["json"] == {
        "model": "deepseek-flash",
        "messages": [{"role": "user", "content": "hỏi gì đó"}],
        "temperature": 0,
    }


def test_strips_a_code_fence_around_the_sql() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return _json_response(200, _completion("```sql\nSELECT 1\n```"))

    client = CommercialClient(
        api_key="k",
        model="deepseek-flash",
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    )

    assert client.complete("q") == "SELECT 1"


def test_only_content_is_used_never_reasoning_content() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        payload = _completion("SELECT 1", model="deepseek-v4-pro")
        payload["choices"][0]["message"]["reasoning_content"] = "vì bảng này..."
        return _json_response(200, payload)

    client = CommercialClient(
        api_key="k",
        model="deepseek-v4-pro",
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    )

    assert client.complete("q") == "SELECT 1"


@pytest.mark.parametrize(
    "make_response",
    [
        lambda: _json_response(500, {"error": "boom"}),
        lambda: _json_response(429, {"error": "rate limited"}),
        lambda: (_ for _ in ()).throw(httpx.ConnectTimeout("timed out")),
    ],
)
def test_retries_once_on_the_fallback_model_after_a_retryable_error(make_response) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        model = json.loads(request.content)["model"]
        calls.append(model)
        if model == "deepseek-flash":
            response = make_response()
            if isinstance(response, httpx.Response):
                return response
            raise response
        return _json_response(200, _completion("SELECT 1", model=model))

    client = CommercialClient(
        api_key="k",
        model="deepseek-flash",
        base_url="https://api.deepseek.com",
        fallback_model="deepseek-v4-pro",
        transport=httpx.MockTransport(handler),
    )

    result = client.complete("q")

    assert result == "SELECT 1"
    assert calls == ["deepseek-flash", "deepseek-v4-pro"]


def test_never_retries_on_a_4xx_auth_or_validation_error() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(json.loads(request.content)["model"])
        return _json_response(401, {"error": "invalid api key"})

    client = CommercialClient(
        api_key="bad",
        model="deepseek-flash",
        base_url="https://api.deepseek.com",
        fallback_model="deepseek-v4-pro",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(httpx.HTTPStatusError):
        client.complete("q")

    assert calls == ["deepseek-flash"]


def test_no_fallback_configured_raises_the_original_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return _json_response(500, {"error": "boom"})

    client = CommercialClient(
        api_key="k",
        model="deepseek-flash",
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(httpx.HTTPStatusError):
        client.complete("q")


def test_fallback_equal_to_primary_model_is_never_retried() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(json.loads(request.content)["model"])
        return _json_response(500, {"error": "boom"})

    client = CommercialClient(
        api_key="k",
        model="deepseek-flash",
        base_url="https://api.deepseek.com",
        fallback_model="deepseek-flash",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(httpx.HTTPStatusError):
        client.complete("q")

    assert calls == ["deepseek-flash"]


def _capture_body(client_kwargs: dict) -> dict:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return _json_response(200, _completion("SELECT 1"))

    client = CommercialClient(
        api_key="secret",
        model="deepseek-flash",
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
        **client_kwargs,
    )
    client.complete("sinh SQL")
    return captured


def test_a_reasoning_effort_is_sent_when_configured() -> None:
    """DeepSeek models think at "high" by default, which blows the 8s budget (NFR-02)."""
    assert _capture_body({"reasoning_effort": "low"})["reasoning_effort"] == "low"


def test_no_reasoning_effort_is_sent_by_default() -> None:
    """OpenAI-style models reject unknown parameters, so the field stays opt-in."""
    assert "reasoning_effort" not in _capture_body({})
