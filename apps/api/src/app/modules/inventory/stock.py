"""Core stock movement — FIFO + row locking (Phase 3 Task 1)."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError
from app.modules.catalog.models import Ingredient
from app.modules.inventory.models import IngredientLot, StockMovement
from app.shared import business_date


@dataclass
class StockChange:
    ingredient_id: int
    delta: Decimal  # >0 = Nhập, <0 = Trừ tự động
    kind: str = "Trừ tự động"
    business_date: date | None = None
    source_order_line_id: int | None = None
    source_receipt_line_id: int | None = None
    source_issue_line_id: int | None = None
    source_stocktake_line_id: int | None = None


def _bd_now() -> date:
    return business_date.business_date_of(business_date.now())


async def lock_ingredient(session: AsyncSession, ingredient_id: int) -> Ingredient:
    # FOR UPDATE on MySQL, no-op on SQLite
    dialect = session.bind.dialect.name if session.bind else "sqlite"
    q = select(Ingredient).where(Ingredient.id == ingredient_id)
    if dialect == "mysql":
        q = q.with_for_update()
    r = await session.execute(q)
    ing = r.scalar_one_or_none()
    if ing is None:
        raise BusinessRuleError("Nguyên liệu không tồn tại.")
    return ing


async def lots_for_fifo(session: AsyncSession, ingredient_id: int) -> list[IngredientLot]:
    r = await session.execute(
        select(IngredientLot)
        .where(
            IngredientLot.ingredient_id == ingredient_id,
            IngredientLot.quantity_remaining > 0,
            IngredientLot.status != "Hết hạn",
        )
        .order_by(IngredientLot.received_at.asc(), IngredientLot.id.asc())
    )
    return list(r.scalars().all())


async def apply_stock_movement(
    session: AsyncSession, change: StockChange, *, actor_id: int | None = None
) -> list[StockMovement]:
    ing = await lock_ingredient(session, change.ingredient_id)
    bd = change.business_date or _bd_now()
    delta = Decimal(str(change.delta))

    movements: list[StockMovement] = []

    if delta > 0:
        # Simple inbound: add to ingredient total, create one movement without lot
        # Caller (receipt) will have created lot; this path used for reversal or direct add
        ing.stock_qty = float(Decimal(str(ing.stock_qty)) + delta)
        m = StockMovement(
            ingredient_id=change.ingredient_id,
            lot_id=None,
            kind=change.kind if change.kind != "Trừ tự động" else "Nhập",
            qty=float(delta),
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
        return movements

    # delta < 0: FIFO draw
    need = -delta
    lots = await lots_for_fifo(session, change.ingredient_id)
    total_avail = sum(Decimal(str(lot_item.quantity_remaining)) for lot_item in lots)
    if total_avail < need:
        raise BusinessRuleError("Không đủ tồn kho.")

    remaining = need
    for lot in lots:
        if remaining <= 0:
            break
        avail = Decimal(str(lot.quantity_remaining))
        take = min(avail, remaining)
        lot.quantity_remaining = float(avail - take)
        # keep status as is (simplified)
        m = StockMovement(
            ingredient_id=change.ingredient_id,
            lot_id=lot.id,
            kind=change.kind,
            qty=float(-take),
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
    ing.stock_qty = float(Decimal(str(ing.stock_qty)) - need)
    await session.flush()
    return movements


async def reverse_movement(
    session: AsyncSession, movement: StockMovement, *, actor_id: int | None = None
) -> StockMovement:
    # return qty to original lot, ignore expiry
    if movement.lot_id is not None:
        lot = await session.get(IngredientLot, movement.lot_id)
        if lot is not None:
            lot.quantity_remaining = float(
                Decimal(str(lot.quantity_remaining)) - Decimal(str(movement.qty))
            )
            await session.flush()
    ing = await lock_ingredient(session, movement.ingredient_id)
    # movement.qty is negative for draw, so -qty is positive
    ing.stock_qty = float(Decimal(str(ing.stock_qty)) - Decimal(str(movement.qty)))
    await session.flush()
    bd = _bd_now()
    rev = StockMovement(
        ingredient_id=movement.ingredient_id,
        lot_id=movement.lot_id,
        kind="Hoàn kho",
        qty=float(-Decimal(str(movement.qty))),
        business_date=bd,
        performed_by=actor_id,
    )
    session.add(rev)
    await session.flush()
    return rev
