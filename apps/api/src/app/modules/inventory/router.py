"""Inventory router."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import Principal, require_roles
from app.modules.inventory import service as svc
from app.modules.inventory.schemas import CountIn, IssueCreate, ReceiptCreate
from app.shared.roles import Role

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post("/receipts", status_code=201)
async def create_receipt(
    payload: ReceiptCreate,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
):
    r = await svc.create_receipt(
        session,
        user.user_id,
        payload.supplier_id,
        payload.receipt_date,
        [ln.model_dump() for ln in payload.lines],
    )
    await session.commit()
    return {"MaPhieuNhap": r.id}


@router.delete("/receipts/{receipt_id}")
async def cancel_receipt(
    receipt_id: int,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
):
    await svc.cancel_receipt(session, user.user_id, receipt_id)
    await session.commit()
    return {"ok": True}


@router.get("/receipts")
async def list_receipts(
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
):
    items = await svc.list_receipts(session)
    return [{"MaPhieuNhap": x.id} for x in items]


@router.post("/issues", status_code=201)
async def create_issue(
    payload: IssueCreate,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
):
    iss = await svc.create_issue(
        session, user.user_id, payload.reason, [ln.model_dump() for ln in payload.lines]
    )
    await session.commit()
    return {"MaPhieuXuat": iss.id}


@router.post("/stocktakes", status_code=201)
async def create_stocktake(
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
):
    st = await svc.create_stocktake(session, user.user_id)
    await session.commit()
    return {"MaPhieuKiemKe": st.id}


@router.post("/stocktakes/{sid}/counts")
async def record_counts(
    sid: int,
    counts: list[CountIn],
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
):
    await svc.record_counts(
        session,
        sid,
        [(c.ingredient_id, __import__("decimal").Decimal(str(c.actual_qty))) for c in counts],
    )
    await session.commit()
    return {"ok": True}


@router.post("/stocktakes/{sid}/confirm")
async def confirm_stocktake(
    sid: int,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
):
    await svc.confirm_stocktake(session, user.user_id, sid)
    await session.commit()
    return {"ok": True}


@router.post("/costing/{month}/close")
async def close_month(
    month: int,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
):
    if month < 100101 or month > 999912 or month % 100 < 1 or month % 100 > 12:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="Tháng không hợp lệ (YYYYMM).")
    from app.modules.inventory.costing import close_month as _close

    items = await _close(session, month)
    await session.commit()
    return items
