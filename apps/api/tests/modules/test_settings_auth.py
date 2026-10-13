"""Auth tests FR-SET-02."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.core.database import get_session
from app.main import app
from app.modules.settings.models import SystemConfig


def _client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_login_returns_a_token_for_an_active_account(session, active_user):
    async with _client(session) as client:
        resp = await client.post(
            "/api/v1/settings/auth/login",
            json={"username": "thungan01", "password": "mat-khau-dung"},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 200, resp.text
    assert resp.json()["role"] == "CASHIER"
    assert "MatKhauHash" not in resp.text


@pytest.mark.asyncio
async def test_locked_account_cannot_log_in(session, locked_user):
    async with _client(session) as client:
        resp = await client.post(
            "/api/v1/settings/auth/login",
            json={"username": "thungan01", "password": "mat-khau-dung"},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.asyncio
async def test_wrong_password_is_rejected_without_revealing_which_field_failed(
    session, active_user
):
    async with _client(session) as client:
        resp = await client.post(
            "/api/v1/settings/auth/login",
            json={"username": "thungan01", "password": "sai-mat-khau"},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 401
    assert (
        resp.json()["error"]["message"]
        == "T\u00ean \u0111\u0103ng nh\u1eadp ho\u1eb7c m\u1eadt kh\u1ea9u kh\u00f4ng \u0111\u00fang."
    )


@pytest.mark.asyncio
async def test_reference_data_can_be_seeded_twice(session):
    from app.modules.settings.service import seed_reference_data
    from tests.helpers import config_count, role_count

    await session.execute(delete(SystemConfig))
    assert await config_count(session) == 0
    await seed_reference_data(session)
    await session.commit()
    first_id = (await session.execute(select(SystemConfig.id))).scalar_one()
    await seed_reference_data(session)
    await session.commit()
    assert await role_count(session) == 3
    assert await config_count(session) == 1
    assert (await session.execute(select(SystemConfig.id))).scalar_one() == first_id


@pytest.mark.anyio
async def test_login_spends_a_password_check_even_for_unknown_or_locked_accounts(
    session, locked_user, monkeypatch
):
    from app.core.errors import UnauthenticatedError
    from app.modules.settings import service

    checks: list[str] = []
    real = service.verify_password

    def counting(plain: str, hashed: str) -> bool:
        checks.append(hashed)
        return real(plain, hashed)

    monkeypatch.setattr(service, "verify_password", counting)

    for username in ("nobody-here", locked_user.username):
        with pytest.raises(UnauthenticatedError):
            await service.authenticate(session, username, "Whatever-123")

    assert len(checks) == 2
