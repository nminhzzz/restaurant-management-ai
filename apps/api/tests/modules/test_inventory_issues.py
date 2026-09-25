"""FR-INV-05/06 — manual stock issues, FIFO draw."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.catalog.models import Ingredient
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from tests.helpers import lot_total, movements_for


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(session, role="WAREHOUSE", username="kho02"):
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


async def _ingredient(session, name="Thịt bò", stock_qty=0):
    ing = Ingredient(name=name, unit="kg", min_stock=0, stock_qty=stock_qty, is_deleted=False)
    session.add(ing)
    await session.flush()
    await session.commit()
    return ing


async def _receipt(session, client, headers, ing, qty, unit_price=1000):
    r = await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": qty, "unit_price": unit_price}]},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["MaPhieuNhap"]


@pytest.mark.anyio
async def test_manual_issue_decreases_stock(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 10)
    r = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 4}]},
        headers=h,
    )
    assert r.status_code == 201, r.text
    await session.refresh(ing)
    assert float(ing.stock_qty) == 6
    assert await lot_total(session, ing.id) == 6


@pytest.mark.anyio
async def test_manual_issue_draws_oldest_lot_first(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 5, unit_price=1000)
    await _receipt(session, client, h, ing, 5, unit_price=2000)
    r = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 3}]},
        headers=h,
    )
    assert r.status_code == 201, r.text
    from sqlalchemy import select as sel

    from app.modules.inventory.models import IngredientLot

    lots = (
        (await session.execute(sel(IngredientLot).where(IngredientLot.ingredient_id == ing.id)))
        .scalars()
        .all()
    )
    lots.sort(key=lambda x: x.received_at)
    assert float(lots[0].quantity_remaining) == 2  # first lot drawn down 5 -> 2
    assert float(lots[1].quantity_remaining) == 5  # second lot untouched


@pytest.mark.anyio
async def test_manual_issue_refused_when_it_would_go_negative(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 2)
    r = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 5}]},
        headers=h,
    )
    assert r.status_code == 422
    await session.refresh(ing)
    assert float(ing.stock_qty) == 2


@pytest.mark.anyio
async def test_manual_issue_records_ledger_movement(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 5)
    await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hỏng", "lines": [{"ingredient_id": ing.id, "quantity": 1}]},
        headers=h,
    )
    moves = await movements_for(session, ing.id)
    kinds = [m["LoaiGiaoDich"] for m in moves]
    assert "Xuất thủ công" in kinds


@pytest.mark.anyio
async def test_list_issues(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 5)
    await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 1}]},
        headers=h,
    )
    r = await client.get("/api/v1/inventory/issues", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["LyDo"] == "Hao hụt"


@pytest.mark.anyio
async def test_list_issues_filters_by_reason_and_date_range(session):
    from datetime import date, timedelta

    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 5)
    await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 1}]},
        headers=h,
    )
    await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hỏng", "lines": [{"ingredient_id": ing.id, "quantity": 1}]},
        headers=h,
    )

    by_reason = await client.get("/api/v1/inventory/issues?reason=Hỏng", headers=h)
    assert by_reason.status_code == 200
    assert by_reason.json()["total"] == 1
    assert by_reason.json()["items"][0]["LyDo"] == "Hỏng"

    tomorrow = date.today() + timedelta(days=1)
    out_of_range = await client.get(
        f"/api/v1/inventory/issues?date_from={tomorrow.isoformat()}&date_to={tomorrow.isoformat()}",
        headers=h,
    )
    assert out_of_range.json()["total"] == 0


@pytest.mark.anyio
async def test_list_issues_rejects_a_malformed_date(session):
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.get("/api/v1/inventory/issues?date_from=25-09-2026", headers=h)
    assert r.status_code == 422


@pytest.mark.anyio
async def test_list_issues_total_reflects_all_rows_across_pages(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 10)
    for _ in range(3):
        await client.post(
            "/api/v1/inventory/issues",
            json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 1}]},
            headers=h,
        )
    r = await client.get("/api/v1/inventory/issues?page=1&page_size=2", headers=h)
    body = r.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
