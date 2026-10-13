"""Money arriving from the payment gateway (FR-SALE-15, FR-SALE-16, NFR-08).

Both gateways (the local simulator and SePay) end in `process_incoming_money`:

* the gateway's own transaction id is UNIQUE, so the same notification twice is one event;
* a transfer that matches the QR attempt, the order and its current total settles the order,
  even when the QR expired or was cancelled in the meantime (late payment);
* anything else (wrong amount, order already paid, closed, cancelled or reopened) is recorded
  as a payment exception for a manager and never changes the order (FR-SALE-17);
* nothing is ever settled from a request that failed authentication, and neither the API key
  nor the raw payload reaches a log.
"""

import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import BusinessRuleError, NotFoundError, UnauthenticatedError
from app.modules.sales.common import (
    audit,
    invoice_of,
    local_now,
    lock_order_and_payment,
    order_total,
)
from app.modules.sales.gateways import sepay
from app.modules.sales.models import PaymentTransaction
from app.modules.sales.payments import (
    QR_CANCELLED,
    QR_EXPIRED,
    QR_PENDING,
    QR_SUCCESS,
    QR_VERIFYING,
    expire_stale_qr,
    settle_paid,
    supersede_open_attempts,
    was_reopened,
)
from app.shared.enums import OrderStatus, PaymentExceptionStatus, PaymentMethod

logger = logging.getLogger(__name__)

_CONTENT_LIMIT = 2000  # GIAO_DICH_THANH_TOAN.NoiDungWebhook
_LATE_OK_STATUSES = frozenset({QR_PENDING, QR_EXPIRED, QR_CANCELLED, QR_VERIFYING})
_PAYABLE_ORDER_STATUSES = frozenset(
    {
        OrderStatus.DANG_MO.value,
        OrderStatus.CHO_XAC_NHAN_THANH_TOAN.value,
        OrderStatus.CHO_XAC_MINH_THANH_TOAN.value,
    }
)


def _summary(fields: dict[str, Any], reason: str | None = None) -> str:
    """The few notification fields worth keeping (never the headers, never the API key)."""
    data = {key: value for key, value in fields.items() if value not in (None, "")}
    if reason:
        data["LyDoNgoaiLe"] = reason
    return json.dumps(data, ensure_ascii=False, default=str)[:_CONTENT_LIMIT]


async def _exists(session: AsyncSession, column, value: str) -> bool:
    return (
        await session.execute(select(PaymentTransaction.id).where(column == value).limit(1))
    ).first() is not None


async def _record_unmatched(session: AsyncSession, gateway_id: str, why: str) -> str:
    """Money we cannot tie to any attempt: logged for a human (FR-SALE-15), nothing else changes."""
    logger.warning("Unmatched gateway transfer (%s)", why)
    audit(
        session,
        actor_id=None,
        action="WEBHOOK_UNMATCHED",
        entity="GIAO_DICH_THANH_TOAN",
        target_id=f"cong:{gateway_id}"[:50],
        after={"LyDo": why},
    )
    await session.flush()
    return "unmatched"


async def _record_exception(
    session: AsyncSession,
    payment: PaymentTransaction,
    *,
    gateway_id: str,
    amount: Decimal,
    reference: str | None,
    summary: dict[str, Any],
    why: str,
) -> str:
    """FR-SALE-16: a pending exception row, one per gateway transaction id."""
    reference_free = reference is not None and not await _exists(
        session, PaymentTransaction.bank_ref, reference
    )
    entry = PaymentTransaction(
        order_id=payment.order_id,
        amount=amount,
        method=PaymentMethod.QR.value,
        status=QR_CANCELLED,
        business_date=payment.business_date,
        created_at=local_now(),
        gateway_transaction_id=gateway_id,
        bank_ref=reference if reference_free else None,
        webhook_content=_summary(summary, why),
        exception_status=PaymentExceptionStatus.CHO_XU_LY.value,
        exception_amount=amount,
    )
    session.add(entry)
    await session.flush()
    audit(
        session,
        actor_id=None,
        action="QR_EXCEPTION_RECORDED",
        entity="GIAO_DICH_THANH_TOAN",
        target_id=entry.id,
        after={
            "MaOrder": payment.order_id,
            "MaGiaoDichGoc": payment.id,
            "MaGiaoDichCong": gateway_id,
            "SoTienNgoaiLe": float(amount),
        },
        reason=why,
    )
    return "exception"


async def process_incoming_money(
    session: AsyncSession,
    *,
    payment_id: int | None,
    gateway_id: str,
    amount: Decimal,
    reference: str | None,
    summary: dict[str, Any],
) -> str:
    """Apply one verified incoming transfer. Returns what happened, never raises on bad money."""
    await expire_stale_qr(session)
    if await _exists(session, PaymentTransaction.gateway_transaction_id, gateway_id):
        return "duplicate"

    if reference is not None:
        # The same transfer, already confirmed by hand: attach the gateway id, collect nothing.
        manual = (
            await session.execute(
                select(PaymentTransaction)
                .where(
                    PaymentTransaction.bank_ref == reference,
                    PaymentTransaction.status == QR_SUCCESS,
                    PaymentTransaction.gateway_transaction_id.is_(None),
                )
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalar_one_or_none()
        if manual is not None and Decimal(str(manual.amount)) == amount:
            manual.gateway_transaction_id = gateway_id
            manual.webhook_content = _summary(summary)
            audit(
                session,
                actor_id=None,
                action="LINK_GATEWAY_TRANSACTION",
                entity="GIAO_DICH_THANH_TOAN",
                target_id=manual.id,
                after={"MaGiaoDichCong": gateway_id},
            )
            await session.flush()
            return "matched_manual"

    if payment_id is None:
        return await _record_unmatched(session, gateway_id, "no payment code in the transfer")
    try:
        order, payment = await lock_order_and_payment(session, payment_id)
    except NotFoundError:
        return await _record_unmatched(session, gateway_id, "unknown payment code")
    if payment.method != PaymentMethod.QR.value:
        return await _record_unmatched(session, gateway_id, "payment code of a cash payment")

    total = await order_total(session, order)
    has_invoice = await invoice_of(session, order.id) is not None
    confirmable = (
        payment.status in _LATE_OK_STATUSES
        and order.status in _PAYABLE_ORDER_STATUSES
        and not has_invoice
        and amount == total
        and not (payment.status == QR_CANCELLED and await was_reopened(session, payment.id))
    )
    if not confirmable:
        if has_invoice or order.status == OrderStatus.DA_THANH_TOAN.value:
            why = "order already paid"
        elif order.status not in _PAYABLE_ORDER_STATUSES:
            why = "order closed or cancelled"
        elif payment.status not in _LATE_OK_STATUSES:
            why = "payment attempt already finished"
        elif amount != total:
            why = "amount does not match the order"
        else:
            why = "payment was reopened by a manager"
        return await _record_exception(
            session,
            payment,
            gateway_id=gateway_id,
            amount=amount,
            reference=reference,
            summary=summary,
            why=why,
        )

    # FR-SALE-16: another QR attempt without money is dropped in the same transaction.
    await supersede_open_attempts(
        session,
        order,
        keep=payment,
        include_verifying=True,
        why="Đã nhận tiền cho giao dịch QR trước",
    )
    payment.gateway_transaction_id = gateway_id
    payment.webhook_content = _summary(summary)
    if (
        reference is not None
        and payment.bank_ref is None
        and not await _exists(session, PaymentTransaction.bank_ref, reference)
    ):
        payment.bank_ref = reference
    await settle_paid(
        session,
        order,
        payment,
        actor_id=None,
        action="CONFIRM_QR_PAYMENT",
        extra={"MaGiaoDichCong": gateway_id},
    )
    return "confirmed"


# --- SePay -------------------------------------------------------------------------------------


async def handle_sepay_transfer(session: AsyncSession, body: dict[str, Any]) -> str:
    settings = get_settings()
    try:
        transfer = sepay.parse_transfer(body)
    except ValueError:
        logger.warning("Ignored a SePay payload that failed validation")
        return "ignored"
    if transfer.direction != "in":
        return "ignored"
    if not sepay.account_matches(transfer, settings.sepay_bank_account):
        logger.warning("Ignored a SePay transfer for another account (id=%s)", transfer.sepay_id)
        return "ignored"
    return await process_incoming_money(
        session,
        payment_id=sepay.payment_id_of(transfer, settings.sepay_payment_prefix),
        gateway_id=f"sepay:{transfer.sepay_id}",
        amount=transfer.amount,
        reference=transfer.reference,
        summary={
            "id": transfer.sepay_id,
            "transferType": transfer.direction,
            "transferAmount": str(transfer.amount),
            "content": transfer.content,
            "referenceCode": transfer.reference,
        },
    )


async def check_payment(session: AsyncSession, payment_id: int) -> PaymentTransaction:
    """ "Kiểm tra lại": ask SePay for the latest transfers and apply the one for this payment."""
    settings = get_settings()
    await expire_stale_qr(session)
    payment = await session.get(PaymentTransaction, payment_id)
    if payment is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    if (
        settings.payment_gateway == "sepay"
        and settings.sepay_api_token
        and payment.method == PaymentMethod.QR.value
        and payment.status in (QR_PENDING, QR_EXPIRED)
    ):
        try:
            rows = await sepay.recent_transfers(
                api_url=settings.sepay_api_url,
                token=settings.sepay_api_token,
                account=settings.sepay_bank_account,
            )
        except httpx.HTTPError:
            logger.warning("SePay transaction listing call failed for payment=%s", payment.id)
            rows = []
        for row in rows:
            try:
                body = sepay.transfer_from_listing(row)
                body["accountNumber"] = settings.sepay_bank_account  # the listing is per account
                transfer = sepay.parse_transfer(body)
            except (ValueError, InvalidOperation):
                logger.warning("Skipped a malformed SePay listing row for payment=%s", payment.id)
                continue
            if sepay.payment_id_of(transfer, settings.sepay_payment_prefix) == payment.id:
                await handle_sepay_transfer(session, body)
                break
        await session.refresh(payment)
    return payment


# --- simulator -----------------------------------------------------------------------------------


async def handle_simulator_webhook(
    session: AsyncSession, *, payment_id: int, amount: Decimal, signature: str
) -> str:
    """Local-only mock gateway; the signature covers "<payment_id>:<amount>"."""
    from app.modules.sales.gateways import simulator

    if not simulator.verify(f"{payment_id}:{amount}", signature):
        logger.warning("Rejected a simulator webhook with a bad signature")
        raise UnauthenticatedError("Chữ ký không hợp lệ.")
    if amount <= 0:
        raise BusinessRuleError("Số tiền không hợp lệ.")
    return await process_incoming_money(
        session,
        payment_id=payment_id,
        gateway_id=f"sim:{payment_id}:{amount}",
        amount=amount,
        reference=None,
        summary={"payment_id": payment_id, "amount": str(amount)},
    )
