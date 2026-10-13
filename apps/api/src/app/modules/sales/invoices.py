"""Invoices and the provisional bill (FR-SALE-21, FR-SALE-26).

An invoice is issued once, inside the transaction that settles the payment, and stores the
content it was issued with; a reprint renders that stored content and only counts the print.
The provisional bill ("PHIẾU TẠM TÍNH - CHƯA THANH TOÁN") is computed from the live order and
never creates an invoice row, an invoice number or revenue.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.catalog.models import DiningTable, Dish
from app.modules.sales.common import (
    LINE_CANCELLED,
    audit_order,
    invoice_of,
    local_now,
    lock_order,
    order_total,
)
from app.modules.sales.models import Invoice, Order, OrderLine, PaymentTransaction
from app.modules.settings.service import get_config
from app.shared.enums import OrderStatus

PROVISIONAL_TITLE = "PHIẾU TẠM TÍNH - CHƯA THANH TOÁN"
_PROVISIONAL_STATUSES = frozenset(
    {
        OrderStatus.DANG_MO.value,
        OrderStatus.CHO_XAC_NHAN_THANH_TOAN.value,
        OrderStatus.CHO_XAC_MINH_THANH_TOAN.value,
    }
)


def invoice_number_for(invoice: Invoice) -> str:
    """HD-ddMMyy-nnnnnn: the Business Date plus the invoice's own id, unique by construction."""
    return f"HD-{invoice.business_date.strftime('%d%m%y')}-{int(invoice.id):06d}"


async def _bill_lines(session: AsyncSession, order: Order) -> list[dict[str, Any]]:
    lines = list(
        (
            await session.execute(
                select(OrderLine)
                .where(OrderLine.order_id == order.id, OrderLine.status != LINE_CANCELLED)
                .order_by(OrderLine.id)
            )
        )
        .scalars()
        .all()
    )
    names: dict[int, str] = {}
    if lines:
        rows = await session.execute(
            select(Dish.id, Dish.name).where(Dish.id.in_({line.dish_id for line in lines}))
        )
        names = {dish_id: name for dish_id, name in rows}
    return [
        {
            "MaMon": line.dish_id,
            "TenMon": names.get(line.dish_id, ""),
            "SoLuong": int(line.quantity),
            "DonGia": float(line.unit_price),
            "ThanhTien": float(Decimal(str(line.unit_price)) * int(line.quantity)),
            "GhiChu": line.note,
        }
        for line in lines
    ]


async def _table_name(session: AsyncSession, order: Order) -> str | None:
    if order.table_id is None:
        return None
    return (
        await session.execute(select(DiningTable.name).where(DiningTable.id == order.table_id))
    ).scalar_one_or_none()


async def _restaurant(session: AsyncSession) -> dict[str, Any]:
    config = await get_config(session)
    return {
        "TenNhaHang": config.restaurant_name,
        "DiaChi": config.address,
        "MauHoaDon": config.invoice_template,
    }


async def issue_invoice(
    session: AsyncSession,
    order: Order,
    payment: PaymentTransaction,
    *,
    total: Decimal,
    actor_id: int | None,
) -> Invoice:
    """Issue the one invoice of a settled order (BusinessDate inherited from the order)."""
    if await invoice_of(session, order.id) is not None:
        raise BusinessRuleError("Order đã có hóa đơn.")
    issued_at = local_now()
    invoice = Invoice(
        order_id=order.id,
        business_date=order.business_date,
        issued_at=issued_at,
        total=total,
        print_count=1,
        payment_transaction_id=payment.id,
        payment_method=payment.method,
        issued_by=actor_id,
    )
    session.add(invoice)
    await session.flush()
    invoice.invoice_number = invoice_number_for(invoice)
    invoice.content = {
        **await _restaurant(session),
        "SoHoaDon": invoice.invoice_number,
        "MaOrderHienThi": order.display_code,
        "LoaiDon": order.order_type,
        "TenBan": await _table_name(session, order),
        "BusinessDate": order.business_date.isoformat(),
        "ThoiDiemXuat": issued_at.isoformat(),
        "PhuongThucThanhToan": payment.method,
        "TongTien": float(total),
        "lines": await _bill_lines(session, order),
    }
    await session.flush()
    return invoice


def invoice_payload(invoice: Invoice) -> dict[str, Any]:
    """The invoice as issued; only the print counter is live."""
    content = dict(invoice.content or {})
    return {
        **content,
        "MaHoaDon": invoice.id,
        "MaOrder": invoice.order_id,
        "SoHoaDon": invoice.invoice_number,
        "NguoiLap": invoice.issued_by,
        "ThoiDiemXuat": invoice.issued_at.isoformat() if invoice.issued_at else None,
        "PhuongThucThanhToan": invoice.payment_method,
        "TongTien": float(invoice.total),
        "SoLanIn": invoice.print_count,
    }


async def get_invoice_payload(session: AsyncSession, order_id: int) -> dict[str, Any]:
    invoice = await invoice_of(session, order_id)
    if invoice is None:
        raise NotFoundError("Hóa đơn không tồn tại.")
    payload = invoice_payload(invoice)
    if invoice.content is None:
        # Issued before the content was stored: render it from the order once more.
        order = await session.get(Order, order_id)
        if order is not None:
            payload.update(
                {
                    **await _restaurant(session),
                    "MaOrderHienThi": order.display_code,
                    "TenBan": await _table_name(session, order),
                    "lines": await _bill_lines(session, order),
                }
            )
    return payload


async def reprint_invoice(
    session: AsyncSession, order_id: int, *, actor_id: int | None = None
) -> dict[str, Any]:
    """FR-SALE-26: the stored content, unchanged; the print counter goes up and is audited."""
    order = await lock_order(session, order_id)
    invoice = await invoice_of(session, order_id)
    if invoice is None:
        raise NotFoundError("Hóa đơn không tồn tại.")
    before = int(invoice.print_count)
    invoice.print_count = before + 1
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action="REPRINT_INVOICE",
        before={"SoLanIn": before},
        after={"SoLanIn": int(invoice.print_count), "SoHoaDon": invoice.invoice_number},
    )
    await session.flush()
    return await get_invoice_payload(session, order_id)


async def provisional_bill(session: AsyncSession, order_id: int) -> dict[str, Any]:
    """FR-SALE-21: what the guests check before paying. Read-only, locks nothing, bills nothing."""
    order = await session.get(Order, order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    if order.status not in _PROVISIONAL_STATUSES:
        raise BusinessRuleError("Order không còn ở bước thanh toán nên không in phiếu tạm tính.")
    lines = await _bill_lines(session, order)
    if not lines:
        raise BusinessRuleError("Order chưa có món nào.")
    now: datetime = local_now()
    return {
        "TieuDe": PROVISIONAL_TITLE,
        **await _restaurant(session),
        "MaOrder": order.id,
        "MaOrderHienThi": order.display_code,
        "LoaiDon": order.order_type,
        "TenBan": await _table_name(session, order),
        "TrangThai": order.status,
        "ThoiDiemIn": now.isoformat(),
        "TongTien": float(await order_total(session, order)),
        "lines": lines,
    }
