"""Floor board for the POS: every table with its open order, plus open takeaway orders."""

from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.catalog.models import DiningTable
from app.modules.sales.models import Order, OrderLine
from app.modules.sales.orders import LINE_CANCELLED, OPEN_ORDER_STATUSES
from app.shared.audit import SystemAuditLog


def _summary(order: Order, totals: dict[int, tuple[int, Decimal]]) -> dict[str, Any]:
    quantity, amount = totals.get(order.id, (0, Decimal(0)))
    return {
        "MaOrder": order.id,
        "MaOrderHienThi": order.display_code,
        "MoLuc": order.created_at.isoformat() if order.created_at else None,
        "SoMon": quantity,
        "TamTinh": float(amount),
        "TrangThai": order.status,
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
    current_ids = [t.current_order_id for t in tables if t.current_order_id is not None]
    open_orders = (
        (
            await session.execute(
                select(Order)
                .where(or_(Order.status.in_(OPEN_ORDER_STATUSES), Order.id.in_(current_ids)))
                .order_by(Order.id)
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

    by_id = {o.id: o for o in open_orders}
    # Legacy rows without a pointer can still expose their active order until migrated.
    by_table = {
        o.table_id: o
        for o in open_orders
        if o.table_id is not None and o.status in OPEN_ORDER_STATUSES
    }

    def current(table: DiningTable) -> Order | None:
        if table.status != "Đang phục vụ":
            return None
        if table.current_order_id is not None:
            return by_id.get(table.current_order_id)
        return by_table.get(table.id)

    return {
        "tables": [
            {
                "MaBan": table.id,
                "TenBan": table.name,
                "TrangThai": table.status,
                "MaOrderDangPhucVu": table.current_order_id,
                "order": _summary(order, totals) if (order := current(table)) is not None else None,
            }
            for table in tables
        ],
        "takeaway": [_summary(o, totals) for o in open_orders if o.table_id is None],
    }


async def release_table(
    session: AsyncSession,
    table_id: int,
    expected_order_id: int | None,
    *,
    actor_id: int | None = None,
) -> DiningTable:
    table = (
        await session.execute(
            select(DiningTable)
            .where(DiningTable.id == table_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if table is None or table.is_deleted:
        raise NotFoundError("Không tìm thấy bàn.")
    if table.status != "Đang phục vụ" or table.current_order_id != expected_order_id:
        raise BusinessRuleError("Bàn đã thay đổi. Vui lòng tải lại sơ đồ bàn.")
    from app.modules.sales.reservations import release_active_holds

    await release_active_holds(session, order_id=expected_order_id, table_id=table.id)
    table.status = "Trống"
    table.current_order_id = None
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="RELEASE_TABLE",
            target_entity="BAN",
            target_id=str(table.id),
            before={"MaOrderDangPhucVu": expected_order_id},
            after={"TrangThai": "Trống"},
        )
    )
    await session.flush()
    return table
