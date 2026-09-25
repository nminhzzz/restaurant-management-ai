"""HTTP layer for the sales module.

Service functions raise `AppError` subclasses (`NotFoundError`, `BusinessRuleError`,
`UnauthenticatedError`); `app.core.errors.register_error_handlers` already maps them to
404 / 422 / 401 responses, so the handlers here stay free of per-endpoint translation.
"""

import contextlib
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import Principal, require_roles
from app.modules.sales import orders, payments
from app.modules.sales.models import Invoice, KitchenTicket, Order, OrderLine
from app.modules.sales.schemas import SubmitOrderIn
from app.shared.roles import Role

router = APIRouter(prefix="/sales", tags=["Module 2 — Sales"])


def _line_payload(line: OrderLine) -> dict:
    return {
        "MaChiTietOrder": line.id,
        "MaMon": line.dish_id,
        "SoLuong": line.quantity,
        "DonGia": float(line.unit_price),
        "MaPhienBanGia": line.price_version_id,
        "MaCongThuc": line.recipe_id,
        "GhiChu": line.note,
        "TrangThai": line.status,
    }


def _order_payload(order: Order, lines: list[OrderLine]) -> dict:
    return {
        "MaOrder": order.id,
        "MaOrderHienThi": order.display_code,
        "MaBan": order.table_id,
        "TrangThai": order.status,
        "ThoiDiemTao": order.created_at.isoformat() if order.created_at else None,
        "ThoiDiemDong": order.updated_at.isoformat() if order.updated_at else None,
        "lines": [_line_payload(line) for line in lines],
    }


@router.post("/orders", status_code=201)
async def create_order(
    payload: SubmitOrderIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    result = await orders.submit_order(
        session,
        {
            "table_id": payload.table_id,
            "order_type": payload.order_type,
            "lines": [line.model_dump() for line in payload.lines],
        },
        actor_id=user.user_id,
    )
    await session.commit()
    body = _order_payload(result["order"], result["lines"])
    body["rejected"] = result["rejected"]
    return body


@router.get("/orders")
async def search_orders(
    code: str | None = None,
    table_id: int | None = None,
    business_date: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    limit: int | None = Query(None, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER, Role.WAREHOUSE)),
):
    filters = []
    if code:
        filters.append(Order.display_code == code)
    if table_id is not None:
        filters.append(Order.table_id == table_id)
    if business_date is not None:
        filters.append(Order.business_date == business_date)
    if date_from is not None:
        filters.append(Order.business_date >= date_from)
    if date_to is not None:
        filters.append(Order.business_date <= date_to)
    if status:
        filters.append(Order.status == status)

    total = (await session.execute(select(func.count(Order.id)).where(*filters))).scalar_one()

    # A year of orders must never reach the browser in one response.
    query = select(Order).where(*filters).order_by(Order.id.desc())
    # `limit` is a backward-compatible alias for `size` (no offset applied).
    query = query.limit(limit) if limit is not None else query.offset((page - 1) * size).limit(size)
    rows = list((await session.execute(query)).scalars().all())
    items = [
        {
            "MaOrder": order.id,
            "MaOrderHienThi": order.display_code,
            "MaBan": order.table_id,
            "BusinessDate": order.business_date.isoformat(),
            "TrangThai": order.status,
        }
        for order in rows
    ]
    return {"total": total, "items": items}


@router.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER, Role.WAREHOUSE)),
):
    await payments.expire_stale_qr(session)
    await session.commit()
    order = await session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order không tồn tại.")
    lines = list(
        (await session.execute(select(OrderLine).where(OrderLine.order_id == order_id)))
        .scalars()
        .all()
    )
    return _order_payload(order, lines)


@router.post("/orders/{order_id}/lines", status_code=201)
async def add_order_line(
    order_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    dish_id = payload.get("dish_id") if payload.get("dish_id") is not None else payload.get("MaMon")
    if dish_id is None:
        raise HTTPException(status_code=422, detail="Thiếu MaMon")
    quantity = payload.get("quantity") or payload.get("SoLuong") or 1
    note = payload.get("note") or payload.get("GhiChu")
    line = await orders.add_line(
        session, order_id, int(dish_id), int(quantity), note, actor_id=user.user_id
    )
    await session.commit()
    return _line_payload(line)


@router.patch("/orders/{order_id}/lines/{line_id}")
async def patch_order_line(
    order_id: int,
    line_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    quantity = payload.get("quantity") or payload.get("SoLuong")
    if quantity is None:
        raise HTTPException(status_code=422, detail="Thiếu SoLuong")
    line = await orders.update_line(
        session, order_id, line_id, int(quantity), actor_id=user.user_id
    )
    await session.commit()
    return {"MaChiTietOrder": line.id, "SoLuong": line.quantity}


@router.patch("/orders/{order_id}/lines/{line_id}/status")
async def patch_line_status(
    order_id: int,
    line_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    to_status = payload.get("to") or payload.get("TrangThai")
    if not to_status:
        raise HTTPException(status_code=422, detail="Thiếu TrangThai")
    line = await orders.advance_line_status(session, line_id, str(to_status))
    await session.commit()
    return {"MaChiTietOrder": line.id, "TrangThai": line.status}


@router.post("/orders/{order_id}/lines/{line_id}/cancel")
async def cancel_order_line(
    order_id: int,
    line_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    reason = payload.get("reason") or payload.get("LyDo") or ""
    await orders.cancel_line(session, line_id, str(reason), actor_id=user.user_id)
    await session.commit()
    return {"ok": True}


@router.post("/orders/{order_id}/move")
async def move_order_table(
    order_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    to_table_id = payload.get("to_table_id") or payload.get("MaBanDich") or payload.get("to")
    if to_table_id is None:
        raise HTTPException(status_code=422, detail="Thiếu MaBanDich")
    order = await orders.move_table(session, order_id, int(to_table_id), actor_id=user.user_id)
    await session.commit()
    return {"MaOrder": order.id, "MaBan": order.table_id}


@router.post("/orders/{order_id}/cancel")
async def cancel_whole_order(
    order_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER)),
):
    reason = payload.get("reason") or payload.get("LyDoHuy") or ""
    order = await orders.cancel_order(session, order_id, str(reason), actor_id=user.user_id)
    await session.commit()
    return {"MaOrder": order.id, "TrangThai": order.status}


@router.get("/orders/{order_id}/tickets")
async def list_tickets(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER, Role.WAREHOUSE)),
):
    """FR-SALE-27/28: kitchen tickets for an order, so the UI can reprint or flag a failed print."""
    tickets = list(
        (
            await session.execute(
                select(KitchenTicket)
                .where(KitchenTicket.order_id == order_id)
                .order_by(KitchenTicket.id.asc())
            )
        )
        .scalars()
        .all()
    )
    return {
        "items": [
            {
                "MaPhieuBep": ticket.id,
                "NoiDung": ticket.content,
                "TrangThai": ticket.status,
                "TrangThaiIn": ticket.print_status,
                "SoLanIn": ticket.print_count,
            }
            for ticket in tickets
        ]
    }


@router.post("/orders/{order_id}/tickets/{ticket_id}/reprint")
async def reprint_ticket(
    order_id: int,
    ticket_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    ticket = await session.get(KitchenTicket, ticket_id)
    if ticket is None or ticket.order_id != order_id:
        raise HTTPException(status_code=404, detail="Phiếu bếp không tồn tại.")
    from app.modules.sales.tickets import record_print_result

    record_print_result(ticket, True)
    await session.commit()
    return {"MaPhieuBep": ticket.id, "SoLanIn": ticket.print_count}


@router.post("/orders/{order_id}/tickets/{ticket_id}/print-result")
async def report_ticket_print_result(
    order_id: int,
    ticket_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    """FR-SALE-28: the UI reports a failed print so staff can be warned and retry."""
    ticket = await session.get(KitchenTicket, ticket_id)
    if ticket is None or ticket.order_id != order_id:
        raise HTTPException(status_code=404, detail="Phiếu bếp không tồn tại.")
    from app.modules.sales.tickets import record_print_result

    ok = bool(payload.get("ok", True))
    record_print_result(ticket, ok)
    await session.commit()
    return {"MaPhieuBep": ticket.id, "TrangThai": ticket.status, "SoLanIn": ticket.print_count}


@router.get("/orders/{order_id}/payments")
async def list_payments(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    """Lets the UI recover the live/expired QR transaction after a reload (FR-SALE-17/18)."""
    await payments.expire_stale_qr(session)
    await session.commit()
    from app.modules.sales.models import PaymentTransaction

    rows = list(
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
    return {
        "items": [
            {
                "MaGiaoDich": p.id,
                "PhuongThuc": p.method,
                "TrangThai": p.status,
                "SoTien": float(p.amount),
                "ThoiDiemTaoQR": p.created_at.isoformat() if p.created_at else None,
                "ThoiDiemHetHan": p.deadline.isoformat() if p.deadline else None,
                "MaThamChieuNganHang": p.bank_ref,
            }
            for p in rows
        ]
    }


@router.post("/orders/{order_id}/pay/cash")
async def pay_order_cash(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    result = await payments.pay_cash(session, order_id, actor_id=user.user_id)
    await session.commit()
    invoice = result["invoice"]
    return {
        "invoice": {"SoHoaDon": str(invoice.id), "TongTien": float(invoice.total)},
        "MaHoaDon": invoice.id,
    }


@router.post("/orders/{order_id}/pay/qr", status_code=201)
async def start_order_qr(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    payment = await payments.start_qr(session, order_id, actor_id=user.user_id)
    await session.commit()
    return {
        "MaGiaoDich": payment.id,
        "TrangThai": payment.status,
        "ThoiDiemTaoQR": payment.created_at.isoformat() if payment.created_at else None,
        "ThoiDiemHetHan": payment.deadline.isoformat() if payment.deadline else None,
    }


@router.post("/webhooks/payment")
async def webhook_payment(
    payload: dict,
    session: AsyncSession = Depends(get_session),
):
    result = await payments.handle_webhook(session, payload)
    await session.commit()
    return {"ok": True, "MaGiaoDich": result["payment"].id}


@router.post("/payments/{payment_id}/cancel")
async def cancel_payment_qr(
    payment_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    payment = await payments.cancel_qr(session, payment_id, actor_id=user.user_id)
    await session.commit()
    return {"MaGiaoDich": payment.id, "TrangThai": payment.status}


@router.post("/orders/{order_id}/reconcile")
async def flag_reconcile(
    order_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    payment_id = payload.get("payment_id") or payload.get("MaGiaoDich")
    if payment_id is None:
        raise HTTPException(status_code=422, detail="Thiếu MaGiaoDich")
    payment = await payments.mark_for_reconciliation(
        session, int(payment_id), actor_id=user.user_id
    )
    await session.commit()
    return {"MaGiaoDich": payment.id, "TrangThai": payment.status}


@router.post("/payments/{payment_id}/reference")
async def bank_reference(
    payment_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    reference = payload.get("reference") or payload.get("MaGiaoDichNganHang") or ""
    evidence = payload.get("evidence") or payload.get("AnhChungTu")
    payment = await payments.record_bank_reference(
        session, int(payment_id), str(reference), evidence, actor_id=user.user_id
    )
    await session.commit()
    return {"MaGiaoDich": payment.id}


@router.post("/payments/{payment_id}/resolve")
async def resolve_payment(
    payment_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER)),
):
    outcome = payload.get("outcome") or payload.get("ketQua") or ""
    payment = await payments.resolve_reconciliation(
        session, int(payment_id), str(outcome), actor_id=user.user_id
    )
    await session.commit()
    return {"MaGiaoDich": payment.id, "TrangThai": payment.status}


async def _invoice_payload(session: AsyncSession, order_id: int, invoice: Invoice) -> dict:
    """FR-SALE-19/23: enough detail (restaurant info, lines, method, time) to print a receipt."""
    from app.modules.catalog.models import Dish
    from app.modules.sales.models import PaymentTransaction
    from app.modules.settings.service import get_config

    order = await session.get(Order, order_id)
    lines = list(
        (await session.execute(select(OrderLine).where(OrderLine.order_id == order_id)))
        .scalars()
        .all()
    )
    dish_ids = {line.dish_id for line in lines}
    dish_names: dict[int, str] = {}
    if dish_ids:
        rows = (await session.execute(select(Dish).where(Dish.id.in_(dish_ids)))).scalars().all()
        dish_names = {dish.id: dish.name for dish in rows}
    payment = (
        (
            await session.execute(
                select(PaymentTransaction)
                .where(PaymentTransaction.order_id == order_id)
                .order_by(PaymentTransaction.id.desc())
            )
        )
        .scalars()
        .first()
    )

    restaurant_name = None
    address = None
    with contextlib.suppress(Exception):
        cfg = await get_config(session)
        restaurant_name = cfg.restaurant_name
        address = cfg.address

    return {
        "SoHoaDon": str(invoice.id),
        "MaOrderHienThi": order.display_code if order else None,
        "TenNhaHang": restaurant_name,
        "DiaChi": address,
        "ThoiDiemXuat": invoice.issued_at.isoformat() if invoice.issued_at else None,
        "PhuongThucThanhToan": payment.method if payment else None,
        "TongTien": float(invoice.total),
        "SoLanIn": invoice.print_count,
        "lines": [
            {
                "MaMon": line.dish_id,
                "TenMon": dish_names.get(line.dish_id, ""),
                "SoLuong": line.quantity,
                "DonGia": float(line.unit_price),
                "ThanhTien": float(line.unit_price) * line.quantity,
            }
            for line in lines
            if line.status != "Đã hủy"
        ],
    }


@router.get("/orders/{order_id}/invoice")
async def get_invoice(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    invoice = (
        await session.execute(select(Invoice).where(Invoice.order_id == order_id))
    ).scalar_one_or_none()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Hóa đơn không tồn tại.")
    return await _invoice_payload(session, order_id, invoice)


@router.post("/orders/{order_id}/invoice/reprint")
async def reprint_invoice_ep(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    invoice = await payments.reprint_invoice(session, order_id)
    await session.commit()
    return await _invoice_payload(session, order_id, invoice)
