"""Allocate short-lived dish selections against available FIFO ingredient lots."""

from datetime import datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.catalog.models import DiningTable
from app.modules.catalog.versions import active_price_version, active_recipe, recipe_items
from app.modules.inventory.models import IngredientLot
from app.modules.inventory.stock import (
    lock_ingredients,
    lock_stocktake_gate,
    refresh_lot_statuses,
)
from app.modules.sales.common import ensure_order_is_open
from app.modules.sales.models import ItemHold, ItemHoldLot, Order
from app.modules.sales.orders import dish_block_reason
from app.shared import business_date
from app.shared.enums import LotStatus

ACTIVE = "Đang giữ"
RELEASED = "Đã hủy"


def _local_naive(moment: datetime) -> datetime:
    return business_date.naive_local(moment)


async def list_holds(
    session: AsyncSession, actor_id: int, selection_id: str, *, for_update: bool = False
) -> list[ItemHold]:
    query = (
        select(ItemHold)
        .where(ItemHold.owner_id == actor_id, ItemHold.selection_id == selection_id)
        .order_by(ItemHold.id)
    )
    if for_update and session.get_bind().dialect.name == "mysql":
        query = query.with_for_update().execution_options(populate_existing=True)
    result = await session.execute(query)
    return list(result.scalars().all())


async def _allocate(
    session: AsyncSession,
    hold: ItemHold,
    recipe_id: int,
    quantity: int,
    now: datetime,
    ttl_minutes: int,
) -> datetime:
    items = await recipe_items(session, recipe_id)
    await lock_ingredients(session, [item.ingredient_id for item in items])
    expires_at = now + timedelta(minutes=ttl_minutes)

    old_query = select(ItemHoldLot).where(ItemHoldLot.hold_id == hold.id)
    if session.get_bind().dialect.name == "mysql":
        old_query = old_query.with_for_update().execution_options(populate_existing=True)
    old_allocations = (await session.execute(old_query)).scalars().all()
    for allocation in old_allocations:
        await session.delete(allocation)
    await session.flush()

    for item in sorted(items, key=lambda row: row.ingredient_id):
        need = Decimal(str(item.quantity)) * quantity
        if need <= 0:
            continue
        query = (
            select(IngredientLot)
            .where(
                IngredientLot.ingredient_id == item.ingredient_id,
                IngredientLot.quantity_remaining > 0,
                IngredientLot.status != LotStatus.HET_HAN.value,
            )
            .order_by(IngredientLot.received_at, IngredientLot.id)
        )
        if session.get_bind().dialect.name == "mysql":
            query = query.with_for_update().execution_options(populate_existing=True)
        lots = (await session.execute(query)).scalars().all()
        for lot in lots:
            if need <= 0:
                break
            lot_expiry = (
                datetime.combine(lot.expiry_date + timedelta(days=1), time.min)
                if lot.expiry_date is not None
                else None
            )
            if lot_expiry is not None and lot_expiry <= now:
                continue
            held_query = (
                select(ItemHoldLot.quantity_held)
                .join(ItemHold, ItemHold.id == ItemHoldLot.hold_id)
                .where(
                    ItemHoldLot.lot_id == lot.id,
                    ItemHold.status == ACTIVE,
                    ItemHold.expires_at > now,
                    ItemHold.id != hold.id,
                )
            )
            if session.get_bind().dialect.name == "mysql":
                held_query = held_query.with_for_update()
            held_rows = await session.execute(held_query)
            reserved = sum((Decimal(str(held)) for held in held_rows.scalars()), Decimal(0))
            available = max(Decimal(0), Decimal(str(lot.quantity_remaining)) - reserved)
            take = min(available, need)
            if take <= 0:
                continue
            session.add(ItemHoldLot(hold_id=hold.id, lot_id=lot.id, quantity_held=take))
            need -= take
            if lot_expiry is not None:
                expires_at = min(expires_at, lot_expiry)
        if need > 0:
            raise BusinessRuleError("Không đủ tồn kho để giữ món.")
    await session.flush()
    return expires_at


async def upsert_hold(
    session: AsyncSession,
    actor_id: int,
    selection_id: str,
    dish_id: int,
    quantity: int,
    note: str | None,
    table_id: int | None,
    order_id: int | None,
) -> ItemHold:
    config = await lock_stocktake_gate(session)
    if quantity <= 0:
        raise BusinessRuleError("Số lượng món phải lớn hơn 0.")
    if not selection_id or len(selection_id) > 64:
        raise BusinessRuleError("Mã lượt chọn không hợp lệ.")
    if order_id is not None:
        order = await session.get(Order, order_id)
        if order is None:
            raise BusinessRuleError("Order không còn mở hoặc bàn không hợp lệ.")
        ensure_order_is_open(order)
        if order.table_id is None or order.table_id != table_id:
            raise BusinessRuleError("Order không còn mở hoặc bàn không hợp lệ.")
    elif table_id is not None:
        table = await session.get(DiningTable, table_id)
        if (
            table is None
            or table.is_deleted
            or table.status != "Trống"
            or table.serving_order_id is not None
        ):
            raise BusinessRuleError("Bàn không khả dụng.")
    reason = await dish_block_reason(session, dish_id)
    if reason is not None:
        raise BusinessRuleError(reason)
    await refresh_lot_statuses(session, config.expiry_warning_days)
    moment = business_date.now()
    now = _local_naive(moment)
    from app.modules.settings.service import effective_business_day_start

    start = await effective_business_day_start(session, moment)
    bd = business_date.business_date_of(moment, start)
    recipe = await active_recipe(session, dish_id, bd)
    price = await active_price_version(session, dish_id, bd)
    if recipe is None or price is None:
        raise BusinessRuleError("Món chưa có công thức hoặc giá hiệu lực.")
    await lock_ingredients(
        session, [item.ingredient_id for item in await recipe_items(session, recipe.id)]
    )
    token_query = select(ItemHold).where(ItemHold.selection_id == selection_id)
    if session.get_bind().dialect.name == "mysql":
        token_query = token_query.with_for_update(read=True)
    token_owner = (await session.execute(token_query)).scalars().first()
    if token_owner is not None and token_owner.owner_id != actor_id:
        raise NotFoundError("Không tìm thấy lượt chọn.")
    existing_lines = await list_holds(session, actor_id, selection_id, for_update=True)
    if any(line.order_id != order_id or line.table_id != table_id for line in existing_lines):
        raise BusinessRuleError("Lượt chọn không khớp order hoặc bàn.")

    hold = next(
        (line for line in existing_lines if line.dish_id == dish_id and line.status == ACTIVE),
        None,
    )
    if hold is None:
        hold = ItemHold(
            owner_id=actor_id,
            selection_id=selection_id,
            dish_id=dish_id,
            recipe_id=recipe.id,
            price_version_id=price.id,
            quantity=quantity,
            note=note,
            table_id=table_id,
            order_id=order_id,
            expires_at=now + timedelta(minutes=config.reservation_hold_minutes),
            status=ACTIVE,
        )
        session.add(hold)
        await session.flush()
    expires_at = await _allocate(
        session, hold, recipe.id, quantity, now, config.reservation_hold_minutes
    )
    hold.quantity = quantity
    hold.note = note
    hold.recipe_id = recipe.id
    hold.price_version_id = price.id
    hold.expires_at = expires_at
    await session.flush()
    return hold


async def release_hold(session: AsyncSession, actor_id: int, hold_id: int) -> list[ItemHoldLot]:
    await lock_stocktake_gate(session)
    lookup = select(ItemHold).where(ItemHold.id == hold_id)
    if session.get_bind().dialect.name == "mysql":
        lookup = lookup.with_for_update(read=True).execution_options(populate_existing=True)
    hold = (await session.execute(lookup)).scalar_one_or_none()
    if hold is None or hold.owner_id != actor_id:
        raise NotFoundError("Không tìm thấy giữ chỗ.")
    await lock_ingredients(
        session, [item.ingredient_id for item in await recipe_items(session, hold.recipe_id)]
    )
    if session.get_bind().dialect.name == "mysql":
        hold = (
            await session.execute(
                select(ItemHold)
                .where(ItemHold.id == hold_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalar_one()
    if hold.status != ACTIVE:
        raise BusinessRuleError("Giữ chỗ đã kết thúc.")
    rows_query = select(ItemHoldLot).where(ItemHoldLot.hold_id == hold.id)
    if session.get_bind().dialect.name == "mysql":
        rows_query = rows_query.with_for_update().execution_options(populate_existing=True)
    rows = (await session.execute(rows_query)).scalars().all()
    hold.status = RELEASED
    await session.flush()
    return list(rows)


async def reallocate_expired_hold(session: AsyncSession, actor_id: int, hold_id: int) -> ItemHold:
    """Recheck an expired line immediately before selection submission."""
    config = await lock_stocktake_gate(session)
    lookup = select(ItemHold).where(ItemHold.id == hold_id)
    if session.get_bind().dialect.name == "mysql":
        lookup = lookup.with_for_update(read=True).execution_options(populate_existing=True)
    hold = (await session.execute(lookup)).scalar_one_or_none()
    if hold is None or hold.owner_id != actor_id:
        raise NotFoundError("Không tìm thấy giữ chỗ.")
    await lock_ingredients(
        session, [item.ingredient_id for item in await recipe_items(session, hold.recipe_id)]
    )
    if session.get_bind().dialect.name == "mysql":
        hold = (
            await session.execute(
                select(ItemHold)
                .where(ItemHold.id == hold_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalar_one()
    if hold.status != ACTIVE:
        raise BusinessRuleError("Giữ chỗ đã kết thúc.")
    now = _local_naive(business_date.now())
    hold.expires_at = await _allocate(
        session,
        hold,
        hold.recipe_id,
        hold.quantity,
        now,
        config.reservation_hold_minutes,
    )
    await session.flush()
    return hold
