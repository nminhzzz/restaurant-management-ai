"""QD-01/QD-02: weighted average costing follows the ledger automatically."""

from datetime import timedelta

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


MONTH = FIXED_NOW.year * 100 + FIXED_NOW.month


async def _average(session, ingredient_id, month=MONTH):
    from sqlalchemy import select as sel

    from app.modules.inventory.models import MonthlyAverageCost

    session.expire_all()
    return (
        await session.execute(
            sel(MonthlyAverageCost).where(
                MonthlyAverageCost.ingredient_id == ingredient_id,
                MonthlyAverageCost.month == month,
            )
        )
    ).scalar_one_or_none()


async def _receive(client, headers, iid, qty, price, **extra):
    r = await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": iid, "quantity": qty, "unit_price": price}], **extra},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["MaPhieuNhap"]


@pytest.mark.anyio
async def test_the_average_follows_receipts_without_any_manual_close(session):
    ing = await _ingredient(session)
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 10, 1000)
    first = await _average(session, iid)
    assert first.avg_cost == 1000
    await _receive(client, h, iid, 10, 2000)
    row = await _average(session, iid)
    # (10*1000 + 10*2000) / 20 = 1500
    assert row.avg_cost == 1500
    assert row.total_qty == 20


@pytest.mark.anyio
async def test_the_manual_month_close_endpoint_no_longer_exists(session):
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(f"/api/v1/inventory/costing/{MONTH}/close", headers=h)
    assert r.status_code in (404, 405)


@pytest.mark.anyio
async def test_a_write_off_is_priced_as_soon_as_it_is_created(session):
    """FR-REP-05b: no month close is needed for the waste cost to be known."""
    from sqlalchemy import select as sel

    from app.modules.inventory.models import StockIssueLine

    ing = await _ingredient(session, "NL hao hụt")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 10, 1500)
    issued = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": iid, "quantity": 2}]},
        headers=h,
    )
    assert issued.status_code == 201, issued.text
    line = (
        await session.execute(sel(StockIssueLine).where(StockIssueLine.ingredient_id == iid))
    ).scalar_one()
    assert line.estimated_cost == 3000


@pytest.mark.anyio
async def test_a_cancelled_receipt_leaves_the_average_at_once(session):
    ing = await _ingredient(session, "NL phiếu hủy")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    cancelled = await _receive(client, h, iid, 10, 1000)
    await _receive(client, h, iid, 10, 2000)
    assert (await _average(session, iid)).avg_cost == 1500
    r = await client.delete(f"/api/v1/inventory/receipts/{cancelled}", headers=h)
    assert r.status_code == 200, r.text
    row = await _average(session, iid)
    assert row.avg_cost == 2000
    assert row.total_qty == 10


@pytest.mark.anyio
async def test_cancelling_the_only_receipt_removes_the_average(session):
    ing = await _ingredient(session, "NL chỉ một phiếu")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    only = await _receive(client, h, iid, 10, 1000)
    await client.delete(f"/api/v1/inventory/receipts/{only}", headers=h)
    assert await _average(session, iid) is None


@pytest.mark.anyio
async def test_editing_a_receipt_price_refreshes_the_average(session):
    from sqlalchemy import select as sel

    from app.modules.inventory.models import GoodsReceiptLine

    ing = await _ingredient(session, "NL sửa giá")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    receipt_id = await _receive(client, h, iid, 10, 1000)
    line = (
        await session.execute(
            sel(GoodsReceiptLine).where(GoodsReceiptLine.receipt_id == receipt_id)
        )
    ).scalar_one()
    r = await client.patch(
        f"/api/v1/inventory/receipts/{receipt_id}",
        json={"lines": [{"line_id": line.id, "quantity": 10, "unit_price": 1800}]},
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert (await _average(session, iid)).avg_cost == 1800


@pytest.mark.anyio
async def test_moving_a_receipt_to_another_month_recomputes_both_months(session):
    from sqlalchemy import select as sel

    from app.modules.inventory.models import GoodsReceiptLine, IngredientLot, StockMovement

    ing = await _ingredient(session, "NL đổi tháng")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    receipt_id = await _receive(client, h, iid, 10, 1000)
    assert (await _average(session, iid)).avg_cost == 1000
    earlier = FIXED_NOW - timedelta(days=40)
    earlier_month = earlier.year * 100 + earlier.month
    line = (
        await session.execute(
            sel(GoodsReceiptLine).where(GoodsReceiptLine.receipt_id == receipt_id)
        )
    ).scalar_one()
    line_id = line.id

    r = await client.patch(
        f"/api/v1/inventory/receipts/{receipt_id}",
        json={
            "receipt_date": earlier.isoformat(),
            "lines": [{"line_id": line_id, "quantity": 10, "unit_price": 1000}],
        },
        headers=h,
    )

    assert r.status_code == 200, r.text
    assert (await _average(session, iid, earlier_month)).avg_cost == 1000
    # The carried stock still prices the current month, now as opening value.
    assert (await _average(session, iid)).avg_cost == 1000
    lot = (
        await session.execute(sel(IngredientLot).where(IngredientLot.receipt_line_id == line_id))
    ).scalar_one()
    assert lot.received_at == earlier
    movement = (
        await session.execute(sel(StockMovement).where(StockMovement.receipt_line_id == line_id))
    ).scalar_one()
    assert movement.business_date == earlier.date()


@pytest.mark.anyio
async def test_a_stocktake_surplus_does_not_dilute_the_month_average(session):
    """The adjustment lot is a reconciliation document, not a purchase (FR-INV-09)."""
    from sqlalchemy import select as sel

    from app.modules.inventory.models import IngredientLot

    ing = await _ingredient(session, "NL kiểm kê dư")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 10, 1000)
    sid = (await client.post("/api/v1/inventory/stocktakes", headers=h)).json()["MaPhieuKiemKe"]
    await client.post(
        f"/api/v1/inventory/stocktakes/{sid}/counts",
        json=[{"ingredient_id": iid, "actual_qty": 15}],
        headers=h,
    )
    confirmed = await client.post(f"/api/v1/inventory/stocktakes/{sid}/confirm", headers=h)
    assert confirmed.status_code == 200, confirmed.text

    row = await _average(session, iid)
    assert row.avg_cost == 1000
    assert row.total_qty == 10
    lots = (
        (await session.execute(sel(IngredientLot).where(IngredientLot.ingredient_id == iid)))
        .scalars()
        .all()
    )
    # The surplus joins the existing lot, so it keeps that lot's purchase price.
    assert sum(lot.quantity_remaining for lot in lots) == 15
    assert all(lot.unit_price == 1000 for lot in lots)


@pytest.mark.anyio
async def test_a_surplus_without_any_price_basis_stays_unpriced_not_zero(session):
    from sqlalchemy import select as sel

    from app.modules.inventory.models import IngredientLot

    ing = await _ingredient(session, "NL chưa từng nhập")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    sid = (await client.post("/api/v1/inventory/stocktakes", headers=h)).json()["MaPhieuKiemKe"]
    await client.post(
        f"/api/v1/inventory/stocktakes/{sid}/counts",
        json=[{"ingredient_id": iid, "actual_qty": 3}],
        headers=h,
    )
    confirmed = await client.post(f"/api/v1/inventory/stocktakes/{sid}/confirm", headers=h)
    assert confirmed.status_code == 200, confirmed.text
    lot = (
        await session.execute(sel(IngredientLot).where(IngredientLot.ingredient_id == iid))
    ).scalar_one()
    assert lot.quantity_remaining == 3
    assert lot.unit_price is None
    assert await _average(session, iid) is None


@pytest.mark.anyio
async def test_a_write_off_with_no_basis_stays_unpriced_and_the_report_says_so(session):
    from sqlalchemy import select as sel

    from app.modules.inventory.models import StockIssueLine
    from app.modules.reports.queries import waste_cost

    ing = await _ingredient(session, "NL xuất không giá")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    # Stock exists only through a surplus count, so there is no purchase price anywhere.
    sid = (await client.post("/api/v1/inventory/stocktakes", headers=h)).json()["MaPhieuKiemKe"]
    await client.post(
        f"/api/v1/inventory/stocktakes/{sid}/counts",
        json=[{"ingredient_id": iid, "actual_qty": 5}],
        headers=h,
    )
    await client.post(f"/api/v1/inventory/stocktakes/{sid}/confirm", headers=h)
    issued = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": iid, "quantity": 2}]},
        headers=h,
    )
    assert issued.status_code == 201, issued.text
    line = (
        await session.execute(sel(StockIssueLine).where(StockIssueLine.ingredient_id == iid))
    ).scalar_one()
    assert line.estimated_cost is None
    _total, uncosted = await waste_cost(session, MONTH)
    assert uncosted >= 1


@pytest.mark.anyio
async def test_the_write_off_made_by_a_stocktake_is_sourced_from_the_stocktake(session):
    from sqlalchemy import select as sel

    from app.modules.inventory.models import StockIssue

    ing = await _ingredient(session, "NL kiểm kê thiếu")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 10, 1000)
    sid = (await client.post("/api/v1/inventory/stocktakes", headers=h)).json()["MaPhieuKiemKe"]
    await client.post(
        f"/api/v1/inventory/stocktakes/{sid}/counts",
        json=[{"ingredient_id": iid, "actual_qty": 7}],
        headers=h,
    )
    assert (
        await client.post(f"/api/v1/inventory/stocktakes/{sid}/confirm", headers=h)
    ).status_code == 200
    issue = (
        await session.execute(sel(StockIssue).where(StockIssue.stocktake_id == sid))
    ).scalar_one()
    assert issue.source == "Kiểm kê"
