"""Config tests FR-SET-04/05."""

from datetime import date, datetime, time

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.settings.models import SystemConfig, User
from app.modules.settings.service import seed_reference_data
from app.shared.audit import SystemAuditLog
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
async def test_seed_config_has_report_defaults(session):
    await seed_reference_data(session)
    cfg = (await session.execute(select(SystemConfig))).scalar_one()
    assert cfg.business_day_start == time(6)
    assert cfg.pending_business_day_start is None
    assert cfg.pending_business_day_effective_date is None
    assert cfg.expiry_warning_days == 3
    assert cfg.ai_daily_question_quota == 50
    assert cfg.reservation_hold_minutes == 5


@pytest.mark.asyncio
async def test_manager_schedules_new_hour_and_audits_complete_snapshots(session, monkeypatch):
    from app.modules.settings import service

    monkeypatch.setattr(service, "now", lambda: datetime(2026, 10, 11, 9))
    client, token = await _mgr(session)
    async with client:
        response = await client.put(
            "/api/v1/settings/config",
            json={
                "GioBatDauBusinessDateMoi": "07:30",
                "SoNgayCanhBaoHetHan": 4,
                "SoCauHoiAIMoiNgay": 75,
                "ThoiGianGiuChoPhut": 8,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["GioBatDauBusinessDate"] == "06:00:00"
    assert body["GioBatDauBusinessDateMoi"] == "07:30:00"
    assert body["NgayHieuLucGioMoi"] == "2026-10-12"
    assert (body["SoNgayCanhBaoHetHan"], body["SoCauHoiAIMoiNgay"], body["ThoiGianGiuChoPhut"]) == (
        4,
        75,
        8,
    )
    audit = (
        await session.execute(
            select(SystemAuditLog).where(SystemAuditLog.action == "UPDATE_CONFIG")
        )
    ).scalar_one()
    assert audit.before["GioBatDauBusinessDate"] == "06:00:00"
    assert audit.before["GioBatDauBusinessDateMoi"] is None
    assert audit.before["NgayHieuLucGioMoi"] is None
    assert audit.after["GioBatDauBusinessDateMoi"] == "07:30:00"
    assert audit.after["NgayHieuLucGioMoi"] == date(2026, 10, 12).isoformat()
    assert audit.before["SoCauHoiAIMoiNgay"] == 50
    assert audit.after["SoCauHoiAIMoiNgay"] == 75


@pytest.mark.asyncio
async def test_earlier_hour_does_not_activate_during_current_business_date(session, monkeypatch):
    from app.modules.settings import service

    current = datetime(2026, 10, 11, 5, 30)
    monkeypatch.setattr(service, "now", lambda: current)
    client, token = await _mgr(session)
    async with client:
        response = await client.put(
            "/api/v1/settings/config",
            json={"GioBatDauBusinessDateMoi": "04:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["GioBatDauBusinessDate"] == "06:00:00"
    assert body["GioBatDauBusinessDateMoi"] == "04:00:00"
    assert body["NgayHieuLucGioMoi"] == "2026-10-12"
    assert datetime.combine(date.fromisoformat(body["NgayHieuLucGioMoi"]), time(4)) > current


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field", ["SoNgayCanhBaoHetHan", "SoCauHoiAIMoiNgay", "ThoiGianGiuChoPhut"]
)
async def test_runtime_settings_must_be_positive(session, field):
    client, token = await _mgr(session)
    async with client:
        response = await client.put(
            "/api/v1/settings/config",
            json={field: 0},
            headers={"Authorization": f"Bearer {token}"},
        )
    app.dependency_overrides.clear()
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_partial_runtime_update_preserves_existing_address(session):
    client, token = await _mgr(session)
    headers = {"Authorization": f"Bearer {token}"}
    async with client:
        first = await client.put(
            "/api/v1/settings/config", json={"DiaChi": "123 Đường A"}, headers=headers
        )
        second = await client.put(
            "/api/v1/settings/config", json={"SoCauHoiAIMoiNgay": 51}, headers=headers
        )
    app.dependency_overrides.clear()
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["DiaChi"] == "123 Đường A"
    assert second.json()["SoCauHoiAIMoiNgay"] == 51


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
