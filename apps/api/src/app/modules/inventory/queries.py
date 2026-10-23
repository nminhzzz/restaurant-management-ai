"""Read-only stock, lot and ledger projections (FR-INV-07/12)."""

from datetime import date, timedelta

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Ingredient
from app.modules.inventory.models import IngredientLot, StockMovement
from app.modules.sales.models import Reservation, ReservationDetail
from app.modules.settings.models import SystemConfig
from app.shared import business_date


def _held_by_lot(moment):
    return (
        select(
            ReservationDetail.lot_id.label("lot_id"),
            func.sum(ReservationDetail.quantity).label("held"),
        )
        .join(Reservation, Reservation.id == ReservationDetail.reservation_id)
        .where(Reservation.status == "Đang giữ", Reservation.expires_at > moment)
        .group_by(ReservationDetail.lot_id)
        .subquery()
    )


def _lot_projection(moment, today):
    held = _held_by_lot(moment)
    eligible = or_(IngredientLot.expiry_date.is_(None), IngredientLot.expiry_date >= today)
    remaining = func.coalesce(IngredientLot.quantity_remaining, 0)
    held_qty = case((eligible, func.coalesce(held.c.held, 0)), else_=0)
    available = case((eligible & (remaining > held_qty), remaining - held_qty), else_=0)
    return held, eligible, remaining, held_qty, available


async def list_stock(
    session: AsyncSession,
    search: str | None = None,
    alerting: bool | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[dict], int]:
    moment = business_date.now()
    today = business_date.business_date_of(moment)
    config = (await session.execute(select(SystemConfig).limit(1))).scalar_one_or_none()
    default = config.default_stock_threshold if config else 10
    warning = config.expiry_warning_days if config else 3
    held, eligible, remaining, held_qty, available = _lot_projection(moment, today)
    lots = (
        select(
            IngredientLot.ingredient_id.label("ingredient_id"),
            func.sum(case((eligible, remaining), else_=0)).label("eligible"),
            func.sum(held_qty).label("held"),
            func.sum(available).label("available"),
            func.min(IngredientLot.expiry_date).label("nearest_expiry"),
            func.sum(case((IngredientLot.expiry_date < today, 1), else_=0)).label("expired"),
            func.sum(
                case(
                    (IngredientLot.expiry_date.between(today, today + timedelta(days=warning)), 1),
                    else_=0,
                )
            ).label("expiring"),
        )
        .outerjoin(held, held.c.lot_id == IngredientLot.id)
        .where(IngredientLot.quantity_remaining > 0)
        .group_by(IngredientLot.ingredient_id)
        .subquery()
    )
    threshold = case((Ingredient.min_stock > 0, Ingredient.min_stock), else_=default)
    available_qty = func.coalesce(lots.c.available, 0)
    statement = (
        select(
            Ingredient,
            threshold,
            func.coalesce(lots.c.eligible, 0),
            func.coalesce(lots.c.held, 0),
            available_qty,
            lots.c.nearest_expiry,
            func.coalesce(lots.c.expired, 0),
            func.coalesce(lots.c.expiring, 0),
        )
        .outerjoin(lots, lots.c.ingredient_id == Ingredient.id)
        .where(Ingredient.is_deleted.is_(False))
    )
    if search:
        safe = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        statement = statement.where(Ingredient.name.ilike(f"%{safe}%", escape="\\"))
    if alerting is not None:
        statement = statement.where(
            available_qty < threshold if alerting else available_qty >= threshold
        )
    total = int(
        (await session.execute(select(func.count()).select_from(statement.subquery()))).scalar_one()
    )
    rows = (
        await session.execute(
            statement.order_by(Ingredient.id).offset((page - 1) * page_size).limit(page_size)
        )
    ).all()
    return [
        {
            "MaNguyenLieu": ing.id,
            "TenNguyenLieu": ing.name,
            "DonViTinh": ing.unit,
            "SoLuongTon": float(ing.stock_qty),
            "SoLuongDuDieuKien": float(eligible_qty),
            "SoLuongGiu": float(held_qty),
            "SoLuongKhaDung": float(available_qty),
            "MucTonToiThieuApDung": float(threshold),
            "CanhBaoTonThap": available_qty < threshold,
            "HanSuDungGanNhat": expiry.isoformat() if expiry else None,
            "SoLoHetHan": int(expired),
            "SoLoSapHetHan": int(expiring),
            "CanhBaoHanSuDung": bool(expired or expiring),
            "ThoiDiemTinh": moment.isoformat(),
        }
        for ing, threshold, eligible_qty, held_qty, available_qty, expiry, expired, expiring in rows
    ], total


async def list_lots(
    session: AsyncSession,
    ingredient_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    moment = business_date.now()
    today = business_date.business_date_of(moment)
    config = (await session.execute(select(SystemConfig).limit(1))).scalar_one_or_none()
    warning = config.expiry_warning_days if config else 3
    held, eligible, remaining, held_qty, available = _lot_projection(moment, today)
    state = case(
        (remaining <= 0, "Đã hết"),
        (~eligible, "Hết hạn"),
        (
            IngredientLot.expiry_date.is_not(None)
            & (IngredientLot.expiry_date <= today + timedelta(days=warning)),
            "Sắp hết hạn",
        ),
        else_="Còn hạn",
    )
    statement = select(IngredientLot, Ingredient.name, Ingredient.unit, held_qty, available, state)
    statement = statement.join(Ingredient, Ingredient.id == IngredientLot.ingredient_id)
    statement = statement.outerjoin(held, held.c.lot_id == IngredientLot.id)
    if ingredient_id is not None:
        statement = statement.where(IngredientLot.ingredient_id == ingredient_id)
    if status:
        statement = statement.where(state == status)
    total = int(
        (await session.execute(select(func.count()).select_from(statement.subquery()))).scalar_one()
    )
    rows = (
        await session.execute(
            statement.order_by(IngredientLot.received_at, IngredientLot.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return [
        {
            "MaLoNguyenLieu": lot.id,
            "MaNguyenLieu": lot.ingredient_id,
            "TenNguyenLieu": name,
            "DonViTinh": unit,
            "MaChiTietNhap": lot.receipt_line_id,
            "NgayNhap": lot.received_at.isoformat(),
            "HanSuDung": lot.expiry_date.isoformat() if lot.expiry_date else None,
            "SoLuongConLai": float(lot.quantity_remaining),
            "SoLuongGiu": float(held_qty),
            "SoLuongKhaDung": float(available_qty),
            "TrangThai": state,
            "LoDieuChinhKiemKe": lot.is_adjustment,
            "ThoiDiemTinh": moment.isoformat(),
        }
        for lot, name, unit, held_qty, available_qty, state in rows
    ], total


async def list_movements(
    session: AsyncSession,
    ingredient_id: int | None = None,
    lot_id: int | None = None,
    order_line_id: int | None = None,
    kind: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    statement = select(StockMovement, Ingredient.name, Ingredient.unit).join(
        Ingredient, Ingredient.id == StockMovement.ingredient_id
    )
    for value, column in [
        (ingredient_id, StockMovement.ingredient_id),
        (lot_id, StockMovement.lot_id),
        (order_line_id, StockMovement.order_line_id),
        (kind, StockMovement.kind),
    ]:
        if value is not None:
            statement = statement.where(column == value)
    if date_from:
        statement = statement.where(StockMovement.business_date >= date_from)
    if date_to:
        statement = statement.where(StockMovement.business_date <= date_to)
    total = int(
        (await session.execute(select(func.count()).select_from(statement.subquery()))).scalar_one()
    )
    rows = (
        await session.execute(
            statement.order_by(StockMovement.occurred_at.desc(), StockMovement.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return [
        {
            "MaGiaoDichKho": movement.id,
            "MaNguyenLieu": movement.ingredient_id,
            "TenNguyenLieu": name,
            "DonViTinh": unit,
            "MaLoNguyenLieu": movement.lot_id,
            "LoaiGiaoDich": movement.kind,
            "SoLuongThayDoi": float(movement.qty),
            "ThoiDiem": movement.occurred_at.isoformat(),
            "BusinessDate": movement.business_date.isoformat(),
            "MaChiTietNhap": movement.receipt_line_id,
            "MaChiTietOrder": movement.order_line_id,
            "MaChiTietXuat": movement.issue_line_id,
            "MaChiTietKiemKe": movement.stocktake_line_id,
            "NguoiThucHien": movement.performed_by,
        }
        for movement, name, unit in rows
    ], total
