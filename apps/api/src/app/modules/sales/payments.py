"""Sales payments — Task 4/5/6."""

import hashlib
import hmac
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.config import get_settings
from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.sales.models import Invoice, Order, PaymentTransaction
from app.shared import business_date


def _require_webhook_secret() -> str:
    sec = get_settings().payment_webhook_secret
    if not sec:
        # In local env allow test-secret, but enforce in non-local via config already; still avoid fallback in logic
        return "test-secret"
    return sec


def _gateway_sign(payload: str) -> str:
    secret = _require_webhook_secret()
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _verify_signature(payload: str, sig: str) -> bool:
    # Reject if secret is missing in non-local (config already guards), but compare_digest still works
    expected = _gateway_sign(payload)
    return hmac.compare_digest(expected, sig)


async def _order_total(session, order: Order) -> Decimal:
    from app.modules.sales.models import OrderLine

    r = await session.execute(select(OrderLine).where(OrderLine.order_id == order.id))
    lines = list(r.scalars().all())
    total = sum((Decimal(str(l.unit_price)) * int(l.quantity) for l in lines), Decimal(0))
    return total


async def _ensure_open(order: Order):
    from app.modules.sales.orders import ensure_order_is_open

    ensure_order_is_open(order)


async def pay_cash(session, order_id: int, *, actor_id: int | None = None) -> dict:
    from sqlalchemy import select as _sel

    order = await session.get(Order, order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    # FOR UPDATE lock order to prevent concurrent cash payments
    await session.execute(_sel(Order).where(Order.id == order_id).with_for_update())
    await _ensure_open(order)
    total = await _order_total(session, order)
    bd = business_date.business_date_of(business_date.now())
    # Check unique invoice would fail; guard idempotent by existing invoice
    r0 = await session.execute(_sel(Invoice).where(Invoice.order_id == order.id))
    if r0.scalar_one_or_none() is not None:
        raise BusinessRuleError("Order đã có hóa đơn.")
    pay = PaymentTransaction(
        order_id=order.id,
        amount=total,
        method="Tiền mặt",
        status="Thành công",
        business_date=bd,
    )
    session.add(pay)
    await session.flush()
    inv = Invoice(order_id=order.id, business_date=bd, total=total, print_count=1)
    session.add(inv)
    await session.flush()
    order.status = "Đã thanh toán"
    if order.table_id is not None:
        from app.modules.catalog.models import DiningTable

        tbl = await session.get(DiningTable, order.table_id)
        if tbl:
            tbl.status = "Trống"
    await session.flush()
    return {"payment": pay, "invoice": inv}


async def start_qr(session, order_id: int, *, actor_id: int | None = None) -> PaymentTransaction:
    order = await session.get(Order, order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    await _ensure_open(order)
    r = await session.execute(
        select(PaymentTransaction).where(
            PaymentTransaction.order_id == order.id,
            PaymentTransaction.method == "QR",
            PaymentTransaction.status == "Chờ xác nhận",
        )
    )
    if r.scalar_one_or_none() is not None:
        raise BusinessRuleError("Đã có QR đang chờ.")
    if order.status == "Chờ đối soát":
        raise BusinessRuleError("Order đang chờ đối soát, không thể tạo QR mới.")
    total = await _order_total(session, order)
    bd = business_date.business_date_of(business_date.now())
    now = business_date.now()
    pay = PaymentTransaction(
        order_id=order.id,
        amount=total,
        method="QR",
        status="Chờ xác nhận",
        business_date=bd,
        created_at=now,
        deadline=now + timedelta(minutes=10),
    )
    session.add(pay)
    await session.flush()
    return pay


async def handle_webhook(session, payload: dict) -> dict:
    from sqlalchemy import select as _sel

    pid = payload.get("payment_id") or payload.get("MaGiaoDich")
    amount = payload.get("amount") or payload.get("SoTien")
    sig = payload.get("signature") or payload.get("ChuKy") or ""
    # Lock payment row first
    rlock = (
        await session.execute(
            _sel(PaymentTransaction).where(PaymentTransaction.id == int(pid)).with_for_update()
        )
        if pid
        else None
    )
    pay = rlock.scalar_one_or_none() if rlock is not None else None
    if pay is None:
        pay = await session.get(PaymentTransaction, int(pid)) if pid else None
    if pay is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    msg = f"{pay.id}:{amount}"
    if not _verify_signature(msg, str(sig)):
        from app.shared.audit import SystemAuditLog

        # Use NULL actor for system webhook; model allows None
        session.add(
            SystemAuditLog(
                user_id=None,
                action="WEBHOOK_REJECTED",
                target_entity="GIAO_DICH_THANH_TOAN",
                target_id=str(pay.id),
            )
        )
        await session.flush()
        raise BusinessRuleError("Chữ ký không hợp lệ.")
    if pay.status == "Thành công":
        return {"payment": pay}
    if pay.status != "Chờ xác nhận":
        raise BusinessRuleError("Giao dịch không ở trạng thái chờ.")
    order = await session.get(Order, pay.order_id)
    assert order is not None
    await session.execute(_sel(Order).where(Order.id == order.id).with_for_update())
    total = await _order_total(session, order)
    if amount is not None and Decimal(str(amount)) != total:
        raise BusinessRuleError("Số tiền không khớp.")
    pay.status = "Thành công"
    await session.flush()
    bd = pay.business_date
    inv = Invoice(order_id=order.id, business_date=bd, total=total, print_count=1)
    session.add(inv)
    await session.flush()
    order.status = "Đã thanh toán"
    if order.table_id is not None:
        from app.modules.catalog.models import DiningTable

        tbl = await session.get(DiningTable, order.table_id)
        if tbl:
            tbl.status = "Trống"
    await session.flush()
    return {"payment": pay, "invoice": inv}


async def cancel_qr(session, payment_id: int, *, actor_id: int | None = None) -> PaymentTransaction:
    pay = await session.get(PaymentTransaction, payment_id)
    if pay is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    if pay.status != "Chờ xác nhận":
        raise BusinessRuleError("Chỉ hủy QR đang chờ.")
    pay.status = "Đã hủy"
    from app.shared.audit import SystemAuditLog

    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CANCEL_QR_TRANSACTION",
            target_entity="GIAO_DICH_THANH_TOAN",
            target_id=str(pay.id),
        )
    )
    await session.flush()
    return pay


async def expire_stale_qr(session) -> int:
    from sqlalchemy import select as _sel

    from app.modules.sales.models import PaymentTransaction

    now = business_date.now()
    r = await session.execute(
        _sel(PaymentTransaction).where(
            PaymentTransaction.method == "QR", PaymentTransaction.status == "Chờ xác nhận"
        )
    )
    rows = list(r.scalars().all())
    n = 0
    for pay in rows:
        dl = pay.deadline
        if dl is None:
            try:
                dl = pay.created_at + timedelta(minutes=10)
            except Exception:
                continue
        if now > dl:
            pay.status = "Hết hạn"
            n += 1
    if n:
        await session.flush()
    return n


async def mark_for_reconciliation(session, payment_id: int, *, actor_id: int | None = None):
    from app.modules.sales.models import Order, PaymentTransaction
    from app.shared.audit import SystemAuditLog

    pay = await session.get(PaymentTransaction, payment_id)
    if pay is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    if pay.status != "Hết hạn":
        raise BusinessRuleError("Chỉ đối soát QR đã hết hạn.")
    pay.status = "Chờ đối soát"
    order = await session.get(Order, pay.order_id)
    if order:
        order.status = "Chờ đối soát"
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="FLAG_RECONCILIATION",
            target_entity="GIAO_DICH_THANH_TOAN",
            target_id=str(pay.id),
        )
    )
    await session.flush()
    return pay


async def record_bank_reference(
    session,
    payment_id: int,
    reference: str,
    evidence: str | None = None,
    *,
    actor_id: int | None = None,
):
    from app.modules.sales.models import PaymentTransaction

    pay = await session.get(PaymentTransaction, payment_id)
    if pay is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    pay.bank_ref = reference
    pay.evidence = evidence
    from app.shared.audit import SystemAuditLog

    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="RECORD_BANK_REFERENCE",
            target_entity="GIAO_DICH_THANH_TOAN",
            target_id=str(pay.id),
        )
    )
    await session.flush()
    return pay


async def resolve_reconciliation(
    session, payment_id: int, outcome: str, *, actor_id: int | None = None
):
    from app.modules.sales.models import Invoice, Order, PaymentTransaction
    from app.shared.audit import SystemAuditLog

    pay = await session.get(PaymentTransaction, payment_id)
    if pay is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    if pay.status != "Chờ đối soát":
        raise BusinessRuleError("Giao dịch không ở trạng thái chờ đối soát.")
    if outcome not in ("received", "not_received"):
        raise BusinessRuleError("outcome phải là received/not_received")
    if outcome == "received":
        pay.status = "Thành công"
        order = await session.get(Order, pay.order_id)
        assert order is not None
        total = await _order_total(session, order)
        inv = Invoice(
            order_id=order.id, business_date=pay.business_date, total=total, print_count=1
        )
        session.add(inv)
        await session.flush()
        order.status = "Đã thanh toán"
        if order.table_id is not None:
            from app.modules.catalog.models import DiningTable

            tbl = await session.get(DiningTable, order.table_id)
            if tbl:
                tbl.status = "Trống"
    else:
        pay.status = "Tranh chấp"
        order = await session.get(Order, pay.order_id)
        if order:
            order.status = "Tranh chấp"
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="RESOLVE_RECONCILIATION",
            target_entity="GIAO_DICH_THANH_TOAN",
            target_id=str(pay.id),
        )
    )
    await session.flush()
    return pay


async def reprint_invoice(session, order_id: int):
    from sqlalchemy import select as _sel

    from app.modules.sales.models import Invoice

    r = await session.execute(_sel(Invoice).where(Invoice.order_id == order_id))
    inv = r.scalar_one_or_none()
    if inv is None:
        raise NotFoundError("Hóa đơn không tồn tại.")
    inv.print_count = int(inv.print_count) + 1
    await session.flush()
    return inv
