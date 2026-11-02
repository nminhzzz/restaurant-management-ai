"""Lot status and cancelled lots (document 04 F.21, BR-LOT-01; TC-BR-19..23)."""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.modules.catalog.models import Ingredient
from app.modules.inventory.lot_status import derive_lot_status
from app.modules.inventory.models import IngredientLot, StockIssueLine, StockMovement
from app.modules.inventory.stock import lots_for_fifo
from app.shared import business_date
from tests.modules.test_inventory_costing import (
    MONTH,
    _headers,
    _ingredient,
    _make_client,
    _receive,
)

pytestmark = pytest.mark.anyio


async def _lots(session, iid):
    session.expire_all()
    return (
        (
            await session.execute(
                select(IngredientLot)
                .where(IngredientLot.ingredient_id == iid)
                .order_by(IngredientLot.id)
            )
        )
        .scalars()
        .all()
    )


async def _issue(client, headers, iid, quantity, **extra):
    r = await client.post(
        "/api/v1/inventory/issues",
        json={
            "reason": "Hao hụt",
            "lines": [{"ingredient_id": iid, "quantity": quantity}],
            **extra,
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r


async def test_cancelling_a_receipt_zeroes_every_lot_and_keeps_the_history(session):
    """TC-BR-19."""
    first, second = await _ingredient(session, "NL A"), await _ingredient(session, "NL B")
    a, b = first.id, second.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    receipt = await client.post(
        "/api/v1/inventory/receipts",
        json={
            "lines": [
                {"ingredient_id": a, "quantity": 4, "unit_price": 1000},
                {"ingredient_id": b, "quantity": 6, "unit_price": 2000},
            ]
        },
        headers=h,
    )
    receipt_id = receipt.json()["MaPhieuNhap"]

    cancelled = await client.delete(f"/api/v1/inventory/receipts/{receipt_id}", headers=h)

    assert cancelled.status_code == 200, cancelled.text
    for iid in (a, b):
        (lot,) = await _lots(session, iid)
        assert lot.quantity_remaining == 0
        assert lot.status == "Đã hủy"
        assert lot.received_quantity > 0  # the lot and its history are kept
    kinds = (await session.execute(select(StockMovement.kind))).scalars().all()
    assert "Nhập" in kinds and "Hoàn kho" in kinds


async def test_a_partial_write_off_keeps_the_rest_of_the_lot_usable(session):
    """TC-BR-20."""
    ing = await _ingredient(session, "NL xuất hủy một phần")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 10, 1000)

    await _issue(client, h, iid, 3)

    (lot,) = await _lots(session, iid)
    assert lot.quantity_remaining == 7
    assert lot.status == "Còn hạn"
    assert [x.id for x in await lots_for_fifo(session, iid)] == [lot.id]
    count = (
        (await session.execute(select(StockMovement).where(StockMovement.kind == "Xuất thủ công")))
        .scalars()
        .all()
    )
    assert sum(abs(m.qty) for m in count) == 3  # the loss is recorded exactly once


async def test_a_cancelled_lot_is_never_drawn_held_or_revived(session):
    """TC-BR-21."""
    from app.modules.sales import reservations

    ing = await _ingredient(session, "NL lô đã hủy")
    iid = ing.id
    cancelled = IngredientLot(
        ingredient_id=iid,
        quantity_remaining=Decimal(5),
        received_quantity=Decimal(5),
        status="Đã hủy",
        received_at=business_date.now(),
    )
    session.add(cancelled)
    await session.commit()
    cancelled_id = cancelled.id

    assert await lots_for_fifo(session, iid, allow_expired=True) == []
    assert await reservations._eligible_lots(session, iid, business_date.now(), lock=False) == []

    client = await _make_client(session)
    h, _ = await _headers(session)
    sid = (await client.post("/api/v1/inventory/stocktakes", headers=h)).json()["MaPhieuKiemKe"]
    await client.post(
        f"/api/v1/inventory/stocktakes/{sid}/counts",
        json=[{"ingredient_id": iid, "actual_qty": 4}],
        headers=h,
    )
    confirmed = await client.post(f"/api/v1/inventory/stocktakes/{sid}/confirm", headers=h)
    assert confirmed.status_code == 200, confirmed.text

    lots = await _lots(session, iid)
    still_cancelled = next(x for x in lots if x.id == cancelled_id)
    assert still_cancelled.status == "Đã hủy"
    adjustment = [x for x in lots if x.id != cancelled_id]
    assert len(adjustment) == 1 and adjustment[0].is_adjustment
    assert adjustment[0].quantity_remaining == 4


async def test_the_average_price_is_rounded_to_two_decimals_half_up(session):
    """TC-BR-22: 10/3 is stored as 3,33 and three units cost 9,99."""
    ing = await _ingredient(session, "NL làm tròn 1")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 1, 3)
    await _receive(client, h, iid, 2, 3.5)

    await _issue(client, h, iid, 3)

    from app.modules.inventory.models import MonthlyAverageCost

    session.expire_all()
    average = await session.get(MonthlyAverageCost, {"ingredient_id": iid, "month": MONTH})
    assert average.avg_cost == Decimal("3.33")
    line = (await session.execute(select(StockIssueLine))).scalars().all()[-1]
    assert line.estimated_cost == Decimal("9.99")


async def test_a_cost_of_half_a_cent_rounds_up(session):
    """TC-BR-23: 1,01 x 0,5 = 0,505 becomes 0,51."""
    ing = await _ingredient(session, "NL làm tròn 2")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 10, 1.01)

    await _issue(client, h, iid, 0.5)

    session.expire_all()
    line = (await session.execute(select(StockIssueLine))).scalars().all()[-1]
    assert line.estimated_cost == Decimal("0.51")


async def test_the_stored_status_follows_the_stock(session):
    ing = await _ingredient(session, "NL trạng thái")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 5, 1000)
    (lot,) = await _lots(session, iid)
    assert lot.status == "Còn hạn"  # no expiry date: never "Sắp hết hạn" or "Hết hạn"

    await _issue(client, h, iid, 5)

    (lot,) = await _lots(session, iid)
    assert lot.quantity_remaining == 0
    assert lot.status == "Đã dùng hết"


async def test_a_lot_close_to_its_expiry_is_marked_as_expiring(session):
    ing = Ingredient(name="NL sắp hết hạn", unit="kg", stock_qty=0, shelf_days=2)
    session.add(ing)
    await session.commit()
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 5, 1000)

    (lot,) = await _lots(session, iid)
    assert lot.status == "Sắp hết hạn"


async def test_the_status_order_prefers_cancelled_then_empty_then_expiry():
    from datetime import date

    lot = IngredientLot(
        quantity_remaining=Decimal(0), expiry_date=date(2026, 1, 1), status="Còn hạn"
    )
    today = date(2026, 9, 24)
    assert derive_lot_status(lot, today, 3) == "Đã dùng hết"  # empty beats expired
    lot.quantity_remaining = Decimal(2)
    assert derive_lot_status(lot, today, 3) == "Hết hạn"
    lot.expiry_date = date(2026, 9, 26)
    assert derive_lot_status(lot, today, 3) == "Sắp hết hạn"
    lot.expiry_date = date(2026, 12, 1)
    assert derive_lot_status(lot, today, 3) == "Còn hạn"
    lot.status = "Đã hủy"
    lot.quantity_remaining = Decimal(9)
    assert derive_lot_status(lot, today, 3) == "Đã hủy"  # cancelled is final


async def test_cancelling_a_receipt_recomputes_costs_of_both_lines_and_later_months(session):
    """TC-BR-19: every line's cost and every dependent period follow the cancellation."""
    from app.modules.inventory.models import MonthlyAverageCost

    a_ing, b_ing = await _ingredient(session, "NL kỳ A"), await _ingredient(session, "NL kỳ B")
    a, b = a_ing.id, b_ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)

    async def receive(lines, when):
        r = await client.post(
            "/api/v1/inventory/receipts",
            json={
                "receipt_date": when,
                "lines": [
                    {"ingredient_id": i, "quantity": q, "unit_price": p} for i, q, p in lines
                ],
            },
            headers=h,
        )
        assert r.status_code == 201, r.text
        return r.json()["MaPhieuNhap"]

    await receive([(a, 10, 1000)], "2026-08-10T09:00:00")
    september = await receive([(a, 10, 3000), (b, 5, 2000)], "2026-09-10T09:00:00")
    await receive([(a, 10, 4500)], "2026-10-05T09:00:00")

    async def average(iid, month):
        session.expire_all()
        row = await session.get(MonthlyAverageCost, {"ingredient_id": iid, "month": month})
        return None if row is None else row.avg_cost

    assert await average(a, 202609) == 2000  # (10x1000 + 10x3000) / 20
    assert await average(b, 202609) == 2000
    assert await average(a, 202610) == Decimal("2833.33")  # (20x2000 + 10x4500) / 30

    cancelled = await client.delete(f"/api/v1/inventory/receipts/{september}", headers=h)
    assert cancelled.status_code == 200, cancelled.text

    assert await average(a, 202609) == 1000  # September keeps only the carried stock
    assert await average(b, 202609) is None  # line B has no basis left
    assert await average(a, 202610) == 2750  # (10x1000 + 10x4500) / 20 propagates forward


async def test_quantities_keep_six_decimals_while_money_is_rounded(session):
    """TC-BR-22: the quantity is never rounded to two decimals."""
    ing = await _ingredient(session, "NL sáu chữ số")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 2.123456, 3)

    await _issue(client, h, iid, 0.123456)

    session.expire_all()
    (lot,) = await _lots(session, iid)
    line = (await session.execute(select(StockIssueLine))).scalars().all()[-1]
    assert Decimal(str(line.quantity)).quantize(Decimal("0.000001")) == Decimal("0.123456")
    assert Decimal(str(lot.quantity_remaining)).quantize(Decimal("0.000001")) == Decimal("2.000000")
    assert line.estimated_cost == Decimal("0.37")  # 3,00 x 0,123456 = 0,370368 -> 0,37


async def test_recomputing_the_same_data_gives_the_same_cost_and_no_new_movements(session):
    """TC-BR-23: repeating the calculation neither changes the cost nor moves stock."""
    from app.modules.inventory.costing import refresh_costing

    ing = await _ingredient(session, "NL tính lại")
    iid = ing.id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 10, 1.01)
    await _issue(client, h, iid, 0.5)

    async def snapshot():
        session.expire_all()
        cost = (await session.execute(select(StockIssueLine))).scalars().all()[-1].estimated_cost
        movements = (await session.execute(select(StockMovement.id))).scalars().all()
        return cost, len(movements)

    first = await snapshot()
    await refresh_costing(session, MONTH)
    await refresh_costing(session, MONTH)
    second = await snapshot()

    assert first == (Decimal("0.51"), first[1])
    assert second == first
