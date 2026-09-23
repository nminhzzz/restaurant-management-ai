"""Accounts tests FR-SET-01/03/06 NFR-10."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import get_session
from app.core.security import hash_password
from app.main import app
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _login(client, username, password):
    return await client.post(
        "/api/v1/settings/auth/login", json={"username": username, "password": password}
    )


async def _auth_client(session, username="thungan01", password="mat-khau-dung"):
    c = await _make_client(session)
    # Actually need to login to get token, but we can use create_access_token directly for manager
    from app.core.security import create_access_token

    # Get user id
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user:
        token = create_access_token(str(user.id), {"role": user.role_id, "username": user.username})
        return c, token
    return c, None


@pytest.mark.asyncio
async def test_only_a_manager_may_create_accounts(session):
    from app.core.security import create_access_token
    from app.shared.roles import Role

    # Seed and create manager + cashier
    await seed_reference_data(session)
    mgr = User(
        username="quanly01",
        password_hash=hash_password("pass123"),
        full_name="QL",
        role_id=Role.MANAGER.value,
        status="Ho\u1ea1t \u0111\u1ed9ng",
    )
    cash = User(
        username="thungan01",
        password_hash=hash_password("pass123"),
        full_name="TN",
        role_id=Role.CASHIER.value,
        status="Ho\u1ea1t \u0111\u1ed9ng",
    )
    session.add_all([mgr, cash])
    await session.flush()
    await session.commit()
    mgr_token = create_access_token(str(mgr.id), {"role": mgr.role_id, "username": mgr.username})
    cash_token = create_access_token(
        str(cash.id), {"role": cash.role_id, "username": cash.username}
    )

    async with await _make_client(session) as client:
        forbidden = await client.post(
            "/api/v1/settings/users",
            json={
                "username": "moi01",
                "password": "pass123",
                "full_name": "Moi",
                "role": "CASHIER",
            },
            headers={"Authorization": f"Bearer {cash_token}"},
        )
        allowed = await client.post(
            "/api/v1/settings/users",
            json={
                "username": "moi01",
                "password": "pass123",
                "full_name": "Moi",
                "role": "CASHIER",
            },
            headers={"Authorization": f"Bearer {mgr_token}"},
        )
    app.dependency_overrides.clear()
    assert forbidden.status_code == 403
    assert allowed.status_code == 201


@pytest.mark.asyncio
async def test_account_creation_is_audited(session):
    from app.core.security import create_access_token
    from app.shared.roles import Role
    from tests.helpers import latest_audit

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
    async with await _make_client(session) as client:
        resp = await client.post(
            "/api/v1/settings/users",
            json={
                "username": "moi01",
                "password": "pass123",
                "full_name": "Moi",
                "role": "CASHIER",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 201
    entry = await latest_audit(session)
    assert entry is not None
    assert entry["LoaiThaoTac"] == "CREATE_USER"


@pytest.mark.asyncio
async def test_a_user_is_given_exactly_one_of_the_three_roles(session):
    from app.core.security import create_access_token
    from app.shared.roles import Role

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
    async with await _make_client(session) as client:
        ok = await client.post(
            "/api/v1/settings/users",
            json={"username": "a01", "password": "pass123", "full_name": "A", "role": "CASHIER"},
            headers={"Authorization": f"Bearer {token}"},
        )
        bad = await client.post(
            "/api/v1/settings/users",
            json={"username": "a02", "password": "pass123", "full_name": "A", "role": "BEP"},
            headers={"Authorization": f"Bearer {token}"},
        )
    app.dependency_overrides.clear()
    assert ok.status_code == 201
    assert bad.status_code in (400, 422)
