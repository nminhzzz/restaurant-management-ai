"""Audit log FR-SET-08/09."""

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
async def test_only_a_manager_can_read_the_audit_log(session):
    await seed_reference_data(session)
    cash = User(
        username="thungan01",
        password_hash=hash_password("pass123"),
        full_name="TN",
        role_id=Role.CASHIER.value,
        status="Ho\u1ea1t \u0111\u1ed9ng",
    )
    wh = User(
        username="kho01",
        password_hash=hash_password("pass123"),
        full_name="Kho",
        role_id=Role.WAREHOUSE.value,
        status="Ho\u1ea1t \u0111\u1ed9ng",
    )
    mgr = User(
        username="quanly01",
        password_hash=hash_password("pass123"),
        full_name="QL",
        role_id=Role.MANAGER.value,
        status="Ho\u1ea1t \u0111\u1ed9ng",
    )
    session.add_all([cash, wh, mgr])
    await session.flush()
    await session.commit()
    cash_tok = create_access_token(str(cash.id), {"role": cash.role_id, "username": cash.username})
    wh_tok = create_access_token(str(wh.id), {"role": wh.role_id, "username": wh.username})
    mgr_tok = create_access_token(str(mgr.id), {"role": mgr.role_id, "username": mgr.username})

    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    async with client:
        assert (
            await client.get(
                "/api/v1/settings/audit-log", headers={"Authorization": f"Bearer {cash_tok}"}
            )
        ).status_code == 403
        assert (
            await client.get(
                "/api/v1/settings/audit-log", headers={"Authorization": f"Bearer {wh_tok}"}
            )
        ).status_code == 403
        assert (
            await client.get(
                "/api/v1/settings/audit-log", headers={"Authorization": f"Bearer {mgr_tok}"}
            )
        ).status_code == 200
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_the_log_cannot_be_edited_or_deleted(session):
    client, token = await _mgr(session)
    async with client:
        deleted = await client.delete(
            "/api/v1/settings/audit-log/1", headers={"Authorization": f"Bearer {token}"}
        )
        patched = await client.patch(
            "/api/v1/settings/audit-log/1", headers={"Authorization": f"Bearer {token}"}
        )
    app.dependency_overrides.clear()
    assert deleted.status_code in (404, 405)
    assert patched.status_code in (404, 405)
