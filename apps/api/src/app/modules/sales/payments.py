"""Cashier and manager payment flows (FR-SALE-13, 14, 18…23, 29, 33…35).

State model (report appendix D):

* QR created               ORDER Đang mở → Chờ xác nhận thanh toán,  payment Chờ xác nhận
* QR expires / cancelled   ORDER → Đang mở,                           payment Hết hạn / Đã hủy
* "Yêu cầu xác minh"       ORDER and payment → Chờ xác minh thanh toán
* manager: received        payment Thành công, ORDER Đã thanh toán, one invoice
* manager: reopen          payment Đã hủy,  ORDER Đang mở
* manager: close unpaid    payment and ORDER → "Đóng - chưa thu được tiền" (en dash in the report)

Money that reaches the bank is handled by `webhooks` and `exceptions`. Every function locks the
ORDER row first and the payment second, re-checks the state under the lock and is therefore safe
against a concurrent webhook, a second click or another cashier (NFR-10).
"""

from datetime import timedelta
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.sales.common import (
    audit,
    audit_order,
    ensure_order_is_open,
    invoice_of,
    local_now,
    lock_order,
    lock_order_and_payment,
    order_state,
    order_total,
)
from app.modules.sales.gateways import sepay, simulator
from app.modules.sales.invoices import issue_invoice
from app.modules.sales.models import ItemHold, Order, PaymentTransaction
from app.shared.enums import OrderStatus, PaymentMethod, PaymentStatus

QR_LIFETIME = timedelta(minutes=10)
QR_PENDING = PaymentStatus.CHO_XAC_NHAN.value
QR_SUCCESS = PaymentStatus.THANH_CONG.value
QR_CANCELLED = PaymentStatus.DA_HUY.value
QR_EXPIRED = PaymentStatus.HET_HAN.value
QR_VERIFYING = PaymentStatus.CHO_XAC_MINH.value
QR_CLOSED_UNPAID = PaymentStatus.DONG_CHUA_THU_DUOC_TIEN.value
_NOTE_LIMIT = 255


def sign_payload(payload: str) -> str:
    """Signature the mock gateway would send for `payload` (used by the seed and the harness)."""
    return simulator.sign(payload)


# --- helpers -----------------------------------------------------------------------------------


async def was_reopened(session: AsyncSession, payment_id: int) -> bool:
    """True once a manager reopened payment for this very transaction (FR-SALE-23)."""
    from app.shared.audit import SystemAuditLog

    return (
        await session.execute(
            select(SystemAuditLog.id)
            .where(
                SystemAuditLog.target_entity == "GIAO_DICH_THANH_TOAN",
                SystemAuditLog.target_id == str(payment_id),
                SystemAuditLog.action == "REOPEN_PAYMENT",
            )
            .limit(1)
        )
    ).first() is not None


async def _attempts(
    session: AsyncSession, order_id: int, statuses: tuple[str, ...], *, except_id: int | None = None
) -> list[PaymentTransaction]:
    query = (
        select(PaymentTransaction)
        .where(PaymentTransaction.order_id == order_id, PaymentTransaction.status.in_(statuses))
        .order_by(PaymentTransaction.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    return [p for p in (await session.execute(query)).scalars() if p.id != except_id]


async def supersede_open_attempts(
    session: AsyncSession,
    order: Order,
    *,
    keep: PaymentTransaction | None = None,
    include_verifying: bool = False,
    actor_id: int | None = None,
    why: str,
) -> list[int]:
    """Cancel the order's other unfinished attempts in the caller's transaction (FR-SALE-16)."""
    statuses = (QR_PENDING, QR_VERIFYING) if include_verifying else (QR_PENDING,)
    cancelled: list[int] = []
    for attempt in await _attempts(
        session, order.id, statuses, except_id=keep.id if keep else None
    ):
        before = attempt.status
        attempt.status = QR_CANCELLED
        cancelled.append(attempt.id)
        audit(
            session,
            actor_id=actor_id,
            action="CANCEL_QR_TRANSACTION",
            entity="GIAO_DICH_THANH_TOAN",
            target_id=attempt.id,
            before={"TrangThai": before},
            after={"TrangThai": attempt.status, "MaOrder": order.id},
            reason=why,
        )
    return cancelled


async def _has_unsent_selection(session: AsyncSession, order_id: int) -> bool:
    return (
        await session.execute(
            select(ItemHold.id)
            .where(ItemHold.order_id == order_id, ItemHold.status == "Đang giữ")
            .limit(1)
        )
    ).first() is not None


async def _ready_to_pay(session: AsyncSession, order: Order) -> Decimal:
    """FR-SALE-13: nothing left to send, something to pay, no invoice yet; returns the total."""
    if await invoice_of(session, order.id) is not None:
        raise BusinessRuleError("Order đã có hóa đơn.")
    if await _has_unsent_selection(session, order.id):
        raise BusinessRuleError("Còn lượt chọn gọi thêm chưa gửi hoặc chưa bỏ, hãy xử lý trước.")
    total = await order_total(session, order)
    if total <= 0:
        raise BusinessRuleError("Order chưa có món nào để thanh toán.")
    return total


async def settle_paid(
    session: AsyncSession,
    order: Order,
    payment: PaymentTransaction,
    *,
    actor_id: int | None,
    action: str,
    reason: str | None = None,
    extra: dict[str, Any] | None = None,
):
    """The one place an order becomes "Đã thanh toán": payment, invoice and order together."""
    total = await order_total(session, order)
    before = order_state(order)
    payment.status = QR_SUCCESS
    await session.flush()
    invoice = await issue_invoice(session, order, payment, total=total, actor_id=actor_id)
    now = local_now()
    order.total = total
    order.status = OrderStatus.DA_THANH_TOAN.value
    order.updated_at = now
    order.closed_at = now
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action=action,
        before=before,
        after={
            **order_state(order),
            "MaGiaoDichTT": payment.id,
            "SoHoaDon": invoice.invoice_number,
            **(extra or {}),
        },
        reason=reason,
    )
    await session.flush()
    return invoice


# --- cash and QR -------------------------------------------------------------------------------


async def pay_cash(session: AsyncSession, order_id: int, *, actor_id: int | None = None) -> dict:
    """FR-SALE-13: cash is a payment that is successful on the spot; no waiting state."""
    await expire_stale_qr(session)
    order = await lock_order(session, order_id)
    ensure_order_is_open(order)
    total = await _ready_to_pay(session, order)
    payment = PaymentTransaction(
        order_id=order.id,
        amount=total,
        method=PaymentMethod.TIEN_MAT.value,
        status=QR_SUCCESS,
        business_date=order.business_date,
        created_at=local_now(),
    )
    session.add(payment)
    await session.flush()
    invoice = await settle_paid(
        session,
        order,
        payment,
        actor_id=actor_id,
        action="PAY_CASH",
        extra={"PhuongThuc": "Tiền mặt"},
    )
    return {"payment": payment, "invoice": invoice}


async def start_qr(
    session: AsyncSession, order_id: int, *, actor_id: int | None = None
) -> PaymentTransaction:
    """FR-SALE-14: one live QR per order; creating it locks the order."""
    await expire_stale_qr(session)
    order = await lock_order(session, order_id)
    if order.status == OrderStatus.CHO_XAC_NHAN_THANH_TOAN.value:
        raise BusinessRuleError("Đã có QR đang chờ.")
    ensure_order_is_open(order)
    total = await _ready_to_pay(session, order)

    now = local_now()
    before = order_state(order)
    payment = PaymentTransaction(
        order_id=order.id,
        amount=total,
        method=PaymentMethod.QR.value,
        status=QR_PENDING,
        business_date=order.business_date,
        created_at=now,
        qr_created_at=now,
        deadline=now + QR_LIFETIME,
    )
    session.add(payment)
    await session.flush()
    payment.qr_code = qr_content(payment)
    order.status = OrderStatus.CHO_XAC_NHAN_THANH_TOAN.value
    order.total = total
    order.updated_at = now
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action="CREATE_QR",
        before=before,
        after={**order_state(order), "MaGiaoDichTT": payment.id, "ThoiDiemHetHan": now.isoformat()},
    )
    await session.flush()
    return payment


def qr_content(payment: PaymentTransaction) -> str:
    """Dynamic QR content stored in MaQR: the SePay image URL, or a simulator token."""
    settings = get_settings()
    if settings.payment_gateway == "sepay":
        return sepay.qr_image_url(
            account=settings.sepay_bank_account,
            bank=settings.sepay_bank_code,
            amount=Decimal(str(payment.amount)),
            code=sepay.payment_code(payment.id, settings.sepay_payment_prefix),
        )
    return f"SIM:{payment.id}"


async def qr_fields(session: AsyncSession, payment: PaymentTransaction) -> dict[str, Any]:
    settings = get_settings()
    if settings.payment_gateway != "sepay" or payment.method != PaymentMethod.QR.value:
        return {}
    code = sepay.payment_code(payment.id, settings.sepay_payment_prefix)
    return {
        "qr_image_url": sepay.qr_image_url(
            account=settings.sepay_bank_account,
            bank=settings.sepay_bank_code,
            amount=Decimal(str(payment.amount)),
            code=code,
        ),
        "payment_code": code,
        "bank_code": settings.sepay_bank_code,
        "bank_account": settings.sepay_bank_account,
        "account_name": settings.sepay_account_name,
    }


async def expire_stale_qr(session: AsyncSession) -> int:
    """FR-SALE-18: a QR still waiting after its deadline expires and its order reopens.

    Each payment is re-read under its order's lock, so a webhook or a cancellation that lands
    in between is never overwritten.
    """
    now = local_now()
    due = (
        await session.execute(
            select(PaymentTransaction.id, PaymentTransaction.order_id).where(
                PaymentTransaction.method == PaymentMethod.QR.value,
                PaymentTransaction.status == QR_PENDING,
                or_(
                    PaymentTransaction.deadline < now,
                    (PaymentTransaction.deadline.is_(None))
                    & (PaymentTransaction.created_at < now - QR_LIFETIME),
                ),
            )
        )
    ).all()
    expired = 0
    for payment_id, order_id in due:
        order = await lock_order(session, int(order_id))
        # One conditional write: a confirmation or cancellation that landed after the read
        # above keeps its state, whatever the isolation level or the database.
        result = cast(
            CursorResult,
            await session.execute(
                update(PaymentTransaction)
                .where(PaymentTransaction.id == payment_id, PaymentTransaction.status == QR_PENDING)
                .values(status=QR_EXPIRED)
                .execution_options(synchronize_session="fetch")
            ),
        )
        if not result.rowcount:
            continue
        expired += 1
        before = order_state(order)
        if order.status == OrderStatus.CHO_XAC_NHAN_THANH_TOAN.value and not await _attempts(
            session, order.id, (QR_PENDING,), except_id=payment_id
        ):
            order.status = OrderStatus.DANG_MO.value
            order.updated_at = now
            audit_order(
                session,
                order,
                actor_id=None,
                action="EXPIRE_QR",
                before=before,
                after={**order_state(order), "MaGiaoDichTT": payment_id},
            )
    if expired:
        await session.flush()
    return expired


async def cancel_qr(
    session: AsyncSession, payment_id: int, *, actor_id: int | None = None
) -> PaymentTransaction:
    """FR-SALE-33: the cashier drops a QR that is still valid (e.g. the guest switches to cash)."""
    await expire_stale_qr(session)
    order, payment = await lock_order_and_payment(session, payment_id)
    if payment.method != PaymentMethod.QR.value or payment.status != QR_PENDING:
        raise BusinessRuleError("Chỉ hủy QR đang chờ.")
    before = order_state(order)
    payment.status = QR_CANCELLED
    if order.status == OrderStatus.CHO_XAC_NHAN_THANH_TOAN.value:
        order.status = OrderStatus.DANG_MO.value
        order.updated_at = local_now()
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action="CANCEL_QR_TRANSACTION",
        before=before,
        after={**order_state(order), "MaGiaoDichTT": payment.id},
    )
    await session.flush()
    return payment


# --- verification (FR-SALE-19, 20, 34) -----------------------------------------------------------


async def _ensure_bank_ref_free(
    session: AsyncSession, reference: str | None, payment_id: int
) -> None:
    if reference is None:
        return
    taken = (
        await session.execute(
            select(PaymentTransaction.id).where(
                PaymentTransaction.bank_ref == reference, PaymentTransaction.id != payment_id
            )
        )
    ).first()
    if taken is not None:
        raise BusinessRuleError("Mã giao dịch ngân hàng này đã được ghi cho giao dịch khác.")


async def request_verification(
    session: AsyncSession,
    payment_id: int,
    *,
    reference: str | None,
    evidence: str | None,
    note: str | None,
    actor_id: int | None,
) -> PaymentTransaction:
    """FR-SALE-19: the guest says they paid but nothing arrived; a manager must verify."""
    await expire_stale_qr(session)
    order, payment = await lock_order_and_payment(session, payment_id)
    if payment.method != PaymentMethod.QR.value:
        raise BusinessRuleError("Chỉ yêu cầu xác minh cho giao dịch QR.")
    if payment.exception_status is not None:
        raise BusinessRuleError("Giao dịch ngoại lệ phải xử lý ở danh sách ngoại lệ.")
    if not (reference or note):
        raise BusinessRuleError("Cần nhập mã giao dịch ngân hàng hoặc nội dung ghi chú.")
    if await invoice_of(session, order.id) is not None:
        raise BusinessRuleError("Order đã có hóa đơn.")
    if order.status == OrderStatus.CHO_XAC_MINH_THANH_TOAN.value:
        raise BusinessRuleError("Order đã ở trạng thái chờ xác minh thanh toán.")
    if order.status not in (
        OrderStatus.DANG_MO.value,
        OrderStatus.CHO_XAC_NHAN_THANH_TOAN.value,
    ):
        ensure_order_is_open(order)
    allowed = {QR_PENDING, QR_EXPIRED}
    # A QR the cashier cancelled can still be claimed by a guest who had already paid,
    # but not one that a manager reopened (FR-SALE-23).
    if (
        order.status == OrderStatus.DANG_MO.value
        and payment.status == QR_CANCELLED
        and not await was_reopened(session, payment.id)
    ):
        allowed.add(QR_CANCELLED)
    if payment.status not in allowed:
        raise BusinessRuleError("Giao dịch này không thể chuyển sang chờ xác minh.")
    await _ensure_bank_ref_free(session, reference, payment.id)

    now = local_now()
    before = {**order_state(order), "TrangThaiGiaoDich": payment.status}
    await supersede_open_attempts(
        session, order, keep=payment, actor_id=actor_id, why="Chuyển sang chờ xác minh thanh toán"
    )
    payment.status = QR_VERIFYING
    if reference:
        payment.bank_ref = reference
    if evidence:
        payment.evidence = evidence
    order.status = OrderStatus.CHO_XAC_MINH_THANH_TOAN.value
    order.updated_at = now
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action="REQUEST_PAYMENT_VERIFICATION",
        before=before,
        after={
            **order_state(order),
            "MaGiaoDichTT": payment.id,
            "MaGiaoDichNganHang": reference,
            "AnhChungTu": evidence,
        },
        reason=note,
    )
    await session.flush()
    return payment


async def add_verification_note(
    session: AsyncSession,
    payment_id: int,
    *,
    note: str,
    reference: str | None,
    evidence: str | None,
    actor_id: int | None,
) -> PaymentTransaction:
    """FR-SALE-20/34: record a check or extra evidence; the order keeps waiting."""
    order, payment = await lock_order_and_payment(session, payment_id)
    if payment.status != QR_VERIFYING or order.status != OrderStatus.CHO_XAC_MINH_THANH_TOAN.value:
        raise BusinessRuleError("Giao dịch không ở trạng thái chờ xác minh thanh toán.")
    await _ensure_bank_ref_free(session, reference, payment.id)
    if reference:
        payment.bank_ref = reference
    if evidence:
        payment.evidence = evidence
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action="PAYMENT_VERIFICATION_NOTE",
        after={
            "MaGiaoDichTT": payment.id,
            "MaGiaoDichNganHang": payment.bank_ref,
            "AnhChungTu": payment.evidence,
        },
        reason=note,
    )
    await session.flush()
    return payment


async def confirm_received(
    session: AsyncSession,
    payment_id: int,
    *,
    note: str | None,
    reference: str | None,
    actor_id: int,
) -> dict:
    """FR-SALE-20: the manager found the money; the invoice is issued exactly once."""
    order, payment = await lock_order_and_payment(session, payment_id)
    if payment.exception_status is not None:
        raise BusinessRuleError("Giao dịch ngoại lệ phải xử lý ở danh sách ngoại lệ.")
    if payment.status != QR_VERIFYING or order.status != OrderStatus.CHO_XAC_MINH_THANH_TOAN.value:
        raise BusinessRuleError("Giao dịch không ở trạng thái chờ xác minh thanh toán.")
    if await invoice_of(session, order.id) is not None:
        raise BusinessRuleError("Order đã có hóa đơn.")
    await _ensure_bank_ref_free(session, reference, payment.id)
    if reference:
        payment.bank_ref = reference
    invoice = await settle_paid(
        session,
        order,
        payment,
        actor_id=actor_id,
        action="CONFIRM_PAYMENT_RECEIVED",
        reason=note,
    )
    return {"payment": payment, "invoice": invoice}


async def reopen_payment(
    session: AsyncSession,
    payment_id: int,
    *,
    reason: str,
    outcome: str,
    actor_id: int,
) -> PaymentTransaction:
    """FR-SALE-23: agreed with the guest to collect again; the old attempt is cancelled and kept."""
    order, payment = await lock_order_and_payment(session, payment_id)
    if payment.status != QR_VERIFYING or order.status != OrderStatus.CHO_XAC_MINH_THANH_TOAN.value:
        raise BusinessRuleError("Giao dịch không ở trạng thái chờ xác minh thanh toán.")
    if await invoice_of(session, order.id) is not None:
        raise BusinessRuleError("Order đã có hóa đơn.")
    before = {**order_state(order), "TrangThaiGiaoDich": payment.status}
    payment.status = QR_CANCELLED
    order.status = OrderStatus.DANG_MO.value
    order.updated_at = local_now()
    audit(
        session,
        actor_id=actor_id,
        action="REOPEN_PAYMENT",
        entity="GIAO_DICH_THANH_TOAN",
        target_id=payment.id,
        before={"TrangThai": QR_VERIFYING},
        after={"TrangThai": payment.status, "MaOrder": order.id, "KetQuaXuLy": outcome},
        reason=reason,
    )
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action="REOPEN_PAYMENT",
        before=before,
        after={**order_state(order), "MaGiaoDichTT": payment.id, "KetQuaXuLy": outcome},
        reason=reason,
    )
    await session.flush()
    return payment


async def close_unpaid(
    session: AsyncSession,
    payment_id: int,
    *,
    reason: str,
    outcome: str,
    actor_id: int,
) -> PaymentTransaction:
    """FR-SALE-35: stop chasing the money. No invoice, no revenue, stock stays consumed."""
    order, payment = await lock_order_and_payment(session, payment_id)
    if payment.status != QR_VERIFYING or order.status != OrderStatus.CHO_XAC_MINH_THANH_TOAN.value:
        raise BusinessRuleError("Giao dịch không ở trạng thái chờ xác minh thanh toán.")
    if await invoice_of(session, order.id) is not None:
        raise BusinessRuleError("Order đã có hóa đơn.")
    unpaid = await order_total(session, order)
    before = {**order_state(order), "TrangThaiGiaoDich": payment.status}
    now = local_now()
    payment.status = QR_CLOSED_UNPAID
    order.status = OrderStatus.DONG_CHUA_THU_DUOC_TIEN.value
    order.total = unpaid
    order.updated_at = now
    order.closed_at = now
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action="CLOSE_ORDER_UNPAID",
        before=before,
        after={
            **order_state(order),
            "MaGiaoDichTT": payment.id,
            "SoTienChuaThu": float(unpaid),
            "KetQuaXuLy": outcome,
        },
        reason=reason,
    )
    await session.flush()
    return payment


# --- reads ------------------------------------------------------------------------------------


async def list_order_payments(session: AsyncSession, order_id: int) -> list[PaymentTransaction]:
    return list(
        (
            await session.execute(
                select(PaymentTransaction)
                .where(PaymentTransaction.order_id == order_id)
                .order_by(PaymentTransaction.id.desc())
            )
        )
        .scalars()
        .all()
    )


async def payment_payload(session: AsyncSession, payment: PaymentTransaction) -> dict[str, Any]:
    item: dict[str, Any] = {
        "MaGiaoDich": payment.id,
        "MaOrder": payment.order_id,
        "PhuongThuc": payment.method,
        "TrangThai": payment.status,
        "SoTien": float(payment.amount),
        "ThoiDiemTaoQR": payment.qr_created_at.isoformat() if payment.qr_created_at else None,
        "ThoiDiemHetHan": payment.deadline.isoformat() if payment.deadline else None,
        "MaThamChieuNganHang": payment.bank_ref,
        "MaGiaoDichNganHang": payment.bank_ref,
        "AnhChungTu": payment.evidence,
        "TrangThaiNgoaiLe": payment.exception_status,
        "SoTienNgoaiLe": (
            float(payment.exception_amount) if payment.exception_amount is not None else None
        ),
        "MaThamChieuHoan": payment.refund_reference,
    }
    if payment.status == QR_PENDING:
        item.update(await qr_fields(session, payment))
    return item


async def get_payment(session: AsyncSession, payment_id: int) -> PaymentTransaction:
    payment = await session.get(PaymentTransaction, payment_id)
    if payment is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    return payment
