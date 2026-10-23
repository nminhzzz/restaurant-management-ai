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
async def test_the_business_day_start_is_scheduled_for_the_next_business_date(session):
    client, token = await _mgr(session)
    async with client:
        updated = await client.put(
            "/api/v1/settings/config",
            json={"GioBatDauBusinessDate": "08:15"},
            headers={"Authorization": f"Bearer {token}"},
        )
        cfg = await client.get(
            "/api/v1/settings/config", headers={"Authorization": f"Bearer {token}"}
        )
    app.dependency_overrides.clear()
    assert updated.status_code == 200
    assert cfg.json()["GioBatDauBusinessDate"] == "06:00:00"
    assert cfg.json()["GioBatDauBusinessDateMoi"] == "08:15:00"
    assert cfg.json()["NgayHieuLucGioMoi"] is not None


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


@pytest.mark.asyncio
async def test_operational_fields_are_saved_and_returned(session):
    """FR-SET-04: expiry warning, hold minutes and the per-user AI quota."""
    client, token = await _mgr(session)
    async with client:
        updated = await client.put(
            "/api/v1/settings/config",
            json={
                "SoNgayCanhBaoHetHan": 2,
                "ThoiGianGiuChoPhut": 7,
                "SoCauHoiAIMoiNgay": 40,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        reloaded = await client.get(
            "/api/v1/settings/config", headers={"Authorization": f"Bearer {token}"}
        )
    app.dependency_overrides.clear()
    assert updated.status_code == 200
    assert updated.json()["SoNgayCanhBaoHetHan"] == 2
    assert updated.json()["ThoiGianGiuChoPhut"] == 7
    assert updated.json()["SoCauHoiAIMoiNgay"] == 40
    assert reloaded.json()["SoCauHoiAIMoiNgay"] == 40


@pytest.mark.asyncio
async def test_operational_fields_reject_out_of_range_values(session):
    client, token = await _mgr(session)
    async with client:
        zero_hold = await client.put(
            "/api/v1/settings/config",
            json={"ThoiGianGiuChoPhut": 0},
            headers={"Authorization": f"Bearer {token}"},
        )
        negative_quota = await client.put(
            "/api/v1/settings/config",
            json={"SoCauHoiAIMoiNgay": -1},
            headers={"Authorization": f"Bearer {token}"},
        )
    app.dependency_overrides.clear()
    assert zero_hold.status_code == 422
    assert negative_quota.status_code == 422


@pytest.mark.asyncio
async def test_expiry_warning_days_must_be_positive(session):
    client, token = await _mgr(session)
    async with client:
        response = await client.put(
            "/api/v1/settings/config",
            json={"SoNgayCanhBaoHetHan": 0},
            headers={"Authorization": f"Bearer {token}"},
        )
    app.dependency_overrides.clear()
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_cutoff_change_before_old_boundary_cannot_start_in_the_past(session, monkeypatch):
    from datetime import date, datetime, time

    from app.modules.settings import service
    from app.shared import business_date

    await seed_reference_data(session)
    monkeypatch.setattr(business_date, "now", lambda: datetime(2026, 10, 1, 5))
    await service.update_config(session, None, {"GioBatDauBusinessDate": "04:30"})
    changes = await business_date.load_business_date_schedule(session)
    with business_date.business_date_schedule(changes):
        assert business_date.business_date_of(datetime(2026, 10, 1, 5)) == date(2026, 9, 30)
        assert business_date.business_date_start(date(2026, 10, 1)) == datetime(2026, 10, 1, 6)
        assert business_date.cutoff_for(date(2026, 10, 2)) == time(4, 30)
    await service.update_config(session, None, {"GioBatDauBusinessDate": "03:15"})
    changes = await business_date.load_business_date_schedule(session)
    with business_date.business_date_schedule(changes):
        assert business_date.business_date_start(date(2026, 10, 1)) == datetime(2026, 10, 1, 6)


@pytest.mark.asyncio
async def test_editing_a_delayed_pending_cutoff_never_reclassifies_current_day(
    session, monkeypatch
):
    from datetime import date, datetime

    from app.modules.settings import service
    from app.shared import business_date

    await seed_reference_data(session)
    monkeypatch.setattr(business_date, "now", lambda: datetime(2026, 9, 30, 22))
    await service.update_config(session, None, {"GioBatDauBusinessDate": "08:15"})
    monkeypatch.setattr(business_date, "now", lambda: datetime(2026, 10, 1, 7))
    for cutoff in ("04:30", "06:00"):
        await service.update_config(session, None, {"GioBatDauBusinessDate": cutoff})
        changes = await business_date.load_business_date_schedule(session)
        with business_date.business_date_schedule(changes):
            assert business_date.business_date_of(datetime(2026, 10, 1, 7)) == date(2026, 9, 30)
            assert business_date.business_date_start(date(2026, 10, 1)) == datetime(
                2026, 10, 1, 8, 15
            )
