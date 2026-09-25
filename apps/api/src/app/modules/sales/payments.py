"""Sales payments — cash, QR, webhook, reconciliation and invoices (FR-SALE-14…19, 23, 29).

The QR gateway is not chosen yet (master roadmap Q1), so signature handling is a
self-contained HMAC adapter: `_gateway_sign` produces the signature and `_verify_signature`
checks it with a constant-time comparison. Swapping in a real gateway only replaces these
two functions; the business flow below is unchanged.
"""

import hashlib
import hmac
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import BusinessRuleError, NotFoundError, UnauthenticatedError
from app.modules.sales.models import Invoice, Order, OrderLine, PaymentTransaction
from app.shared import business_date
from app.shared.audit import SystemAuditLog

logger = logging.getLogger(__name__)

QR_LIFETIME = timedelta(minutes=10)
QR_PENDING = "Chờ xác nhận"
QR_SUCCESS = "Thành công"
QR_CANCELLED = "Đã hủy"
QR_EXPIRED = "Hết hạn"
QR_RECONCILING = "Chờ đối soát"
QR_DISPUTED = "Tranh chấp"


def _require_webhook_secret() -> str:
    """Signing key for the mock gateway (never a real one — see Q1)."""
    secret = get_settings().payment_webhook_secret
    return secret or "test-secret"


def _gateway_sign(payload: str) -> str:
    return hmac.new(
        _require_webhook_secret().encode(), payload.encode(), hashlib.sha256
    ).hexdigest()


def _verify_signature(payload: str, signature: str) -> bool:
    return hmac.compare_digest(_gateway_sign(payload), signature)


def sign_payload(payload: str) -> str:
    """Signature the mock gateway would send for `payload`.

    Exposed so the seed and the harness drive the webhook the same way the gateway
    does, instead of re-implementing the signing rule.
    """
    return _gateway_sign(payload)


async def _order_total(session: AsyncSession, order: Order) -> Decimal:
    lines = (
        (await session.execute(select(OrderLine).where(OrderLine.order_id == order.id)))
        .scalars()
        .all()
    )
    return sum((Decimal(str(line.unit_price)) * int(line.quantity) for line in lines), Decimal(0))


def _settle(order: Order, status: str, now: datetime) -> None:
    order.status = status
    order.updated_at = now


async def _free_table(session: AsyncSession, order: Order) -> None:
    if order.table_id is None:
        return
    from app.modules.catalog.models import DiningTable

    table = await session.get(DiningTable, order.table_id)
    if table is not None:
        table.status = "Trống"


async def _issue_invoice(
    session: AsyncSession, order: Order, *, business_date_value: date, total: Decimal
) -> Invoice:
    invoice = Invoice(
        order_id=order.id, business_date=business_date_value, total=total, print_count=1
    )
    session.add(invoice)
    await session.flush()
    return invoice


async def pay_cash(session: AsyncSession, order_id: int, *, actor_id: int | None = None) -> dict:
    await expire_stale_qr(session)
    now = business_date.now()
    order = await session.get(Order, order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    await session.execute(select(Order).where(Order.id == order_id).with_for_update())
    from app.modules.sales.orders import ensure_order_is_open

    ensure_order_is_open(order)
    existing = (
        await session.execute(select(Invoice).where(Invoice.order_id == order.id))
    ).scalar_one_or_none()
    if existing is not None:
        raise BusinessRuleError("Order đã có hóa đơn.")

    total = await _order_total(session, order)
    bd = business_date.business_date_of(now)
    payment = PaymentTransaction(
        order_id=order.id,
        amount=total,
        method="Tiền mặt",
        status=QR_SUCCESS,
        business_date=bd,
    )
    session.add(payment)
    await session.flush()
    invoice = await _issue_invoice(session, order, business_date_value=bd, total=total)
    _settle(order, "Đã thanh toán", now)
    await _free_table(session, order)
    await session.flush()
    return {"payment": payment, "invoice": invoice}


async def start_qr(
    session: AsyncSession, order_id: int, *, actor_id: int | None = None
) -> PaymentTransaction:
    await expire_stale_qr(session)
    order = await session.get(Order, order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    from app.modules.sales.orders import ensure_order_is_open

    ensure_order_is_open(order)
    live = (
        await session.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.order_id == order.id,
                PaymentTransaction.method == "QR",
                PaymentTransaction.status == QR_PENDING,
            )
        )
    ).scalar_one_or_none()
    if live is not None:
        raise BusinessRuleError("Đã có QR đang chờ.")

    now = business_date.now()
    payment = PaymentTransaction(
        order_id=order.id,
        amount=await _order_total(session, order),
        method="QR",
        status=QR_PENDING,
        business_date=business_date.business_date_of(now),
        created_at=now,
        deadline=now + QR_LIFETIME,
    )
    session.add(payment)
    await session.flush()
    return payment


async def handle_webhook(session: AsyncSession, payload: dict) -> dict:
    payment_id = payload.get("payment_id") or payload.get("MaGiaoDich")
    amount = payload.get("amount") or payload.get("SoTien")
    signature = payload.get("signature") or payload.get("ChuKy") or ""
    if payment_id is None:
        raise NotFoundError("Giao dịch không tồn tại.")

    payment = (
        await session.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.id == int(payment_id))
            .with_for_update()
        )
    ).scalar_one_or_none()
    if payment is None:
        raise NotFoundError("Giao dịch không tồn tại.")

    if not _verify_signature(f"{payment.id}:{amount}", str(signature)):
        logger.warning("Rejected payment webhook with a bad signature payment=%s", payment.id)
        session.add(
            SystemAuditLog(
                user_id=None,
                action="WEBHOOK_REJECTED",
                target_entity="GIAO_DICH_THANH_TOAN",
                target_id=str(payment.id),
            )
        )
        await session.flush()
        raise UnauthenticatedError("Chữ ký không hợp lệ.")

    if payment.status == QR_SUCCESS:
        return {"payment": payment}
    if payment.status != QR_PENDING:
        raise BusinessRuleError("Giao dịch không ở trạng thái chờ.")

    order = await session.get(Order, payment.order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    await session.execute(select(Order).where(Order.id == order.id).with_for_update())
    total = await _order_total(session, order)
    if amount is not None and Decimal(str(amount)) != total:
        raise BusinessRuleError("Số tiền không khớp.")

    now = business_date.now()
    payment.status = QR_SUCCESS
    await session.flush()
    invoice = await _issue_invoice(
        session, order, business_date_value=payment.business_date, total=total
    )
    _settle(order, "Đã thanh toán", now)
    await _free_table(session, order)
    await session.flush()
    return {"payment": payment, "invoice": invoice}


async def cancel_qr(
    session: AsyncSession, payment_id: int, *, actor_id: int | None = None
) -> PaymentTransaction:
    payment = await session.get(PaymentTransaction, payment_id)
    if payment is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    if payment.status != QR_PENDING:
        raise BusinessRuleError("Chỉ hủy QR đang chờ.")
    payment.status = QR_CANCELLED
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CANCEL_QR_TRANSACTION",
            target_entity="GIAO_DICH_THANH_TOAN",
            target_id=str(payment.id),
        )
    )
    await session.flush()
    return payment


async def expire_stale_qr(session: AsyncSession) -> int:
    now = business_date.now()
    pending = (
        (
            await session.execute(
                select(PaymentTransaction).where(
                    PaymentTransaction.method == "QR",
                    PaymentTransaction.status == QR_PENDING,
                )
            )
        )
        .scalars()
        .all()
    )
    expired = 0
    for payment in pending:
        deadline = payment.deadline
        if deadline is None:
            deadline = payment.created_at + QR_LIFETIME if payment.created_at else None
        if deadline is not None and now > deadline:
            payment.status = QR_EXPIRED
            expired += 1
    if expired:
        await session.flush()
    return expired


async def mark_for_reconciliation(
    session: AsyncSession, payment_id: int, *, actor_id: int | None = None
) -> PaymentTransaction:
    await expire_stale_qr(session)
    payment = await session.get(PaymentTransaction, payment_id)
    if payment is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    if payment.status != QR_EXPIRED:
        raise BusinessRuleError("Chỉ đối soát QR đã hết hạn.")
    payment.status = QR_RECONCILING
    order = await session.get(Order, payment.order_id)
    if order is not None:
        _settle(order, QR_RECONCILING, business_date.now())
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="FLAG_RECONCILIATION",
            target_entity="GIAO_DICH_THANH_TOAN",
            target_id=str(payment.id),
        )
    )
    await session.flush()
    return payment


async def record_bank_reference(
    session: AsyncSession,
    payment_id: int,
    reference: str,
    evidence: str | None = None,
    *,
    actor_id: int | None = None,
) -> PaymentTransaction:
    payment = await session.get(PaymentTransaction, payment_id)
    if payment is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    payment.bank_ref = reference
    payment.evidence = evidence
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="RECORD_BANK_REFERENCE",
            target_entity="GIAO_DICH_THANH_TOAN",
            target_id=str(payment.id),
        )
    )
    await session.flush()
    return payment


async def resolve_reconciliation(
    session: AsyncSession, payment_id: int, outcome: str, *, actor_id: int | None = None
) -> PaymentTransaction:
    payment = await session.get(PaymentTransaction, payment_id)
    if payment is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    if payment.status != QR_RECONCILING:
        raise BusinessRuleError("Giao dịch không ở trạng thái chờ đối soát.")
    if outcome not in ("received", "not_received"):
        raise BusinessRuleError("outcome phải là received/not_received.")

    now = business_date.now()
    order = await session.get(Order, payment.order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    if outcome == "received":
        payment.status = QR_SUCCESS
        total = await _order_total(session, order)
        await _issue_invoice(session, order, business_date_value=payment.business_date, total=total)
        _settle(order, "Đã thanh toán", now)
        await _free_table(session, order)
    else:
        payment.status = QR_DISPUTED
        _settle(order, QR_DISPUTED, now)
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="RESOLVE_RECONCILIATION",
            target_entity="GIAO_DICH_THANH_TOAN",
            target_id=str(payment.id),
            after={"ketQua": outcome},
        )
    )
    await session.flush()
    return payment


async def reprint_invoice(session: AsyncSession, order_id: int) -> Invoice:
    invoice = (
        await session.execute(select(Invoice).where(Invoice.order_id == order_id))
    ).scalar_one_or_none()
    if invoice is None:
        raise NotFoundError("Hóa đơn không tồn tại.")
    invoice.print_count = int(invoice.print_count) + 1
    await session.flush()
    return invoice
