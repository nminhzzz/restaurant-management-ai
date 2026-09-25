"""NFR-15: unexpected errors are logged with enough context to investigate them,
while the user sees a Vietnamese message and never the internals (rule 5)."""

import logging

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.errors import BusinessRuleError, register_error_handlers


def _app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.post("/boom")
    async def boom(payload: dict) -> dict:
        raise RuntimeError("database exploded at host db-internal:3306")

    @app.post("/rule")
    async def rule(payload: dict) -> dict:
        raise BusinessRuleError("Chỉ sửa món ở trạng thái Chờ.")

    return app


def _client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.anyio
async def test_an_unexpected_error_is_logged_with_operation_and_input(caplog):
    caplog.set_level(logging.ERROR, logger="app.errors")

    async with _client(_app()) as client:
        response = await client.post("/boom?table=5", json={"MaBan": 5, "password": "bí-mật-123"})

    record = next(r for r in caplog.records if r.name == "app.errors")
    logged = record.getMessage()
    assert "POST /boom" in logged
    assert "table=5" in logged
    assert '"MaBan": 5' in logged
    assert "bí-mật-123" not in logged
    assert record.exc_info is not None
    assert response.json()["error"]["error_id"] in logged


@pytest.mark.anyio
async def test_the_user_gets_a_vietnamese_message_without_internals():
    async with _client(_app()) as client:
        response = await client.post("/boom", json={})

    assert response.status_code == 500
    body = response.json()["error"]
    assert body["code"] == "INTERNAL_ERROR"
    assert "Hệ thống gặp lỗi" in body["message"]
    assert "db-internal" not in response.text
    assert "Traceback" not in response.text


@pytest.mark.anyio
async def test_a_business_rule_violation_is_logged_as_a_warning(caplog):
    caplog.set_level(logging.WARNING, logger="app.errors")

    async with _client(_app()) as client:
        response = await client.post("/rule", json={"MaChiTietOrder": 9})

    assert response.status_code == 422
    record = next(r for r in caplog.records if r.name == "app.errors")
    assert record.levelno == logging.WARNING
    assert "BUSINESS_RULE_VIOLATION" in record.getMessage()
    assert "POST /rule" in record.getMessage()
