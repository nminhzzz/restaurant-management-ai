"""HTTP layer for the sales module.

Roles follow the report's tables 9 and 10: the kitchen role (WAREHOUSE) has no access to orders,
payments or invoices; cashiers take orders, payments and verification requests; the manager
alone cancels whole orders and decides what happens to unverified or exceptional money.
The two gateway webhooks are the only routes without a login; they authenticate by the
gateway's own means and are bounded in size and fields.

Service functions raise `AppError` subclasses (`NotFoundError`, `BusinessRuleError`,
`UnauthenticatedError`); `app.core.errors.register_error_handlers` maps them to 404 / 422 / 401.
"""

import json
import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.dependencies import Principal, require_roles
from app.core.errors import AppError, BusinessRuleError, NotFoundError, UnauthenticatedError
from app.modules.catalog.models import DiningTable, Dish
from app.modules.sales import exceptions, floor, holds, invoices, orders, payments, webhooks
from app.modules.sales.common import order_total
from app.modules.sales.gateways import sepay, simulator
from app.modules.sales.models import KitchenTicket, Order, OrderLine
from app.modules.sales.schemas import (
    AddLineIn,
    ApplyExceptionIn,
    CancelLineIn,
    CancelOrderIn,
    ConfirmReceivedIn,
    CreateSelectionIn,
    LineStatusIn,
    ManagerDecisionIn,
    MoveTableIn,
    PrintResultIn,
    RefundExceptionIn,
    SimulatorWebhookIn,
    SubmitOrderIn,
    SubmitSelectionIn,
    UpdateLineIn,
    UpsertSelectionLineIn,
    VerificationNoteIn,
    VerificationRequestIn,
)
from app.modules.sales.tickets import record_print_result
from app.shared.enums import PaymentExceptionStatus
from app.shared.roles import Role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sales", tags=["Module 2 — Sales"])

_STAFF = (Role.MANAGER, Role.CASHIER)
_MANAGER = (Role.MANAGER,)


class PayloadTooLargeError(AppError):
    status_code = 413
    code = "PAYLOAD_TOO_LARGE"


def _line_payload(line: OrderLine, dish_names: dict[int, str] | None = None) -> dict:
    payload = {
        "MaChiTietOrder": line.id,
        "MaMon": line.dish_id,
        "SoLuong": line.quantity,
        "DonGia": float(line.unit_price),
        "ThanhTien": float(line.unit_price) * int(line.quantity),
        "MaPhienBanGia": line.price_version_id,
        "MaCongThuc": line.recipe_id,
        "GhiChu": line.note,
        "TrangThai": line.status,
    }
    if dish_names is not None:
        payload["TenMon"] = dish_names.get(line.dish_id)
    return payload


def _order_payload(order: Order, lines: list[OrderLine]) -> dict:
    return {
        "MaOrder": order.id,
        "MaOrderHienThi": order.display_code,
        "MaBan": order.table_id,
        "LoaiDon": order.order_type,
        "TrangThai": order.status,
        "BusinessDate": order.business_date.isoformat(),
        "ThoiDiemTao": order.created_at.isoformat() if order.created_at else None,
        "ThoiDiemDong": order.updated_at.isoformat() if order.updated_at else None,
        "lines": [_line_payload(line) for line in lines],
    }


async def _read_json_limited(request: Request) -> dict[str, Any]:
    """Webhook bodies are small; refuse anything larger before it is parsed."""
    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit() and int(declared) > sepay.MAX_BODY_BYTES:
        raise PayloadTooLargeError("Nội dung yêu cầu quá lớn.")
    received = bytearray()
    async for chunk in request.stream():
        received.extend(chunk)
        if len(received) > sepay.MAX_BODY_BYTES:
            raise PayloadTooLargeError("Nội dung yêu cầu quá lớn.")
    try:
        body = json.loads(bytes(received) or b"null")
    except ValueError as exc:
        raise BusinessRuleError("Nội dung yêu cầu không hợp lệ.") from exc
    if not isinstance(body, dict):
        raise BusinessRuleError("Nội dung yêu cầu không hợp lệ.")
    return body


# --- floor and selections ----------------------------------------------------------------------


@router.get("/floor")
async def get_floor(
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    return await floor.floor_board(session)


@router.post("/selections", status_code=201)
async def create_selection(
    payload: CreateSelectionIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    selection_id = await orders.create_selection(
        session,
        user.user_id,
        payload.selection_id,
        table_id=payload.table_id,
        order_id=payload.order_id,
    )
    await session.commit()
    return {"MaLuotChon": selection_id}


@router.put("/selections/{selection_id}/lines/{dish_id}")
async def upsert_selection_line(
    selection_id: str,
    dish_id: int,
    payload: UpsertSelectionLineIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    hold = await holds.upsert_hold(
        session,
        user.user_id,
        selection_id,
        dish_id,
        payload.quantity,
        payload.note,
        payload.table_id,
        payload.order_id,
    )
    await session.commit()
    return {
        "MaGiuCho": hold.id,
        "MaLuotChon": hold.selection_id,
        "MaMon": hold.dish_id,
        "SoLuong": hold.quantity,
        "ThoiDiemHetHan": hold.expires_at.isoformat(),
        "TrangThai": hold.status,
    }


@router.delete("/holds/{hold_id}")
async def delete_selection_hold(
    hold_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    await holds.release_hold(session, user.user_id, hold_id)
    await session.commit()
    return {"MaGiuCho": hold_id, "TrangThai": "Đã hủy"}


@router.post("/selections/{selection_id}/submit")
async def submit_selection(
    selection_id: str,
    payload: SubmitSelectionIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    result = await orders.submit_selection(
        session, user.user_id, selection_id, payload.send_request_id
    )
    await session.commit()
    return {
        "MaOrder": result["order"].id if result["order"] is not None else None,
        "MaOrderHienThi": result["order"].display_code if result["order"] is not None else None,
        "CanXacNhanLai": result["CanXacNhanLai"],
        "stale": result["stale"],
        "lines": [_line_payload(line) for line in result["lines"]],
    }


# --- orders --------------------------------------------------------------------------------------


@router.post("/orders", status_code=201)
async def create_order(
    payload: SubmitOrderIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
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
    user: Principal = Depends(require_roles(*_STAFF)),
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
            "LoaiDon": order.order_type,
            "BusinessDate": order.business_date.isoformat(),
            "TrangThai": order.status,
            "TongTien": float(order.total or 0),
        }
        for order in rows
    ]
    return {"total": total, "items": items}


@router.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    await payments.expire_stale_qr(session)
    await session.commit()
    order = await session.get(Order, order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    lines = list(
        (
            await session.execute(
                select(OrderLine).where(OrderLine.order_id == order_id).order_by(OrderLine.id)
            )
        )
        .scalars()
        .all()
    )
    names = {
        dish_id: name
        for dish_id, name in await session.execute(
            select(Dish.id, Dish.name).where(Dish.id.in_({line.dish_id for line in lines}))
        )
    }
    table_name = None
    if order.table_id is not None:
        table_name = (
            await session.execute(select(DiningTable.name).where(DiningTable.id == order.table_id))
        ).scalar_one_or_none()
    body = _order_payload(order, lines)
    body["lines"] = [_line_payload(line, names) for line in lines]
    body["TenBan"] = table_name
    body["TongTien"] = float(await order_total(session, order))
    body["DaKhoa"] = order.status != "Đang mở"
    return body


@router.post("/orders/{order_id}/lines", status_code=201)
async def add_order_line(
    order_id: int,
    payload: AddLineIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    line = await orders.add_line(
        session, order_id, payload.dish_id, payload.quantity, payload.note, actor_id=user.user_id
    )
    await session.commit()
    return _line_payload(line)


@router.patch("/orders/{order_id}/lines/{line_id}")
async def patch_order_line(
    order_id: int,
    line_id: int,
    payload: UpdateLineIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    line = await orders.update_line(
        session, order_id, line_id, payload.quantity, actor_id=user.user_id
    )
    await session.commit()
    return {"MaChiTietOrder": line.id, "SoLuong": line.quantity}


@router.patch("/orders/{order_id}/lines/{line_id}/status")
async def patch_line_status(
    order_id: int,
    line_id: int,
    payload: LineStatusIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    line = await orders.advance_line_status(
        session, order_id, line_id, payload.to_status, actor_id=user.user_id
    )
    await session.commit()
    return {"MaChiTietOrder": line.id, "TrangThai": line.status}


@router.post("/orders/{order_id}/lines/{line_id}/cancel")
async def cancel_order_line(
    order_id: int,
    line_id: int,
    payload: CancelLineIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    await orders.cancel_line(session, order_id, line_id, payload.reason, actor_id=user.user_id)
    await session.commit()
    return {"ok": True}


@router.post("/orders/{order_id}/move")
async def move_order_table(
    order_id: int,
    payload: MoveTableIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    order = await orders.move_table(session, order_id, payload.to_table_id, actor_id=user.user_id)
    await session.commit()
    return {"MaOrder": order.id, "MaBan": order.table_id}


@router.post("/orders/{order_id}/cancel")
async def cancel_whole_order(
    order_id: int,
    payload: CancelOrderIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_MANAGER)),
):
    order = await orders.cancel_order(
        session, order_id, payload.reason, actor_id=user.user_id, guests_left=payload.guests_left
    )
    await session.commit()
    return {"MaOrder": order.id, "TrangThai": order.status}


# --- kitchen tickets -----------------------------------------------------------------------------


@router.get("/orders/{order_id}/tickets")
async def list_tickets(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    """FR-SALE-32: the kitchen tickets of an order, so the UI can reprint or flag a failed print."""
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


async def _ticket_of(session: AsyncSession, order_id: int, ticket_id: int) -> KitchenTicket:
    ticket = await session.get(KitchenTicket, ticket_id)
    if ticket is None or ticket.order_id != order_id:
        raise NotFoundError("Phiếu bếp không tồn tại.")
    return ticket


@router.post("/orders/{order_id}/tickets/{ticket_id}/reprint")
async def reprint_ticket(
    order_id: int,
    ticket_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    ticket = await _ticket_of(session, order_id, ticket_id)
    record_print_result(ticket, True)
    await session.commit()
    return {"MaPhieuBep": ticket.id, "SoLanIn": ticket.print_count}


@router.post("/orders/{order_id}/tickets/{ticket_id}/print-result")
async def report_ticket_print_result(
    order_id: int,
    ticket_id: int,
    payload: PrintResultIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    """FR-SALE-32: the UI reports a failed print so staff can be warned and retry."""
    ticket = await _ticket_of(session, order_id, ticket_id)
    record_print_result(ticket, payload.ok)
    await session.commit()
    return {"MaPhieuBep": ticket.id, "TrangThai": ticket.status, "SoLanIn": ticket.print_count}


# --- payments ------------------------------------------------------------------------------------


@router.get("/orders/{order_id}/payments")
async def list_payments(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    """Lets the UI recover the live, expired or waiting transaction after a reload."""
    await payments.expire_stale_qr(session)
    await session.commit()
    rows = await payments.list_order_payments(session, order_id)
    return {"items": [await payments.payment_payload(session, p) for p in rows]}


@router.get("/orders/{order_id}/provisional-bill")
async def get_provisional_bill(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    """FR-SALE-21: "PHIẾU TẠM TÍNH - CHƯA THANH TOÁN"; creates no invoice and locks nothing."""
    return await invoices.provisional_bill(session, order_id)


@router.post("/orders/{order_id}/pay/cash")
async def pay_order_cash(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    result = await payments.pay_cash(session, order_id, actor_id=user.user_id)
    await session.commit()
    invoice = result["invoice"]
    return {
        "invoice": {"SoHoaDon": invoice.invoice_number, "TongTien": float(invoice.total)},
        "MaHoaDon": invoice.id,
    }


@router.post("/orders/{order_id}/pay/qr", status_code=201)
async def start_order_qr(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    payment = await payments.start_qr(session, order_id, actor_id=user.user_id)
    await session.commit()
    return {
        "MaGiaoDich": payment.id,
        "TrangThai": payment.status,
        "SoTien": float(payment.amount),
        "ThoiDiemTaoQR": payment.qr_created_at.isoformat() if payment.qr_created_at else None,
        "ThoiDiemHetHan": payment.deadline.isoformat() if payment.deadline else None,
        **(await payments.qr_fields(session, payment)),
    }


@router.post("/payments/{payment_id}/check")
async def check_payment(
    payment_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    payment = await webhooks.check_payment(session, payment_id)
    await session.commit()
    return {"MaGiaoDich": payment.id, "TrangThai": payment.status}


@router.post("/payments/{payment_id}/cancel")
async def cancel_payment_qr(
    payment_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    """FR-SALE-33: drop a QR that is still valid; the order goes back to "Đang mở"."""
    payment = await payments.cancel_qr(session, payment_id, actor_id=user.user_id)
    await session.commit()
    return {"MaGiaoDich": payment.id, "TrangThai": payment.status}


@router.post("/payments/{payment_id}/verification")
async def request_payment_verification(
    payment_id: int,
    payload: VerificationRequestIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    """FR-SALE-19: "Yêu cầu xác minh" — payment and order become "Chờ xác minh thanh toán"."""
    payment = await payments.request_verification(
        session,
        payment_id,
        reference=payload.bank_reference,
        evidence=payload.evidence,
        note=payload.note,
        actor_id=user.user_id,
    )
    await session.commit()
    return {"MaGiaoDich": payment.id, "MaOrder": payment.order_id, "TrangThai": payment.status}


@router.post("/payments/{payment_id}/verification-notes")
async def add_payment_verification_note(
    payment_id: int,
    payload: VerificationNoteIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    """FR-SALE-20/34: save a check result or extra evidence; the order keeps waiting."""
    payment = await payments.add_verification_note(
        session,
        payment_id,
        note=payload.note,
        reference=payload.bank_reference,
        evidence=payload.evidence,
        actor_id=user.user_id,
    )
    await session.commit()
    return {"MaGiaoDich": payment.id, "TrangThai": payment.status}


@router.post("/payments/{payment_id}/confirm-received")
async def confirm_payment_received(
    payment_id: int,
    payload: ConfirmReceivedIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_MANAGER)),
):
    """FR-SALE-20: "Xác nhận đã nhận tiền" — one invoice, order "Đã thanh toán"."""
    result = await payments.confirm_received(
        session,
        payment_id,
        note=payload.note,
        reference=payload.bank_reference,
        actor_id=user.user_id,
    )
    await session.commit()
    return {
        "MaGiaoDich": result["payment"].id,
        "TrangThai": result["payment"].status,
        "SoHoaDon": result["invoice"].invoice_number,
    }


@router.post("/payments/{payment_id}/reopen")
async def reopen_payment(
    payment_id: int,
    payload: ManagerDecisionIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_MANAGER)),
):
    """FR-SALE-23: "Mở lại thanh toán" — the order returns to "Đang mở"."""
    payment = await payments.reopen_payment(
        session, payment_id, reason=payload.reason, outcome=payload.outcome, actor_id=user.user_id
    )
    await session.commit()
    return {"MaGiaoDich": payment.id, "MaOrder": payment.order_id, "TrangThai": payment.status}


@router.post("/payments/{payment_id}/close-unpaid")
async def close_order_unpaid(
    payment_id: int,
    payload: ManagerDecisionIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_MANAGER)),
):
    """FR-SALE-35: "Đóng order chưa thu được tiền"."""
    payment = await payments.close_unpaid(
        session, payment_id, reason=payload.reason, outcome=payload.outcome, actor_id=user.user_id
    )
    await session.commit()
    return {"MaGiaoDich": payment.id, "MaOrder": payment.order_id, "TrangThai": payment.status}


# --- payment exceptions (FR-SALE-16/17, FR-REP-02) ---------------------------------------------


@router.get("/payment-exceptions")
async def list_payment_exceptions(
    status: str | None = Query(None, max_length=30),
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_MANAGER)),
):
    """Money that reached the bank but was not applied automatically, newest first."""
    if status is not None and status not in {s.value for s in PaymentExceptionStatus}:
        raise BusinessRuleError("Trạng thái ngoại lệ không hợp lệ.")
    return {"items": await exceptions.list_exceptions(session, status)}


@router.post("/payment-exceptions/{payment_id}/apply")
async def apply_payment_exception(
    payment_id: int,
    payload: ApplyExceptionIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_MANAGER)),
):
    entry = await exceptions.apply_exception(
        session, payment_id, note=payload.note, actor_id=user.user_id
    )
    await session.commit()
    return {
        "MaGiaoDich": entry.id,
        "MaOrder": entry.order_id,
        "TrangThaiNgoaiLe": entry.exception_status,
    }


@router.post("/payment-exceptions/{payment_id}/refund")
async def refund_payment_exception(
    payment_id: int,
    payload: RefundExceptionIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_MANAGER)),
):
    entry = await exceptions.refund_exception(
        session,
        payment_id,
        refund_reference=payload.refund_reference,
        note=payload.note,
        actor_id=user.user_id,
    )
    await session.commit()
    return {
        "MaGiaoDich": entry.id,
        "MaOrder": entry.order_id,
        "TrangThaiNgoaiLe": entry.exception_status,
        "MaThamChieuHoan": entry.refund_reference,
    }


# --- invoices ------------------------------------------------------------------------------------


@router.get("/orders/{order_id}/invoice")
async def get_invoice(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    return await invoices.get_invoice_payload(session, order_id)


@router.post("/orders/{order_id}/invoice/reprint")
async def reprint_invoice_ep(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(*_STAFF)),
):
    """FR-SALE-26: the invoice exactly as issued; only the print counter changes."""
    payload = await invoices.reprint_invoice(session, order_id, actor_id=user.user_id)
    await session.commit()
    return payload


# --- gateway webhooks (the only routes without a login) --------------------------------------------


@router.post("/webhooks/payment")
async def webhook_payment(
    payload: SimulatorWebhookIn, session: AsyncSession = Depends(get_session)
):
    """Mock gateway for local development and automated tests; absent everywhere else."""
    if not simulator.enabled():
        raise NotFoundError("Không tìm thấy.")
    try:
        outcome = await webhooks.handle_simulator_webhook(
            session,
            payment_id=payload.payment_id,
            amount=payload.amount,
            signature=payload.signature,
        )
        await session.commit()
    except IntegrityError:
        # A concurrent delivery of the same transaction id won the unique key (NFR-08).
        await session.rollback()
        outcome = "duplicate"
    return {"ok": True, "MaGiaoDich": payload.payment_id, "KetQua": outcome}


@router.post("/webhooks/sepay")
async def webhook_sepay(request: Request, session: AsyncSession = Depends(get_session)):
    settings = get_settings()
    if settings.payment_gateway != "sepay":
        raise NotFoundError("Không tìm thấy.")
    if not sepay.api_key_matches(
        request.headers.get("Authorization"), settings.sepay_webhook_api_key
    ):
        # Technical log only: an unauthenticated caller must not be able to write business rows.
        logger.warning("Rejected a SePay webhook with a bad API key")
        raise UnauthenticatedError("API key không hợp lệ.")
    body = await _read_json_limited(request)
    try:
        await webhooks.handle_sepay_transfer(session, body)
        await session.commit()
    except IntegrityError:
        # A concurrent delivery of the same transaction id won the unique key (NFR-08).
        await session.rollback()
        logger.warning("Duplicate SePay delivery resolved by the unique transaction id")
    return {"success": True}
