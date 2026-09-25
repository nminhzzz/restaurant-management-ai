"""Sales payments — Task 4."""

import hmac
import hashlib
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.sales.models import Invoice, Order, PaymentTransaction
from app.shared import business_date


def _gateway_sign(payload: str) -> str:
    secret = get_settings().payment_webhook_secret or "test-secret"
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _verify_signature(payload: str, sig: str) -> bool:
    expected = _gateway_sign(payload)
    return hmac.compare_digest(expected, sig)


async def _order_total(session: AsyncSession, order: Order) -> Decimal:
    from app.modules.sales.models import OrderLine
    r = await session.execute(select(OrderLine).where(OrderLine.order_id == order.id))
    lines = list(r.scalars().all())
    total = sum((Decimal(str(l.unit_price)) * int(l.quantity) for l in lines), Decimal(0))
    return total


async def _ensure_open(order: Order):
    from app.modules.sales.orders import ensure_order_is_open
    ensure_order_is_open(order)


async def pay_cash(session: AsyncSession, order_id: int, *, actor_id: int | None = None) -> dict:
    order = await session.get(Order, order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    await _ensure_open(order)
    total = await _order_total(session, order)
    bd = business_date.business_date_of(business_date.now())
    pay = PaymentTransaction(order_id=order.id, amount=float(total), method="Tiền mặt", status="Thành công", business_date=bd)
    session.add(pay)
    await session.flush()
    inv = Invoice(order_id=order.id, business_date=bd, total=float(total))
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


async def start_qr(session: AsyncSession, order_id: int, *, actor_id: int | None = None) -> PaymentTransaction:
    order = await session.get(Order, order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    await _ensure_open(order)
    # refuse if live QR exists
    r = await session.execute(select(PaymentTransaction).where(PaymentTransaction.order_id == order.id, PaymentTransaction.method == "QR", PaymentTransaction.status == "Chờ xác nhận"))
    if r.scalar_one_or_none() is not None:
        raise BusinessRuleError("Đã có QR đang chờ.")
    # also block if reconciliation pending (order Chờ đối soát)
    if order.status == "Chờ đối soát":
        raise BusinessRuleError("Order đang chờ đối soát, không thể tạo QR mới.")
    total = await _order_total(session, order)
    bd = business_date.business_date_of(business_date.now())
    now = business_date.now()
    pay = PaymentTransaction(order_id=order.id, amount=float(total), method="QR", status="Chờ xác nhận", business_date=bd, created_at=now)
    # store deadline in memory attr? Use extra field not persisted -> expose via API computed
    pay._deadline = now + timedelta(minutes=10)  # type: ignore[attr-defined]
    session.add(pay)
    await session.flush()
    return pay


async def handle_webhook(session: AsyncSession, payload: dict) -> dict:
    # payload: payment_id, amount, signature
    pid = payload.get("payment_id") or payload.get("MaGiaoDich")
    amount = payload.get("amount") or payload.get("SoTien")
    sig = payload.get("signature") or payload.get("ChuKy") or ""
    pay = await session.get(PaymentTransaction, int(pid)) if pid else None
    if pay is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    # verify signature
    msg = f"{pay.id}:{amount}"
    if not _verify_signature(msg, str(sig)):
        from app.shared.audit import SystemAuditLog
        session.add(SystemAuditLog(user_id=0, action="WEBHOOK_REJECTED", target_entity="GIAO_DICH_THANH_TOAN", target_id=str(pay.id)))
        await session.flush()
        raise BusinessRuleError("Chữ ký không hợp lệ.")
    # idempotent
    if pay.status == "Thành công":
        return {"payment": pay}
    if pay.status != "Chờ xác nhận":
        raise BusinessRuleError("Giao dịch không ở trạng thái chờ.")
    order = await session.get(Order, pay.order_id)
    assert order is not None
    total = await _order_total(session, order)
    if amount is not None and Decimal(str(amount)) != total:
        raise BusinessRuleError("Số tiền không khớp.")
    pay.status = "Thành công"
    await session.flush()
    # invoice
    bd = pay.business_date
    inv = Invoice(order_id=order.id, business_date=bd, total=float(total))
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


async def cancel_qr(session: AsyncSession, payment_id: int, *, actor_id: int | None = None) -> PaymentTransaction:
    pay = await session.get(PaymentTransaction, payment_id)
    if pay is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    if pay.status != "Chờ xác nhận":
        raise BusinessRuleError("Chỉ hủy QR đang chờ.")
    pay.status = "Đã hủy"
    from app.shared.audit import SystemAuditLog
    session.add(SystemAuditLog(user_id=actor_id or 0, action="CANCEL_QR_TRANSACTION", target_entity="GIAO_DICH_THANH_TOAN", target_id=str(pay.id)))
    await session.flush()
    return pay
