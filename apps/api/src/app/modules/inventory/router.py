"""Inventory router."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import Principal, require_roles
from app.modules.inventory import service as svc
from app.modules.inventory.schemas import CountIn, IssueCreate, ReceiptCreate, ReceiptUpdate
from app.shared.audit import SystemAuditLog
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


@router.patch("/receipts/{receipt_id}")
async def update_receipt(
    receipt_id: int,
    payload: ReceiptUpdate,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
):
    await svc.update_receipt(
        session, user.user_id, receipt_id, [ln.model_dump() for ln in payload.lines]
    )
    await session.commit()
    return {"ok": True}


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
    page: int = 1,
    page_size: int = 20,
    supplier_id: int | None = None,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    items = await svc.list_receipts(
        session, page=page, page_size=page_size, supplier_id=supplier_id
    )
    return [
        {
            "MaPhieuNhap": x.id,
            "MaNhaCungCap": x.supplier_id,
            "NgayNhap": x.receipt_date.isoformat() if x.receipt_date else None,
            "TrangThai": x.status,
        }
        for x in items
    ]


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
    from app.modules.inventory.costing import backfill_issue_costs
    from app.modules.inventory.costing import close_month as _close

    items = await _close(session, month)
    # Without the backfill, write-offs keep a cost of 0 and the report stays
    # "tạm tính" forever (FR-REP-05b).
    priced = await backfill_issue_costs(session, month)
    session.add(
        SystemAuditLog(
            user_id=user.user_id,
            action="CLOSE_COSTING_MONTH",
            target_entity="GIA_BINH_QUAN_THANG",
            target_id=str(month),
            after={"SoNguyenLieu": len(items), "SoDongHaoHutDaTinhGia": priced},
        )
    )
    await session.commit()
    # Serialize via dict to keep precision; avoid leaking ORM directly
    return [
        {
            "MaNguyenLieu": r.ingredient_id,
            "Thang": r.month,
            "GiaBinhQuan": float(r.avg_cost),
            "TongSoLuongNhap": float(r.total_qty),
            "ThoiDiemTinh": r.computed_at.isoformat() if r.computed_at else None,
        }
        for r in items
    ]


@router.get("/stock")
async def list_stock(
    search: str | None = None,
    alerting: bool | None = None,
    page: int = 1,
    page_size: int = 50,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    items = await svc.list_stock(
        session, search=search, alerting=alerting, page=page, page_size=page_size
    )
    return {"items": items, "page": page, "page_size": page_size}


@router.get("/issues")
async def list_issues(
    page: int = 1,
    page_size: int = 20,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
):
    from sqlalchemy import select as sel

    from app.modules.inventory.models import StockIssue

    q = (
        sel(StockIssue)
        .order_by(StockIssue.id.desc())
        .offset((max(1, page) - 1) * min(max(1, page_size), 100))
        .limit(min(max(1, page_size), 100))
    )
    rows = (await session.execute(q)).scalars().all()
    return [{"MaPhieuXuat": r.id, "LyDo": r.reason, "TrangThai": r.status} for r in rows]


@router.get("/stocktakes")
async def list_stocktakes(
    page: int = 1,
    page_size: int = 20,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
):
    from sqlalchemy import select as sel

    from app.modules.inventory.models import Stocktake

    q = (
        sel(Stocktake)
        .order_by(Stocktake.id.desc())
        .offset((max(1, page) - 1) * min(max(1, page_size), 100))
        .limit(min(max(1, page_size), 100))
    )
    rows = (await session.execute(q)).scalars().all()
    return [{"MaPhieuKiemKe": r.id, "TrangThai": r.status} for r in rows]
