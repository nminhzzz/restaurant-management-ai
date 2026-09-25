"""HTTP layer for the sales module — Task 1."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import Principal, require_roles
from app.modules.sales.schemas import SubmitOrderIn
from app.shared.roles import Role

router = APIRouter(prefix="/sales", tags=["Module 2 \u2014 Sales"])


@router.post("/orders", status_code=201)
async def create_order(
    payload: SubmitOrderIn,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    from app.modules.sales.orders import submit_order

    try:
        result = await submit_order(
            session,
            {
                "table_id": payload.table_id,
                "order_type": payload.order_type,
                "lines": [l.model_dump() for l in payload.lines],
            },
            actor_id=user.user_id,
        )
    except Exception as e:
        from app.core.errors import BusinessRuleError

        if isinstance(e, BusinessRuleError):
            raise HTTPException(status_code=422, detail=str(e))
        raise
    await session.commit()
    order = result["order"]
    lines = result["lines"]
    return {
        "MaOrder": order.id,
        "MaOrderHienThi": order.display_code,
        "MaBan": order.table_id,
        "TrangThai": order.status,
        "lines": [
            {
                "MaChiTietOrder": l.id,
                "MaMon": l.dish_id,
                "SoLuong": l.quantity,
                "DonGia": float(l.unit_price),
                "MaPhienBanGia": l.price_version_id,
                "MaCongThuc": l.recipe_id,
                "GhiChu": l.note,
                "TrangThai": l.status,
            }
            for l in lines
        ],
        "rejected": result["rejected"],
    }


@router.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER, Role.WAREHOUSE)),
):
    from app.modules.sales.models import Order, OrderLine

    order = await session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order kh\u00f4ng t\u1ed3n t\u1ea1i.")
    from sqlalchemy import select

    r = await session.execute(select(OrderLine).where(OrderLine.order_id == order_id))
    lines = list(r.scalars().all())
    return {
        "MaOrder": order.id,
        "MaOrderHienThi": order.display_code,
        "MaBan": order.table_id,
        "TrangThai": order.status,
        "lines": [
            {
                "MaChiTietOrder": l.id,
                "MaMon": l.dish_id,
                "SoLuong": l.quantity,
                "DonGia": float(l.unit_price),
                "MaPhienBanGia": l.price_version_id,
                "MaCongThuc": l.recipe_id,
                "GhiChu": l.note,
                "TrangThai": l.status,
            }
            for l in lines
        ],
    }


@router.post("/orders/{order_id}/lines", status_code=201)
async def add_order_line(
    order_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    from app.modules.sales.orders import add_line

    try:
        _did_raw = (
            payload.get("dish_id") if payload.get("dish_id") is not None else payload.get("MaMon")
        )
        if _did_raw is None:
            raise HTTPException(status_code=422, detail="Thieu MaMon")
        _qty = payload.get("quantity") or payload.get("SoLuong") or 1
        _note = payload.get("note") or payload.get("GhiChu")
        line = await add_line(
            session, order_id, int(_did_raw), int(_qty), _note, actor_id=user.user_id
        )
    except Exception as e:
        from app.core.errors import BusinessRuleError, NotFoundError

        if isinstance(e, NotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        if isinstance(e, BusinessRuleError):
            raise HTTPException(status_code=422, detail=str(e))
        raise
    await session.commit()
    return {"MaChiTietOrder": line.id, "MaMon": line.dish_id, "SoLuong": line.quantity}


@router.patch("/orders/{order_id}/lines/{line_id}")
async def patch_order_line(
    order_id: int,
    line_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    from app.modules.sales.orders import update_line

    qty = payload.get("quantity") or payload.get("SoLuong")
    if qty is None:
        raise HTTPException(status_code=422, detail="Thi\u1ebfu SoLuong")
    try:
        line = await update_line(session, order_id, line_id, int(qty), actor_id=user.user_id)
    except Exception as e:
        from app.core.errors import BusinessRuleError, NotFoundError

        if isinstance(e, NotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        if isinstance(e, BusinessRuleError):
            raise HTTPException(status_code=422, detail=str(e))
        raise
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
    to = payload.get("to") or payload.get("TrangThai")
    if not to:
        raise HTTPException(status_code=422, detail="Thieu TrangThai")
    from app.modules.sales.orders import advance_line_status

    try:
        line = await advance_line_status(session, line_id, str(to))
    except Exception as e:
        from app.core.errors import BusinessRuleError, NotFoundError

        if isinstance(e, NotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        if isinstance(e, BusinessRuleError):
            raise HTTPException(status_code=422, detail=str(e))
        raise
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
    from app.modules.sales.orders import cancel_line

    try:
        line = await cancel_line(session, line_id, str(reason), actor_id=user.user_id)
    except Exception as e:
        from app.core.errors import BusinessRuleError, NotFoundError

        if isinstance(e, NotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        if isinstance(e, BusinessRuleError):
            raise HTTPException(status_code=422, detail=str(e))
        raise
    await session.commit()
    return {"ok": True}


@router.post("/orders/{order_id}/move")
async def move_order_table(
    order_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    to_id = payload.get("to_table_id") or payload.get("MaBanDich") or payload.get("to")
    if to_id is None:
        raise HTTPException(status_code=422, detail="Thieu MaBanDich")
    from app.modules.sales.orders import move_table

    try:
        order = await move_table(session, order_id, int(to_id), actor_id=user.user_id)
    except Exception as e:
        from app.core.errors import BusinessRuleError, NotFoundError

        if isinstance(e, NotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        if isinstance(e, BusinessRuleError):
            raise HTTPException(status_code=422, detail=str(e))
        raise
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
    from app.modules.sales.orders import cancel_order

    try:
        order = await cancel_order(session, order_id, str(reason), actor_id=user.user_id)
    except Exception as e:
        from app.core.errors import BusinessRuleError, NotFoundError

        if isinstance(e, NotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        if isinstance(e, BusinessRuleError):
            raise HTTPException(status_code=422, detail=str(e))
        raise
    await session.commit()
    return {"MaOrder": order.id, "TrangThai": order.status}


@router.post("/orders/{order_id}/tickets/{ticket_id}/reprint")
async def reprint_ticket(
    order_id: int,
    ticket_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    from app.modules.sales.models import KitchenTicket

    t = await session.get(KitchenTicket, ticket_id)
    if t is None or t.order_id != order_id:
        raise HTTPException(status_code=404, detail="Phiếu bếp không tồn tại.")
    # unlimited reprint
    from app.modules.sales.tickets import record_print_result

    record_print_result(t, True)
    await session.commit()
    return {"MaPhieuBep": t.id, "SoLanIn": t.print_count}


@router.post("/orders/{order_id}/pay/cash")
async def pay_order_cash(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    from app.modules.sales.payments import pay_cash

    try:
        res = await pay_cash(session, order_id, actor_id=user.user_id)
    except Exception as e:
        from app.core.errors import BusinessRuleError, NotFoundError

        if isinstance(e, NotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        if isinstance(e, BusinessRuleError):
            raise HTTPException(status_code=422, detail=str(e))
        raise
    await session.commit()
    inv = res["invoice"]
    return {"invoice": {"SoHoaDon": str(inv.id), "TongTien": float(inv.total)}, "MaHoaDon": inv.id}


@router.post("/orders/{order_id}/pay/qr", status_code=201)
async def start_order_qr(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    from app.modules.sales.payments import start_qr

    try:
        pay = await start_qr(session, order_id, actor_id=user.user_id)
    except Exception as e:
        from app.core.errors import BusinessRuleError, NotFoundError

        if isinstance(e, NotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        if isinstance(e, BusinessRuleError):
            raise HTTPException(status_code=422, detail=str(e))
        raise
    await session.commit()
    dl = getattr(pay, "_deadline", None)
    return {
        "MaGiaoDich": pay.id,
        "TrangThai": pay.status,
        "ThoiDiemTaoQR": pay.created_at.isoformat() if pay.created_at else None,
        "ThoiDiemHetHan": dl.isoformat() if dl else None,
    }


@router.post("/webhooks/payment")
async def webhook_payment(
    payload: dict,
    session: AsyncSession = Depends(get_session),
):
    from app.modules.sales.payments import handle_webhook

    try:
        res = await handle_webhook(session, payload)
    except Exception as e:
        from app.core.errors import BusinessRuleError, NotFoundError

        if isinstance(e, NotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        if isinstance(e, BusinessRuleError):
            # signature invalid -> 401
            if "Chữ ký" in str(e):
                raise HTTPException(status_code=401, detail=str(e))
            raise HTTPException(status_code=422, detail=str(e))
        raise
    await session.commit()
    return {"ok": True, "MaGiaoDich": res["payment"].id}


@router.post("/payments/{payment_id}/cancel")
async def cancel_payment_qr(
    payment_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    from app.modules.sales.payments import cancel_qr

    try:
        pay = await cancel_qr(session, payment_id, actor_id=user.user_id)
    except Exception as e:
        from app.core.errors import BusinessRuleError, NotFoundError

        if isinstance(e, NotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        if isinstance(e, BusinessRuleError):
            raise HTTPException(status_code=422, detail=str(e))
        raise
    await session.commit()
    return {"MaGiaoDich": pay.id, "TrangThai": pay.status}


@router.post("/orders/{order_id}/reconcile")
async def flag_reconcile(
    order_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    pid = payload.get("payment_id") or payload.get("MaGiaoDich")
    if pid is None:
        raise HTTPException(status_code=422, detail="Thieu MaGiaoDich")
    from app.modules.sales.payments import mark_for_reconciliation

    try:
        pay = await mark_for_reconciliation(session, int(pid), actor_id=user.user_id)
    except Exception as e:
        from app.core.errors import BusinessRuleError, NotFoundError

        if isinstance(e, NotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        if isinstance(e, BusinessRuleError):
            raise HTTPException(status_code=422, detail=str(e))
        raise
    await session.commit()
    return {"MaGiaoDich": pay.id, "TrangThai": pay.status}


@router.post("/payments/{payment_id}/reference")
async def bank_reference(
    payment_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    ref = payload.get("reference") or payload.get("MaGiaoDichNganHang") or ""
    ev = payload.get("evidence") or payload.get("AnhChungTu")
    from app.modules.sales.payments import record_bank_reference

    try:
        pay = await record_bank_reference(
            session, int(payment_id), str(ref), ev, actor_id=user.user_id
        )
    except Exception as e:
        from app.core.errors import NotFoundError

        if isinstance(e, NotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        raise
    await session.commit()
    return {"MaGiaoDich": pay.id}


@router.post("/payments/{payment_id}/resolve")
async def resolve_payment(
    payment_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER)),
):
    outcome = payload.get("outcome") or payload.get("ketQua") or ""
    from app.modules.sales.payments import resolve_reconciliation

    try:
        pay = await resolve_reconciliation(
            session, int(payment_id), str(outcome), actor_id=user.user_id
        )
    except Exception as e:
        from app.core.errors import BusinessRuleError, NotFoundError

        if isinstance(e, NotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        if isinstance(e, BusinessRuleError):
            raise HTTPException(status_code=422, detail=str(e))
        raise
    await session.commit()
    return {"MaGiaoDich": pay.id, "TrangThai": pay.status}


@router.get("/orders")
async def search_orders(
    code: str | None = None,
    table_id: int | None = None,
    business_date: str | None = None,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER, Role.WAREHOUSE)),
):
    from sqlalchemy import select as _sel

    from app.modules.sales.models import Order

    q = _sel(Order)
    if code:
        q = q.where(Order.display_code == code)
    if table_id is not None:
        q = q.where(Order.table_id == table_id)
    if business_date:
        from datetime import date as _date

        try:
            bd = _date.fromisoformat(business_date)
            q = q.where(Order.business_date == bd)
        except Exception:
            pass
    r = await session.execute(q)
    rows = list(r.scalars().all())
    items = [
        {
            "MaOrder": o.id,
            "MaOrderHienThi": o.display_code,
            "MaBan": o.table_id,
            "BusinessDate": o.business_date.isoformat(),
            "TrangThai": o.status,
        }
        for o in rows
    ]
    return {"total": len(items), "items": items}


@router.get("/orders/{order_id}/invoice")
async def get_invoice(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    from sqlalchemy import select as _sel

    from app.modules.sales.models import Invoice

    r = await session.execute(_sel(Invoice).where(Invoice.order_id == order_id))
    inv = r.scalar_one_or_none()
    if inv is None:
        raise HTTPException(status_code=404, detail="Hoa don khong ton tai")
    return {"SoHoaDon": str(inv.id), "TongTien": float(inv.total), "SoLanIn": inv.print_count}


@router.post("/orders/{order_id}/invoice/reprint")
async def reprint_invoice_ep(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    from app.modules.sales.payments import reprint_invoice

    try:
        inv = await reprint_invoice(session, order_id)
    except Exception as e:
        from app.core.errors import NotFoundError

        if isinstance(e, NotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        raise
    await session.commit()
    return {"SoHoaDon": str(inv.id), "TongTien": float(inv.total), "SoLanIn": inv.print_count}
