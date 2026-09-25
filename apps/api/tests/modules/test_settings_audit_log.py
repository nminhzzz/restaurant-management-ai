"""Audit log FR-SET-08/09."""

from datetime import UTC, datetime

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


@pytest.mark.asyncio
async def test_the_target_filter_narrows_to_that_entity(session):
    client, token = await _mgr(session)
    async with client:
        created = await client.post(
            "/api/v1/settings/users",
            json={
                "username": "moi01",
                "password": "pass123",
                "full_name": "Moi",
                "role": "CASHIER",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert created.status_code == 201

        all_entries = await client.get(
            "/api/v1/settings/audit-log", headers={"Authorization": f"Bearer {token}"}
        )
        user_entries = await client.get(
            "/api/v1/settings/audit-log?target=NGUOI_DUNG",
            headers={"Authorization": f"Bearer {token}"},
        )
        other_entries = await client.get(
            "/api/v1/settings/audit-log?target=SYSTEM",
            headers={"Authorization": f"Bearer {token}"},
        )
    app.dependency_overrides.clear()
    assert all_entries.status_code == 200
    assert user_entries.status_code == 200
    assert other_entries.status_code == 200
    assert user_entries.json()["total"] >= 1
    assert all(item["DoiTuong"] == "NGUOI_DUNG" for item in user_entries.json()["items"])
    assert other_entries.json()["total"] == 0


@pytest.mark.asyncio
async def test_the_date_range_filter_narrows_by_occurred_at(session):
    client, token = await _mgr(session)
    async with client:
        created = await client.post(
            "/api/v1/settings/users",
            json={
                "username": "moi01",
                "password": "pass123",
                "full_name": "Moi",
                "role": "CASHIER",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert created.status_code == 201

        today = datetime.now(UTC).date().isoformat()
        in_range = await client.get(
            f"/api/v1/settings/audit-log?date_from={today}&date_to={today}",
            headers={"Authorization": f"Bearer {token}"},
        )
        out_of_range = await client.get(
            "/api/v1/settings/audit-log?date_from=2000-01-01&date_to=2000-01-02",
            headers={"Authorization": f"Bearer {token}"},
        )
    app.dependency_overrides.clear()
    assert in_range.status_code == 200
    assert in_range.json()["total"] >= 1
    assert out_of_range.status_code == 200
    assert out_of_range.json()["total"] == 0


@pytest.mark.asyncio
async def test_a_malformed_date_range_is_rejected(session):
    client, token = await _mgr(session)
    async with client:
        resp = await client.get(
            "/api/v1/settings/audit-log?date_from=not-a-date",
            headers={"Authorization": f"Bearer {token}"},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_the_actions_endpoint_lists_distinct_action_codes_for_managers_only(session):
    client, token = await _mgr(session)
    async with client:
        created = await client.post(
            "/api/v1/settings/users",
            json={
                "username": "moi01",
                "password": "pass123",
                "full_name": "Moi",
                "role": "CASHIER",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert created.status_code == 201

        resp = await client.get(
            "/api/v1/settings/audit-log/actions",
            headers={"Authorization": f"Bearer {token}"},
        )
        cash = User(
            username="thungan02",
            password_hash=hash_password("pass123"),
            full_name="TN",
            role_id=Role.CASHIER.value,
            status="Hoạt động",
        )
        session.add(cash)
        await session.flush()
        await session.commit()
        cash_tok = create_access_token(
            str(cash.id), {"role": cash.role_id, "username": cash.username}
        )
        forbidden = await client.get(
            "/api/v1/settings/audit-log/actions",
            headers={"Authorization": f"Bearer {cash_tok}"},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert "CREATE_USER" in resp.json()
    assert forbidden.status_code == 403
