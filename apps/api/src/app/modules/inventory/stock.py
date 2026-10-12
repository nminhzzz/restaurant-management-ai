"""Core stock movement — FIFO + row locking (Phase 3 Task 1)."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError
from app.modules.catalog.models import Ingredient
from app.modules.inventory.models import IngredientLot, StockMovement
from app.modules.settings.models import SystemConfig
from app.modules.settings.service import effective_business_day_start
from app.shared import business_date
from app.shared.enums import LotStatus, StockMovementType, StocktakeStatus


@dataclass
class StockChange:
    ingredient_id: int
    delta: Decimal  # >0 = Nhập, <0 = Trừ tự động
    kind: str = StockMovementType.TRU_TU_DONG
    allow_expired: bool = False
    business_date: date | None = None
    source_order_line_id: int | None = None
    source_receipt_line_id: int | None = None
    source_issue_line_id: int | None = None
    source_stocktake_line_id: int | None = None


async def _bd_now(session: AsyncSession) -> date:
    moment = business_date.now()
    start = await effective_business_day_start(session, moment)
    return business_date.business_date_of(moment, start)


async def lock_ingredient(session: AsyncSession, ingredient_id: int) -> Ingredient:
    try:
        bind = session.get_bind()
        dialect = bind.dialect.name if bind is not None else "sqlite"
    except Exception:
        dialect = "sqlite"
    q = select(Ingredient).where(Ingredient.id == ingredient_id)
    if dialect == "mysql":
        q = q.with_for_update().execution_options(populate_existing=True)
    r = await session.execute(q)
    ing = r.scalar_one_or_none()
    if ing is None:
        raise BusinessRuleError("Nguyên liệu không tồn tại.")
    return ing


async def lock_ingredients(session: AsyncSession, ingredient_ids: list[int]) -> None:
    for ingredient_id in sorted(set(ingredient_ids)):
        await lock_ingredient(session, ingredient_id)


async def lock_stocktake_gate(session: AsyncSession, *, allow_active: bool = False) -> SystemConfig:
    """Serialize all stock decisions against the singleton config row."""
    from app.modules.inventory.models import Stocktake

    query = (
        select(SystemConfig)
        .order_by(SystemConfig.id)
        .limit(1)
        .execution_options(populate_existing=True)
    )
    if session.get_bind().dialect.name == "mysql":
        query = query.with_for_update()
    config = (await session.execute(query)).scalar_one_or_none()
    if config is None:
        raise BusinessRuleError("Chưa có cấu hình hệ thống.")
    if not allow_active:
        active_query = (
            select(Stocktake.id)
            .where(Stocktake.status == StocktakeStatus.DANG_KIEM_KE.value)
            .limit(1)
        )
        if session.get_bind().dialect.name == "mysql":
            active_query = active_query.with_for_update()
        active = (await session.execute(active_query)).scalar_one_or_none()
        if active is not None:
            raise BusinessRuleError("Đang kiểm kê, không thể thay đổi tồn kho.")
    return config


async def lots_for_fifo(
    session: AsyncSession, ingredient_id: int, *, allow_expired: bool = False
) -> list[IngredientLot]:
    conds = [
        IngredientLot.ingredient_id == ingredient_id,
        IngredientLot.quantity_remaining > 0,
    ]
    if not allow_expired:
        conds.append(IngredientLot.status != LotStatus.HET_HAN.value)
        conds.append(
            or_(
                IngredientLot.expiry_date.is_(None),
                IngredientLot.expiry_date >= business_date.now().date(),
            )
        )
    q = (
        select(IngredientLot)
        .where(*conds)
        .order_by(IngredientLot.received_at.asc(), IngredientLot.id.asc())
    )
    if session.get_bind().dialect.name == "mysql":
        q = q.with_for_update().execution_options(populate_existing=True)
    r = await session.execute(q)
    return list(r.scalars().all())


async def active_held_quantity(session: AsyncSession, lot_id: int) -> Decimal:
    from app.modules.sales.models import ItemHold, ItemHoldLot

    query = (
        select(ItemHoldLot.quantity_held)
        .join(ItemHold, ItemHold.id == ItemHoldLot.hold_id)
        .where(
            ItemHoldLot.lot_id == lot_id,
            ItemHold.status == "Đang giữ",
            ItemHold.expires_at > business_date.now(),
        )
    )
    if session.get_bind().dialect.name == "mysql":
        query = query.with_for_update()
    held = await session.execute(query)
    return sum((Decimal(str(value)) for value in held.scalars()), Decimal(0))


async def apply_stock_movement(
    session: AsyncSession, change: StockChange, *, actor_id: int | None = None
) -> list[StockMovement]:
    await lock_stocktake_gate(session)
    ing = await lock_ingredient(session, change.ingredient_id)
    bd = change.business_date if change.business_date is not None else await _bd_now(session)
    delta = Decimal(str(change.delta))

    movements: list[StockMovement] = []

    if delta > 0:
        # Inbound must be tied to a receipt (Nhap) or stocktake adjustment
        # Validate source matches kind to satisfy CHECK movement_source_matches_kind
        if (
            change.kind == StockMovementType.NHAP or change.kind == "Nhập"
        ) and change.source_receipt_line_id is None:
            raise BusinessRuleError("Thiếu MaChiTietNhap cho giao dịch Nhập.")
        if (
            change.kind == StockMovementType.DIEU_CHINH_KIEM_KE
            or change.kind == "Điều chỉnh kiểm kê"
        ) and change.source_stocktake_line_id is None:
            raise BusinessRuleError("Thiếu MaChiTietKiemKe cho điều chỉnh kiểm kê.")
        ing.stock_qty = ing.stock_qty + delta
        kind_val = (
            change.kind if change.kind != StockMovementType.TRU_TU_DONG else StockMovementType.NHAP
        )
        # lot_id stays None for inbound; lot is tracked separately via IngredientLot
        m = StockMovement(
            ingredient_id=change.ingredient_id,
            lot_id=None,
            kind=kind_val,
            qty=delta,
            business_date=bd,
            receipt_line_id=change.source_receipt_line_id,
            order_line_id=change.source_order_line_id,
            issue_line_id=change.source_issue_line_id,
            stocktake_line_id=change.source_stocktake_line_id,
            performed_by=actor_id,
        )
        session.add(m)
        await session.flush()
        movements.append(m)
        try:
            from app.modules.inventory.service import recompute_automatic_out_of_stock

            await recompute_automatic_out_of_stock(session, [change.ingredient_id])
        except Exception:
            pass
        return movements

    # delta < 0: FIFO draw
    need = -delta
    lots = await lots_for_fifo(session, change.ingredient_id, allow_expired=change.allow_expired)
    availability = {
        lot.id: max(
            Decimal(0),
            Decimal(str(lot.quantity_remaining)) - await active_held_quantity(session, lot.id),
        )
        for lot in lots
    }
    total_avail = sum(availability.values(), Decimal(0))
    if total_avail < need:
        raise BusinessRuleError("Không đủ tồn kho.")

    remaining = need
    for lot in lots:
        if remaining <= 0:
            break
        avail = availability[lot.id]
        take = min(avail, remaining)
        if take <= 0:
            continue
        lot.quantity_remaining = Decimal(str(lot.quantity_remaining)) - take
        # keep status as is (simplified)
        m = StockMovement(
            ingredient_id=change.ingredient_id,
            lot_id=lot.id,
            kind=change.kind,
            qty=-take,
            business_date=bd,
            receipt_line_id=change.source_receipt_line_id,
            order_line_id=change.source_order_line_id,
            issue_line_id=change.source_issue_line_id,
            stocktake_line_id=change.source_stocktake_line_id,
            performed_by=actor_id,
        )
        session.add(m)
        movements.append(m)
        remaining -= take

    # update ingredient total
    ing.stock_qty = ing.stock_qty - need
    await session.flush()
    # Task 6: auto-hide dishes whose recipe can no longer be fulfilled
    try:
        from app.modules.inventory.service import (
            recompute_automatic_out_of_stock,
        )  # lazy to avoid cycle

        await recompute_automatic_out_of_stock(session, [change.ingredient_id])
    except Exception:
        pass
    return movements


async def reverse_movement(
    session: AsyncSession, movement: StockMovement, *, actor_id: int | None = None
) -> StockMovement:
    await lock_stocktake_gate(session)
    ing = await lock_ingredient(session, movement.ingredient_id)
    # return qty to original lot, ignore expiry
    if movement.lot_id is not None:
        lot = await session.get(IngredientLot, movement.lot_id)
        if lot is not None:
            lot.quantity_remaining = lot.quantity_remaining - movement.qty
            await session.flush()
    # movement.qty is negative for draw, so -qty is positive
    ing.stock_qty = ing.stock_qty - movement.qty
    await session.flush()
    bd = await _bd_now(session)
    rev = StockMovement(
        ingredient_id=movement.ingredient_id,
        lot_id=movement.lot_id,
        kind=StockMovementType.HOAN_KHO,
        qty=-movement.qty,
        business_date=bd,
        receipt_line_id=movement.receipt_line_id,
        order_line_id=movement.order_line_id,
        issue_line_id=movement.issue_line_id,
        stocktake_line_id=movement.stocktake_line_id,
        performed_by=actor_id,
    )
    # Fallback lineage for Hoan kho (CHECK now allows order/receipt/stocktake)
    if (
        rev.order_line_id is None
        and rev.receipt_line_id is None
        and rev.stocktake_line_id is None
        and rev.issue_line_id is None
    ):
        rev.receipt_line_id = movement.receipt_line_id
        if rev.receipt_line_id is None and rev.lot_id is not None:
            try:
                _lot = await session.get(IngredientLot, rev.lot_id)
                if _lot is not None:
                    rev.receipt_line_id = _lot.receipt_line_id
            except Exception:
                pass
    session.add(rev)
    await session.flush()
    return rev
