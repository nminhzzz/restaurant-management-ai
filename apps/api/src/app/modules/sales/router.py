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

