"""Config tests FR-SET-04/05."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from app.shared.roles import Role


async def _mgr(session):
    await seed_reference_data(session)
    mgr = User(
        username="quanly01",
        password_hash=hash_password("pass123"),
        full_name="QL",
        role_id=Role.MANAGER.value,
        status="Ho\u1ea1t \u0111\u1ed9ng",
    )
    session.add(mgr)
    await session.flush()
    await session.commit()
    token = create_access_token(str(mgr.id), {"role": mgr.role_id, "username": mgr.username})

    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test"), token


@pytest.mark.asyncio
async def test_config_is_a_singleton(session):
    client, token = await _mgr(session)
    async with client:
        first = await client.put(
            "/api/v1/settings/config",
            json={"TenNhaHang": "Qu\u00e1n A"},
            headers={"Authorization": f"Bearer {token}"},
        )
        second = await client.put(
            "/api/v1/settings/config",
            json={"TenNhaHang": "Qu\u00e1n B"},
            headers={"Authorization": f"Bearer {token}"},
        )
    app.dependency_overrides.clear()
    assert first.json()["MaCauHinh"] == second.json()["MaCauHinh"]


@pytest.mark.asyncio
async def test_the_business_day_start_cannot_be_edited_from_the_api(session):
    client, token = await _mgr(session)
    async with client:
        await client.put(
            "/api/v1/settings/config",
            json={"GioBatDauBusinessDate": "08:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        cfg = await client.get(
            "/api/v1/settings/config", headers={"Authorization": f"Bearer {token}"}
        )
    app.dependency_overrides.clear()
    assert cfg.json()["GioBatDauBusinessDate"] in ("06:00:00", "06:00")


@pytest.mark.asyncio
async def test_a_non_manager_cannot_read_the_config(session):
    await seed_reference_data(session)
    cash = User(
        username="thungan01",
        password_hash=hash_password("pass123"),
        full_name="TN",
        role_id=Role.CASHIER.value,
        status="Ho\u1ea1t \u0111\u1ed9ng",
    )
    session.add(cash)
    await session.flush()
    await session.commit()
    token = create_access_token(str(cash.id), {"role": cash.role_id, "username": cash.username})

    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    async with client:
        resp = await client.get(
            "/api/v1/settings/config", headers={"Authorization": f"Bearer {token}"}
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 403
