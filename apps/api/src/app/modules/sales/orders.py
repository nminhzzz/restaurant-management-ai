"""Order lifecycle: submit, lines, stock, table moves, cancellation (FR-SALE-01…13, 22, 27…30).

Stock is drawn through `inventory.stock.apply_stock_movement` (or, for held selections, from the
exact lots the holds reserved) and returned lot by lot through `_return_line_stock`. A return
mirrors the draw ledger of the line, so a reduce-then-cancel sequence can never give back more
than was taken, and every "Hoàn kho" movement carries the order line it reverses (report 3.2.2).

Everything that changes an order locks the stocktake gate, then the ORDER row, then the
ingredients in ascending id (FR-INV-11, NFR-08), and writes one audit row with before/after
(FR-SET-08). Anything that does not hold in full is refused in full (FR-SALE-05, NFR-10).
"""

import logging
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, ConflictError, NotFoundError
from app.modules.catalog.models import DiningTable, Dish, DishPriceVersion, Recipe
from app.modules.catalog.versions import (
    active_price_version,
    active_price_version_for_update,
    active_recipe,
    active_recipe_for_update,
    recipe_items,
)
from app.modules.inventory.models import IngredientLot, StockMovement
from app.modules.inventory.stock import (
    StockChange,
    apply_stock_movement,
    dish_is_out_of_stock,
    lock_ingredient,
    lock_ingredients,
    lock_stocktake_gate,
    refresh_lot_statuses,
    sellable_available,
)
from app.modules.sales.common import (
    LINE_CANCELLED,
    OPEN_ORDER_STATUSES,
    audit_order,
    current_business_date,
    ensure_order_is_open,
    local_now,
    lock_order,
    lock_table,
    refresh_order_total,
)
from app.modules.sales.models import (
    DemOrder,
    ItemHold,
    ItemHoldLot,
    Order,
    OrderLine,
    TableMoveLog,
)
from app.modules.sales.tickets import write_kitchen_ticket
from app.modules.settings.service import effective_business_day_start, get_config
from app.shared import business_date
from app.shared.enums import (
    DishStatus,
    OrderLineStatus,
    OrderStatus,
    OrderType,
    StockMovementType,
    TableStatus,
)

logger = logging.getLogger(__name__)

__all__ = ["LINE_CANCELLED", "OPEN_ORDER_STATUSES", "ensure_order_is_open"]

LINE_WAITING = OrderLineStatus.CHO_LAM.value
LINE_CONFIRMED = OrderLineStatus.DA_XAC_NHAN_XONG.value
LINE_SERVED = OrderLineStatus.DA_PHUC_VU.value
LINE_FORWARD = {LINE_WAITING: LINE_CONFIRMED, LINE_CONFIRMED: LINE_SERVED}
HOLD_ACTIVE = "Đang giữ"
HOLD_RELEASED = "Đã hủy"
HOLD_SENT = "Đã gửi"
REASON_LIMIT = 255


def _dialect_name(session: AsyncSession) -> str:
    try:
        bind = session.get_bind()
        if bind is not None:
            return bind.dialect.name
    except Exception:  # pragma: no cover - defensive, mirrors inventory.stock
        pass
    return "sqlite"


async def _claim_display_number(session: AsyncSession, bd: date) -> int:
    """Claim the next order number for a Business Date (FR-SALE-04).

    On MySQL the counter is bumped in its own committed transaction on a separate
    connection, so a rollback of the order transaction cannot hand the number back.
    """
    if _dialect_name(session) == "mysql":
        from app.core.database import get_engine

        params = {"bd": bd.isoformat()}
        async with get_engine().begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO DEM_ORDER (BusinessDate, SoDaCap) VALUES (:bd, 1) "
                    "ON DUPLICATE KEY UPDATE SoDaCap = SoDaCap + 1"
                ),
                params,
            )
            result = await conn.execute(
                text("SELECT SoDaCap FROM DEM_ORDER WHERE BusinessDate = :bd"), params
            )
            return int(result.scalar_one())

    counter = (
        await session.execute(select(DemOrder).where(DemOrder.business_date == bd))
    ).scalar_one_or_none()
    if counter is None:
        counter = DemOrder(business_date=bd, count=1)
        session.add(counter)
    else:
        counter.count = int(counter.count) + 1
    await session.flush()
    return int(counter.count)


async def next_display_code(session: AsyncSession, bd: date) -> str:
    number = await _claim_display_number(session, bd)
    return f"ORD-{bd.strftime('%d%m%y')}-{number:03d}"


async def create_selection(
    session: AsyncSession,
    actor_id: int,
    selection_id: str | None = None,
    *,
    table_id: int | None = None,
    order_id: int | None = None,
) -> str:
    """Create a client selection token or verify that a supplied token is reusable."""
    if selection_id is None:
        return uuid4().hex
    if not selection_id or len(selection_id) > 64:
        raise BusinessRuleError("Mã lượt chọn không hợp lệ.")
    from app.modules.sales.holds import list_holds

    token_owner = (
        await session.execute(
            select(ItemHold.owner_id).where(ItemHold.selection_id == selection_id).limit(1)
        )
    ).scalar_one_or_none()
    if token_owner is not None and token_owner != actor_id:
        raise NotFoundError("Không tìm thấy lượt chọn.")
    lines = await list_holds(session, actor_id, selection_id)
    if lines and any(line.table_id != table_id or line.order_id != order_id for line in lines):
        raise BusinessRuleError("Lượt chọn không khớp order hoặc bàn.")
    return selection_id


# --- what may be ordered ---------------------------------------------------------------------


async def dish_block_reason(session: AsyncSession, dish_id: int) -> str | None:
    """Why a dish cannot be sold at all (deleted, draft, manually paused), else None."""
    row = (
        await session.execute(select(Dish.is_deleted, Dish.status).where(Dish.id == dish_id))
    ).one_or_none()
    if row is None or row.is_deleted:
        return "Món không tồn tại hoặc đã bị xóa."
    if row.status == DishStatus.NHAP.value:
        return "Món chưa có công thức (đang ở trạng thái Nháp)."
    if row.status == DishStatus.TAM_DUNG.value:
        return "Món đang tạm dừng phục vụ."
    return None


async def refresh_stock_flags(session: AsyncSession, ingredient_ids: list[int]) -> None:
    """Bring lot statuses and the derived out-of-stock flag of the dishes in line with stock."""
    from app.modules.inventory.service import recompute_automatic_out_of_stock

    config = await get_config(session)
    await refresh_lot_statuses(session, config.expiry_warning_days)
    if ingredient_ids:
        await recompute_automatic_out_of_stock(session, sorted(set(ingredient_ids)))


async def orderable_versions(
    session: AsyncSession, dish_id: int, bd: date, *, check_stock: bool
) -> tuple[DishPriceVersion, Recipe]:
    """The price and recipe versions a new line would be pinned to, or why it is refused.

    A dish is refused when it is deleted, a draft, paused by hand, out of ingredients
    (derived live from unexpired, unheld lots), or has no active price or recipe.
    """
    reason = await dish_block_reason(session, dish_id)
    if reason is not None:
        raise BusinessRuleError(reason)
    price = await active_price_version(session, dish_id, bd)
    if price is None:
        raise BusinessRuleError("Món chưa có giá.")
    recipe = await active_recipe(session, dish_id, bd)
    if recipe is None:
        raise BusinessRuleError("Món chưa có công thức.")
    if check_stock and await dish_is_out_of_stock(session, dish_id):
        raise BusinessRuleError("Món đã hết nguyên liệu.")
    return price, recipe


async def ensure_stock_for(session: AsyncSession, wanted: list[tuple[int, int]]) -> None:
    """All-or-nothing availability check for (recipe_id, portions) pairs, expired lots excluded."""
    need: dict[int, Decimal] = {}
    for recipe_id, portions in wanted:
        for item in await recipe_items(session, recipe_id):
            need[item.ingredient_id] = need.get(item.ingredient_id, Decimal(0)) + (
                Decimal(str(item.quantity)) * portions
            )
    available = await sellable_available(session, list(need))
    if any(available[ingredient_id] < quantity for ingredient_id, quantity in need.items()):
        raise BusinessRuleError("Không đủ tồn kho.")


async def _check_dine_in_table(session: AsyncSession, table_id: int | None) -> DiningTable | None:
    """A new dine-in order needs a free table (FR-CAT-18); the row is locked for the check."""
    if table_id is None:
        raise BusinessRuleError("Order tại chỗ cần chọn bàn.")
    table = await lock_table(session, table_id)
    if (
        table is None
        or table.is_deleted
        or table.status != TableStatus.TRONG.value
        or table.serving_order_id is not None
    ):
        raise BusinessRuleError("Bàn không khả dụng.")
    return table


def _occupy(table: DiningTable, order: Order) -> None:
    table.status = TableStatus.DANG_PHUC_VU.value
    table.serving_order_id = order.id


def _check_addon_table(table: DiningTable | None, order: Order) -> None:
    """Add-ons only reach an order whose table still serves exactly that order (FR-SALE-06)."""
    if (
        table is None
        or table.is_deleted
        or table.status != TableStatus.DANG_PHUC_VU.value
        or table.serving_order_id != order.id
    ):
        raise BusinessRuleError("Bàn đã được giải phóng hoặc không còn phục vụ order này.")


def _order_after_submit(order: Order, lines: list[OrderLine]) -> dict[str, Any]:
    return {
        "TrangThai": order.status,
        "TongTien": float(order.total or 0),
        "Dong": [
            {"MaChiTietOrder": line.id, "MaMon": line.dish_id, "SoLuong": int(line.quantity)}
            for line in lines
        ],
    }


# --- selection submit ------------------------------------------------------------------------


def _hold_local_naive(moment: datetime) -> datetime:
    return business_date.naive_local(moment)


async def _selection_result(
    session: AsyncSession, holds: list[ItemHold], *, reconfirm: bool
) -> dict:
    line_ids = [hold.order_line_id for hold in holds if hold.order_line_id is not None]
    lines = (
        list(
            (
                await session.execute(
                    select(OrderLine).where(OrderLine.id.in_(line_ids)).order_by(OrderLine.id)
                )
            )
            .scalars()
            .all()
        )
        if line_ids
        else []
    )
    order = await session.get(Order, lines[0].order_id) if lines else None
    stale = [
        {"MaGiuCho": hold.id, "MaMon": hold.dish_id}
        for hold in holds
        if hold.order_line_id is None and hold.send_request_id is not None
    ]
    return {
        "order": order,
        "lines": lines,
        "stale": stale,
        "CanXacNhanLai": reconfirm or bool(stale),
    }


async def submit_selection(
    session: AsyncSession,
    actor_id: int,
    selection_id: str,
    send_request_id: str,
) -> dict:
    """Atomically turn a selection's held lot quantities into order deductions.

    All-or-nothing (FR-SALE-05): if any held dish changed price or recipe, was deleted, paused
    or is still a draft, nothing is sent; the affected holds are released and the staff
    confirm the new content before sending again.
    """
    from app.modules.sales.holds import reallocate_expired_hold

    if not send_request_id or len(send_request_id) > 100:
        raise BusinessRuleError("Mã yêu cầu gửi không hợp lệ.")

    # Lock first to serialize requests. Existing idempotency keys replay even if a
    # stocktake began after the original send; new sends check the active flag below.
    config = await lock_stocktake_gate(session, allow_active=True)
    query = (
        select(ItemHold)
        .where(ItemHold.selection_id == selection_id, ItemHold.owner_id == actor_id)
        .order_by(ItemHold.id)
    )
    if _dialect_name(session) == "mysql":
        query = query.with_for_update().execution_options(populate_existing=True)
    selection_holds = list((await session.execute(query)).scalars().all())
    if not selection_holds:
        raise NotFoundError("Không tìm thấy lượt chọn.")

    all_key_rows = list(
        (
            await session.execute(
                select(ItemHold)
                .where(ItemHold.send_request_id == send_request_id)
                .order_by(ItemHold.id)
            )
        )
        .scalars()
        .all()
    )
    if all_key_rows:
        if any(
            hold.owner_id != actor_id or hold.selection_id != selection_id for hold in all_key_rows
        ):
            raise ConflictError("Mã yêu cầu gửi đã được dùng cho lượt chọn khác.")
        return await _selection_result(session, all_key_rows, reconfirm=False)

    await lock_stocktake_gate(session)

    open_holds = [hold for hold in selection_holds if hold.status == HOLD_ACTIVE]
    if not open_holds:
        raise BusinessRuleError("Lượt chọn không còn món đang giữ.")
    table_id = open_holds[0].table_id
    order_id = open_holds[0].order_id
    if any(hold.table_id != table_id or hold.order_id != order_id for hold in open_holds):
        raise BusinessRuleError("Lượt chọn không khớp order hoặc bàn.")

    moment = business_date.now()
    now = _hold_local_naive(moment)
    start = await effective_business_day_start(session, moment)
    bd = business_date.business_date_of(moment, start)
    order: Order | None = None
    if order_id is not None:
        order = await lock_order(session, order_id)
        ensure_order_is_open(order)
        if order.table_id is None or order.table_id != table_id:
            raise BusinessRuleError("Order không còn thuộc bàn đã chọn.")
    table: DiningTable | None = None
    if table_id is not None:
        table = (
            await lock_table(session, table_id)
            if order is not None
            else await _check_dine_in_table(session, table_id)
        )
        if order is not None:
            _check_addon_table(table, order)

    # Lock active version rows by dish id before ingredients. Catalog apply-now updates
    # those version rows before it locks recipe ingredients, so this order avoids cycles.
    current_versions: dict[int, tuple[DishPriceVersion | None, Recipe | None]] = {}
    for dish_id in sorted({hold.dish_id for hold in open_holds}):
        price = await active_price_version_for_update(session, dish_id, bd)
        recipe = await active_recipe_for_update(session, dish_id, bd)
        current_versions[dish_id] = (price, recipe)

    # Take all ingredient locks in deterministic order before touching allocations.
    ingredient_ids: list[int] = []
    for hold in open_holds:
        ingredient_ids.extend(
            item.ingredient_id for item in await recipe_items(session, hold.recipe_id)
        )
    await lock_ingredients(session, ingredient_ids)
    await refresh_lot_statuses(session, config.expiry_warning_days)

    stale_holds: list[ItemHold] = []
    for hold in open_holds:
        price, recipe = current_versions[hold.dish_id]
        if (
            price is None
            or recipe is None
            or price.id != hold.price_version_id
            or recipe.id != hold.recipe_id
            or await dish_block_reason(session, hold.dish_id) is not None
        ):
            hold.status = HOLD_RELEASED
            hold.send_request_id = send_request_id
            hold.send_line_id = str(hold.id)
            stale_holds.append(hold)

    if stale_holds:
        await session.flush()
        return await _selection_result(session, stale_holds, reconfirm=True)

    if order is None:
        # No table is a takeaway order; a table is occupied only in this transaction.
        order_type = OrderType.TAI_CHO.value if table_id is not None else OrderType.MANG_VE.value
        display_code = await next_display_code(session, bd)
        order = Order(
            business_date=bd,
            table_id=table_id,
            order_type=order_type,
            status=OrderStatus.DANG_MO.value,
            created_by=actor_id,
            display_code=display_code,
            created_at=now,
        )
        session.add(order)
        await session.flush()
        if table is not None:
            _occupy(table, order)

    created_lines: list[OrderLine] = []
    touched_ingredients: list[int] = []
    for hold in open_holds:
        # Reallocate only an expired line, immediately before converting its lots.
        if hold.expires_at <= now:
            await reallocate_expired_hold(session, actor_id, hold.id)
        if hold.expires_at <= now:
            raise BusinessRuleError("Giữ chỗ đã hết hạn, vui lòng chọn lại món.")
        recipe_rows = await recipe_items(session, hold.recipe_id)
        expected = {
            item.ingredient_id: Decimal(str(item.quantity)) * int(hold.quantity)
            for item in recipe_rows
        }
        allocations_query = select(ItemHoldLot).where(ItemHoldLot.hold_id == hold.id)
        if _dialect_name(session) == "mysql":
            allocations_query = allocations_query.with_for_update().execution_options(
                populate_existing=True
            )
        allocations = list((await session.execute(allocations_query)).scalars().all())
        held_by_ingredient: dict[int, Decimal] = {}
        for allocation in allocations:
            lot = await session.get(IngredientLot, allocation.lot_id)
            if lot is None or lot.ingredient_id not in expected:
                raise BusinessRuleError("Phân bổ giữ chỗ không còn hợp lệ.")
            expiry = (
                datetime.combine(lot.expiry_date + timedelta(days=1), time.min)
                if lot.expiry_date is not None
                else None
            )
            if expiry is not None and expiry <= now:
                raise BusinessRuleError("Lô nguyên liệu đã hết hạn, vui lòng gửi lại món.")
            held = Decimal(str(allocation.quantity_held))
            if Decimal(str(lot.quantity_remaining)) < held:
                raise BusinessRuleError("Tồn lô không đủ để hoàn tất món đã giữ.")
            held_by_ingredient[lot.ingredient_id] = (
                held_by_ingredient.get(lot.ingredient_id, Decimal(0)) + held
            )
        if held_by_ingredient != expected:
            raise BusinessRuleError("Phân bổ giữ chỗ không khớp công thức món.")

        price, recipe = current_versions[hold.dish_id]
        if price is None or recipe is None:
            raise BusinessRuleError("Phiên bản món đã thay đổi, vui lòng xác nhận lại.")
        line = OrderLine(
            order_id=order.id,
            dish_id=hold.dish_id,
            quantity=hold.quantity,
            unit_price=Decimal(str(price.price)),
            total=Decimal(str(price.price)) * int(hold.quantity),
            price_version_id=price.id,
            recipe_id=recipe.id,
            note=hold.note,
            status=LINE_WAITING,
            added_at=now,
        )
        session.add(line)
        await session.flush()
        for allocation in allocations:
            lot = await session.get(IngredientLot, allocation.lot_id)
            if lot is None:  # guarded above; retain the check across ORM reloads
                raise BusinessRuleError("Lô nguyên liệu không còn tồn tại.")
            ingredient = await lock_ingredient(session, lot.ingredient_id)
            held = Decimal(str(allocation.quantity_held))
            lot.quantity_remaining = Decimal(str(lot.quantity_remaining)) - held
            ingredient.stock_qty = Decimal(str(ingredient.stock_qty)) - held
            session.add(
                StockMovement(
                    ingredient_id=ingredient.id,
                    lot_id=lot.id,
                    kind=StockMovementType.TRU_TU_DONG,
                    qty=-held,
                    balance_after=ingredient.stock_qty,
                    business_date=bd,
                    order_line_id=line.id,
                    performed_by=actor_id,
                )
            )
            touched_ingredients.append(ingredient.id)
        hold.status = HOLD_SENT
        hold.send_request_id = send_request_id
        hold.send_line_id = str(hold.id)
        hold.order_line_id = line.id
        created_lines.append(line)

    before = None if order_id is None else {"TongTien": float(order.total or 0)}
    await refresh_order_total(session, order)
    await write_kitchen_ticket(session, order, created_lines)
    await session.flush()
    await refresh_stock_flags(session, touched_ingredients)
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action="SUBMIT_ORDER" if order_id is None else "ADD_ORDER_LINES",
        before=before,
        after=_order_after_submit(order, created_lines),
    )
    await session.flush()
    return await _selection_result(
        session, created_lines_to_holds(open_holds, created_lines), reconfirm=False
    )


def created_lines_to_holds(holds: list[ItemHold], lines: list[OrderLine]) -> list[ItemHold]:
    """Return the submitted hold rows in the same order as their created order lines."""
    line_ids = {line.id for line in lines}
    return [hold for hold in holds if hold.order_line_id in line_ids]


# --- direct submit / add line ----------------------------------------------------------------


def _line_from(dish_id: int, quantity: int, price: DishPriceVersion, recipe: Recipe) -> OrderLine:
    unit_price = Decimal(str(price.price))
    return OrderLine(
        dish_id=dish_id,
        quantity=quantity,
        unit_price=unit_price,
        total=unit_price * quantity,
        price_version_id=price.id,
        recipe_id=recipe.id,
        status=LINE_WAITING,
    )


async def _draw_line_stock(
    session: AsyncSession, line: OrderLine, quantity: int, bd: date, *, actor_id: int | None
) -> None:
    if line.recipe_id is None:
        return
    items = await recipe_items(session, line.recipe_id)
    await lock_ingredients(session, [item.ingredient_id for item in items])
    for item in sorted(items, key=lambda row: row.ingredient_id):
        await apply_stock_movement(
            session,
            StockChange(
                ingredient_id=int(item.ingredient_id),
                delta=-(Decimal(str(item.quantity)) * quantity),
                kind=StockMovementType.TRU_TU_DONG,
                source_order_line_id=line.id,
                business_date=bd,
            ),
            actor_id=actor_id,
        )


async def _return_line_stock(
    session: AsyncSession,
    line: OrderLine,
    dishes: Decimal,
    *,
    business_date_value: date,
    actor_id: int | None = None,
) -> None:
    """Hand `dishes` portions of this line back, lot by lot, mirroring its draw ledger.

    The amount still outstanding on each lot is what that lot gave minus what it already got
    back (BR-LOT-01): the return lands on the very lot that was drawn, even one that has
    expired since, and two draws that shared a lot are never counted twice.
    """
    if line.recipe_id is None or dishes <= 0:
        return
    needed: dict[int, Decimal] = {}
    for item in await recipe_items(session, line.recipe_id):
        needed[item.ingredient_id] = needed.get(item.ingredient_id, Decimal(0)) + (
            Decimal(str(item.quantity)) * dishes
        )
    await lock_ingredients(session, list(needed))
    ledger = list(
        (
            await session.execute(
                select(StockMovement)
                .where(StockMovement.order_line_id == line.id, StockMovement.lot_id.is_not(None))
                .order_by(StockMovement.id.asc())
            )
        )
        .scalars()
        .all()
    )
    outstanding: dict[int, Decimal] = {}
    draws: list[StockMovement] = []
    for movement in ledger:
        lot_key = int(movement.lot_id)  # type: ignore[arg-type]  # filtered NOT NULL above
        amount = Decimal(str(movement.qty))
        if amount < 0:
            draws.append(movement)
            outstanding[lot_key] = outstanding.get(lot_key, Decimal(0)) - amount
        elif movement.kind == StockMovementType.HOAN_KHO:
            outstanding[lot_key] = outstanding.get(lot_key, Decimal(0)) - amount

    for ingredient_id, amount in needed.items():
        remaining = amount
        ingredient = await lock_ingredient(session, ingredient_id)
        for draw in draws:
            if remaining <= 0:
                break
            if draw.ingredient_id != ingredient_id:
                continue
            lot_key = int(draw.lot_id)  # type: ignore[arg-type]
            take = min(outstanding.get(lot_key, Decimal(0)), remaining)
            if take <= 0:
                continue
            outstanding[lot_key] -= take
            remaining -= take
            lot = await session.get(IngredientLot, lot_key)
            if lot is not None:
                lot.quantity_remaining = Decimal(str(lot.quantity_remaining)) + take
            ingredient.stock_qty = Decimal(str(ingredient.stock_qty)) + take
            session.add(
                StockMovement(
                    ingredient_id=ingredient_id,
                    lot_id=lot_key,
                    kind=StockMovementType.HOAN_KHO,
                    qty=take,
                    balance_after=ingredient.stock_qty,
                    business_date=business_date_value,
                    order_line_id=line.id,
                    performed_by=actor_id,
                )
            )
        if remaining > 0:
            logger.warning("Line %s had less drawn stock than it should return", line.id)
    await session.flush()
    await refresh_stock_flags(session, list(needed))


async def _release_addon_holds(session: AsyncSession, order_id: int) -> None:
    """Unsent add-on selections of a finished order stop holding stock (FR-SALE-11, FR-CAT-18)."""
    await session.execute(
        update(ItemHold)
        .where(ItemHold.order_id == order_id, ItemHold.status == HOLD_ACTIVE)
        .values(status=HOLD_RELEASED)
        .execution_options(synchronize_session="fetch")
    )


def _line_state(line: OrderLine) -> dict[str, Any]:
    return {
        "MaChiTietOrder": line.id,
        "MaMon": line.dish_id,
        "SoLuong": int(line.quantity),
        "TrangThai": line.status,
    }


async def submit_order(
    session: AsyncSession, payload: dict, *, actor_id: int | None = None
) -> dict:
    """Create an order and draw its stock in one step (no hold stage), all-or-nothing."""
    config = await lock_stocktake_gate(session)
    now = business_date.now()
    start = await effective_business_day_start(session, now)
    bd = business_date.business_date_of(now, start)
    order_type = payload.get("order_type") or OrderType.TAI_CHO.value
    table_id = payload.get("table_id")
    lines_in: list[dict] = payload.get("lines") or []
    if not lines_in:
        raise BusinessRuleError("Order cần ít nhất một món.")
    if order_type not in (OrderType.TAI_CHO.value, OrderType.MANG_VE.value):
        raise BusinessRuleError("Loại đơn không hợp lệ.")

    wanted: list[tuple[int, int, str | None]] = []
    for line_input in lines_in:
        dish_id = line_input.get("dish_id") or line_input.get("MaMon")
        if dish_id is None:
            raise BusinessRuleError("Thiếu mã món.")
        quantity = int(line_input.get("quantity") or line_input.get("SoLuong") or 1)
        if quantity < 1:
            raise BusinessRuleError("Số lượng món phải lớn hơn 0.")
        wanted.append((int(dish_id), quantity, line_input.get("note") or line_input.get("GhiChu")))

    ingredient_ids: list[int] = []
    for dish_id, _, _ in wanted:
        recipe = await active_recipe(session, dish_id, bd)
        if recipe is not None:
            ingredient_ids.extend(
                item.ingredient_id for item in await recipe_items(session, recipe.id)
            )
    await lock_ingredients(session, ingredient_ids)
    await refresh_lot_statuses(session, config.expiry_warning_days)

    # Validate every line before anything is written: one bad line refuses the whole order.
    resolved: list[tuple[int, int, str | None, DishPriceVersion, Recipe]] = []
    problems: list[str] = []
    for dish_id, quantity, note in wanted:
        try:
            price, recipe = await orderable_versions(session, dish_id, bd, check_stock=True)
        except BusinessRuleError as error:
            problems.append(f"Món {dish_id}: {error.message}")
            continue
        resolved.append((dish_id, quantity, note, price, recipe))
    if problems:
        raise BusinessRuleError(" ".join(problems))
    await ensure_stock_for(
        session, [(recipe.id, quantity) for _, quantity, _, _, recipe in resolved]
    )

    table: DiningTable | None = None
    if order_type == OrderType.MANG_VE.value:
        table_id = None
    else:
        table = await _check_dine_in_table(session, table_id)

    display_code = await next_display_code(session, bd)
    order = Order(
        business_date=bd,
        table_id=table_id,
        order_type=order_type,
        status=OrderStatus.DANG_MO.value,
        created_by=actor_id,
        display_code=display_code,
        created_at=business_date.naive_local(now),
    )
    session.add(order)
    await session.flush()
    if table is not None:
        _occupy(table, order)

    created_lines: list[OrderLine] = []
    for dish_id, quantity, note, price, recipe in resolved:
        line = _line_from(dish_id, quantity, price, recipe)
        line.order_id = order.id
        line.note = note
        session.add(line)
        await session.flush()
        await _draw_line_stock(session, line, quantity, bd, actor_id=actor_id)
        created_lines.append(line)

    await refresh_order_total(session, order)
    await write_kitchen_ticket(session, order, created_lines)
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action="SUBMIT_ORDER",
        after=_order_after_submit(order, created_lines),
    )
    await session.flush()
    return {"order": order, "lines": created_lines, "rejected": []}


async def _locked_line(session: AsyncSession, order_id: int, line_id: int) -> OrderLine:
    """The line, only if it belongs to this order (a line id from another order is a 404)."""
    line = (
        await session.execute(
            select(OrderLine)
            .where(OrderLine.id == line_id, OrderLine.order_id == order_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if line is None:
        raise NotFoundError("Dòng món không tồn tại.")
    return line


async def add_line(
    session: AsyncSession,
    order_id: int,
    dish_id: int,
    quantity: int,
    note: str | None = None,
    *,
    actor_id: int | None = None,
) -> OrderLine:
    """Add a dish to an open order, priced by the version effective now (FR-SALE-06)."""
    config = await lock_stocktake_gate(session)
    order = await lock_order(session, order_id)
    ensure_order_is_open(order)
    if quantity < 1:
        raise BusinessRuleError("Số lượng món phải lớn hơn 0.")
    if order.table_id is None:
        raise BusinessRuleError("Order mang về không gọi thêm được, hãy tạo order mới.")
    _check_addon_table(await lock_table(session, order.table_id), order)

    bd = await current_business_date(session)
    recipe = await active_recipe(session, dish_id, bd)
    if recipe is not None:
        await lock_ingredients(
            session, [item.ingredient_id for item in await recipe_items(session, recipe.id)]
        )
    await refresh_lot_statuses(session, config.expiry_warning_days)
    price, recipe = await orderable_versions(session, dish_id, bd, check_stock=True)
    await ensure_stock_for(session, [(recipe.id, quantity)])

    before = {"TongTien": float(order.total or 0)}
    line = _line_from(dish_id, quantity, price, recipe)
    line.order_id = order.id
    line.note = note
    session.add(line)
    await session.flush()
    await _draw_line_stock(session, line, quantity, bd, actor_id=actor_id)
    await refresh_order_total(session, order)
    await write_kitchen_ticket(session, order, [line])
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action="ADD_ORDER_LINES",
        before=before,
        after=_order_after_submit(order, [line]),
    )
    await session.flush()
    return line


async def update_line(
    session: AsyncSession,
    order_id: int,
    line_id: int,
    quantity: int,
    *,
    actor_id: int | None = None,
) -> OrderLine:
    """Change a waiting line's quantity: a decrease hands stock back, an increase draws more."""
    config = await lock_stocktake_gate(session)
    order = await lock_order(session, order_id)
    ensure_order_is_open(order)
    line = await _locked_line(session, order_id, line_id)
    if line.status != LINE_WAITING:
        raise BusinessRuleError("Chỉ sửa món ở trạng thái Chờ làm.")
    if quantity < 1:
        raise BusinessRuleError("Số lượng món phải lớn hơn 0.")
    if line.recipe_id is not None:
        await lock_ingredients(
            session, [item.ingredient_id for item in await recipe_items(session, line.recipe_id)]
        )

    bd = await current_business_date(session)
    before = _line_state(line)
    delta = quantity - int(line.quantity)
    if delta > 0:
        await refresh_lot_statuses(session, config.expiry_warning_days)
        reason = await dish_block_reason(session, line.dish_id)
        if reason is not None:
            raise BusinessRuleError(reason)
        if line.recipe_id is not None:
            await ensure_stock_for(session, [(line.recipe_id, delta)])
        await _draw_line_stock(session, line, delta, bd, actor_id=actor_id)
        line.quantity = quantity
        await write_kitchen_ticket(session, order, [line], quantities={line.id: delta})
    elif delta < 0:
        await _return_line_stock(
            session, line, Decimal(-delta), business_date_value=bd, actor_id=actor_id
        )
        line.quantity = quantity
    line.total = Decimal(str(line.unit_price)) * quantity
    totals_before = float(order.total or 0)
    await refresh_order_total(session, order)
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action="UPDATE_ORDER_LINE",
        before={**before, "TongTien": totals_before},
        after={**_line_state(line), "TongTien": float(order.total or 0)},
    )
    await session.flush()
    return line


async def advance_line_status(
    session: AsyncSession,
    order_id: int,
    line_id: int,
    to_status: str,
    *,
    actor_id: int | None = None,
) -> OrderLine:
    """Chờ làm → Đã xác nhận xong → Đã phục vụ (FR-SALE-09); never on a cancelled order."""
    order = await lock_order(session, order_id)
    if order.status in (OrderStatus.DA_HUY.value, OrderStatus.TU_DONG_DONG.value):
        raise BusinessRuleError("Order đã bị hủy.")
    line = await _locked_line(session, order_id, line_id)
    if LINE_FORWARD.get(line.status) != to_status:
        raise BusinessRuleError(f"Không thể chuyển từ {line.status} sang {to_status}.")
    before = _line_state(line)
    line.status = to_status
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action="UPDATE_ORDER_LINE_STATUS",
        before=before,
        after=_line_state(line),
    )
    await session.flush()
    return line


async def cancel_line(
    session: AsyncSession,
    order_id: int,
    line_id: int,
    reason: str,
    *,
    actor_id: int | None = None,
) -> OrderLine:
    """FR-SALE-10/11: cancel a waiting line, return its stock, auto-close an emptied order."""
    await lock_stocktake_gate(session)
    order = await lock_order(session, order_id)
    ensure_order_is_open(order)
    line = await _locked_line(session, order_id, line_id)
    if line.status != LINE_WAITING:
        raise BusinessRuleError("Chỉ hủy món ở trạng thái Chờ làm.")
    if not reason or not reason.strip():
        raise BusinessRuleError("Cần lý do hủy.")
    if line.recipe_id is not None:
        await lock_ingredients(
            session, [item.ingredient_id for item in await recipe_items(session, line.recipe_id)]
        )

    bd = await current_business_date(session)
    before = _line_state(line)
    totals_before = float(order.total or 0)
    await _return_line_stock(
        session, line, Decimal(line.quantity), business_date_value=bd, actor_id=actor_id
    )
    line.status = LINE_CANCELLED
    await session.flush()
    await refresh_order_total(session, order)

    remaining = (
        await session.execute(
            select(OrderLine.id)
            .where(OrderLine.order_id == order.id, OrderLine.status != LINE_CANCELLED)
            .limit(1)
        )
    ).first()
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action="CANCEL_ORDER_LINE",
        before={**before, "TongTien": totals_before},
        after={**_line_state(line), "TongTien": float(order.total or 0)},
        reason=reason.strip(),
    )
    if remaining is None:
        # The last line is gone: the order closes by itself, the table waits for the cashier
        # to confirm the guests left (FR-SALE-11, FR-CAT-18).
        order.status = OrderStatus.TU_DONG_DONG.value
        order.updated_at = local_now()
        order.closed_at = order.updated_at
        order.cancel_reason = reason.strip()[:500]
        await _release_addon_holds(session, order.id)
        audit_order(
            session,
            order,
            actor_id=actor_id,
            action="AUTO_CLOSE_ORDER",
            before={"TrangThai": OrderStatus.DANG_MO.value},
            after={"TrangThai": order.status},
            reason=reason.strip(),
        )
    await session.flush()
    return line


async def move_table(
    session: AsyncSession, order_id: int, to_table_id: int, *, actor_id: int | None = None
) -> Order:
    """FR-SALE-12: move an open dine-in order to another free table."""
    order = await lock_order(session, order_id)
    ensure_order_is_open(order)
    if order.table_id is None:
        raise BusinessRuleError("Order mang về không có bàn để đổi.")
    if to_table_id == order.table_id:
        raise BusinessRuleError("Bàn đích trùng bàn hiện tại.")
    # Both rows are locked in ascending id so two concurrent moves cannot deadlock.
    locked = {
        table_id: await lock_table(session, table_id)
        for table_id in sorted({order.table_id, to_table_id})
    }
    source, destination = locked[order.table_id], locked[to_table_id]
    if destination is None or destination.is_deleted:
        raise BusinessRuleError("Bàn đích không tồn tại.")
    if destination.status != TableStatus.TRONG.value or destination.serving_order_id is not None:
        raise BusinessRuleError("Bàn đích đang bận.")
    if (
        source is None
        or source.status != TableStatus.DANG_PHUC_VU.value
        or source.serving_order_id != order.id
    ):
        raise BusinessRuleError("Bàn đã được giải phóng, không thể đổi bàn cho order này.")

    source_id = source.id
    source.status = TableStatus.TRONG.value
    source.serving_order_id = None
    destination.status = TableStatus.DANG_PHUC_VU.value
    destination.serving_order_id = order.id
    order.table_id = to_table_id
    order.updated_at = local_now()
    session.add(
        TableMoveLog(
            order_id=order.id, from_table=source_id, to_table=to_table_id, performed_by=actor_id
        )
    )
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action="MOVE_ORDER_TABLE",
        before={"MaBan": source_id},
        after={"MaBan": to_table_id},
    )
    await session.flush()
    return order


async def cancel_order(
    session: AsyncSession,
    order_id: int,
    reason: str,
    *,
    actor_id: int | None = None,
    guests_left: bool = False,
) -> Order:
    """FR-SALE-27…30: cancel a whole open order; waiting lines go back to stock.

    The table is only freed when the manager says the guests already left; otherwise the
    cashier confirms it (FR-CAT-18).
    """
    await lock_stocktake_gate(session)
    from app.modules.sales.payments import expire_stale_qr

    await expire_stale_qr(session)
    order = await lock_order(session, order_id)
    ensure_order_is_open(order)
    if not reason or not reason.strip():
        raise BusinessRuleError("Cần lý do hủy order.")

    lines = list(
        (
            await session.execute(
                select(OrderLine).where(OrderLine.order_id == order.id).order_by(OrderLine.id)
            )
        )
        .scalars()
        .all()
    )
    ingredient_ids: list[int] = []
    for line in lines:
        if line.status == LINE_WAITING and line.recipe_id is not None:
            ingredient_ids.extend(
                item.ingredient_id for item in await recipe_items(session, line.recipe_id)
            )
    await lock_ingredients(session, ingredient_ids)
    bd = await current_business_date(session)
    before = {"TrangThai": order.status, "TongTien": float(order.total or 0)}
    for line in lines:
        if line.status == LINE_WAITING:
            await _return_line_stock(
                session,
                line,
                Decimal(line.quantity),
                business_date_value=bd,
                actor_id=actor_id,
            )
        if line.status != LINE_CANCELLED:
            line.status = LINE_CANCELLED
    order.status = OrderStatus.DA_HUY.value
    order.updated_at = local_now()
    order.closed_at = order.updated_at
    order.cancel_reason = reason.strip()[:500]
    await _release_addon_holds(session, order.id)
    if guests_left and order.table_id is not None and actor_id is not None:
        from app.modules.catalog.service import release_table

        await release_table(session, actor_id, order.table_id, order.id)
    audit_order(
        session,
        order,
        actor_id=actor_id,
        action="CANCEL_ORDER",
        before=before,
        after={"TrangThai": order.status, "GiaiPhongBan": guests_left},
        reason=reason.strip(),
    )
    await session.flush()
    return order
