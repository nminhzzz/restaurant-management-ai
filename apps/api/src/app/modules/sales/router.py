"""HTTP layer for the sales module.

Service functions raise `AppError` subclasses (`NotFoundError`, `BusinessRuleError`,
`UnauthenticatedError`); `app.core.errors.register_error_handlers` already maps them to
404 / 422 / 401 responses, so the handlers here stay free of per-endpoint translation.
"""

import contextlib
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
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
    business_date: str | None = None,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER, Role.WAREHOUSE)),
):
    query = select(Order)
    if code:
        query = query.where(Order.display_code == code)
    if table_id is not None:
        query = query.where(Order.table_id == table_id)
    if business_date:
        with contextlib.suppress(ValueError):
            query = query.where(Order.business_date == date.fromisoformat(business_date))
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
    return {"total": len(items), "items": items}


@router.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER, Role.WAREHOUSE)),
):
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
    return {
        "SoHoaDon": str(invoice.id),
        "TongTien": float(invoice.total),
        "SoLanIn": invoice.print_count,
    }


@router.post("/orders/{order_id}/invoice/reprint")
async def reprint_invoice_ep(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    invoice = await payments.reprint_invoice(session, order_id)
    await session.commit()
    return {
        "SoHoaDon": str(invoice.id),
        "TongTien": float(invoice.total),
        "SoLanIn": invoice.print_count,
    }
