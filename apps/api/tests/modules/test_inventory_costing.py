"""Monthly weighted average costing close."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.catalog.models import Ingredient
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from tests.helpers import FIXED_NOW


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(session, role="MANAGER", username="mgr_cost"):
    await seed_reference_data(session)
    from sqlalchemy import select as sel

    r = await session.execute(sel(User).where(User.username == username))
    u = r.scalar_one_or_none()
    if u is None:
        u = User(
            username=username,
            password_hash=hash_password("pass"),
            full_name=username,
            role_id=role,
            status="Hoạt động",
        )
        session.add(u)
        await session.flush()
        await session.commit()
    tok = create_access_token(str(u.id), {"role": u.role_id, "username": u.username})
    return {"Authorization": f"Bearer {tok}"}, u


async def _ingredient(session, name="NL Cost"):
    ing = Ingredient(name=name, unit="kg", min_stock=0, stock_qty=0, is_deleted=False)
    session.add(ing)
    await session.flush()
    await session.commit()
    return ing


@pytest.mark.anyio
async def test_close_month_computes_weighted_average(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    # Two receipts in the same (frozen) business month at different unit prices.
    await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 10, "unit_price": 1000}]},
        headers=h,
    )
    await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 10, "unit_price": 2000}]},
        headers=h,
    )
    month = FIXED_NOW.year * 100 + FIXED_NOW.month
    r = await client.post(f"/api/v1/inventory/costing/{month}/close", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    row = next(x for x in body if x["MaNguyenLieu"] == ing.id)
    # (10*1000 + 10*2000) / 20 = 1500
    assert row["GiaBinhQuan"] == 1500
    assert row["TongSoLuongNhap"] == 20


@pytest.mark.anyio
async def test_close_month_rejects_invalid_month(session):
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post("/api/v1/inventory/costing/202513/close", headers=h)
    assert r.status_code == 422


@pytest.mark.anyio
async def test_close_month_requires_manager(session):
    client = await _make_client(session)
    h, _ = await _headers(session, role="WAREHOUSE", username="kho_cost")
    month = FIXED_NOW.year * 100 + FIXED_NOW.month
    r = await client.post(f"/api/v1/inventory/costing/{month}/close", headers=h)
    assert r.status_code == 403


@pytest.mark.anyio
async def test_closing_a_month_prices_its_write_offs_and_is_audited(session):
    """FR-REP-05b: waste stays at cost 0 ("tạm tính") until the month is closed.

    Closing through the API must also backfill the write-offs, otherwise the
    provisional label on the cost report never clears.
    """
    from sqlalchemy import select as sel

    from app.modules.inventory.models import StockIssueLine
    from app.shared.audit import SystemAuditLog

    ing = await _ingredient(session, "NL hao hụt cần chốt")
    client = await _make_client(session)
    h, manager = await _headers(session)
    await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 10, "unit_price": 1500}]},
        headers=h,
    )
    issued = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 2}]},
        headers=h,
    )
    assert issued.status_code == 201, issued.text

    month = FIXED_NOW.year * 100 + FIXED_NOW.month
    r = await client.post(f"/api/v1/inventory/costing/{month}/close", headers=h)

    assert r.status_code == 200, r.text
    line = (
        await session.execute(sel(StockIssueLine).where(StockIssueLine.ingredient_id == ing.id))
    ).scalar_one()
    await session.refresh(line)
    assert line.estimated_cost == 3000
    audit = (
        await session.execute(
            sel(SystemAuditLog).where(SystemAuditLog.action == "CLOSE_COSTING_MONTH")
        )
    ).scalar_one()
    assert audit.user_id == manager.id
    assert audit.target_id == str(month)
