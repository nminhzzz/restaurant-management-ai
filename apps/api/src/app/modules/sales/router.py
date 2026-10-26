"""HTTP layer for the sales module.

Service functions raise `AppError` subclasses (`NotFoundError`, `BusinessRuleError`,
`UnauthenticatedError`); `app.core.errors.register_error_handlers` already maps them to
404 / 422 / 401 responses, so the handlers here stay free of per-endpoint translation.
"""

import contextlib
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.dependencies import Principal, require_roles
from app.core.errors import NotFoundError, UnauthenticatedError
from app.modules.catalog.models import Dish, DishPriceVersion
from app.modules.sales import floor, orders, payments, reservations
from app.modules.sales.gateways import sepay
from app.modules.sales.models import Invoice, KitchenTicket, Order, OrderLine, Reservation
from app.modules.sales.schemas import (
    AddLinesIn,
    HoldCreate,
    HoldOut,
    HoldReleaseIn,
    HoldUpdate,
    ReleaseTableIn,
    SubmitOrderIn,
)
from app.shared import business_date
from app.shared.audit import SystemAuditLog
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


async def _hold_payload(session: AsyncSession, hold: Reservation) -> HoldOut:
    dish = await session.get(Dish, hold.dish_id)
    price = (
        await session.get(DishPriceVersion, hold.price_version_id)
        if hold.price_version_id is not None
        else None
    )
    return HoldOut(
        MaGiuCho=hold.id,
        MaLuotChon=hold.selection_code,
        MaBan=hold.table_id,
        MaMon=hold.dish_id,
        TenMon=dish.name if dish is not None else None,
        SoLuong=hold.quantity,
        GhiChu=hold.note,
        ThoiDiemHetHan=hold.expires_at,
        TrangThai=hold.status,
        DonGia=float(price.price) if price is not None else None,
        MaPhienBanGia=hold.price_version_id,
        MaCongThuc=hold.recipe_id,
    )


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


@router.get("/floor")
async def get_floor(
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    return await floor.floor_board(session)


@router.post("/tables/{table_id}/release")
async def release_table(
    table_id: int,
    payload: ReleaseTableIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    table = await floor.release_table(session, table_id, payload.order_id, actor_id=user.user_id)
    await session.commit()
    return {"MaBan": table.id, "TrangThai": table.status}


@router.post("/holds", response_model=HoldOut, status_code=201)
async def create_hold(
    payload: HoldCreate,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    hold = await reservations.create_hold(
        session,
        user_id=user.user_id,
        selection_code=payload.selection_code,
        table_id=payload.table_id,
        order_id=payload.order_id,
        dish_id=payload.dish_id,
        quantity=payload.quantity,
        note=payload.note,
    )
    await session.commit()
    return await _hold_payload(session, hold)


@router.get("/holds", response_model=list[HoldOut])
async def list_holds(
    selection_code: str | None = None,
    order_id: int | None = None,
    include_expired: bool = False,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    holds = await reservations.list_holds(
        session,
        user_id=user.user_id,
        selection_code=selection_code,
        order_id=order_id,
        include_expired=include_expired,
    )
    await session.commit()
    return [await _hold_payload(session, hold) for hold in holds]


@router.post("/holds/release")
async def release_selection(
    payload: HoldReleaseIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    """FR-SALE-08: drop the whole unsent selection and release its stock at once."""
    released = await reservations.release_selection(
        session,
        user_id=user.user_id,
        selection_code=payload.selection_code,
        order_id=payload.order_id,
    )
    await session.commit()
    return {"released": released}


@router.patch("/holds/{hold_id}", response_model=HoldOut)
async def update_hold(
    hold_id: int,
    payload: HoldUpdate,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    hold = await reservations.update_hold(
        session, hold_id=hold_id, user_id=user.user_id, quantity=payload.quantity
    )
    await session.commit()
    return await _hold_payload(session, hold)


@router.delete("/holds/{hold_id}")
async def release_hold(
    hold_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    hold = await reservations.release_hold(session, hold_id=hold_id, user_id=user.user_id)
    await session.commit()
    return {"MaGiuCho": hold.id, "TrangThai": hold.status}


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
            "request_id": payload.request_id,
        },
        actor_id=user.user_id,
        confirm_expired=payload.confirm_expired,
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
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
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
    return {"total": total, "items": await orders.list_summaries(session, rows)}


@router.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
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
    quantity = int(payload.get("quantity") or payload.get("SoLuong") or 1)
    if quantity < 1:
        raise HTTPException(status_code=422, detail="SoLuong phải lớn hơn 0.")
    note = payload.get("note") or payload.get("GhiChu")
    line = await orders.add_line(
        session,
        order_id,
        int(dish_id),
        int(quantity),
        note,
        actor_id=user.user_id,
        hold_id=payload.get("hold_id"),
        request_line_id=payload.get("request_line_id") or payload.get("MaYeuCauDong"),
        confirm_expired=bool(payload.get("XacNhanHetHan") or payload.get("confirm_expired")),
    )
    await session.commit()
    return _line_payload(line)


@router.post("/orders/{order_id}/lines/bulk", status_code=201)
async def add_order_lines(
    order_id: int,
    payload: AddLinesIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    """FR-SALE-03: all confirmed lines succeed or the whole submission is rolled back."""
    lines = await orders.add_lines(
        session,
        order_id,
        [line.model_dump() for line in payload.lines],
        actor_id=user.user_id,
        confirm_expired=payload.confirm_expired,
    )
    await session.commit()
    return {"items": [_line_payload(line) for line in lines]}


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
    if int(quantity) < 1:
        raise HTTPException(status_code=422, detail="SoLuong phải lớn hơn 0.")
    line = await orders.update_line(
        session,
        order_id,
        line_id,
        int(quantity),
        actor_id=user.user_id,
        request_line_id=payload.get("request_line_id"),
    )
    await session.commit()
    return {
        "MaChiTietOrder": line.id,
        "SoLuong": line.quantity,
        "message": "Đã gọi thêm thành dòng món mới."
        if line.id != line_id
        else "Đã cập nhật số lượng.",
    }


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
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
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
                "LoiIn": ticket.print_error,
                "ThoiDiemIn": ticket.printed_at,
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
    from app.modules.sales.tickets import request_reprint

    ticket = await request_reprint(session, order_id, ticket_id)
    await session.commit()
    return {
        "MaPhieuBep": ticket.id,
        "SoLanIn": ticket.print_count,
        "TrangThaiIn": ticket.print_status,
        "NoiDung": ticket.content,
    }


@router.post("/orders/{order_id}/tickets/{ticket_id}/print-result")
async def report_ticket_print_result(
    order_id: int,
    ticket_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    """Accept staff problem reports; browser cannot establish printer success."""
    if payload.get("ok") is not False:
        raise HTTPException(status_code=422, detail="Kết quả gửi in chỉ do máy chủ ghi nhận.")
    from app.modules.sales.tickets import report_print_problem

    ticket = await report_print_problem(session, order_id, ticket_id)
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
    items = []
    for p in rows:
        item = {
            "MaGiaoDich": p.id,
            "PhuongThuc": p.method,
            "TrangThai": p.status,
            "SoTien": float(p.amount),
            "ThoiDiemTaoQR": p.created_at.isoformat() if p.created_at else None,
            "ThoiDiemHetHan": p.deadline.isoformat() if p.deadline else None,
            "ThoiDiemTao": p.created_at.isoformat() if p.created_at else None,
            "MaThamChieuNganHang": p.bank_ref,
            "AnhChungTu": p.evidence,
        }
        if p.status == payments.QR_PENDING:
            item.update(await payments.qr_fields(session, p))
        items.append(item)
    return {"items": items}


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
        "invoice": {
            "SoHoaDon": invoice.invoice_number or str(invoice.id),
            "TongTien": float(invoice.total),
        },
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
        "SoTien": float(payment.amount),
        "ThoiDiemTaoQR": payment.created_at.isoformat() if payment.created_at else None,
        "ThoiDiemHetHan": payment.deadline.isoformat() if payment.deadline else None,
        **(await payments.qr_fields(session, payment)),
    }


@router.post("/webhooks/payment")
async def webhook_payment(
    payload: dict,
    session: AsyncSession = Depends(get_session),
):
    if get_settings().payment_gateway == "sepay":
        raise NotFoundError("Không tìm thấy.")
    result = await payments.handle_webhook(session, payload)
    await session.commit()
    return {"ok": True, "MaGiaoDich": result["payment"].id}


@router.post("/webhooks/sepay")
async def webhook_sepay(request: Request, session: AsyncSession = Depends(get_session)):
    settings = get_settings()
    if settings.payment_gateway != "sepay":
        raise NotFoundError("Không tìm thấy.")
    if not sepay.api_key_matches(
        request.headers.get("Authorization"), settings.sepay_webhook_api_key
    ):
        session.add(
            SystemAuditLog(
                user_id=None,
                action="WEBHOOK_REJECTED",
                target_entity="GIAO_DICH_THANH_TOAN",
                target_id="sepay",
            )
        )
        await session.commit()
        raise UnauthenticatedError("API key không hợp lệ.")
    body = await request.json()
    await payments.handle_sepay_transfer(session, body if isinstance(body, dict) else {})
    await session.commit()
    return {"success": True}


@router.post("/payments/{payment_id}/check")
async def check_payment(
    payment_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    payment = await payments.check_payment(session, payment_id)
    await session.commit()
    return {"MaGiaoDich": payment.id, "TrangThai": payment.status}


@router.post("/payments/{payment_id}/cancel")
async def cancel_payment_qr(
    payment_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    payment = await payments.cancel_qr(session, payment_id, actor_id=user.user_id)
    await session.commit()
    return {"MaGiaoDich": payment.id, "TrangThai": payment.status}


@router.post("/payments/{payment_id}/request-verification")
async def request_payment_verification(
    payment_id: int,
    payload: dict | None = None,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    body = payload or {}
    payment = await payments.request_verification(
        session,
        payment_id,
        actor_id=user.user_id,
        bank_ref=body.get("reference") or body.get("bank_ref") or body.get("MaGiaoDichNganHang"),
        evidence=body.get("evidence") or body.get("AnhChungTu"),
        note=body.get("note") or body.get("GhiChu"),
    )
    await session.commit()
    return {"MaGiaoDich": payment.id, "TrangThai": payment.status}


@router.post("/payments/{payment_id}/reopen")
async def reopen_payment(
    payment_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER)),
):
    reason = payload.get("reason") or payload.get("LyDo") or ""
    outcome = payload.get("outcome") or payload.get("KetQuaXuLy")
    order = await payments.reopen_payment(
        session,
        payment_id,
        reason=str(reason),
        outcome=str(outcome) if outcome else None,
        actor_id=user.user_id,
    )
    await session.commit()
    return {"MaOrder": order.id, "TrangThai": order.status}


@router.post("/orders/{order_id}/close-unpaid")
async def close_unpaid_order(
    order_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER)),
):
    reason = payload.get("reason") or payload.get("LyDo") or ""
    outcome = payload.get("outcome") or payload.get("KetQuaXuLy")
    order = await payments.close_unpaid_order(
        session,
        order_id,
        reason=str(reason),
        outcome=str(outcome) if outcome else None,
        actor_id=user.user_id,
    )
    await session.commit()
    return {"MaOrder": order.id, "TrangThai": order.status}


@router.post("/payments/{payment_id}/apply-late")
async def apply_late_payment(
    payment_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER)),
):
    result = await payments.apply_late_payment(
        session,
        payment_id,
        actor_id=user.user_id,
        bank_ref=payload.get("bank_ref") or payload.get("MaGiaoDichNganHang"),
    )
    await session.commit()
    return {
        "MaGiaoDich": result["payment"].id,
        "MaHoaDon": result["invoice"].id,
        "TrangThai": result["payment"].status,
    }


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
    reference = (
        payload.get("reference")
        or payload.get("bank_ref")
        or payload.get("MaGiaoDichNganHang")
        or ""
    )
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
    raw_amount = payload.get("received_amount") or payload.get("SoTienNhan")
    note = payload.get("note") or payload.get("GhiChu")
    payment = await payments.resolve_reconciliation(
        session,
        int(payment_id),
        str(outcome),
        actor_id=user.user_id,
        received_amount=Decimal(str(raw_amount)) if raw_amount is not None else None,
        note=str(note) if note else None,
    )
    await session.commit()
    return {"MaGiaoDich": payment.id, "TrangThai": payment.status}


@router.get("/payment-exceptions")
async def list_payment_exceptions(
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER)),
):
    """FR-SALE-17: money the gateway reported that no order could absorb."""
    rows = await payments.list_exceptions(session, status=status)
    return {
        "items": [
            {
                "MaNgoaiLe": exception.id,
                "MaOrder": exception.order_id,
                "MaOrderHienThi": order_code,
                "MaGiaoDich": exception.payment_transaction_id,
                "MaGiaoDichCong": exception.bank_ref,
                "SoTien": float(exception.amount),
                "TrangThai": exception.status,
                "LyDo": exception.reason,
                "GhiChu": exception.note,
                "MaThamChieuHoan": exception.refund_ref,
                "SoTienHoan": float(exception.refund_amount)
                if exception.refund_amount is not None
                else None,
                "ThoiDiemTao": exception.created_at.isoformat() if exception.created_at else None,
                "ThoiDiemXuLy": exception.resolved_at.isoformat()
                if exception.resolved_at
                else None,
                "NguoiXuLy": exception.resolved_by,
            }
            for exception, order_code in rows
        ]
    }


@router.post("/payment-exceptions/{exception_id}/resolve")
async def resolve_payment_exception(
    exception_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER)),
):
    outcome = payload.get("outcome") or payload.get("ketQua") or ""
    note = payload.get("note") or payload.get("GhiChu")
    refund_ref = payload.get("refund_ref") or payload.get("MaThamChieuHoan")
    refund_amount = payload.get("refund_amount") or payload.get("SoTienHoan")
    exception = await payments.resolve_exception(
        session,
        exception_id,
        outcome=str(outcome),
        actor_id=user.user_id,
        note=str(note) if note is not None else None,
        refund_ref=str(refund_ref) if refund_ref is not None else None,
        refund_amount=Decimal(str(refund_amount)) if refund_amount is not None else None,
    )
    await session.commit()
    return {
        "MaNgoaiLe": exception.id,
        "TrangThai": exception.status,
        "MaGiaoDichCong": exception.bank_ref,
        "MaThamChieuHoan": exception.refund_ref,
        "SoTienHoan": float(exception.refund_amount)
        if exception.refund_amount is not None
        else None,
    }


async def _invoice_payload(session: AsyncSession, order_id: int, invoice: Invoice) -> dict:
    """FR-SALE-19/23: enough detail (restaurant info, lines, method, time) to print a receipt."""
    if invoice.snapshot:
        payload = dict(invoice.snapshot)
        payload["SoHoaDon"] = invoice.invoice_number or str(invoice.id)
        payload["SoLanIn"] = invoice.print_count
        return payload
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
        "SoHoaDon": invoice.invoice_number or str(invoice.id),
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


@router.get("/orders/{order_id}/provisional-invoice")
async def get_provisional_invoice(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    """FR-SALE-21: a bill to check before paying; it creates no HOA_DON and no revenue."""
    from app.modules.catalog.models import Dish
    from app.modules.settings.service import get_config

    order = await session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order không tồn tại.")
    lines = list(
        (
            await session.execute(
                select(OrderLine).where(
                    OrderLine.order_id == order_id, OrderLine.status != "Đã hủy"
                )
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
    with contextlib.suppress(Exception):
        cfg = await get_config(session)
        restaurant_name = cfg.restaurant_name
        address = cfg.address
    total = sum((Decimal(str(line.unit_price)) * int(line.quantity) for line in lines), Decimal(0))
    return {
        "TieuDe": "PHIẾU TẠM TÍNH - CHƯA THANH TOÁN",
        "MaOrderHienThi": order.display_code,
        "TenNhaHang": restaurant_name,
        "DiaChi": address,
        "ThoiDiemXuat": business_date.now().isoformat(),
        "TongTien": float(total),
        "lines": [
            {
                "MaMon": line.dish_id,
                "TenMon": names.get(line.dish_id, ""),
                "SoLuong": line.quantity,
                "DonGia": float(line.unit_price),
                "ThanhTien": float(line.unit_price) * int(line.quantity),
            }
            for line in lines
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
