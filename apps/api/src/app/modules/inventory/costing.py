"""Monthly weighted average costing."""

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.models import (
    GoodsReceipt,
    GoodsReceiptLine,
    IngredientLot,
    MonthlyAverageCost,
    StockIssueLine,
    StockMovement,
)
from app.shared import business_date as _bd
from app.shared.enums import ReceiptStatus, StockMovementType


async def _opening_quantities(session: AsyncSession, start: datetime) -> dict[int, Decimal]:
    """Stock on hand at the start of the month, per ingredient.

    Receipts are counted from the receipt lines that still stand (a cancelled receipt never
    entered the stock, and an edited one keeps its corrected quantity) on the same calendar
    basis as the month's own receipts; everything else comes from the ledger by Business Date.
    """
    received = await session.execute(
        select(GoodsReceiptLine.ingredient_id, func.sum(GoodsReceiptLine.quantity))
        .join(GoodsReceipt, GoodsReceiptLine.receipt_id == GoodsReceipt.id)
        .where(
            GoodsReceipt.receipt_date < start,
            GoodsReceipt.status != ReceiptStatus.DA_HUY.value,
        )
        .group_by(GoodsReceiptLine.ingredient_id)
    )
    moved = await session.execute(
        select(StockMovement.ingredient_id, func.sum(StockMovement.qty))
        .where(
            StockMovement.kind != StockMovementType.NHAP.value,
            StockMovement.business_date < start.date(),
        )
        .group_by(StockMovement.ingredient_id)
    )
    opening: dict[int, Decimal] = {}
    for ingredient_id, quantity in (*received.all(), *moved.all()):
        opening[int(ingredient_id)] = opening.get(int(ingredient_id), Decimal(0)) + Decimal(
            str(quantity or 0)
        )
    return opening


async def _previous_averages(session: AsyncSession, month: int) -> dict[int, Decimal]:
    """The average of the nearest earlier month that has one, per ingredient."""
    rows = await session.execute(
        select(MonthlyAverageCost.ingredient_id, MonthlyAverageCost.avg_cost)
        .where(MonthlyAverageCost.month < month)
        .order_by(MonthlyAverageCost.month)
    )
    return {int(ingredient_id): Decimal(str(avg)) for ingredient_id, avg in rows}  # latest wins


async def close_month(session: AsyncSession, month: int) -> list[MonthlyAverageCost]:
    """FR-REP-05a: weighted average over the opening stock and the month's receipts.

    The opening stock carries the nearest earlier average; an ingredient with no receipt in the
    month keeps that average so its cost never falls to 0. An opening stock that has no earlier
    average to price it is left out of the weighting.
    """
    # month format YYYYMM int - validate 1..12
    year = month // 100
    m = month % 100
    if m < 1 or m > 12 or year < 1000 or year > 9999:
        from app.core.errors import BusinessRuleError

        raise BusinessRuleError("Tháng không hợp lệ (YYYYMM).")
    start = datetime(year, m, 1)
    if m == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, m + 1, 1)
    # aggregate per ingredient
    q = (
        select(
            GoodsReceiptLine.ingredient_id,
            func.sum(GoodsReceiptLine.quantity).label("qty"),
            func.sum(GoodsReceiptLine.quantity * GoodsReceiptLine.unit_price).label("total"),
        )
        .join(GoodsReceipt, GoodsReceiptLine.receipt_id == GoodsReceipt.id)
        .where(
            GoodsReceipt.receipt_date >= start,
            GoodsReceipt.receipt_date < end,
            # A cancelled receipt never entered the stock (FR-INV-02), and the zero-price
            # receipts that older stocktakes fabricated for their surplus are not purchases.
            GoodsReceipt.status != ReceiptStatus.DA_HUY.value,
            ~select(IngredientLot.id)
            .where(
                IngredientLot.receipt_line_id == GoodsReceiptLine.id,
                IngredientLot.is_adjustment.is_(True),
            )
            .exists(),
        )
        .group_by(GoodsReceiptLine.ingredient_id)
    )
    purchases = {
        int(ing_id): (Decimal(str(qty or 0)), Decimal(str(total or 0)))
        for ing_id, qty, total in (await session.execute(q)).all()
    }
    previous = await _previous_averages(session, month)
    opening = await _opening_quantities(session, start)
    out = []
    for ing_id in sorted({*purchases, *previous}):
        qty, total = purchases.get(ing_id, (Decimal(0), Decimal(0)))
        opening_avg = previous.get(ing_id)
        if qty > 0:
            opening_qty = max(Decimal(0), opening.get(ing_id, Decimal(0)))
            if opening_avg is not None and opening_qty > 0:
                qty_basis = opening_qty + qty
                total_basis = opening_qty * opening_avg + total
            else:
                qty_basis, total_basis = qty, total
            # The column is DECIMAL(18,4); quantising here keeps the stored value exact and
            # silences MySQL's "Data truncated" warning without changing the average.
            avg = (total_basis / qty_basis).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        else:
            assert opening_avg is not None  # an ingredient is listed only for a reason
            avg = opening_avg
        existing = await session.get(MonthlyAverageCost, {"ingredient_id": ing_id, "month": month})
        if existing:
            existing.avg_cost = avg
            existing.total_qty = qty
            existing.computed_at = _bd.now()
        else:
            existing = MonthlyAverageCost(
                ingredient_id=ing_id,
                month=month,
                avg_cost=avg,
                total_qty=qty,
                computed_at=_bd.now(),
            )
            session.add(existing)
        out.append(existing)
    await session.flush()
    return out


async def average_costs(
    session: AsyncSession, month: int, ingredient_ids: list[int]
) -> dict[int, Decimal]:
    """The closed average of `month` per ingredient; ingredients not priced yet are absent."""
    if not ingredient_ids:
        return {}
    rows = await session.execute(
        select(MonthlyAverageCost.ingredient_id, MonthlyAverageCost.avg_cost).where(
            MonthlyAverageCost.month == month,
            MonthlyAverageCost.ingredient_id.in_(ingredient_ids),
        )
    )
    return {int(ingredient_id): Decimal(str(avg)) for ingredient_id, avg in rows}


async def backfill_issue_costs(session: AsyncSession, month: int) -> int:
    # find avg for month
    costs = {
        c.ingredient_id: Decimal(str(c.avg_cost))
        for c in (
            await session.execute(
                select(MonthlyAverageCost).where(MonthlyAverageCost.month == month)
            )
        )
        .scalars()
        .all()
    }
    if not costs:
        return 0
    year = month // 100
    m = month % 100
    start = datetime(year, m, 1)
    end = datetime(year + 1, 1, 1) if m == 12 else datetime(year, m + 1, 1)
    from app.modules.inventory.models import StockIssue
    from app.modules.sales.models import Order, OrderLine

    issue_date = func.coalesce(StockIssue.issue_date, StockIssue.created_at)
    # Manual and stocktake write-offs belong to the month they were issued in ...
    q = (
        select(StockIssueLine)
        .join(StockIssue, StockIssueLine.issue_id == StockIssue.id)
        .where(
            StockIssueLine.estimated_cost == 0,
            StockIssueLine.order_line_id.is_(None),
            issue_date >= start,
            issue_date < end,
        )
    )
    lines = list((await session.execute(q)).scalars().all())
    # ... prepared-dish write-offs to the month of the order they came from (FR-REP-05a).
    by_order = (
        select(StockIssueLine)
        .join(OrderLine, OrderLine.id == StockIssueLine.order_line_id)
        .join(Order, Order.id == OrderLine.order_id)
        .where(
            StockIssueLine.estimated_cost == 0,
            Order.business_date >= start.date(),
            Order.business_date < end.date(),
        )
    )
    lines.extend((await session.execute(by_order)).scalars().all())
    updated = 0
    for ln in lines:
        avg = costs.get(ln.ingredient_id)
        if avg is not None:
            ln.estimated_cost = avg * ln.quantity
            updated += 1
    await session.flush()
    return updated
