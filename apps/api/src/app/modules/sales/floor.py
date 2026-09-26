"""Floor board for the POS: every table with its open order, plus open takeaway orders."""

from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import DiningTable
from app.modules.sales.models import Order, OrderLine
from app.modules.sales.orders import LINE_CANCELLED, OPEN_ORDER_STATUSES


def _summary(order: Order, totals: dict[int, tuple[int, Decimal]]) -> dict[str, Any]:
    quantity, amount = totals.get(order.id, (0, Decimal(0)))
    return {
        "MaOrder": order.id,
        "MaOrderHienThi": order.display_code,
        "MoLuc": order.created_at.isoformat() if order.created_at else None,
        "SoMon": quantity,
        "TamTinh": float(amount),
    }


async def floor_board(session: AsyncSession) -> dict[str, list[dict[str, Any]]]:
    tables = (
        (
            await session.execute(
                select(DiningTable)
                .where(DiningTable.is_deleted.is_(False))
                .order_by(DiningTable.id)
            )
        )
        .scalars()
        .all()
    )
    open_orders = (
        (
            await session.execute(
                select(Order).where(Order.status.in_(OPEN_ORDER_STATUSES)).order_by(Order.id)
            )
        )
        .scalars()
        .all()
    )
    totals: dict[int, tuple[int, Decimal]] = {}
    if open_orders:
        rows = await session.execute(
            select(
                OrderLine.order_id,
                func.coalesce(func.sum(OrderLine.quantity), 0),
                func.coalesce(func.sum(OrderLine.unit_price * OrderLine.quantity), 0),
            )
            .where(
                OrderLine.order_id.in_([o.id for o in open_orders]),
                OrderLine.status != LINE_CANCELLED,
            )
            .group_by(OrderLine.order_id)
        )
        totals = {
            order_id: (int(quantity), Decimal(str(amount))) for order_id, quantity, amount in rows
        }

    by_table = {o.table_id: o for o in open_orders if o.table_id is not None}
    return {
        "tables": [
            {
                "MaBan": table.id,
                "TenBan": table.name,
                "TrangThai": table.status,
                "order": _summary(by_table[table.id], totals) if table.id in by_table else None,
            }
            for table in tables
        ],
        "takeaway": [_summary(o, totals) for o in open_orders if o.table_id is None],
    }
