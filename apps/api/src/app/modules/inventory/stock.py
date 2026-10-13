"""Core stock movement — FIFO + row locking (Phase 3 Task 1)."""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import case, or_, select
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
    lot_id: int | None = None  # the lot an inbound movement created or topped up


async def _bd_now(session: AsyncSession) -> date:
    moment = business_date.now()
    start = await effective_business_day_start(session, moment)
    return business_date.business_date_of(moment, start)


def today_local() -> date:
    """Calendar day in the restaurant's timezone; the reference for lot expiry."""
    return business_date.now().date()


def lot_status_expression(today: date, warning_days: int):
    """SQL expression of a lot's status by expiry and remaining quantity (FR-INV-14)."""
    warning_end = today + timedelta(days=warning_days)
    return case(
        (IngredientLot.quantity_remaining <= 0, LotStatus.DA_DUNG_HET.value),
        (IngredientLot.expiry_date.is_(None), LotStatus.CON_HAN.value),
        (IngredientLot.expiry_date < today, LotStatus.HET_HAN.value),
        (IngredientLot.expiry_date <= warning_end, LotStatus.SAP_HET_HAN.value),
        else_=LotStatus.CON_HAN.value,
    )


async def refresh_lot_statuses(session: AsyncSession, warning_days: int) -> list[int]:
    """Bring every lot's stored status in line with its expiry date and quantity.

    Idempotent, and cheap once converged: only lots whose status changed are touched.
    Returns the ingredients whose sellable stock may have changed, so the caller can
    refresh the dishes that depend on them.
    """
    target = lot_status_expression(today_local(), warning_days)
    stale = (
        (await session.execute(select(IngredientLot, target).where(IngredientLot.status != target)))
        .tuples()
        .all()
    )
    changed: set[int] = set()
    for lot, new_status in stale:
        previous = lot.status
        lot.status = new_status
        sellable = {LotStatus.CON_HAN.value, LotStatus.SAP_HET_HAN.value}
        if (previous in sellable) != (new_status in sellable):
            changed.add(lot.ingredient_id)
    if stale:
        await session.flush()
    if changed:
        from app.modules.inventory.service import recompute_automatic_out_of_stock

        await recompute_automatic_out_of_stock(session, sorted(changed))
    return sorted(changed)


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
                IngredientLot.expiry_date >= today_local(),
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


async def sellable_available(
    session: AsyncSession, ingredient_ids: list[int]
) -> dict[int, Decimal]:
    """FR-INV-10: stock on unexpired lots minus the holds still in force, per ingredient."""
    from app.modules.sales.models import ItemHold, ItemHoldLot

    if not ingredient_ids:
        return {}
    lots = (
        await session.execute(
            select(
                IngredientLot.id, IngredientLot.ingredient_id, IngredientLot.quantity_remaining
            ).where(
                IngredientLot.ingredient_id.in_(ingredient_ids),
                IngredientLot.quantity_remaining > 0,
                IngredientLot.status != LotStatus.HET_HAN.value,
                or_(
                    IngredientLot.expiry_date.is_(None),
                    IngredientLot.expiry_date >= today_local(),
                ),
            )
        )
    ).all()
    held: dict[int, Decimal] = {}
    if lots:
        rows = await session.execute(
            select(ItemHoldLot.lot_id, ItemHoldLot.quantity_held)
            .join(ItemHold, ItemHold.id == ItemHoldLot.hold_id)
            .where(
                ItemHoldLot.lot_id.in_([lot_id for lot_id, _, _ in lots]),
                ItemHold.status == "Đang giữ",
                ItemHold.expires_at > business_date.now(),
            )
        )
        for lot_id, quantity in rows:
            held[lot_id] = held.get(lot_id, Decimal(0)) + Decimal(str(quantity))
    available = {ingredient_id: Decimal(0) for ingredient_id in ingredient_ids}
    for lot_id, ingredient_id, remaining in lots:
        free = max(Decimal(0), Decimal(str(remaining)) - held.get(lot_id, Decimal(0)))
        available[ingredient_id] += free
    return available


async def held_by_ingredient(
    session: AsyncSession, ingredient_ids: list[int]
) -> dict[int, Decimal]:
    """Quantity currently reserved by unexpired holds on sellable lots, per ingredient."""
    from app.modules.sales.models import ItemHold, ItemHoldLot

    if not ingredient_ids:
        return {}
    rows = await session.execute(
        select(IngredientLot.ingredient_id, ItemHoldLot.quantity_held)
        .join(ItemHoldLot, ItemHoldLot.lot_id == IngredientLot.id)
        .join(ItemHold, ItemHold.id == ItemHoldLot.hold_id)
        .where(
            IngredientLot.ingredient_id.in_(ingredient_ids),
            IngredientLot.status != LotStatus.HET_HAN.value,
            ItemHold.status == "Đang giữ",
            ItemHold.expires_at > business_date.now(),
        )
    )
    held: dict[int, Decimal] = {}
    for ingredient_id, quantity in rows:
        held[ingredient_id] = held.get(ingredient_id, Decimal(0)) + Decimal(str(quantity))
    return held


async def dish_is_out_of_stock(session: AsyncSession, dish_id: int) -> bool:
    """FR-CAT-27: derived from the live availability, never read from a stored flag."""
    from app.modules.catalog.models import Recipe, RecipeItem
    from app.modules.catalog.versions import promote_due_versions
    from app.shared.enums import VersionStatus

    await promote_due_versions(session)
    recipe_id = (
        await session.execute(
            select(Recipe.id)
            .where(Recipe.dish_id == dish_id, Recipe.status == VersionStatus.HIEU_LUC.value)
            .order_by(Recipe.business_date.desc(), Recipe.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if recipe_id is None:
        return False
    items = (
        (await session.execute(select(RecipeItem).where(RecipeItem.recipe_id == recipe_id)))
        .scalars()
        .all()
    )
    available = await sellable_available(session, [item.ingredient_id for item in items])
    return any(available[item.ingredient_id] < Decimal(str(item.quantity)) for item in items)


async def apply_stock_movement(
    session: AsyncSession, change: StockChange, *, actor_id: int | None = None
) -> list[StockMovement]:
    config = await lock_stocktake_gate(session)
    await refresh_lot_statuses(session, config.expiry_warning_days)
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
        m = StockMovement(
            ingredient_id=change.ingredient_id,
            lot_id=change.lot_id,
            kind=kind_val,
            qty=delta,
            balance_after=ing.stock_qty,
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

    # update ingredient total; each ledger row records the running balance (TonSauGiaoDich)
    balance = Decimal(str(ing.stock_qty))
    for m in movements:
        balance += Decimal(str(m.qty))
        m.balance_after = balance
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
    """Undo a draw on the very lot it came from, even when that lot has since expired
    (BR-LOT-01). Only movements tied to an order line can be returned (report 3.2.2)."""
    if movement.order_line_id is None:
        raise BusinessRuleError("Chỉ hoàn kho được giao dịch trừ kho của dòng món.")
    config = await lock_stocktake_gate(session)
    ing = await lock_ingredient(session, movement.ingredient_id)
    if movement.lot_id is not None:
        lot = await session.get(IngredientLot, movement.lot_id)
        if lot is not None:
            lot.quantity_remaining = lot.quantity_remaining - movement.qty
            await session.flush()
    # movement.qty is negative for a draw, so -qty is positive
    ing.stock_qty = ing.stock_qty - movement.qty
    await session.flush()
    bd = await _bd_now(session)
    rev = StockMovement(
        ingredient_id=movement.ingredient_id,
        lot_id=movement.lot_id,
        kind=StockMovementType.HOAN_KHO,
        qty=-movement.qty,
        balance_after=ing.stock_qty,
        business_date=bd,
        order_line_id=movement.order_line_id,
        performed_by=actor_id,
    )
    session.add(rev)
    await session.flush()
    await refresh_lot_statuses(session, config.expiry_warning_days)
    return rev
