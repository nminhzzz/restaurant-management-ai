"""Monthly weighted average costing."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.models import (
    GoodsReceipt,
    GoodsReceiptLine,
    MonthlyAverageCost,
    StockIssueLine,
)


async def close_month(session: AsyncSession, month: int) -> list[MonthlyAverageCost]:
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
        )
        .group_by(GoodsReceiptLine.ingredient_id)
    )
    rows = (await session.execute(q)).all()
    out = []
    for ing_id, qty, total in rows:
        if not qty:
            continue
        avg = Decimal(str(total)) / Decimal(str(qty))
        existing = await session.get(MonthlyAverageCost, {"ingredient_id": ing_id, "month": month})
        if existing:
            existing.avg_cost = float(avg)
            existing.total_qty = float(qty)
        else:
            existing = MonthlyAverageCost(
                ingredient_id=ing_id, month=month, avg_cost=float(avg), total_qty=float(qty)
            )
            session.add(existing)
        out.append(existing)
    await session.flush()
    return out


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
            ln.estimated_cost = float(avg * Decimal(str(ln.quantity)))
            updated += 1
    await session.flush()
    return updated
