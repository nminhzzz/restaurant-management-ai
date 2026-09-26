"""Sales payments — cash, QR, webhook, reconciliation and invoices (FR-SALE-14…19, 23, 29).

Gateway specifics live in app.modules.sales.gateways; this module owns the business
flow shared by every gateway.
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import BusinessRuleError, NotFoundError, UnauthenticatedError
from app.modules.sales.gateways import sepay, simulator
from app.modules.sales.models import Invoice, Order, OrderLine, PaymentTransaction
from app.modules.sales.orders import LINE_CANCELLED
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


def sign_payload(payload: str) -> str:
    """Signature the mock gateway would send for `payload`.

    Exposed so the seed and the harness drive the webhook the same way the gateway
    does, instead of re-implementing the signing rule.
    """
    return simulator.sign(payload)


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

    total = await order_total(session, order)
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
        amount=await order_total(session, order),
        method="QR",
        status=QR_PENDING,
        business_date=business_date.business_date_of(now),
        created_at=now,
        deadline=now + QR_LIFETIME,
    )
    session.add(payment)
    await session.flush()
    return payment


async def confirm_payment(
    session: AsyncSession, payment: PaymentTransaction, *, bank_ref: str | None = None
) -> dict:
    """Settle a pending QR payment whose amount the caller has already checked."""
    order = await session.get(Order, payment.order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    await session.execute(select(Order).where(Order.id == order.id).with_for_update())
    total = await order_total(session, order)
    payment.status = QR_SUCCESS
    if bank_ref is not None:
        payment.bank_ref = bank_ref
    await session.flush()
    invoice = await _issue_invoice(
        session, order, business_date_value=payment.business_date, total=total
    )
    _settle(order, "Đã thanh toán", business_date.now())
    await _free_table(session, order)
    await session.flush()
    return {"payment": payment, "invoice": invoice}


async def to_reconciliation(
    session: AsyncSession, payment: PaymentTransaction, *, bank_ref: str | None, action: str
) -> None:
    """Money arrived but cannot be matched automatically; a manager resolves it."""
    payment.status = QR_RECONCILING
    if bank_ref is not None:
        payment.bank_ref = bank_ref
    order = await session.get(Order, payment.order_id)
    if order is not None:
        _settle(order, QR_RECONCILING, business_date.now())
    session.add(
        SystemAuditLog(
            user_id=None,
            action=action,
            target_entity="GIAO_DICH_THANH_TOAN",
            target_id=str(payment.id),
        )
    )
    await session.flush()


async def qr_fields(session: AsyncSession, payment: PaymentTransaction) -> dict[str, Any]:
    settings = get_settings()
    if settings.payment_gateway != "sepay" or payment.method != "QR":
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


async def handle_sepay_transfer(session: AsyncSession, body: dict[str, Any]) -> str:
    settings = get_settings()
    try:
        transfer = sepay.parse_transfer(body)
    except ValueError:
        logger.warning("Ignored a SePay payload without id or amount")
        return "ignored"
    if transfer.direction != "in":
        return "ignored"

    bank_ref = f"sepay:{transfer.sepay_id}"
    seen = (
        await session.execute(
            select(PaymentTransaction.id).where(PaymentTransaction.bank_ref == bank_ref)
        )
    ).first()
    if seen is not None:
        return "duplicate"

    payment_id = sepay.payment_id_of(transfer, settings.sepay_payment_prefix)
    payment = None
    if payment_id is not None:
        await expire_stale_qr(session)
        payment = (
            await session.execute(
                select(PaymentTransaction)
                .where(PaymentTransaction.id == payment_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
    if payment is None:
        session.add(
            SystemAuditLog(
                user_id=None,
                action="WEBHOOK_UNMATCHED",
                target_entity="GIAO_DICH_THANH_TOAN",
                target_id=bank_ref,
            )
        )
        await session.flush()
        return "unmatched"
    if payment.status == QR_SUCCESS:
        return "duplicate"

    order = await session.get(Order, payment.order_id)
    if order is None or order.status != "Đang mở":
        # Money for an order that is already settled or cancelled: record it for a human,
        # never reopen or re-invoice the order.
        payment.bank_ref = payment.bank_ref or bank_ref
        session.add(
            SystemAuditLog(
                user_id=None,
                action="WEBHOOK_UNMATCHED",
                target_entity="GIAO_DICH_THANH_TOAN",
                target_id=str(payment.id),
            )
        )
        await session.flush()
        return "unmatched"

    total = await order_total(session, order)
    if payment.status == QR_PENDING and transfer.amount == total:
        await confirm_payment(session, payment, bank_ref=bank_ref)
        return "confirmed"
    await to_reconciliation(
        session, payment, bank_ref=bank_ref, action="WEBHOOK_NEEDS_RECONCILIATION"
    )
    return "reconciling"


async def check_payment(session: AsyncSession, payment_id: int) -> PaymentTransaction:
    settings = get_settings()
    payment = await session.get(PaymentTransaction, payment_id)
    if payment is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    if (
        settings.payment_gateway == "sepay"
        and settings.sepay_api_token
        and payment.status == QR_PENDING
    ):
        rows = await sepay.recent_transfers(
            api_url=settings.sepay_api_url,
            token=settings.sepay_api_token,
            account=settings.sepay_bank_account,
        )
        for row in rows:
            body = sepay.transfer_from_listing(row)
            transfer = sepay.parse_transfer(body)
            if sepay.payment_id_of(transfer, settings.sepay_payment_prefix) == payment.id:
                await handle_sepay_transfer(session, body)
                break
        await session.refresh(payment)
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

    if not simulator.verify(f"{payment.id}:{amount}", str(signature)):
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
    total = await order_total(session, order)
    if amount is not None and Decimal(str(amount)) != total:
        raise BusinessRuleError("Số tiền không khớp.")

    return await confirm_payment(session, payment)


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
        total = await order_total(session, order)
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
