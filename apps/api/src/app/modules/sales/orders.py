"""Order lifecycle — submit, lines, stock, table moves and cancellation (FR-SALE-01…13, 20, 24, 26).

Stock is drawn through `inventory.stock.apply_stock_movement` and returned through the
quantity-based helper below. Returning by *current line quantity* (not by replaying every
original ledger row) is what keeps a reduce-then-cancel sequence from returning more than
was taken: the two operations together return exactly the quantity the line was charged for.
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, ConflictError, NotFoundError
from app.modules.catalog.models import DiningTable, DishPriceVersion, Ingredient, Recipe
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
    lock_ingredient,
    lock_ingredients,
    lock_stocktake_gate,
)
from app.modules.sales.models import (
    DemOrder,
    ItemHold,
    ItemHoldLot,
    KitchenTicket,
    Order,
    OrderLine,
)
from app.modules.sales.tickets import render_ticket
from app.modules.settings.service import effective_business_day_start
from app.shared import business_date
from app.shared.audit import SystemAuditLog
from app.shared.enums import StockMovementType

OPEN_ORDER_STATUSES: frozenset[str] = frozenset({"Đang mở"})
LINE_WAITING = "Chờ"
LINE_CONFIRMED = "Đã xác nhận xong"
LINE_SERVED = "Đã phục vụ"
LINE_CANCELLED = "Đã hủy"
LINE_FORWARD = {LINE_WAITING: LINE_CONFIRMED, LINE_CONFIRMED: LINE_SERVED}
HOLD_ACTIVE = "Đang giữ"
HOLD_RELEASED = "Đã hủy"
HOLD_SENT = "Đã gửi"


def ensure_order_is_open(order: Order) -> None:
    """The single choke point for FR-SALE-20/25: settled orders reject every mutation."""
    if order.status not in OPEN_ORDER_STATUSES:
        raise BusinessRuleError("Order đã đóng.")


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


def _hold_local_naive(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment
    return moment.astimezone(business_date.VN_TZ).replace(tzinfo=None)


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
    """Atomically turn a selection's held lot quantities into order deductions."""
    from app.modules.sales.holds import reallocate_expired_hold

    if not send_request_id or len(send_request_id) > 100:
        raise BusinessRuleError("Mã yêu cầu gửi không hợp lệ.")

    # Lock first to serialize requests. Existing idempotency keys replay even if a
    # stocktake began after the original send; new sends check the active flag below.
    await lock_stocktake_gate(session, allow_active=True)
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
    order = await session.get(Order, order_id) if order_id is not None else None
    if order_id is not None and (order is None or order.status not in OPEN_ORDER_STATUSES):
        raise BusinessRuleError("Order không còn mở.")
    if order is not None and order.table_id != table_id:
        raise BusinessRuleError("Order không còn thuộc bàn đã chọn.")

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

    stale_holds: list[ItemHold] = []
    for hold in open_holds:
        price, recipe = current_versions[hold.dish_id]
        if (
            price is None
            or recipe is None
            or price.id != hold.price_version_id
            or recipe.id != hold.recipe_id
        ):
            hold.status = HOLD_RELEASED
            hold.send_request_id = send_request_id
            hold.send_line_id = str(hold.id)
            stale_holds.append(hold)

    ready_holds = [hold for hold in open_holds if hold not in stale_holds]
    if not ready_holds:
        await session.flush()
        return await _selection_result(session, stale_holds, reconfirm=True)

    if order is None:
        # No table is a takeaway order; a table is occupied only in this transaction.
        order_type = "Tại chỗ" if table_id is not None else "Mang về"
        display_code = await next_display_code(session, bd)
        order = Order(
            business_date=bd,
            table_id=table_id,
            order_type=order_type,
            status="Đang mở",
            created_by=actor_id,
            display_code=display_code,
            created_at=moment,
        )
        session.add(order)
        await session.flush()
    if table_id is not None:
        table = await session.get(DiningTable, table_id)
        allowed_statuses = {"Đang phục vụ"} if order_id is not None else {"Trống"}
        if table is None or table.is_deleted or table.status not in allowed_statuses:
            raise BusinessRuleError("Bàn không khả dụng.")
        table.status = "Đang phục vụ"

    created_lines: list[OrderLine] = []
    for hold in ready_holds:
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
                    business_date=bd,
                    order_line_id=line.id,
                    performed_by=actor_id,
                )
            )
        hold.status = HOLD_SENT
        hold.send_request_id = send_request_id
        hold.send_line_id = str(hold.id)
        hold.order_line_id = line.id
        created_lines.append(line)

    if not created_lines:
        if order_id is None:
            await session.delete(order)
        await session.flush()
        return await _selection_result(session, stale_holds, reconfirm=True)
    if order_id is None:
        write_kitchen_ticket(session, order, created_lines)
    else:
        write_kitchen_ticket(session, order, created_lines)
    await session.flush()
    return await _selection_result(
        session,
        [*created_lines_to_holds(ready_holds, created_lines), *stale_holds],
        reconfirm=bool(stale_holds),
    )


def created_lines_to_holds(holds: list[ItemHold], lines: list[OrderLine]) -> list[ItemHold]:
    """Return the submitted hold rows in the same order as their created order lines."""
    line_ids = {line.id for line in lines}
    return [hold for hold in holds if hold.order_line_id in line_ids]


def write_kitchen_ticket(
    session: AsyncSession, order: Order, lines: list[OrderLine]
) -> KitchenTicket:
    ticket = KitchenTicket(
        order_id=order.id,
        status="Chờ in",
        print_status="Chờ in",
        print_count=1,
        content=render_ticket(order, lines),
    )
    session.add(ticket)
    return ticket


async def _resolve_line_inputs(
    session: AsyncSession, dish_id: int, quantity: int, bd: date
) -> tuple[OrderLine, bool, str | None]:
    """Snapshot price/recipe for a dish; the flag reports whether the line can be ordered."""
    price_version = await active_price_version(session, dish_id, bd)
    recipe = await active_recipe(session, dish_id, bd)
    line = OrderLine(
        dish_id=dish_id,
        quantity=quantity,
        unit_price=Decimal(str(price_version.price)) if price_version else Decimal("0"),
        total=(Decimal(str(price_version.price)) * quantity) if price_version else Decimal("0"),
        price_version_id=price_version.id if price_version else None,
        recipe_id=recipe.id if recipe else None,
        status=LINE_WAITING,
    )
    if price_version is None:
        return line, False, "Món chưa có giá"
    if recipe is None:
        return line, True, None
    for item in await recipe_items(session, recipe.id):
        ingredient = await session.get(Ingredient, item.ingredient_id)
        needed = Decimal(str(item.quantity)) * quantity
        if ingredient is None or Decimal(str(ingredient.stock_qty)) < needed:
            return line, False, "không đủ tồn kho"
    return line, True, None


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
    """Return the ingredients for `dishes` portions of this line, FIFO per drawn movement."""
    if line.recipe_id is None or dishes <= 0:
        return
    needed: dict[int, Decimal] = {}
    for item in await recipe_items(session, line.recipe_id):
        needed[item.ingredient_id] = needed.get(item.ingredient_id, Decimal(0)) + (
            Decimal(str(item.quantity)) * dishes
        )
    await lock_ingredients(session, list(needed))
    drawings = list(
        (
            await session.execute(
                select(StockMovement)
                .where(StockMovement.order_line_id == line.id, StockMovement.qty < 0)
                .order_by(StockMovement.id.asc())
            )
        )
        .scalars()
        .all()
    )
    # Amount already handed back per ingredient. Returns are always a prefix of the draw
    # sequence, so tracking the running total per ingredient is enough to resume correctly
    # even when several draw movements share one lot.
    returned: dict[int, Decimal] = {}
    reversals = (
        (
            await session.execute(
                select(StockMovement).where(
                    StockMovement.order_line_id == line.id, StockMovement.qty > 0
                )
            )
        )
        .scalars()
        .all()
    )
    for reversal in reversals:
        returned[reversal.ingredient_id] = returned.get(
            reversal.ingredient_id, Decimal(0)
        ) + Decimal(str(reversal.qty))

    for ingredient_id, amount in needed.items():
        remaining = amount
        skip = returned.get(ingredient_id, Decimal(0))
        for movement in drawings:
            if remaining <= 0:
                break
            if movement.ingredient_id != ingredient_id or movement.lot_id is None:
                continue
            drawn = -Decimal(str(movement.qty))
            if drawn <= 0:
                continue
            if skip >= drawn:
                skip -= drawn
                continue
            take = min(drawn - skip, remaining)
            skip = Decimal(0)
            lot = await session.get(IngredientLot, movement.lot_id)
            if lot is not None:
                lot.quantity_remaining = Decimal(str(lot.quantity_remaining)) + take
            ingredient = await session.get(Ingredient, ingredient_id)
            if ingredient is not None:
                ingredient.stock_qty = Decimal(str(ingredient.stock_qty)) + take
            session.add(
                StockMovement(
                    ingredient_id=ingredient_id,
                    lot_id=movement.lot_id,
                    kind=StockMovementType.HOAN_KHO,
                    qty=take,
                    business_date=business_date_value,
                    order_line_id=line.id,
                    performed_by=actor_id,
                )
            )
            returned[movement.lot_id] = returned.get(movement.lot_id, Decimal(0)) + take
            remaining -= take
    await session.flush()


async def _current_business_date(session: AsyncSession) -> date:
    moment = business_date.now()
    start = await effective_business_day_start(session, moment)
    return business_date.business_date_of(moment, start)


async def _set_order_status(session: AsyncSession, order: Order, status: str) -> None:
    order.status = status
    order.updated_at = business_date.now()


async def _free_table(session: AsyncSession, order: Order) -> None:
    if order.table_id is None:
        return
    table = await session.get(DiningTable, order.table_id)
    if table is not None:
        table.status = "Trống"


async def submit_order(
    session: AsyncSession, payload: dict, *, actor_id: int | None = None
) -> dict:
    await lock_stocktake_gate(session)
    now = business_date.now()
    start = await effective_business_day_start(session, now)
    bd = business_date.business_date_of(now, start)
    order_type = payload.get("order_type") or "Tại chỗ"
    table_id = payload.get("table_id")
    lines_in: list[dict] = payload.get("lines") or []
    ingredient_ids: list[int] = []
    for line_input in lines_in:
        dish_id = line_input.get("dish_id") or line_input.get("MaMon")
        if dish_id is None:
            continue
        recipe = await active_recipe(session, int(dish_id), bd)
        if recipe is not None:
            ingredient_ids.extend(
                item.ingredient_id for item in await recipe_items(session, recipe.id)
            )
    await lock_ingredients(session, ingredient_ids)

    if order_type == "Mang về":
        table_id = None
    elif table_id is not None:
        table = await session.get(DiningTable, table_id)
        if table is None or table.is_deleted:
            raise BusinessRuleError("Bàn không tồn tại.")
        table.status = "Đang phục vụ"

    display_code = await next_display_code(session, bd)
    order = Order(
        business_date=bd,
        table_id=table_id,
        order_type=order_type,
        status="Đang mở",
        created_by=actor_id,
        display_code=display_code,
        created_at=now,
    )
    session.add(order)
    await session.flush()

    created_lines: list[OrderLine] = []
    rejected: list[dict] = []
    for line_input in lines_in:
        dish_id = line_input.get("dish_id") or line_input.get("MaMon")
        if dish_id is None:
            continue
        quantity = int(line_input.get("quantity") or line_input.get("SoLuong") or 1)
        note = line_input.get("note") or line_input.get("GhiChu")
        line, ok, reason = await _resolve_line_inputs(session, int(dish_id), quantity, bd)
        if not ok:
            rejected.append({"MaMon": int(dish_id), "reason": reason})
            continue
        line.order_id = order.id
        line.note = note
        session.add(line)
        await session.flush()
        await _draw_line_stock(session, line, quantity, bd, actor_id=actor_id)
        created_lines.append(line)

    if not created_lines:
        await session.delete(order)
        await session.flush()
        raise BusinessRuleError("Không có món nào đủ tồn kho.")

    write_kitchen_ticket(session, order, created_lines)
    await session.flush()
    return {"order": order, "lines": created_lines, "rejected": rejected}


async def add_line(
    session: AsyncSession,
    order_id: int,
    dish_id: int,
    quantity: int,
    note: str | None = None,
    *,
    actor_id: int | None = None,
) -> OrderLine:
    await lock_stocktake_gate(session)
    order = await session.get(Order, order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    ensure_order_is_open(order)

    recipe = await active_recipe(session, dish_id, order.business_date)
    if recipe is not None:
        await lock_ingredients(
            session, [item.ingredient_id for item in await recipe_items(session, recipe.id)]
        )
    line, ok, reason = await _resolve_line_inputs(session, dish_id, quantity, order.business_date)
    if not ok:
        raise BusinessRuleError(
            "Món chưa có giá." if reason == "Món chưa có giá" else "Không đủ tồn kho."
        )
    line.order_id = order.id
    line.note = note
    session.add(line)
    await session.flush()
    await _draw_line_stock(session, line, quantity, order.business_date, actor_id=actor_id)
    write_kitchen_ticket(session, order, [line])
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
    await lock_stocktake_gate(session)
    order = await session.get(Order, order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    ensure_order_is_open(order)
    line = await session.get(OrderLine, line_id)
    if line is None or line.order_id != order_id:
        raise NotFoundError("Dòng món không tồn tại.")
    if line.status != LINE_WAITING:
        raise BusinessRuleError("Chỉ sửa món ở trạng thái Chờ.")
    if line.recipe_id is not None:
        await lock_ingredients(
            session, [item.ingredient_id for item in await recipe_items(session, line.recipe_id)]
        )

    delta = quantity - int(line.quantity)
    if delta > 0:
        _, ok, _reason = await _resolve_line_inputs(
            session, line.dish_id, delta, order.business_date
        )
        if not ok:
            raise BusinessRuleError("Không đủ tồn kho.")
        await _draw_line_stock(session, line, delta, order.business_date, actor_id=actor_id)
        line.quantity = int(line.quantity) + delta
    elif delta < 0:
        current_bd = await _current_business_date(session)
        await _return_line_stock(
            session, line, Decimal(-delta), business_date_value=current_bd, actor_id=actor_id
        )
        line.quantity = quantity
    await session.flush()
    return line


async def advance_line_status(session: AsyncSession, line_id: int, to_status: str) -> OrderLine:
    line = await session.get(OrderLine, line_id)
    if line is None:
        raise NotFoundError("Dòng món không tồn tại.")
    if LINE_FORWARD.get(line.status) != to_status:
        raise BusinessRuleError(f"Không thể chuyển từ {line.status} sang {to_status}.")
    line.status = to_status
    await session.flush()
    return line


async def cancel_line(
    session: AsyncSession, line_id: int, reason: str, *, actor_id: int | None = None
) -> OrderLine:
    await lock_stocktake_gate(session)
    line = await session.get(OrderLine, line_id)
    if line is None:
        raise NotFoundError("Dòng món không tồn tại.")
    if line.status != LINE_WAITING:
        raise BusinessRuleError("Chỉ hủy món ở trạng thái Chờ.")
    order = await session.get(Order, line.order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    ensure_order_is_open(order)
    if not reason or not reason.strip():
        raise BusinessRuleError("Cần lý do hủy.")
    if line.recipe_id is not None:
        await lock_ingredients(
            session, [item.ingredient_id for item in await recipe_items(session, line.recipe_id)]
        )

    current_bd = await _current_business_date(session)
    await _return_line_stock(
        session, line, Decimal(line.quantity), business_date_value=current_bd, actor_id=actor_id
    )
    line.status = LINE_CANCELLED
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CANCEL_ORDER_LINE",
            target_entity="CHI_TIET_ORDER",
            target_id=str(line.id),
            after={"SoLuong": int(line.quantity)},
            reason=reason,
        )
    )
    await session.flush()

    remaining = (
        await session.execute(
            select(OrderLine).where(
                OrderLine.order_id == order.id, OrderLine.status != LINE_CANCELLED
            )
        )
    ).scalar_one_or_none()
    if remaining is None:
        await _set_order_status(session, order, "Tự động đóng")
        await _free_table(session, order)
        await session.flush()
    return line


async def move_table(
    session: AsyncSession, order_id: int, to_table_id: int, *, actor_id: int | None = None
) -> Order:
    order = await session.get(Order, order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    ensure_order_is_open(order)
    destination = await session.get(DiningTable, to_table_id)
    if destination is None or destination.is_deleted:
        raise BusinessRuleError("Bàn đích không tồn tại.")
    if destination.status != "Trống":
        raise BusinessRuleError("Bàn đích đang bận.")

    source_id = order.table_id
    if source_id is not None:
        source = await session.get(DiningTable, source_id)
        if source is not None:
            source.status = "Trống"
    destination.status = "Đang phục vụ"
    order.table_id = to_table_id
    from app.modules.sales.models import TableMoveLog

    session.add(TableMoveLog(order_id=order.id, from_table=source_id, to_table=to_table_id))
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="MOVE_ORDER_TABLE",
            target_entity="ORDER",
            target_id=str(order.id),
        )
    )
    await session.flush()
    return order


async def cancel_order(
    session: AsyncSession, order_id: int, reason: str, *, actor_id: int | None = None
) -> Order:
    await lock_stocktake_gate(session)
    from app.modules.sales.payments import QR_PENDING, PaymentTransaction, expire_stale_qr

    await expire_stale_qr(session)
    order = await session.get(Order, order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    if order.status == "Chờ đối soát":
        raise BusinessRuleError("Order đang chờ đối soát QR, không thể hủy.")
    ensure_order_is_open(order)
    live_qr = (
        await session.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.order_id == order.id,
                PaymentTransaction.method == "QR",
                PaymentTransaction.status == QR_PENDING,
            )
        )
    ).scalar_one_or_none()
    if live_qr is not None:
        raise BusinessRuleError("Giao dịch QR đang chờ xác nhận, không thể hủy order.")
    if not reason or not reason.strip():
        raise BusinessRuleError("Cần lý do hủy order.")

    lines = list(
        (await session.execute(select(OrderLine).where(OrderLine.order_id == order.id)))
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
    current_bd = await _current_business_date(session)
    for line in lines:
        if line.status == LINE_WAITING:
            await _return_line_stock(
                session,
                line,
                Decimal(line.quantity),
                business_date_value=current_bd,
                actor_id=actor_id,
            )
        if line.status != LINE_CANCELLED:
            line.status = LINE_CANCELLED
    await _set_order_status(session, order, "Đã hủy")
    order.cancel_reason = reason
    await _free_table(session, order)
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CANCEL_ORDER",
            target_entity="ORDER",
            target_id=str(order.id),
            reason=reason,
        )
    )
    await session.flush()
    return order
