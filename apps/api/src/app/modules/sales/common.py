"""Locking, clock and audit helpers shared by the sales services.

Every service that changes an order takes the ORDER row lock first and the payment rows
second, so a webhook, a cashier and a manager acting at once queue up instead of deadlocking
or overwriting each other (FR-SALE-17, FR-SALE-20, NFR-10).
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.catalog.models import DiningTable
from app.modules.sales.models import Invoice, Order, OrderLine, PaymentTransaction
from app.modules.settings.service import effective_business_day_start
from app.shared import business_date
from app.shared.audit import SystemAuditLog
from app.shared.enums import OrderLineStatus, OrderStatus

OPEN_ORDER_STATUSES: frozenset[str] = frozenset({OrderStatus.DANG_MO.value})
LINE_CANCELLED = OrderLineStatus.DA_HUY.value

_LOCK_MESSAGES = {
    OrderStatus.CHO_XAC_NHAN_THANH_TOAN.value: (
        "Order đang chờ xác nhận thanh toán QR nên đã bị khóa. "
        "Hãy hủy mã QR hoặc chờ mã hết hạn trước."
    ),
    OrderStatus.CHO_XAC_MINH_THANH_TOAN.value: (
        "Order đang chờ xác minh thanh toán nên đã bị khóa."
    ),
    OrderStatus.DA_THANH_TOAN.value: "Order đã thanh toán nên đã bị khóa.",
    OrderStatus.DONG_CHUA_THU_DUOC_TIEN.value: (
        "Order đã đóng vì chưa thu được tiền nên đã bị khóa."
    ),
}


def ensure_order_is_open(order: Order) -> None:
    """FR-SALE-22: the single choke point; every state but "Đang mở" rejects mutations."""
    if order.status not in OPEN_ORDER_STATUSES:
        raise BusinessRuleError(_LOCK_MESSAGES.get(order.status, "Order đã đóng."))


def local_now() -> datetime:
    return business_date.local_now()


async def current_business_date(session: AsyncSession) -> date:
    moment = business_date.now()
    start = await effective_business_day_start(session, moment)
    return business_date.business_date_of(moment, start)


async def lock_order(session: AsyncSession, order_id: int) -> Order:
    order = (
        await session.execute(
            select(Order)
            .where(Order.id == order_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    return order


async def lock_payment(session: AsyncSession, payment_id: int) -> PaymentTransaction:
    payment = (
        await session.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.id == payment_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if payment is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    return payment


async def lock_order_and_payment(
    session: AsyncSession, payment_id: int
) -> tuple[Order, PaymentTransaction]:
    """Order first, then the payment: the same order every other flow uses."""
    order_id = (
        await session.execute(
            select(PaymentTransaction.order_id).where(PaymentTransaction.id == payment_id)
        )
    ).scalar_one_or_none()
    if order_id is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    order = await lock_order(session, int(order_id))
    return order, await lock_payment(session, payment_id)


async def lock_table(session: AsyncSession, table_id: int) -> DiningTable | None:
    return (
        await session.execute(
            select(DiningTable)
            .where(DiningTable.id == table_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()


async def order_total(session: AsyncSession, order: Order) -> Decimal:
    lines = (
        (
            await session.execute(
                select(OrderLine).where(
                    OrderLine.order_id == order.id, OrderLine.status != LINE_CANCELLED
                )
            )
        )
        .scalars()
        .all()
    )
    return sum((Decimal(str(line.unit_price)) * int(line.quantity) for line in lines), Decimal(0))


async def refresh_order_total(session: AsyncSession, order: Order) -> Decimal:
    total = await order_total(session, order)
    order.total = total
    return total


async def invoice_of(session: AsyncSession, order_id: int) -> Invoice | None:
    return (
        await session.execute(select(Invoice).where(Invoice.order_id == order_id))
    ).scalar_one_or_none()


def audit(
    session: AsyncSession,
    *,
    actor_id: int | None,
    action: str,
    entity: str,
    target_id: int | str,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
) -> SystemAuditLog:
    """One FR-SET-08 row. The timestamp is Asia/Ho_Chi_Minh, set here, not by the DB server."""
    entry = SystemAuditLog(
        user_id=actor_id,
        action=action,
        target_entity=entity,
        target_id=str(target_id),
        before=before,
        after=after,
        reason=reason[:255] if reason else None,
        occurred_at=local_now(),
    )
    session.add(entry)
    return entry


def audit_order(
    session: AsyncSession,
    order: Order,
    *,
    actor_id: int | None,
    action: str,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
) -> SystemAuditLog:
    """Order-level entry (DoiTuong = ORDER): the reports read the latest one for reason/closer."""
    return audit(
        session,
        actor_id=actor_id,
        action=action,
        entity="ORDER",
        target_id=order.id,
        before=before,
        after=after,
        reason=reason,
    )


def order_state(order: Order) -> dict[str, Any]:
    return {"TrangThai": order.status, "TongTien": float(order.total or 0)}
