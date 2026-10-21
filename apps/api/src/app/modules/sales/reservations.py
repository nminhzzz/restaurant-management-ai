"""Ingredient holds for an in-progress selection (FR-SALE-01/05/08, FR-INV-10/11).

A hold only reserves lot quantities; it never writes `GIAO_DICH_KHO`. The stock is
deducted exactly once when the hold is sent and converted into an ORDER line.
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.catalog.models import DiningTable, Ingredient, Recipe, RecipeItem
from app.modules.catalog.service import ensure_dish_sellable
from app.modules.catalog.versions import active_price_version, active_recipe, recipe_items
from app.modules.inventory.models import IngredientLot, StockMovement
from app.modules.inventory.stock import ensure_no_open_stocktake
from app.modules.sales.models import Order, Reservation, ReservationDetail
from app.modules.settings.service import get_config
from app.shared import business_date
from app.shared.enums import LotStatus, StockMovementType, VersionStatus

HOLD_ACTIVE = "Đang giữ"
HOLD_SENT = "Đã gửi"
HOLD_RELEASED = "Đã giải phóng"
HOLD_EXPIRED = "Hết hạn"
HOLD_STATUSES = (HOLD_ACTIVE, HOLD_SENT, HOLD_RELEASED, HOLD_EXPIRED)


def _now() -> datetime:
    return business_date.now().replace(tzinfo=None)


def _business_date() -> date:
    return business_date.business_date_of(business_date.now())


async def _hold_minutes(session: AsyncSession) -> int:
    try:
        return int((await get_config(session)).hold_minutes)
    except Exception:
        return 5


async def _active_holds_by_lot(
    session: AsyncSession, lot_ids: list[int], now: datetime
) -> dict[int, Decimal]:
    if not lot_ids:
        return {}
    rows = await session.execute(
        select(ReservationDetail.lot_id, func.sum(ReservationDetail.quantity))
        .join(Reservation, Reservation.id == ReservationDetail.reservation_id)
        .where(
            ReservationDetail.lot_id.in_(lot_ids),
            Reservation.status == HOLD_ACTIVE,
            Reservation.expires_at > now,
        )
        .group_by(ReservationDetail.lot_id)
    )
    return {lot_id: Decimal(str(quantity or 0)) for lot_id, quantity in rows}


async def _lock_ingredients(session: AsyncSession, ingredient_ids: list[int]) -> None:
    ids = sorted(set(ingredient_ids))
    if not ids:
        return
    await session.execute(
        select(Ingredient).where(Ingredient.id.in_(ids)).order_by(Ingredient.id).with_for_update()
    )


async def _eligible_lots(
    session: AsyncSession, ingredient_id: int, now: datetime, *, lock: bool = True
):
    today = now.date()
    statement = (
        select(IngredientLot)
        .where(
            IngredientLot.ingredient_id == ingredient_id,
            IngredientLot.quantity_remaining > 0,
            IngredientLot.status != LotStatus.HET_HAN.value,
            or_(
                IngredientLot.expiry_date.is_(None),
                IngredientLot.expiry_date >= today,
            ),
        )
        .order_by(IngredientLot.received_at.asc(), IngredientLot.id.asc())
    )
    if lock:
        statement = statement.with_for_update()
    return list((await session.execute(statement)).scalars().all())


async def _allocate(
    session: AsyncSession, ingredient_id: int, need: Decimal, now: datetime
) -> list[tuple[IngredientLot, Decimal]]:
    lots = await _eligible_lots(session, ingredient_id, now)
    held = await _active_holds_by_lot(session, [lot.id for lot in lots], now)
    allocations: list[tuple[IngredientLot, Decimal]] = []
    remaining = need
    for lot in lots:
        if remaining <= 0:
            break
        available = Decimal(str(lot.quantity_remaining)) - held.get(lot.id, Decimal(0))
        if available <= 0:
            continue
        take = min(available, remaining)
        allocations.append((lot, take))
        remaining -= take
    if remaining > 0:
        raise BusinessRuleError("Không đủ tồn kho khả dụng.")
    return allocations


def _expiry_for(now: datetime, minutes: int, lots: list[IngredientLot]) -> datetime:
    expires = now + timedelta(minutes=minutes)
    lot_expiries = [lot.expiry_date for lot in lots if lot.expiry_date is not None]
    if lot_expiries:
        earliest = min(lot_expiries)
        capped = datetime.combine(earliest, time(23, 59, 59))
        if capped < expires:
            expires = capped
    if expires <= now:
        raise BusinessRuleError("Lô nguyên liệu đã hết hạn sử dụng.")
    return expires


async def _add_details(
    session: AsyncSession,
    reservation: Reservation,
    allocations: list[tuple[IngredientLot, Decimal]],
) -> None:
    existing = {
        detail.lot_id: detail
        for detail in (
            await session.execute(
                select(ReservationDetail).where(ReservationDetail.reservation_id == reservation.id)
            )
        )
        .scalars()
        .all()
    }
    for lot, quantity in allocations:
        detail = existing.get(lot.id)
        if detail is None:
            session.add(
                ReservationDetail(
                    reservation_id=reservation.id,
                    lot_id=lot.id,
                    quantity=quantity,
                )
            )
        else:
            detail.quantity = Decimal(str(detail.quantity)) + quantity


async def create_hold(
    session: AsyncSession,
    *,
    user_id: int,
    selection_code: str | None,
    table_id: int | None,
    dish_id: int,
    quantity: int,
    note: str | None = None,
    order_id: int | None = None,
) -> Reservation:
    if quantity <= 0:
        raise BusinessRuleError("Số lượng phải lớn hơn 0.")
    await ensure_no_open_stocktake(session)
    await ensure_dish_sellable(session, dish_id)
    now = _now()
    bd = _business_date()
    price = await active_price_version(session, dish_id, bd)
    if price is None:
        raise BusinessRuleError("Món chưa có giá.")
    recipe = await active_recipe(session, dish_id, bd)
    if recipe is None:
        raise BusinessRuleError("Món chưa có công thức hiệu lực.")
    items = await recipe_items(session, recipe.id)
    await _lock_ingredients(session, [item.ingredient_id for item in items])

    if order_id is not None:
        order = await session.get(Order, order_id)
        if order is None or order.status != "Đang mở":
            raise BusinessRuleError("Order không còn mở.")
        if order.table_id != table_id:
            raise BusinessRuleError("Lượt giữ chỗ khác bàn của order.")
    elif table_id is not None:
        table = await session.get(DiningTable, table_id)
        if table is None or table.is_deleted:
            raise BusinessRuleError("Bàn không tồn tại.")
        if table.status != "Trống" or table.current_order_id is not None:
            raise BusinessRuleError("Bàn đang phục vụ.")

    allocations: list[tuple[IngredientLot, Decimal]] = []
    for item in items:
        need = Decimal(str(item.quantity)) * quantity
        allocations.extend(await _allocate(session, item.ingredient_id, need, now))

    code = selection_code or uuid4().hex
    if len(code) > 36:
        raise BusinessRuleError("Mã lượt chọn tối đa 36 ký tự.")
    reservation = Reservation(
        selection_code=code,
        user_id=user_id,
        table_id=table_id,
        order_id=order_id,
        dish_id=dish_id,
        recipe_id=recipe.id,
        price_version_id=price.id,
        quantity=quantity,
        note=note,
        expires_at=_expiry_for(now, await _hold_minutes(session), [lot for lot, _ in allocations]),
        status=HOLD_ACTIVE,
    )
    session.add(reservation)
    await session.flush()
    await _add_details(session, reservation, allocations)
    await session.flush()
    return reservation


async def _owned_active(session: AsyncSession, hold_id: int, user_id: int) -> Reservation:
    reservation = (
        await session.execute(
            select(Reservation).where(Reservation.id == hold_id).with_for_update()
        )
    ).scalar_one_or_none()
    if reservation is None or reservation.user_id != user_id:
        raise NotFoundError("Không tìm thấy lượt giữ chỗ.")
    if reservation.status != HOLD_ACTIVE:
        raise BusinessRuleError("Lượt giữ chỗ không còn hiệu lực.")
    if reservation.expires_at <= _now():
        reservation.status = HOLD_EXPIRED
        await session.flush()
        raise BusinessRuleError("Lượt giữ chỗ đã hết hạn.")
    return reservation


async def update_hold(
    session: AsyncSession, *, hold_id: int, user_id: int, quantity: int
) -> Reservation:
    if quantity <= 0:
        raise BusinessRuleError("Số lượng phải lớn hơn 0.")
    await ensure_no_open_stocktake(session)
    reservation = await _owned_active(session, hold_id, user_id)
    await ensure_dish_sellable(session, reservation.dish_id)
    current = int(reservation.quantity)
    if quantity == current:
        return reservation
    if reservation.recipe_id is None:
        raise BusinessRuleError("Món chưa có công thức hiệu lực.")

    items = await recipe_items(session, reservation.recipe_id)
    await _lock_ingredients(session, [item.ingredient_id for item in items])
    # Re-allocate the whole line: release the old details first so the new
    # quantity is checked against the lots (including the quantity being replaced).
    await session.execute(
        delete(ReservationDetail).where(ReservationDetail.reservation_id == reservation.id)
    )
    await session.flush()
    now = _now()
    allocations: list[tuple[IngredientLot, Decimal]] = []
    for item in items:
        allocations.extend(
            await _allocate(
                session,
                item.ingredient_id,
                Decimal(str(item.quantity)) * quantity,
                now,
            )
        )
    await _add_details(session, reservation, allocations)
    reservation.quantity = quantity
    reservation.expires_at = _expiry_for(
        now, await _hold_minutes(session), [lot for lot, _ in allocations]
    )
    await session.flush()
    return reservation


async def release_hold(session: AsyncSession, *, hold_id: int, user_id: int) -> Reservation:
    reservation = await _owned_active(session, hold_id, user_id)
    reservation.status = HOLD_RELEASED
    await session.execute(
        delete(ReservationDetail).where(ReservationDetail.reservation_id == reservation.id)
    )
    await session.flush()
    return reservation


async def release_active_holds(
    session: AsyncSession, *, order_id: int | None = None, table_id: int | None = None
) -> int:
    """FR-CAT-18/FR-SALE-13: leaving an order/table must not keep stock reserved."""
    conditions = [Reservation.status == HOLD_ACTIVE]
    if order_id is not None:
        conditions.append(Reservation.order_id == order_id)
    if table_id is not None:
        conditions.append(Reservation.table_id == table_id)
    if len(conditions) == 1:
        return 0
    rows = list((await session.execute(select(Reservation).where(*conditions))).scalars().all())
    for reservation in rows:
        reservation.status = HOLD_RELEASED
        await session.execute(
            delete(ReservationDetail).where(ReservationDetail.reservation_id == reservation.id)
        )
    if rows:
        await session.flush()
    return len(rows)


async def expire_due_holds(session: AsyncSession) -> int:
    now = _now()
    rows = list(
        (
            await session.execute(
                select(Reservation).where(
                    Reservation.status == HOLD_ACTIVE,
                    Reservation.expires_at <= now,
                )
            )
        )
        .scalars()
        .all()
    )
    for reservation in rows:
        reservation.status = HOLD_EXPIRED
    if rows:
        await session.flush()
    return len(rows)


async def list_holds(
    session: AsyncSession, *, user_id: int, selection_code: str | None = None
) -> list[Reservation]:
    await expire_due_holds(session)
    query = select(Reservation).where(
        Reservation.user_id == user_id,
        Reservation.status == HOLD_ACTIVE,
        Reservation.expires_at > _now(),
    )
    if selection_code:
        query = query.where(Reservation.selection_code == selection_code)
    return list((await session.execute(query.order_by(Reservation.id.asc()))).scalars().all())


async def get_active_hold(session: AsyncSession, hold_id: int, user_id: int) -> Reservation:
    return await _owned_active(session, hold_id, user_id)


async def consume_hold(
    session: AsyncSession,
    reservation: Reservation,
    *,
    order_line_id: int,
    business_date_value: date,
    actor_id: int | None,
) -> None:
    """Convert a hold into stock consumption exactly once (FR-SALE-03, FR-INV-03)."""
    if reservation.status != HOLD_ACTIVE:
        raise BusinessRuleError("Lượt giữ chỗ không còn hiệu lực.")
    await ensure_no_open_stocktake(session)
    await ensure_dish_sellable(session, reservation.dish_id)
    today = _business_date()
    current_price = await active_price_version(session, reservation.dish_id, today)
    if current_price is not None and current_price.id != reservation.price_version_id:
        raise BusinessRuleError(
            f"Giá món đã thay đổi thành {current_price.price}; vui lòng chọn lại món."
        )
    current_recipe = await active_recipe(session, reservation.dish_id, today)
    if current_recipe is not None and current_recipe.id != reservation.recipe_id:
        raise BusinessRuleError("Công thức món đã thay đổi; vui lòng chọn lại món.")
    details = list(
        (
            await session.execute(
                select(ReservationDetail)
                .where(ReservationDetail.reservation_id == reservation.id)
                .with_for_update()
            )
        )
        .scalars()
        .all()
    )
    affected: list[int] = []
    for detail in details:
        lot = (
            await session.execute(
                select(IngredientLot).where(IngredientLot.id == detail.lot_id).with_for_update()
            )
        ).scalar_one_or_none()
        if (
            lot is None
            or Decimal(str(lot.quantity_remaining)) < Decimal(str(detail.quantity))
            or (lot.expiry_date is not None and lot.expiry_date < today)
        ):
            raise BusinessRuleError("Lô giữ chỗ không còn đủ số lượng hoặc đã hết hạn.")
        ingredient = await session.get(Ingredient, lot.ingredient_id)
        if ingredient is None:
            raise BusinessRuleError("Nguyên liệu không tồn tại.")
        quantity = Decimal(str(detail.quantity))
        lot.quantity_remaining = Decimal(str(lot.quantity_remaining)) - quantity
        ingredient.stock_qty = Decimal(str(ingredient.stock_qty)) - quantity
        session.add(
            StockMovement(
                ingredient_id=ingredient.id,
                lot_id=lot.id,
                kind=StockMovementType.TRU_TU_DONG,
                qty=-quantity,
                business_date=business_date_value,
                order_line_id=order_line_id,
                performed_by=actor_id,
            )
        )
        affected.append(ingredient.id)
    reservation.status = HOLD_SENT
    reservation.order_line_id = order_line_id
    await session.flush()
    if affected:
        from app.modules.inventory.service import recompute_automatic_out_of_stock

        await recompute_automatic_out_of_stock(session, affected)


async def available_quantity(
    session: AsyncSession,
    ingredient_id: int,
    now: datetime | None = None,
    *,
    lock: bool = True,
) -> Decimal:
    moment = now or _now()
    lots = await _eligible_lots(session, ingredient_id, moment, lock=lock)
    held = await _active_holds_by_lot(session, [lot.id for lot in lots], moment)
    return sum(
        (
            max(
                Decimal(0),
                Decimal(str(lot.quantity_remaining)) - held.get(lot.id, Decimal(0)),
            )
            for lot in lots
        ),
        Decimal(0),
    )


async def available_portions_for_dishes(
    session: AsyncSession, dish_ids: list[int], now: datetime | None = None
) -> dict[int, int]:
    """Batch the menu availability query: a handful of queries for the whole page."""
    if not dish_ids:
        return {}
    moment = now or _now()
    bd = _business_date()
    recipe_rows = (
        await session.execute(
            select(Recipe.dish_id, Recipe.id)
            .where(
                Recipe.dish_id.in_(dish_ids),
                Recipe.status == VersionStatus.HIEU_LUC.value,
                Recipe.business_date <= bd,
            )
            .order_by(Recipe.dish_id.asc(), Recipe.business_date.desc(), Recipe.id.desc())
        )
    ).all()
    recipes: dict[int, int] = {}
    for dish_id, recipe_id in recipe_rows:
        recipes.setdefault(int(dish_id), int(recipe_id))
    if not recipes:
        return {int(dish_id): 0 for dish_id in dish_ids}

    item_rows = (
        await session.execute(
            select(RecipeItem.recipe_id, RecipeItem.ingredient_id, RecipeItem.quantity).where(
                RecipeItem.recipe_id.in_(list(recipes.values()))
            )
        )
    ).all()
    by_recipe: dict[int, list[tuple[int, Decimal]]] = {}
    ingredient_ids: set[int] = set()
    for recipe_id, ingredient_id, quantity in item_rows:
        by_recipe.setdefault(int(recipe_id), []).append(
            (int(ingredient_id), Decimal(str(quantity)))
        )
        ingredient_ids.add(int(ingredient_id))

    if not ingredient_ids:
        return {int(dish_id): 0 for dish_id in dish_ids}
    today = moment.date()
    lots = list(
        (
            await session.execute(
                select(IngredientLot).where(
                    IngredientLot.ingredient_id.in_(list(ingredient_ids)),
                    IngredientLot.quantity_remaining > 0,
                    IngredientLot.status != LotStatus.HET_HAN.value,
                    or_(
                        IngredientLot.expiry_date.is_(None),
                        IngredientLot.expiry_date >= today,
                    ),
                )
            )
        )
        .scalars()
        .all()
    )
    held = await _active_holds_by_lot(session, [lot.id for lot in lots], moment)
    available: dict[int, Decimal] = {}
    for lot in lots:
        available[lot.ingredient_id] = available.get(lot.ingredient_id, Decimal(0)) + max(
            Decimal(0),
            Decimal(str(lot.quantity_remaining)) - held.get(lot.id, Decimal(0)),
        )

    result: dict[int, int] = {}
    for dish_id, recipe_id in recipes.items():
        portions: int | None = None
        for ingredient_id, quantity in by_recipe.get(recipe_id, []):
            if quantity <= 0:
                continue
            ingredient_portions = int(available.get(ingredient_id, Decimal(0)) // quantity)
            portions = (
                ingredient_portions if portions is None else min(portions, ingredient_portions)
            )
        result[dish_id] = max(portions or 0, 0)
    return {int(dish_id): result.get(int(dish_id), 0) for dish_id in dish_ids}


async def available_portions(
    session: AsyncSession, dish_id: int, now: datetime | None = None
) -> int:
    """How many portions can still be held from current stock (FR-SALE-01/04)."""
    return (await available_portions_for_dishes(session, [dish_id], now)).get(dish_id, 0)
