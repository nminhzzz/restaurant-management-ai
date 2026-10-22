"""Monthly weighted average costing."""

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, or_, select
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


async def _previous_costs(session: AsyncSession, month: int) -> dict[int, Decimal]:
    """Latest known average cost before `month` (FR-REP-05a carry-forward)."""
    rows = (
        await session.execute(
            select(
                MonthlyAverageCost.ingredient_id,
                MonthlyAverageCost.month,
                MonthlyAverageCost.avg_cost,
            )
            .where(MonthlyAverageCost.month < month)
            .order_by(
                MonthlyAverageCost.ingredient_id.asc(),
                MonthlyAverageCost.month.desc(),
            )
        )
    ).all()
    out: dict[int, Decimal] = {}
    for ingredient_id, _month, avg in rows:
        out.setdefault(int(ingredient_id), Decimal(str(avg)))
    return out


async def _opening_state(
    session: AsyncSession, month: int, previous: dict[int, Decimal]
) -> tuple[dict[int, Decimal], dict[int, Decimal]]:
    """Quantity and value of stock at the start of the month.

    The ledger is the source of truth: the sum of every movement before the month
    is the quantity on hand. Value uses the previous month's average when it exists;
    otherwise the weighted purchase price of the lots received before the month.
    """
    start, _ = _bd.business_month_range(month)
    qty_rows = (
        await session.execute(
            select(StockMovement.ingredient_id, func.sum(StockMovement.qty))
            .where(StockMovement.business_date < start.date())
            .group_by(StockMovement.ingredient_id)
        )
    ).all()
    quantities = {
        int(ingredient_id): max(Decimal(str(qty or 0)), Decimal(0))
        for ingredient_id, qty in qty_rows
    }

    lot_rows = (
        await session.execute(
            select(
                IngredientLot.ingredient_id,
                func.sum(IngredientLot.received_quantity),
                func.sum(IngredientLot.received_quantity * IngredientLot.unit_price),
            )
            .where(IngredientLot.received_at < start)
            .group_by(IngredientLot.ingredient_id)
        )
    ).all()
    lot_avg: dict[int, Decimal] = {}
    for ingredient_id, qty, total in lot_rows:
        if qty and Decimal(str(qty)) > 0:
            lot_avg[int(ingredient_id)] = Decimal(str(total)) / Decimal(str(qty))

    values: dict[int, Decimal] = {}
    for ingredient_id, qty in quantities.items():
        unit = previous.get(ingredient_id) or lot_avg.get(ingredient_id) or Decimal(0)
        values[ingredient_id] = qty * unit
    return quantities, values


async def close_month(session: AsyncSession, month: int) -> list[MonthlyAverageCost]:
    start, end = _bd.business_month_range(month)
    previous = await _previous_costs(session, month)
    opening_qty, opening_value = await _opening_state(session, month, previous)

    # Purchases in the month, excluding cancelled receipts and stocktake-surplus lines.
    q = (
        select(
            GoodsReceiptLine.ingredient_id,
            func.sum(GoodsReceiptLine.quantity).label("qty"),
            func.sum(GoodsReceiptLine.quantity * GoodsReceiptLine.unit_price).label("total"),
        )
        .join(GoodsReceipt, GoodsReceiptLine.receipt_id == GoodsReceipt.id)
        .outerjoin(IngredientLot, IngredientLot.receipt_line_id == GoodsReceiptLine.id)
        .where(
            GoodsReceipt.receipt_date >= start,
            GoodsReceipt.receipt_date < end,
            GoodsReceipt.status != "Đã hủy",
            or_(IngredientLot.is_adjustment.is_(False), IngredientLot.id.is_(None)),
        )
        .group_by(GoodsReceiptLine.ingredient_id)
    )
    purchases = {
        int(row[0]): (Decimal(str(row[1] or 0)), Decimal(str(row[2] or 0)))
        for row in (await session.execute(q)).all()
    }

    ingredient_ids = sorted(set(opening_qty) | set(purchases))
    out: list[MonthlyAverageCost] = []
    for ing_id in ingredient_ids:
        buy_qty, buy_total = purchases.get(ing_id, (Decimal(0), Decimal(0)))
        open_qty = opening_qty.get(ing_id, Decimal(0))
        denominator = open_qty + buy_qty
        if denominator > 0:
            avg = (opening_value.get(ing_id, Decimal(0)) + buy_total) / denominator
        elif ing_id in previous:
            # No stock movement and no purchase: keep last month's unit cost so a later
            # report can still cost anything that was consumed from carried stock.
            avg = previous[ing_id]
        else:
            continue
        avg = avg.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        existing = await session.get(MonthlyAverageCost, {"ingredient_id": ing_id, "month": month})
        if existing:
            existing.avg_cost = avg
            existing.total_qty = buy_qty
            existing.computed_at = _bd.now()
        else:
            existing = MonthlyAverageCost(
                ingredient_id=ing_id,
                month=month,
                avg_cost=avg,
                total_qty=buy_qty,
                computed_at=_bd.now(),
            )
            session.add(existing)
        out.append(existing)
    await session.flush()
    return out


async def backfill_issue_costs(session: AsyncSession, month: int) -> int:
    start, end = _bd.business_month_range(month)
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
    from app.modules.inventory.models import StockIssue

    q = (
        select(StockIssueLine)
        .join(StockIssue, StockIssueLine.issue_id == StockIssue.id)
        .where(
            StockIssueLine.estimated_cost == 0,
            StockIssue.created_at >= start,
            StockIssue.created_at < end,
        )
    )
    lines = (await session.execute(q)).scalars().all()
    updated = 0
    for ln in lines:
        avg = costs.get(ln.ingredient_id)
        if avg is not None:
            ln.estimated_cost = (avg * ln.quantity).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
            updated += 1
    await session.flush()
    return updated
