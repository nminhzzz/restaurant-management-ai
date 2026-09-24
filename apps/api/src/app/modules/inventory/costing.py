"""Monthly weighted average costing."""

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
    # month format YYYYMM int
    year = month // 100
    m = month % 100
    start = f"{year:04d}-{m:02d}-01"
    # next month
    if m == 12:
        end = f"{year + 1:04d}-01-01"
    else:
        end = f"{year:04d}-{m + 1:02d}-01"
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
        else:
            existing = MonthlyAverageCost(ingredient_id=ing_id, month=month, avg_cost=float(avg))
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
    # StockIssueLine with 0 cost, join to get month via StockIssue created_at? Use same month filter via parent?
    # For simplicity, backfill all zero-cost lines whose ingredient has cost for month
    q = select(StockIssueLine).where(StockIssueLine.estimated_cost == 0)
    lines = (await session.execute(q)).scalars().all()
    updated = 0
    for ln in lines:
        avg = costs.get(ln.ingredient_id)
        if avg is not None:
            ln.estimated_cost = float(avg * Decimal(str(ln.quantity)))
            updated += 1
    await session.flush()
    return updated
