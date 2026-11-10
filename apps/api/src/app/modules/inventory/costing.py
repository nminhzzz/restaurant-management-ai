"""Moving weighted average costing (document 04 G.1; FR-INV-02/03/04/09, FR-REP-11).

Every ingredient has one current unit cost. It is recalculated when stock arrives with a value
of its own — a receipt, a corrected or cancelled receipt, a dish handed back to stock — and each
recalculation is one row of LICH_SU_GIA_BINH_QUAN. Sales, write-offs and stocktake adjustments
take the current unit cost and never move it.

The value of a movement is written once, when it happens, and is never recomputed. An ingredient
without a valid receipt has no unit cost: its movements carry NULL, never 0, until the first
receipt prices them.
"""

from collections.abc import Iterable
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.models import AverageCostHistory, StockIssueLine, StockMovement
from app.shared import business_date

CENT = Decimal("0.01")
MILLISECOND = timedelta(milliseconds=1)


def money(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def movement_value(quantity: Decimal, unit_cost: Decimal | None) -> Decimal | None:
    """Rounded unit cost x quantity, signed like the quantity; None while there is no unit cost."""
    if unit_cost is None:
        return None
    return money(Decimal(str(quantity)) * unit_cost)


def blended_cost(stock: Decimal, unit_cost: Decimal, quantity: Decimal, value: Decimal) -> Decimal:
    """Unit cost after `quantity` worth `value` joins (or, when negative, leaves) the stock.

    With nothing left there is nothing to divide by, so the unit cost in force stays. The same
    holds when taking a receipt back out would leave a negative value: stock drawn in between
    already carried that value away at the average.
    """
    remaining = stock + quantity
    if remaining <= 0:
        return unit_cost
    blended = (stock * unit_cost + value) / remaining
    if blended < 0:
        return unit_cost
    return money(blended)


def _latest_rows():
    latest = (
        select(
            AverageCostHistory.ingredient_id.label("ingredient_id"),
            func.max(AverageCostHistory.effective_at).label("effective_at"),
        )
        .group_by(AverageCostHistory.ingredient_id)
        .subquery()
    )
    return select(AverageCostHistory.ingredient_id, AverageCostHistory.avg_cost).join(
        latest,
        (latest.c.ingredient_id == AverageCostHistory.ingredient_id)
        & (latest.c.effective_at == AverageCostHistory.effective_at),
    )


async def current_unit_costs(
    session: AsyncSession, ingredient_ids: Iterable[int] | None = None
) -> dict[int, Decimal]:
    """Unit cost in force per ingredient; an ingredient that was never priced is absent."""
    statement = _latest_rows()
    if ingredient_ids is not None:
        statement = statement.where(AverageCostHistory.ingredient_id.in_(set(ingredient_ids)))
    return {
        int(ingredient_id): Decimal(str(cost))
        for ingredient_id, cost in await session.execute(statement)
    }


async def current_unit_cost(session: AsyncSession, ingredient_id: int) -> Decimal | None:
    cost = await session.scalar(
        select(AverageCostHistory.avg_cost)
        .where(AverageCostHistory.ingredient_id == ingredient_id)
        .order_by(AverageCostHistory.effective_at.desc())
        .limit(1)
    )
    return None if cost is None else Decimal(str(cost))


async def value_at_current_cost(session: AsyncSession, movement: StockMovement) -> None:
    """A draw, write-off or stocktake adjustment: valued at the unit cost in force, once."""
    movement.value = movement_value(
        movement.qty, await current_unit_cost(session, movement.ingredient_id)
    )


async def _record(
    session: AsyncSession,
    ingredient_id: int,
    unit_cost: Decimal,
    stock_after: Decimal,
    movement: StockMovement | None,
) -> AverageCostHistory:
    if movement is not None and movement.id is None:
        await session.flush()
    moment = _to_millisecond(business_date.now())
    latest = await session.scalar(
        select(func.max(AverageCostHistory.effective_at)).where(
            AverageCostHistory.ingredient_id == ingredient_id
        )
    )
    # Two recalculations inside one millisecond still need distinct, ordered keys.
    if latest is not None and moment <= latest:
        moment = latest + MILLISECOND
    row = AverageCostHistory(
        ingredient_id=ingredient_id,
        effective_at=moment,
        avg_cost=unit_cost,
        stock_qty=stock_after,
        movement_id=None if movement is None else movement.id,
    )
    session.add(row)
    await session.flush()
    return row


def _to_millisecond(moment: datetime) -> datetime:
    naive = moment.replace(tzinfo=None)
    return naive.replace(microsecond=naive.microsecond // 1000 * 1000)


async def _price_backlog(session: AsyncSession, ingredient_id: int, unit_cost: Decimal) -> None:
    """The first unit cost prices everything that moved while the ingredient had none."""
    movements = await session.scalars(
        select(StockMovement).where(
            StockMovement.ingredient_id == ingredient_id, StockMovement.value.is_(None)
        )
    )
    for movement in movements:
        movement.value = movement_value(movement.qty, unit_cost)
    lines = await session.scalars(
        select(StockIssueLine).where(
            StockIssueLine.ingredient_id == ingredient_id, StockIssueLine.estimated_cost.is_(None)
        )
    )
    for line in lines:
        line.estimated_cost = movement_value(line.quantity, unit_cost)
    await session.flush()


async def record_purchase(
    session: AsyncSession, movement: StockMovement, *, stock_before: Decimal, unit_price: Decimal
) -> None:
    """A receipt line joined the stock at its own price."""
    quantity = Decimal(str(movement.qty))
    movement.value = money(quantity * unit_price)
    current = await current_unit_cost(session, movement.ingredient_id)
    if current is None:
        unit_cost = money(unit_price)
        await _price_backlog(session, movement.ingredient_id, unit_cost)
    else:
        unit_cost = blended_cost(stock_before, current, quantity, quantity * unit_price)
    await _record(session, movement.ingredient_id, unit_cost, stock_before + quantity, movement)


async def record_receipt_correction(
    session: AsyncSession,
    ingredient_id: int,
    *,
    stock_before: Decimal,
    old_quantity: Decimal,
    old_price: Decimal,
    new_quantity: Decimal,
    new_price: Decimal,
    movement: StockMovement | None = None,
) -> None:
    """A receipt line was corrected or cancelled (`new_quantity` 0).

    The old quantity and value leave the average first; only then does the corrected line join.
    Values already written on earlier movements stay as they are.
    """
    if movement is not None:
        movement.value = money(new_quantity * new_price - old_quantity * old_price)
    current = await current_unit_cost(session, ingredient_id)
    stock_without = stock_before - old_quantity
    if current is None:
        unit_cost = money(new_price)
    else:
        unit_cost = blended_cost(stock_before, current, -old_quantity, -old_quantity * old_price)
        if new_quantity > 0:
            unit_cost = blended_cost(
                stock_without, unit_cost, new_quantity, new_quantity * new_price
            )
    await _record(session, ingredient_id, unit_cost, stock_without + new_quantity, movement)


async def record_return(
    session: AsyncSession,
    ingredient_id: int,
    *,
    stock_before: Decimal,
    quantity: Decimal,
    value: Decimal | None,
    movement: StockMovement | None = None,
) -> None:
    """Stock handed back by a cancelled dish, at the value it left with (FR-INV-04)."""
    current = await current_unit_cost(session, ingredient_id)
    if value is None or current is None:
        return
    unit_cost = blended_cost(stock_before, current, quantity, value)
    await _record(session, ingredient_id, unit_cost, stock_before + quantity, movement)
