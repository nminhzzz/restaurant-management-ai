"""Manager handling of QR payment exceptions (FR-SALE-16, FR-SALE-17, FR-REP-02).

An exception is a GIAO_DICH_THANH_TOAN row created by the webhook for money that could not be
applied automatically. It stays "Chờ xử lý", outside revenue, until a manager either

* applies it to the order (the order was reopened, or closed without payment, and the money
  covers it exactly): the order becomes "Đã thanh toán" with one invoice; or
* records the refund made outside the system: amount, reference, who and when.
"""

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError
from app.modules.sales.common import (
    audit,
    invoice_of,
    local_now,
    lock_order_and_payment,
    order_total,
)
from app.modules.sales.models import Order, PaymentTransaction
from app.modules.sales.payments import settle_paid, supersede_open_attempts
from app.shared.enums import OrderStatus, PaymentExceptionStatus

# Orders the money can still be applied to; a paid, cancelled or auto-closed order needs a refund.
_APPLICABLE_ORDER_STATUSES = frozenset(
    {
        OrderStatus.DANG_MO.value,
        OrderStatus.CHO_XAC_NHAN_THANH_TOAN.value,
        OrderStatus.CHO_XAC_MINH_THANH_TOAN.value,
        OrderStatus.DONG_CHUA_THU_DUOC_TIEN.value,
    }
)


def _pending(entry: PaymentTransaction) -> bool:
    return entry.exception_status == PaymentExceptionStatus.CHO_XU_LY.value


async def can_apply(session: AsyncSession, order: Order, entry: PaymentTransaction) -> bool:
    return (
        _pending(entry)
        and order.status in _APPLICABLE_ORDER_STATUSES
        and await invoice_of(session, order.id) is None
        and entry.exception_amount is not None
        and Decimal(str(entry.exception_amount)) == await order_total(session, order)
    )


async def list_exceptions(session: AsyncSession, status: str | None) -> list[dict[str, Any]]:
    """Exceptions newest first; `status=None` lists all, otherwise one TrangThaiNgoaiLe."""
    query = (
        select(PaymentTransaction, Order)
        .join(Order, Order.id == PaymentTransaction.order_id)
        .where(PaymentTransaction.exception_status.is_not(None))
        .order_by(PaymentTransaction.id.desc())
    )
    if status is not None:
        query = query.where(PaymentTransaction.exception_status == status)
    items = []
    for entry, order in (await session.execute(query)).all():
        items.append(
            {
                "MaGiaoDich": entry.id,
                "MaOrder": order.id,
                "MaOrderHienThi": order.display_code,
                "TrangThaiOrder": order.status,
                "TongTienOrder": float(await order_total(session, order)),
                "SoTienNgoaiLe": float(entry.exception_amount or 0),
                "MaGiaoDichCong": entry.gateway_transaction_id,
                "MaGiaoDichNganHang": entry.bank_ref,
                "TrangThaiNgoaiLe": entry.exception_status,
                "MaThamChieuHoan": entry.refund_reference,
                "ThoiDiemNhan": entry.created_at.isoformat() if entry.created_at else None,
                "ThoiDiemXuLy": (
                    entry.exception_handled_at.isoformat() if entry.exception_handled_at else None
                ),
                "NguoiXuLy": entry.exception_handled_by,
                "CoTheApDung": await can_apply(session, order, entry),
            }
        )
    return items


async def apply_exception(
    session: AsyncSession, payment_id: int, *, note: str | None, actor_id: int
) -> PaymentTransaction:
    """FR-SALE-17 (a)/(b): lock the order and the rows, re-check, settle once."""
    order, entry = await lock_order_and_payment(session, payment_id)
    if not _pending(entry):
        raise BusinessRuleError("Khoản ngoại lệ này đã được xử lý.")
    if not await can_apply(session, order, entry):
        raise BusinessRuleError(
            "Không thể áp dụng khoản này cho order (order đã thanh toán, đã hủy, "
            "hoặc số tiền không còn khớp); hãy ghi nhận hoàn tiền."
        )
    await supersede_open_attempts(
        session,
        order,
        keep=entry,
        include_verifying=True,
        actor_id=actor_id,
        why="Áp dụng khoản tiền ngoại lệ cho order",
    )
    entry.exception_status = PaymentExceptionStatus.DA_AP_DUNG.value
    entry.exception_handled_at = local_now()
    entry.exception_handled_by = actor_id
    await settle_paid(
        session,
        order,
        entry,
        actor_id=actor_id,
        action="APPLY_PAYMENT_EXCEPTION",
        reason=note,
        extra={"MaGiaoDichCong": entry.gateway_transaction_id},
    )
    audit(
        session,
        actor_id=actor_id,
        action="APPLY_PAYMENT_EXCEPTION",
        entity="GIAO_DICH_THANH_TOAN",
        target_id=entry.id,
        before={"TrangThaiNgoaiLe": PaymentExceptionStatus.CHO_XU_LY.value},
        after={"TrangThaiNgoaiLe": entry.exception_status, "MaOrder": order.id},
        reason=note,
    )
    await session.flush()
    return entry


async def refund_exception(
    session: AsyncSession,
    payment_id: int,
    *,
    refund_reference: str,
    note: str | None,
    actor_id: int,
) -> PaymentTransaction:
    """FR-SALE-17 (c): money refunded outside the system; keep reference, who and when."""
    _, entry = await lock_order_and_payment(session, payment_id)
    if not _pending(entry):
        raise BusinessRuleError("Khoản ngoại lệ này đã được xử lý.")
    entry.exception_status = PaymentExceptionStatus.DA_HOAN_TIEN.value
    entry.refund_reference = refund_reference
    entry.exception_handled_at = local_now()
    entry.exception_handled_by = actor_id
    audit(
        session,
        actor_id=actor_id,
        action="REFUND_PAYMENT_EXCEPTION",
        entity="GIAO_DICH_THANH_TOAN",
        target_id=entry.id,
        before={"TrangThaiNgoaiLe": PaymentExceptionStatus.CHO_XU_LY.value},
        after={
            "TrangThaiNgoaiLe": entry.exception_status,
            "SoTienHoan": float(entry.exception_amount or 0),
            "MaThamChieuHoan": refund_reference,
            "MaOrder": entry.order_id,
        },
        reason=note,
    )
    await session.flush()
    return entry
