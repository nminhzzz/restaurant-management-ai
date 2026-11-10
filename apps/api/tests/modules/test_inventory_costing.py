"""Moving weighted average costing (handoff 2026-11-08 A1; document 04 G.1)."""

from datetime import timedelta
from decimal import Decimal

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


async def _unit_cost(session, ingredient_id):
    from app.modules.inventory.costing import current_unit_cost

    session.expire_all()
    return await current_unit_cost(session, ingredient_id)


async def _history(session, ingredient_id):
    from sqlalchemy import select as sel

    from app.modules.inventory.models import AverageCostHistory

    session.expire_all()
    return list(
        (
            await session.execute(
                sel(AverageCostHistory)
                .where(AverageCostHistory.ingredient_id == ingredient_id)
                .order_by(AverageCostHistory.effective_at)
            )
        )
        .scalars()
        .all()
    )


async def _movements(session, ingredient_id):
    from sqlalchemy import select as sel

    from app.modules.inventory.models import StockMovement

    session.expire_all()
    return list(
        (
            await session.execute(
                sel(StockMovement)
                .where(StockMovement.ingredient_id == ingredient_id)
                .order_by(StockMovement.id)
            )
        )
        .scalars()
        .all()
    )


async def _receive(client, headers, iid, qty, price, **extra):
    r = await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": iid, "quantity": qty, "unit_price": price}], **extra},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["MaPhieuNhap"]


async def _issue(client, headers, iid, qty, reason="Hao hụt"):
    r = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": reason, "lines": [{"ingredient_id": iid, "quantity": qty}]},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _issue_costs(session, iid):
    from sqlalchemy import select as sel

    from app.modules.inventory.models import StockIssueLine

    session.expire_all()
    return [
        line.estimated_cost
        for line in (
            await session.execute(
                sel(StockIssueLine)
                .where(StockIssueLine.ingredient_id == iid)
                .order_by(StockIssueLine.id)
            )
        ).scalars()
    ]


async def _receipt_line(session, receipt_id):
    from sqlalchemy import select as sel

    from app.modules.inventory.models import GoodsReceiptLine

    return (
        await session.execute(
            sel(GoodsReceiptLine).where(GoodsReceiptLine.receipt_id == receipt_id)
        )
    ).scalar_one()


async def _count(session, client, headers, iid, actual):
    sid = (await client.post("/api/v1/inventory/stocktakes", headers=headers)).json()[
        "MaPhieuKiemKe"
    ]
    await client.post(
        f"/api/v1/inventory/stocktakes/{sid}/counts",
        json=[{"ingredient_id": iid, "actual_qty": actual}],
        headers=headers,
    )
    confirmed = await client.post(f"/api/v1/inventory/stocktakes/{sid}/confirm", headers=headers)
    assert confirmed.status_code == 200, confirmed.text
    return sid


@pytest.mark.parametrize(
    "stock,unit_cost,quantity,value,expected",
    [
        (0, 0, 10, 2_000_000, "200000.00"),  # the first receipt sets the unit cost
        (10, 200_000, 10, 2_600_000, "230000.00"),  # handoff A1 example
        (20, 230_000, -10, -2_600_000, "200000.00"),  # the second receipt taken back out
        (150, 15_000, 20, 240_000, "14647.06"),  # TC-BR-24
        (1, 4, 2, 6, "3.33"),  # TC-BR-22: 10/3 half up
        (10, 200_000, -10, -2_000_000, "200000"),  # nothing left: the unit cost stays
    ],
)
def test_the_blended_unit_cost_follows_the_formula(stock, unit_cost, quantity, value, expected):
    from app.modules.inventory.costing import blended_cost

    result = blended_cost(Decimal(stock), Decimal(unit_cost), Decimal(quantity), Decimal(value))

    assert result == Decimal(expected)


def test_taking_back_more_value_than_the_stock_holds_keeps_the_unit_cost():
    """Stock drawn in between already carried value away; a negative cost is never stored."""
    from app.modules.inventory.costing import blended_cost

    assert blended_cost(Decimal(12), Decimal(200), Decimal(-10), Decimal(-3000)) == 200


@pytest.mark.parametrize(
    "quantity,unit_cost,expected",
    [("3", "3.33", "9.99"), ("0.5", "1.01", "0.51"), ("-2", "100", "-200.00"), ("1", None, None)],
)
def test_a_movement_value_is_rounded_half_up_and_unknown_without_a_unit_cost(
    quantity, unit_cost, expected
):
    """TC-BR-22/23; an unknown value is None, never 0."""
    from app.modules.inventory.costing import movement_value

    cost = None if unit_cost is None else Decimal(unit_cost)

    result = movement_value(Decimal(quantity), cost)

    assert result == (None if expected is None else Decimal(expected))


@pytest.mark.anyio
async def test_receipts_and_a_cancellation_move_the_unit_cost_as_in_the_handoff(session):
    """Beef 0 in stock: 10 kg at 200.000, 10 kg at 260.000, then the second receipt cancelled."""
    ing = await _ingredient(session, "Bò")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)

    await _receive(client, h, iid, 10, 200_000)
    assert await _unit_cost(session, iid) == 200_000
    second = await _receive(client, h, iid, 10, 260_000)
    assert await _unit_cost(session, iid) == 230_000
    cancelled = await client.delete(f"/api/v1/inventory/receipts/{second}", headers=h)
    assert cancelled.status_code == 200, cancelled.text

    assert await _unit_cost(session, iid) == 200_000
    history = [
        (row.avg_cost, row.stock_qty, row.movement_id) for row in await _history(session, iid)
    ]
    movements = [(m.id, m.value) for m in await _movements(session, iid)]
    assert [row[:2] for row in history] == [(200_000, 10), (230_000, 20), (200_000, 10)]
    assert [row[2] for row in history] == [movement_id for movement_id, _ in movements]
    assert [value for _, value in movements] == [2_000_000, 2_600_000, -2_600_000]


@pytest.mark.anyio
async def test_the_manual_month_close_endpoint_no_longer_exists(session):
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(f"/api/v1/inventory/costing/{MONTH}/close", headers=h)
    assert r.status_code in (404, 405)


@pytest.mark.anyio
async def test_each_issue_takes_the_unit_cost_in_force_and_keeps_it(session):
    """TC-REP-11, TC-BR-12/13: 15.000 then 21.000; issues cost 750.000 and 1.050.000."""
    ing = await _ingredient(session, "NL hai lần nhập")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 100, 10_000)

    await _receive(client, h, iid, 100, 20_000)
    assert await _unit_cost(session, iid) == 15_000
    await _issue(client, h, iid, 50)
    rows_after_first_issue = len(await _history(session, iid))
    await _receive(client, h, iid, 100, 30_000)
    assert await _unit_cost(session, iid) == 21_000  # (150 x 15.000 + 100 x 30.000) / 250
    await _issue(client, h, iid, 50)

    assert await _issue_costs(session, iid) == [750_000, 1_050_000]
    # An issue never moves the unit cost, so it writes no history row of its own.
    assert rows_after_first_issue == 2
    assert len(await _history(session, iid)) == 3
    assert await _unit_cost(session, iid) == 21_000
    issued = [m.value for m in await _movements(session, iid) if m.kind == "Xuất thủ công"]
    assert issued == [-750_000, -1_050_000]


@pytest.mark.anyio
async def test_cancelling_the_only_receipt_keeps_the_unit_cost_in_force(session):
    """Nothing is left to divide by, so the unit cost stays and no division happens."""
    ing = await _ingredient(session, "NL chỉ một phiếu")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    only = await _receive(client, h, iid, 10, 1000)

    cancelled = await client.delete(f"/api/v1/inventory/receipts/{only}", headers=h)

    assert cancelled.status_code == 200, cancelled.text
    assert await _unit_cost(session, iid) == 1000
    assert (await _history(session, iid))[-1].stock_qty == 0


@pytest.mark.anyio
async def test_correcting_only_the_price_recalculates_without_a_stock_movement(session):
    """Document 04 F.27: MaGiaoDichKho is NULL when only the unit price was corrected."""
    ing = await _ingredient(session, "NL sửa giá")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    receipt_id = await _receive(client, h, iid, 10, 1000)
    line = await _receipt_line(session, receipt_id)

    r = await client.patch(
        f"/api/v1/inventory/receipts/{receipt_id}",
        json={"lines": [{"line_id": line.id, "quantity": 10, "unit_price": 1800}]},
        headers=h,
    )

    assert r.status_code == 200, r.text
    assert await _unit_cost(session, iid) == 1800
    history = await _history(session, iid)
    assert len(history) == 2
    assert history[-1].movement_id is None
    assert len(await _movements(session, iid)) == 1


@pytest.mark.anyio
async def test_a_corrected_line_leaves_the_average_before_it_rejoins(session):
    """FR-INV-02: the old quantity and value go out first, then the corrected line comes in."""
    ing = await _ingredient(session, "NL sửa lượng")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 10, 1000)
    receipt_id = await _receive(client, h, iid, 10, 2000)
    assert await _unit_cost(session, iid) == 1500
    line = await _receipt_line(session, receipt_id)

    r = await client.patch(
        f"/api/v1/inventory/receipts/{receipt_id}",
        json={"lines": [{"line_id": line.id, "quantity": 20, "unit_price": 1500}]},
        headers=h,
    )

    assert r.status_code == 200, r.text
    # Out: (20 x 1500 - 10 x 2000) / 10 = 1000. In: (10 x 1000 + 20 x 1500) / 30 = 1333,33.
    assert await _unit_cost(session, iid) == Decimal("1333.33")
    assert (await _history(session, iid))[-1].stock_qty == 30
    assert (await _movements(session, iid))[-1].value == 10_000  # 20 x 1500 - 10 x 2000


@pytest.mark.anyio
async def test_moving_the_receipt_date_changes_the_lot_but_not_the_unit_cost(session):
    """TC-BR-14: lot date, expiry and FIFO order follow; the unit cost and its history do not."""
    from sqlalchemy import select as sel

    from app.modules.inventory.models import IngredientLot, StockMovement
    from app.shared.audit import SystemAuditLog

    ing = await _ingredient(session, "NL đổi ngày")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    receipt_id = await _receive(client, h, iid, 10, 1000)
    earlier = FIXED_NOW - timedelta(days=40)
    line_id = (await _receipt_line(session, receipt_id)).id

    r = await client.patch(
        f"/api/v1/inventory/receipts/{receipt_id}",
        json={
            "receipt_date": earlier.isoformat(),
            "lines": [{"line_id": line_id, "quantity": 10, "unit_price": 1000}],
        },
        headers=h,
    )

    assert r.status_code == 200, r.text
    assert await _unit_cost(session, iid) == 1000
    assert len(await _history(session, iid)) == 1
    lot = (
        await session.execute(sel(IngredientLot).where(IngredientLot.receipt_line_id == line_id))
    ).scalar_one()
    assert lot.received_at == earlier
    movement = (
        await session.execute(sel(StockMovement).where(StockMovement.receipt_line_id == line_id))
    ).scalar_one()
    assert movement.business_date == earlier.date()
    audit = (
        await session.execute(sel(SystemAuditLog).where(SystemAuditLog.action == "UPDATE_RECEIPT"))
    ).scalar_one()
    assert audit.before["NgayNhap"] != audit.after["NgayNhap"]
    assert audit.before["ChiTiet"] == audit.after["ChiTiet"]


@pytest.mark.anyio
async def test_a_stocktake_surplus_is_valued_at_the_unit_cost_without_moving_it(session):
    """TC-BR-18: the surplus is a reconciliation, not a purchase (FR-INV-09)."""
    from sqlalchemy import select as sel

    from app.modules.inventory.models import IngredientLot

    ing = await _ingredient(session, "NL kiểm kê dư")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 10, 1000)

    await _count(session, client, h, iid, 15)

    assert await _unit_cost(session, iid) == 1000
    assert len(await _history(session, iid)) == 1
    adjustment = (await _movements(session, iid))[-1]
    assert (adjustment.kind, adjustment.qty, adjustment.value) == ("Điều chỉnh kiểm kê", 5, 5000)
    lots = (
        (await session.execute(sel(IngredientLot).where(IngredientLot.ingredient_id == iid)))
        .scalars()
        .all()
    )
    # The surplus joins the existing lot, so it keeps that lot's purchase price.
    assert sum(lot.quantity_remaining for lot in lots) == 15
    assert all(lot.unit_price == 1000 for lot in lots)


@pytest.mark.anyio
async def test_a_stocktake_shortage_is_valued_once_on_the_adjustment_and_its_voucher(session):
    """TC-BR-10: one adjustment lowers the stock; the voucher only documents it."""
    from sqlalchemy import select as sel

    from app.modules.inventory.models import StockIssue

    ing = await _ingredient(session, "NL kiểm kê thiếu")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 10, 1000)

    sid = await _count(session, client, h, iid, 7)

    issue = (
        await session.execute(sel(StockIssue).where(StockIssue.stocktake_id == sid))
    ).scalar_one()
    assert issue.source == "Kiểm kê"
    assert await _issue_costs(session, iid) == [3000]
    adjustments = [m for m in await _movements(session, iid) if m.kind == "Điều chỉnh kiểm kê"]
    assert [(m.qty, m.value) for m in adjustments] == [(-3, -3000)]
    assert await _unit_cost(session, iid) == 1000


@pytest.mark.anyio
async def test_an_ingredient_never_received_has_no_unit_cost_and_unknown_values(session):
    """TC-BR-17: the count is recorded; value and lot price stay unknown, never 0."""
    from sqlalchemy import select as sel

    from app.modules.inventory.models import IngredientLot
    from app.modules.reports.queries import waste_cost

    ing = await _ingredient(session, "NL chưa từng nhập")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)

    await _count(session, client, h, iid, 5)
    await _issue(client, h, iid, 2)

    lot = (
        await session.execute(sel(IngredientLot).where(IngredientLot.ingredient_id == iid))
    ).scalar_one()
    assert lot.unit_price is None
    assert await _unit_cost(session, iid) is None
    assert await _history(session, iid) == []
    assert [m.value for m in await _movements(session, iid)] == [None, None]
    assert await _issue_costs(session, iid) == [None]
    _total, unvalued = await waste_cost(session, MONTH)
    assert unvalued >= 1


@pytest.mark.anyio
async def test_the_first_receipt_prices_everything_that_moved_before_it(session):
    """TC-BR-25: adjustment 5, one unit consumed, then 5 x 6: unit cost 6,00, priced once."""
    ing = await _ingredient(session, "NL định giá sau")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _count(session, client, h, iid, 5)
    await _issue(client, h, iid, 1)
    before = await _movements(session, iid)
    assert [m.value for m in before] == [None, None]

    await _receive(client, h, iid, 5, 6)

    assert await _unit_cost(session, iid) == Decimal("6.00")
    after = await _movements(session, iid)
    assert len(after) == len(before) + 1  # only the receipt itself was added
    assert [m.value for m in after] == [30, -6, 30]
    assert await _issue_costs(session, iid) == [6]
    assert (await _history(session, iid))[0].stock_qty == 9


@pytest.mark.anyio
async def test_a_value_once_written_is_not_touched_by_the_next_first_price_pass(session):
    """Only unknown values are filled in; a known value is never recomputed."""
    ing = await _ingredient(session, "NL không tính lại")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 10, 100)
    await _issue(client, h, iid, 2)

    await _receive(client, h, iid, 10, 900)

    assert await _issue_costs(session, iid) == [200]
    assert [m.value for m in await _movements(session, iid)] == [1000, -200, 9000]


@pytest.mark.anyio
async def test_a_receipt_carries_the_total_of_its_lines(session):
    """TC-CAT-16: the supplier's purchase history showed 0 ₫ for every receipt."""
    from app.modules.inventory.models import GoodsReceipt

    first = (await _ingredient(session, "NL tổng tiền 1")).id
    second = (await _ingredient(session, "NL tổng tiền 2")).id
    client = await _make_client(session)
    h, _ = await _headers(session)
    created = await client.post(
        "/api/v1/inventory/receipts",
        json={
            "lines": [
                {"ingredient_id": first, "quantity": 1000, "unit_price": 200},
                {"ingredient_id": second, "quantity": 2, "unit_price": 1500},
            ]
        },
        headers=h,
    )
    receipt_id = created.json()["MaPhieuNhap"]

    detail = await client.get(f"/api/v1/inventory/receipts/{receipt_id}", headers=h)

    assert detail.json()["TongTien"] == 203_000
    line = detail.json()["lines"][0]
    edited = await client.patch(
        f"/api/v1/inventory/receipts/{receipt_id}",
        json={"lines": [{"line_id": line["MaChiTietNhap"], "quantity": 500, "unit_price": 200}]},
        headers=h,
    )
    assert edited.status_code == 200, edited.text
    session.expire_all()
    assert (await session.get(GoodsReceipt, receipt_id)).total == 103_000
