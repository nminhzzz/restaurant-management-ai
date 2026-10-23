"""Sales payments — cash, QR, webhook, reconciliation and invoices (FR-SALE-14…19, 23, 29).

Gateway specifics live in app.modules.sales.gateways; this module owns the business
flow shared by every gateway.
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, cast

import httpx
import segno
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.errors import BusinessRuleError, NotFoundError, UnauthenticatedError
from app.modules.sales.gateways import sepay, simulator
from app.modules.sales.models import (
    Invoice,
    Order,
    OrderLine,
    PaymentException,
    PaymentTransaction,
)
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
QR_VERIFYING = "Chờ xác minh thanh toán"
QR_PENDING_ORDER = "Chờ xác nhận thanh toán"
PAYMENT_CLOSED_UNPAID = "Đóng \u2013 chưa thu được tiền"

EXCEPTION_PENDING = "Chờ xử lý"
EXCEPTION_APPLIED = "Đã áp dụng"
EXCEPTION_REFUNDED = "Đã hoàn tiền"


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
                select(OrderLine)
                .where(OrderLine.order_id == order.id, OrderLine.status != LINE_CANCELLED)
                # A plain SELECT after waiting on the order lock may still read the
                # pre-lock snapshot under REPEATABLE READ; locking reads see the
                # quantity the cashier just committed.
                .with_for_update()
            )
        )
        .scalars()
        .all()
    )
    return sum((Decimal(str(line.unit_price)) * int(line.quantity) for line in lines), Decimal(0))


def _settle(order: Order, status: str, now: datetime) -> None:
    order.status = status
    order.updated_at = now
    order.closed_at = now


async def _next_invoice_number(session: AsyncSession, business_date_value: date) -> str:
    from app.modules.sales.invoice_numbers import next_invoice_number

    return await next_invoice_number(session, business_date_value)


async def _issue_invoice(
    session: AsyncSession,
    order: Order,
    *,
    business_date_value: date,
    total: Decimal,
    payment: PaymentTransaction | None = None,
    actor_id: int | None = None,
) -> Invoice:
    """Issue the single invoice of an order, retrying if another till took the number."""
    for _attempt in range(5):
        invoice_number = await _next_invoice_number(session, business_date_value)
        invoice = Invoice(
            order_id=order.id,
            business_date=business_date_value,
            total=total,
            print_count=1,
            payment_transaction_id=payment.id if payment else None,
            payment_method=payment.method if payment else None,
            invoice_number=invoice_number,
            issued_by=actor_id or order.created_by,
        )
        try:
            async with session.begin_nested():
                session.add(invoice)
        except IntegrityError:
            # Another order in the same business date grabbed this number first.
            continue
        invoice.snapshot = await _invoice_snapshot(
            session,
            order,
            invoice_number=invoice_number,
            total=total,
            payment=payment,
        )
        await session.flush()
        return invoice
    raise BusinessRuleError("Không cấp được số hóa đơn, vui lòng thử lại.")


async def _invoice_snapshot(
    session: AsyncSession,
    order: Order,
    *,
    invoice_number: str,
    total: Decimal,
    payment: PaymentTransaction | None,
) -> dict[str, Any]:
    """Freeze what the guest was billed so a later rename/re-price cannot edit history."""
    from app.modules.catalog.models import Dish
    from app.modules.settings.service import get_config

    lines = (
        (
            await session.execute(
                select(OrderLine)
                .where(OrderLine.order_id == order.id, OrderLine.status != LINE_CANCELLED)
                # A plain SELECT after waiting on the order lock may still read the
                # pre-lock snapshot under REPEATABLE READ; locking reads see the
                # quantity the cashier just committed.
                .with_for_update()
            )
        )
        .scalars()
        .all()
    )
    dish_ids = {line.dish_id for line in lines}
    names: dict[int, str] = {}
    if dish_ids:
        dishes = (await session.execute(select(Dish).where(Dish.id.in_(dish_ids)))).scalars().all()
        names = {dish.id: dish.name for dish in dishes}
    restaurant_name = None
    address = None
    try:
        cfg = await get_config(session)
        restaurant_name = cfg.restaurant_name
        address = cfg.address
    except Exception:  # a missing config must not block a payment
        pass
    return {
        "SoHoaDon": invoice_number,
        "MaOrderHienThi": order.display_code,
        "TenNhaHang": restaurant_name,
        "DiaChi": address,
        "ThoiDiemXuat": business_date.now().isoformat(),
        "PhuongThucThanhToan": payment.method if payment else None,
        "TongTien": float(total),
        "lines": [
            {
                "MaMon": line.dish_id,
                "TenMon": names.get(line.dish_id, ""),
                "SoLuong": line.quantity,
                "DonGia": float(line.unit_price),
                "ThanhTien": float(line.unit_price) * line.quantity,
            }
            for line in lines
        ],
    }


async def _ensure_no_unsent_holds(session: AsyncSession, order: Order) -> None:
    from app.modules.sales.models import Reservation

    conditions = [
        Reservation.status == "Đang giữ",
        Reservation.expires_at > business_date.now().replace(tzinfo=None),
    ]
    target = [Reservation.order_id == order.id]
    if order.table_id is not None:
        target.append(Reservation.table_id == order.table_id)
    found = (
        await session.execute(select(Reservation.id).where(*conditions, or_(*target)).limit(1))
    ).first()
    if found is not None:
        raise BusinessRuleError(
            "Còn món chưa gửi trong lượt chọn, hãy gửi hoặc bỏ trước khi thanh toán."
        )


async def pay_cash(session: AsyncSession, order_id: int, *, actor_id: int | None = None) -> dict:
    await expire_stale_qr(session)
    now = business_date.now()
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
    from app.modules.sales.orders import ensure_order_is_open

    ensure_order_is_open(order)
    await _ensure_no_unsent_holds(session, order)
    live_qr = (
        await session.execute(
            select(PaymentTransaction.id).where(
                PaymentTransaction.order_id == order.id,
                PaymentTransaction.method == "QR",
                PaymentTransaction.status == QR_PENDING,
            )
        )
    ).first()
    if live_qr is not None:
        raise BusinessRuleError("Giao dịch QR đang chờ xác nhận, không thể thu tiền mặt.")
    existing = (
        await session.execute(select(Invoice).where(Invoice.order_id == order.id))
    ).scalar_one_or_none()
    if existing is not None:
        raise BusinessRuleError("Order đã có hóa đơn.")

    total = await order_total(session, order)
    order.total = total
    bd = order.business_date
    payment = PaymentTransaction(
        order_id=order.id,
        amount=total,
        method="Tiền mặt",
        status=QR_SUCCESS,
        business_date=bd,
    )
    session.add(payment)
    await session.flush()
    invoice = await _issue_invoice(
        session, order, business_date_value=bd, total=total, payment=payment, actor_id=actor_id
    )
    _settle(order, "Đã thanh toán", now)
    await session.flush()
    return {"payment": payment, "invoice": invoice}


async def start_qr(
    session: AsyncSession, order_id: int, *, actor_id: int | None = None
) -> PaymentTransaction:
    await expire_stale_qr(session)
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
    from app.modules.sales.orders import ensure_order_is_open

    ensure_order_is_open(order)
    await _ensure_no_unsent_holds(session, order)
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
        business_date=order.business_date,
        created_at=now,
        deadline=now + QR_LIFETIME,
    )
    session.add(payment)
    order.status = QR_PENDING_ORDER
    order.updated_at = now
    await session.flush()
    return payment


async def confirm_payment(
    session: AsyncSession,
    payment: PaymentTransaction,
    *,
    bank_ref: str | None = None,
    actor_id: int | None = None,
) -> dict:
    """Settle a pending QR payment whose amount the caller has already checked."""
    order = await session.get(Order, payment.order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    await session.execute(
        select(Order)
        .where(Order.id == order.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    # Re-check under lock: another transaction may have settled/cancelled this
    # payment or order between the caller's check and this call. Expired and
    # cancelled QRs are accepted here because FR-SALE-16 lets late money settle
    # an order that is still open.
    if payment.status not in (
        QR_PENDING,
        QR_VERIFYING,
        QR_EXPIRED,
        QR_CANCELLED,
    ) or order.status not in ("Đang mở", QR_PENDING_ORDER, QR_VERIFYING):
        raise BusinessRuleError("Giao dịch hoặc order đã đổi trạng thái trước khi xác nhận.")
    total = await order_total(session, order)
    order.total = total
    payment.status = QR_SUCCESS
    if bank_ref is not None:
        payment.bank_ref = bank_ref
        if bank_ref.startswith("sepay:"):
            payment.gateway_transaction_id = bank_ref
    await session.flush()
    invoice = await _issue_invoice(
        session,
        order,
        business_date_value=payment.business_date,
        total=total,
        payment=payment,
        actor_id=actor_id,
    )
    _settle(order, "Đã thanh toán", business_date.now())
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
    if payment.method != "QR":
        return {}
    if settings.payment_gateway == "simulator":
        # A real image so the screen can be reviewed offline; it encodes the mock
        # transfer, not a bank payload, and the UI labels it as simulated.
        code = f"SIM{payment.id}"
        payload = f"SIMULATED|{code}|{int(Decimal(str(payment.amount)))}"
        return {
            "qr_image_url": segno.make(payload).svg_data_uri(scale=5, border=2),
            "payment_code": code,
            "bank_code": "MÔ PHỎNG",
            "bank_account": "0000000000",
            "account_name": "Thanh toán mô phỏng",
            "simulated": True,
        }
    if settings.payment_gateway != "sepay":
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


async def _has_success_or_invoice(session: AsyncSession, order_id: int) -> bool:
    successful = await session.scalar(
        select(func.count())
        .select_from(PaymentTransaction)
        .where(
            PaymentTransaction.order_id == order_id,
            PaymentTransaction.status == QR_SUCCESS,
        )
    )
    invoice = await session.scalar(
        select(func.count()).select_from(Invoice).where(Invoice.order_id == order_id)
    )
    return bool(successful or invoice)


async def _was_reopened(session: AsyncSession, payment_id: int) -> bool:
    """FR-SALE-16: money for a payment a manager already reopened is an exception."""
    count = await session.scalar(
        select(func.count())
        .select_from(SystemAuditLog)
        .where(
            SystemAuditLog.action == "REOPEN_PAYMENT",
            SystemAuditLog.target_entity == "GIAO_DICH_THANH_TOAN",
            SystemAuditLog.target_id == str(payment_id),
        )
    )
    return bool(count)


async def _cancel_other_qrs(session: AsyncSession, order_id: int, *, keep_payment_id: int) -> None:
    """FR-SALE-16: late money voids a newer QR that has not received money."""
    rows = (
        (
            await session.execute(
                select(PaymentTransaction).where(
                    PaymentTransaction.order_id == order_id,
                    PaymentTransaction.id != keep_payment_id,
                    PaymentTransaction.method == "QR",
                    PaymentTransaction.status.in_((QR_PENDING, QR_VERIFYING)),
                )
            )
        )
        .scalars()
        .all()
    )
    for other in rows:
        other.status = QR_CANCELLED
        session.add(
            SystemAuditLog(
                user_id=None,
                action="LATE_PAYMENT_VOIDS_QR",
                target_entity="GIAO_DICH_THANH_TOAN",
                target_id=str(other.id),
                after={"MaOrder": order_id, "GiaoDichDuocApDung": keep_payment_id},
            )
        )
    if rows:
        await session.flush()


async def record_exception(
    session: AsyncSession,
    *,
    payment: PaymentTransaction | None,
    order_id: int | None,
    bank_ref: str,
    amount: Decimal,
    reason: str,
) -> PaymentException:
    """Keep unmatched money for a human, once per gateway transaction."""
    existing = (
        await session.execute(select(PaymentException).where(PaymentException.bank_ref == bank_ref))
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    exception = PaymentException(
        payment_transaction_id=payment.id if payment is not None else None,
        order_id=order_id if order_id is not None else (payment.order_id if payment else None),
        bank_ref=bank_ref,
        amount=amount,
        reason=reason,
        status=EXCEPTION_PENDING,
        business_date=business_date.business_date_of(business_date.now()),
    )
    try:
        async with session.begin_nested():
            session.add(exception)
    except IntegrityError:
        # A concurrent delivery of the same transfer won the unique constraint.
        return (
            await session.execute(
                select(PaymentException).where(PaymentException.bank_ref == bank_ref)
            )
        ).scalar_one()
    session.add(
        SystemAuditLog(
            user_id=None,
            action="WEBHOOK_UNMATCHED",
            target_entity="NGOAI_LE_THANH_TOAN",
            target_id=str(exception.id),
        )
    )
    await session.flush()
    return exception


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
            select(PaymentTransaction.id).where(
                or_(
                    PaymentTransaction.bank_ref == bank_ref,
                    PaymentTransaction.gateway_transaction_id == bank_ref,
                )
            )
        )
    ).first()
    seen_exception = (
        await session.execute(
            select(PaymentException.id).where(PaymentException.bank_ref == bank_ref)
        )
    ).first()
    if seen is not None or seen_exception is not None:
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
                .execution_options(populate_existing=True)
            )
        ).scalar_one_or_none()
    if payment is None:
        logger.warning("Unmatched SePay transfer sepay_id=%s", transfer.sepay_id)
        await record_exception(
            session,
            payment=None,
            order_id=None,
            bank_ref=bank_ref,
            amount=transfer.amount,
            reason="Không xác định được giao dịch của nhà hàng",
        )
        return "unmatched"

    # Two deliveries can pass the pre-lock SELECT together. After taking the row
    # lock, the winner's write is visible; the loser must be a duplicate, not a
    # "duplicate money" exception.
    if bank_ref in (payment.bank_ref, payment.gateway_transaction_id):
        return "duplicate"

    order = await session.get(Order, payment.order_id)
    if order is not None:
        order = (
            await session.execute(
                select(Order)
                .where(Order.id == order.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalar_one_or_none()

    if payment.method != "QR":
        logger.warning(
            "SePay transfer sepay_id=%s matched a non-QR payment=%s", transfer.sepay_id, payment.id
        )
        await record_exception(
            session,
            payment=payment,
            order_id=payment.order_id,
            bank_ref=bank_ref,
            amount=transfer.amount,
            reason="Tiền về cho giao dịch không phải QR",
        )
        return "unmatched"

    if payment.status == QR_SUCCESS:
        # New money for a payment that is already settled: never double-invoice.
        logger.warning(
            "SePay transfer sepay_id=%s arrived for an already-settled payment=%s",
            transfer.sepay_id,
            payment.id,
        )
        await record_exception(
            session,
            payment=payment,
            order_id=payment.order_id,
            bank_ref=bank_ref,
            amount=transfer.amount,
            reason="Thu trùng cho giao dịch đã thanh toán",
        )
        return "unmatched"

    total = await order_total(session, order) if order is not None else Decimal(0)
    reopened = await _was_reopened(session, payment.id)
    late = payment.status in (QR_EXPIRED, QR_CANCELLED)
    normal = payment.status in (QR_PENDING, QR_VERIFYING)
    already_paid = await _has_success_or_invoice(session, order.id) if order is not None else False
    order_open = order is not None and order.status in (
        "Đang mở",
        QR_PENDING_ORDER,
        QR_VERIFYING,
    )
    if order is None:
        await record_exception(
            session,
            payment=payment,
            order_id=payment.order_id,
            bank_ref=bank_ref,
            amount=transfer.amount,
            reason="Order của giao dịch không còn tồn tại",
        )
        return "unmatched"

    if order_open and transfer.amount == total and not already_paid:
        if normal or (late and not reopened):
            try:
                async with session.begin_nested():
                    await _cancel_other_qrs(session, order.id, keep_payment_id=payment.id)
                    await confirm_payment(session, payment, bank_ref=bank_ref)
                return "confirmed"
            except BusinessRuleError:
                # Rolling back a savepoint expires changed ORM objects. Reload
                # explicitly before logging or recording the unmatched money.
                await session.refresh(payment)
                await session.refresh(order)
                # Lost a race with another confirmation/cancellation: record it, don't 500.
                logger.warning(
                    "SePay transfer sepay_id=%s raced payment=%s; recording for review",
                    transfer.sepay_id,
                    payment.id,
                )
                await record_exception(
                    session,
                    payment=payment,
                    order_id=order.id,
                    bank_ref=bank_ref,
                    amount=transfer.amount,
                    reason="Giao dịch đã đổi trạng thái trước khi xác nhận",
                )
                return "unmatched"
        else:
            await record_exception(
                session,
                payment=payment,
                order_id=order.id,
                bank_ref=bank_ref,
                amount=transfer.amount,
                reason="Order đã mở lại thanh toán; quản lý cần áp dụng khoản cũ",
            )
            return "unmatched"

    await record_exception(
        session,
        payment=payment,
        order_id=order.id if order is not None else payment.order_id,
        bank_ref=bank_ref,
        amount=transfer.amount,
        reason=(
            "Order đã đóng, đã hủy hoặc đã thanh toán bằng giao dịch khác"
            if not order_open or already_paid
            else "Số tiền không khớp với order"
        ),
    )
    if order_open and not already_paid and transfer.amount != total:
        await to_reconciliation(
            session,
            payment,
            bank_ref=bank_ref,
            action="WEBHOOK_NEEDS_RECONCILIATION",
        )
        return "reconciling"
    return "unmatched"


async def check_payment(session: AsyncSession, payment_id: int) -> PaymentTransaction:
    settings = get_settings()
    payment = await session.get(PaymentTransaction, payment_id)
    if payment is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    # A late transfer is the common case once a QR lapses, so "Kiểm tra lại" must
    # also ask the gateway for expired/verifying payments, not only live ones.
    if (
        settings.payment_gateway == "sepay"
        and settings.sepay_api_token
        and payment.status in (QR_PENDING, QR_EXPIRED, QR_VERIFYING)
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
                transfer = sepay.parse_transfer(body)
            except (ValueError, InvalidOperation):
                logger.warning("Skipped a malformed SePay listing row for payment=%s", payment.id)
                continue
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

    if amount is None:
        raise BusinessRuleError("Thiếu số tiền.")

    if payment.status == QR_SUCCESS:
        return {"payment": payment}
    if payment.status != QR_PENDING:
        raise BusinessRuleError("Giao dịch không ở trạng thái chờ.")

    order = await session.get(Order, payment.order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    await session.execute(select(Order).where(Order.id == order.id).with_for_update())
    total = await order_total(session, order)
    if Decimal(str(amount)) != total:
        raise BusinessRuleError("Số tiền không khớp.")

    return await confirm_payment(session, payment)


async def cancel_qr(
    session: AsyncSession, payment_id: int, *, actor_id: int | None = None
) -> PaymentTransaction:
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
    if payment.status != QR_PENDING:
        raise BusinessRuleError("Chỉ hủy QR đang chờ.")
    payment.status = QR_CANCELLED
    order = await session.get(Order, payment.order_id)
    if order is not None and order.status == QR_PENDING_ORDER:
        order.status = "Đang mở"
        order.updated_at = business_date.now()
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
    """Expire stale pending QRs with one conditional write (FR-SALE-17).

    A plain read-then-write-by-primary-key would clobber a status change (a
    webhook confirmation, a cancellation) that lands between the read and the
    write; this stays correct because the WHERE clause re-checks `status` at
    write time instead of trusting a snapshot read earlier.
    """
    now = business_date.now()
    stale_order_ids = set(
        (
            await session.execute(
                select(PaymentTransaction.order_id).where(
                    PaymentTransaction.method == "QR",
                    PaymentTransaction.status == QR_PENDING,
                    or_(
                        PaymentTransaction.deadline < now,
                        and_(
                            PaymentTransaction.deadline.is_(None),
                            PaymentTransaction.created_at < now - QR_LIFETIME,
                        ),
                    ),
                )
            )
        )
        .scalars()
        .all()
    )
    result = cast(
        CursorResult,
        await session.execute(
            update(PaymentTransaction)
            .where(
                PaymentTransaction.method == "QR",
                PaymentTransaction.status == QR_PENDING,
                or_(
                    PaymentTransaction.deadline < now,
                    and_(
                        PaymentTransaction.deadline.is_(None),
                        PaymentTransaction.created_at < now - QR_LIFETIME,
                    ),
                ),
            )
            .values(status=QR_EXPIRED)
            .execution_options(synchronize_session="fetch")
        ),
    )
    expired = result.rowcount or 0
    if expired:
        await session.execute(
            update(Order)
            .where(Order.id.in_(stale_order_ids), Order.status == QR_PENDING_ORDER)
            .values(status="Đang mở", updated_at=now)
        )
        await session.flush()
    return expired


async def expire_qr_tick(*, factory: async_sessionmaker[AsyncSession] | None = None) -> int:
    """Expire stale QRs without waiting for a cashier to open the payment screen.

    FR-SALE-14 says a QR lapses after 10 minutes; the lazy check in the request
    paths only helps if someone is looking at the order.
    """
    if factory is None:
        from app.core.database import get_session_factory

        factory = get_session_factory()
    async with factory() as session:
        try:
            expired = await expire_stale_qr(session)
            await session.commit()
            return expired
        except Exception:
            await session.rollback()
            raise


async def sync_recent_transfers(*, factory: async_sessionmaker[AsyncSession] | None = None) -> int:
    """Settle transfers from the bank listing when a webhook was missed or unavailable.

    A stored cursor keeps the window from sliding past transfers that arrived while
    the API was down; the handler itself stays idempotent per gateway id.
    """
    from app.core.database import get_session_factory
    from app.modules.settings.models import SystemConfig

    settings = get_settings()
    if settings.payment_gateway != "sepay" or not settings.sepay_api_token:
        return 0
    session_factory = factory or get_session_factory()

    async with session_factory() as setup_session:
        config = (await setup_session.execute(select(SystemConfig))).scalar_one_or_none()
        cursor = config.sepay_cursor if config is not None else None
    try:
        rows = await sepay.recent_transfers(
            api_url=settings.sepay_api_url,
            token=settings.sepay_api_token,
            account=settings.sepay_bank_account,
            since_id=cursor,
        )
    except httpx.HTTPError:
        logger.warning("SePay transaction listing failed; will retry on the next tick")
        return 0

    confirmed = 0
    processed_id = cursor
    try:
        rows = sorted(rows, key=lambda row: int(str(row["id"])))
    except (KeyError, TypeError, ValueError):
        logger.error("SePay listing has an invalid id; cursor was not advanced")
        return 0
    for row in rows:
        row_id = row.get("id")
        if cursor is not None and int(str(row_id)) < int(cursor):
            continue
        try:
            body = sepay.transfer_from_listing(row)
            transfer = sepay.parse_transfer(body)
        except (ValueError, InvalidOperation):
            logger.warning("Skipped a malformed SePay listing row")
            break
        # Money that does not reference one of our payments is ordinary bank
        # activity (rent, suppliers, old transfers). Recording every such row as a
        # payment exception would bury the ones a manager must actually resolve.
        if sepay.payment_id_of(transfer, settings.sepay_payment_prefix) is None:
            processed_id = str(row_id) if row_id is not None else processed_id
            continue
        async with session_factory() as session:
            try:
                result = await handle_sepay_transfer(session, body)
                await session.commit()
            except Exception:
                await session.rollback()
                logger.exception("Could not apply a SePay listing transfer")
                # Stop here so the cursor does not skip the failed transfer.
                break
        if result == "confirmed":
            confirmed += 1
        processed_id = str(row_id) if row_id is not None else processed_id

    if processed_id and processed_id != cursor:
        async with session_factory() as setup_session:
            config = (await setup_session.execute(select(SystemConfig))).scalar_one_or_none()
            if config is not None:
                # Another worker may already have committed a newer cursor.
                await setup_session.execute(
                    update(SystemConfig)
                    .where(
                        SystemConfig.id == config.id,
                        SystemConfig.sepay_cursor == cursor,
                    )
                    .values(sepay_cursor=processed_id)
                )
                await setup_session.commit()
    return confirmed


async def request_verification(
    session: AsyncSession,
    payment_id: int,
    *,
    actor_id: int | None = None,
    bank_ref: str | None = None,
    evidence: str | None = None,
    note: str | None = None,
) -> PaymentTransaction:
    """FR-SALE-19: the guest says they paid while the system has not recorded it."""
    await expire_stale_qr(session)
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
    if payment.status == QR_VERIFYING:
        return payment
    if payment.status not in (QR_PENDING, QR_EXPIRED):
        raise BusinessRuleError("Giao dịch không ở trạng thái chờ xác minh.")
    order = (
        await session.execute(
            select(Order)
            .where(Order.id == payment.order_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    if order.status not in ("Đang mở", QR_PENDING_ORDER):
        raise BusinessRuleError("Order đã đổi trạng thái trước khi yêu cầu xác minh.")
    reference = (bank_ref or "").strip()
    if reference and payment.bank_ref and payment.bank_ref != reference:
        raise BusinessRuleError("Mã giao dịch ngân hàng đã ghi nhận, không thể ghi đè.")
    if reference:
        payment.bank_ref = reference
    if evidence:
        payment.evidence = evidence
    payment.status = QR_VERIFYING
    order.status = QR_VERIFYING
    order.updated_at = business_date.now()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="REQUEST_PAYMENT_VERIFICATION",
            target_entity="GIAO_DICH_THANH_TOAN",
            target_id=str(payment.id),
            reason=(note or "").strip() or None,
            after={
                "MaOrder": order.id,
                "TrangThai": QR_VERIFYING,
                "MaGiaoDichNganHang": payment.bank_ref,
                "AnhChungTu": payment.evidence,
                "GhiChu": (note or "").strip() or None,
            },
        )
    )
    await session.flush()
    return payment


async def reopen_payment(
    session: AsyncSession,
    payment_id: int,
    *,
    reason: str,
    outcome: str | None = None,
    actor_id: int | None = None,
) -> Order:
    """FR-SALE-23: return a verifying order to the open state for another payment."""
    if not reason.strip():
        raise BusinessRuleError("Cần lý do mở lại thanh toán.")
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
    if payment.status != QR_VERIFYING:
        raise BusinessRuleError("Giao dịch không ở trạng thái chờ xác minh.")
    order = (
        await session.execute(
            select(Order)
            .where(Order.id == payment.order_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    successful = await session.scalar(
        select(func.count())
        .select_from(PaymentTransaction)
        .where(
            PaymentTransaction.order_id == order.id,
            PaymentTransaction.status == QR_SUCCESS,
        )
    )
    if successful:
        raise BusinessRuleError("Order đã có thanh toán thành công, không thể mở lại.")
    before = {
        "MaGiaoDich": payment.status,
        "MaOrder": order.status,
    }
    payment.status = QR_CANCELLED
    order.status = "Đang mở"
    order.updated_at = business_date.now()
    order.closed_at = None
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="REOPEN_PAYMENT",
            target_entity="GIAO_DICH_THANH_TOAN",
            target_id=str(payment.id),
            reason=reason,
            before=before,
            after={
                "MaGiaoDich": payment.status,
                "MaOrder": order.status,
                "MaGiaoDichNganHang": payment.bank_ref,
                "KetQuaXuLy": (outcome or "").strip() or None,
            },
        )
    )
    await session.flush()
    return order


async def close_unpaid_order(
    session: AsyncSession,
    order_id: int,
    *,
    reason: str,
    outcome: str | None = None,
    actor_id: int | None = None,
) -> Order:
    """FR-SALE-35: stop chasing an unreceived payment without issuing an invoice."""
    if not reason.strip():
        raise BusinessRuleError("Cần lý do đóng order chưa thu tiền.")
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
    if order.status != QR_VERIFYING:
        raise BusinessRuleError("Chỉ đóng order đang chờ xác minh thanh toán.")
    successful = await session.scalar(
        select(func.count())
        .select_from(PaymentTransaction)
        .where(
            PaymentTransaction.order_id == order.id,
            PaymentTransaction.status == QR_SUCCESS,
        )
    )
    invoice = await session.scalar(
        select(func.count()).select_from(Invoice).where(Invoice.order_id == order.id)
    )
    if successful or invoice:
        raise BusinessRuleError("Order đã có thanh toán/hóa đơn, không thể đóng chưa thu.")
    payments = (
        (
            await session.execute(
                select(PaymentTransaction)
                .where(
                    PaymentTransaction.order_id == order.id,
                    PaymentTransaction.status == QR_VERIFYING,
                )
                .with_for_update()
            )
        )
        .scalars()
        .all()
    )
    for payment in payments:
        payment.status = PAYMENT_CLOSED_UNPAID
    from app.modules.sales.reservations import release_active_holds

    await release_active_holds(session, order_id=order.id, table_id=order.table_id)
    before = {"TrangThai": order.status}
    order.status = PAYMENT_CLOSED_UNPAID
    order.total = await order_total(session, order)
    order.cancel_reason = reason
    order.updated_at = business_date.now()
    order.closed_at = business_date.now()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CLOSE_UNPAID_ORDER",
            target_entity="ORDER",
            target_id=str(order.id),
            reason=reason,
            before=before,
            after={
                "TrangThai": order.status,
                "SoTienChuaThu": float(order.total),
                "LyDo": reason,
                "KetQuaXuLy": (outcome or "").strip() or None,
            },
        )
    )
    await session.flush()
    return order


async def apply_late_payment(
    session: AsyncSession,
    payment_id: int,
    *,
    actor_id: int | None = None,
    bank_ref: str | None = None,
) -> dict:
    """FR-SALE-17b: money arrives after the order was closed unpaid.

    Apply it once, issue the invoice, and let the order leave the closed-unpaid
    report and its cost move back to the paid (05a) group.
    """
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
    if payment.status != PAYMENT_CLOSED_UNPAID:
        raise BusinessRuleError("Giao dịch không ở trạng thái đóng chưa thu.")
    order = (
        await session.execute(
            select(Order)
            .where(Order.id == payment.order_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    if order.status != PAYMENT_CLOSED_UNPAID:
        raise BusinessRuleError("Order không ở trạng thái đóng chưa thu.")
    successful = await session.scalar(
        select(func.count())
        .select_from(PaymentTransaction)
        .where(
            PaymentTransaction.order_id == order.id,
            PaymentTransaction.status == QR_SUCCESS,
        )
    )
    invoice_count = await session.scalar(
        select(func.count()).select_from(Invoice).where(Invoice.order_id == order.id)
    )
    if successful or invoice_count:
        raise BusinessRuleError("Order đã có thanh toán/hóa đơn, không thể áp dụng lại.")
    total = await order_total(session, order)
    order.total = total
    payment.status = QR_SUCCESS
    if bank_ref is not None:
        payment.bank_ref = bank_ref
        if bank_ref.startswith("sepay:"):
            payment.gateway_transaction_id = bank_ref
    await session.flush()
    invoice = await _issue_invoice(
        session,
        order,
        business_date_value=payment.business_date,
        total=total,
        payment=payment,
        actor_id=actor_id,
    )
    _settle(order, "Đã thanh toán", business_date.now())
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="APPLY_LATE_PAYMENT",
            target_entity="GIAO_DICH_THANH_TOAN",
            target_id=str(payment.id),
            after={"MaOrder": order.id, "MaHoaDon": invoice.id},
        )
    )
    await session.flush()
    return {"payment": payment, "invoice": invoice}


async def mark_for_reconciliation(
    session: AsyncSession, payment_id: int, *, actor_id: int | None = None
) -> PaymentTransaction:
    await expire_stale_qr(session)
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
    if payment.status != QR_EXPIRED:
        raise BusinessRuleError("Chỉ đối soát QR đã hết hạn.")
    order = (
        await session.execute(
            select(Order)
            .where(Order.id == payment.order_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    if order.status not in ("Đang mở", QR_PENDING_ORDER):
        raise BusinessRuleError("Order đã đổi trạng thái trước khi đối soát.")
    payment.status = QR_RECONCILING
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
    reference = (reference or "").strip()
    if not reference:
        raise BusinessRuleError("Cần nhập mã giao dịch ngân hàng.")
    if payment.status == QR_SUCCESS or await _has_success_or_invoice(session, payment.order_id):
        raise BusinessRuleError("Giao dịch đã thanh toán, không thể sửa mã ngân hàng.")
    if payment.bank_ref and payment.bank_ref != reference:
        # The reference is the idempotency key of the bank transfer. Rewriting it
        # would let a replayed webhook look like new money.
        raise BusinessRuleError("Mã giao dịch ngân hàng đã ghi nhận, không thể ghi đè.")
    before = {
        "MaGiaoDichNganHang": payment.bank_ref,
        "AnhChungTu": payment.evidence,
    }
    payment.bank_ref = reference
    payment.evidence = evidence
    try:
        async with session.begin_nested():
            await session.flush()
    except IntegrityError as exc:
        raise BusinessRuleError("Mã giao dịch ngân hàng đã dùng cho giao dịch khác.") from exc
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="RECORD_BANK_REFERENCE",
            target_entity="GIAO_DICH_THANH_TOAN",
            target_id=str(payment.id),
            before=before,
            after={
                "MaGiaoDichNganHang": reference,
                "AnhChungTu": evidence,
            },
        )
    )
    await session.flush()
    return payment


async def resolve_reconciliation(
    session: AsyncSession,
    payment_id: int,
    outcome: str,
    *,
    actor_id: int | None = None,
    received_amount: Decimal | None = None,
    note: str | None = None,
) -> PaymentTransaction:
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
    if payment.status not in (QR_RECONCILING, QR_VERIFYING):
        raise BusinessRuleError("Giao dịch không ở trạng thái chờ đối soát/xác minh.")
    if outcome not in ("received", "not_received"):
        raise BusinessRuleError("outcome phải là received/not_received.")

    now = business_date.now()
    before_status = payment.status
    order = (
        await session.execute(
            select(Order)
            .where(Order.id == payment.order_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    if outcome == "received":
        total = await order_total(session, order)
        if received_amount is None or Decimal(str(received_amount)) != total:
            raise BusinessRuleError(
                "Số tiền thực nhận phải bằng đúng tổng order trước khi xác nhận."
            )
        # Money the gateway already reported with a different amount is evidence
        # the guest has not paid in full; it must be applied or refunded first.
        pending = (
            (
                await session.execute(
                    select(PaymentException)
                    .where(
                        PaymentException.payment_transaction_id == payment.id,
                        PaymentException.status == EXCEPTION_PENDING,
                    )
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
            )
            .scalars()
            .all()
        )
        if pending:
            raise BusinessRuleError(
                "Còn khoản ngoại lệ chưa xử lý; hãy dùng thao tác áp dụng hoặc hoàn tiền "
                "trong danh sách ngoại lệ để tránh ghi nhận cùng khoản tiền hai lần."
            )
        payment.status = QR_SUCCESS
        order.total = total
        await _issue_invoice(
            session,
            order,
            business_date_value=payment.business_date,
            total=total,
            payment=payment,
            actor_id=actor_id,
        )
        _settle(order, "Đã thanh toán", now)
    else:
        if payment.status == QR_VERIFYING:
            # Keep waiting for the guest/gateway; do not silently dispute or reopen.
            _settle(order, QR_VERIFYING, now)
        else:
            payment.status = QR_DISPUTED
            _settle(order, QR_DISPUTED, now)
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="RESOLVE_RECONCILIATION",
            target_entity="GIAO_DICH_THANH_TOAN",
            target_id=str(payment.id),
            before={"TrangThai": before_status},
            after={
                "ketQua": outcome,
                "TrangThai": payment.status,
                "MaGiaoDichNganHang": payment.bank_ref,
                "AnhChungTu": payment.evidence,
                "GhiChu": (note or "").strip() or None,
            },
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


async def list_exceptions(
    session: AsyncSession, *, status: str | None = None
) -> list[tuple[PaymentException, str | None]]:
    """FR-SALE-17: money waiting for a manager, newest first."""
    stmt = (
        select(PaymentException, Order.display_code)
        .outerjoin(Order, Order.id == PaymentException.order_id)
        .order_by(PaymentException.created_at.desc(), PaymentException.id.desc())
    )
    if status:
        stmt = stmt.where(PaymentException.status == status)
    rows = (await session.execute(stmt)).all()
    return [(row[0], row[1]) for row in rows]


async def _apply_exception_money(
    session: AsyncSession, exception: PaymentException, *, actor_id: int | None
) -> None:
    if exception.payment_transaction_id is None:
        raise BusinessRuleError("Khoản này không gắn với giao dịch của order.")
    payment = (
        await session.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.id == exception.payment_transaction_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if payment is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    order = (
        await session.execute(
            select(Order)
            .where(Order.id == payment.order_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    if await _has_success_or_invoice(session, order.id):
        raise BusinessRuleError("Order đã có thanh toán/hóa đơn, chỉ có thể hoàn tiền.")
    total = await order_total(session, order)
    if Decimal(str(exception.refund_amount or 0)) > 0:
        raise BusinessRuleError("Khoản tiền đã hoàn một phần, chỉ có thể hoàn tiếp phần còn lại.")
    if Decimal(str(exception.amount)) != total:
        raise BusinessRuleError("Số tiền không còn khớp với order, chỉ có thể hoàn tiền.")

    if order.status == PAYMENT_CLOSED_UNPAID and payment.status == PAYMENT_CLOSED_UNPAID:
        await apply_late_payment(
            session, payment.id, actor_id=actor_id, bank_ref=exception.bank_ref
        )
        return
    if order.status not in ("Đang mở", QR_RECONCILING, QR_VERIFYING):
        raise BusinessRuleError("Order không ở trạng thái có thể áp dụng khoản tiền.")

    await _cancel_other_qrs(session, order.id, keep_payment_id=payment.id)
    payment.status = QR_SUCCESS
    payment.bank_ref = exception.bank_ref
    order.total = total
    await session.flush()
    await _issue_invoice(
        session,
        order,
        business_date_value=payment.business_date,
        total=total,
        payment=payment,
        actor_id=actor_id,
    )
    _settle(order, "Đã thanh toán", business_date.now())
    await session.flush()


async def _release_reconciling_payment(session: AsyncSession, exception: PaymentException) -> None:
    """Refunded money frees the order again, but never reopens a settled bill.

    A wrong-amount transfer puts the order in "Chờ đối soát". Once that money is
    returned, the guest still owes the bill: the order must go back to "Đang mở"
    so a new cash/QR payment can be taken.
    """
    if exception.payment_transaction_id is None:
        return
    payment = await session.get(PaymentTransaction, exception.payment_transaction_id)
    if payment is None or payment.status not in (QR_RECONCILING, QR_VERIFYING):
        return
    order = (
        await session.execute(
            select(Order)
            .where(Order.id == payment.order_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if order is None:
        return
    if order.status not in (QR_RECONCILING, QR_VERIFYING):
        return
    if await _has_success_or_invoice(session, order.id):
        return
    payment.status = QR_CANCELLED
    order.status = "Đang mở"
    order.updated_at = business_date.now()
    order.closed_at = None
    await session.flush()


async def resolve_exception(
    session: AsyncSession,
    exception_id: int,
    *,
    outcome: str,
    actor_id: int | None,
    note: str | None = None,
    refund_ref: str | None = None,
    refund_amount: Decimal | None = None,
) -> PaymentException:
    """FR-SALE-17: apply the money to its order or record an external refund."""
    if outcome not in ("applied", "refunded"):
        raise BusinessRuleError("Kết quả xử lý phải là applied hoặc refunded.")
    # All money paths lock payment -> order -> exception. Looking up immutable
    # linkage first avoids taking the exception lock in the opposite order to
    # reconciliation/webhooks.
    linkage = await session.scalar(
        select(PaymentException.payment_transaction_id).where(PaymentException.id == exception_id)
    )
    if linkage is not None:
        linked_payment = await session.scalar(
            select(PaymentTransaction)
            .where(PaymentTransaction.id == linkage)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if linked_payment is not None:
            await session.execute(
                select(Order)
                .where(Order.id == linked_payment.order_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
    exception = (
        await session.execute(
            select(PaymentException)
            .where(PaymentException.id == exception_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if exception is None:
        raise NotFoundError("Khoản ngoại lệ không tồn tại.")
    if exception.status != EXCEPTION_PENDING:
        raise BusinessRuleError("Khoản ngoại lệ đã được xử lý.")
    if outcome == "refunded":
        if not (note or "").strip():
            raise BusinessRuleError("Cần ghi chú hoàn tiền ngoài hệ thống.")
        refund_ref = (refund_ref or "").strip()
        if not refund_ref:
            raise BusinessRuleError("Cần nhập mã tham chiếu hoàn tiền của ngân hàng.")
        already = Decimal(str(exception.refund_amount or 0))
        remaining = Decimal(str(exception.amount)) - already
        released = Decimal(str(refund_amount)) if refund_amount is not None else remaining
        if released <= 0 or released > remaining:
            raise BusinessRuleError("Số tiền hoàn phải lớn hơn 0 và không vượt số còn lại.")
        exception.refund_ref = refund_ref
        # Cumulative: a partial refund keeps the exception open for the rest.
        exception.refund_amount = already + released
        fully_refunded = exception.refund_amount >= Decimal(str(exception.amount))
    if outcome == "applied":
        await _apply_exception_money(session, exception, actor_id=actor_id)
    else:
        fully_refunded = exception.refund_amount is not None and Decimal(
            str(exception.refund_amount)
        ) >= Decimal(str(exception.amount))
        if fully_refunded:
            await _release_reconciling_payment(session, exception)

    if outcome == "applied":
        exception.status = EXCEPTION_APPLIED
    elif fully_refunded:
        exception.status = EXCEPTION_REFUNDED
    else:
        exception.status = EXCEPTION_PENDING
    recorded_note = (note or "").strip() or None
    if outcome == "refunded" and not fully_refunded:
        recorded_note = (
            f"{recorded_note or ''} · đã hoàn {exception.refund_amount}/{exception.amount}"
        ).strip(" ·")
    exception.note = recorded_note
    exception.resolved_at = business_date.now()
    exception.resolved_by = actor_id
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="RESOLVE_PAYMENT_EXCEPTION",
            target_entity="NGOAI_LE_THANH_TOAN",
            target_id=str(exception.id),
            after={
                "ketQua": outcome,
                "MaGiaoDichCong": exception.bank_ref,
                "MaThamChieuHoan": exception.refund_ref,
                "SoTienHoan": float(exception.refund_amount)
                if exception.refund_amount is not None
                else None,
            },
            reason=exception.note,
        )
    )
    await session.flush()
    return exception
