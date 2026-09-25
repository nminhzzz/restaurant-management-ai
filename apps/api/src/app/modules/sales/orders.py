"""Order lifecycle — submit, lines, stock, table moves and cancellation (FR-SALE-01…13, 20, 24, 26).

Stock is drawn through `inventory.stock.apply_stock_movement` and returned through the
quantity-based helper below. Returning by *current line quantity* (not by replaying every
original ledger row) is what keeps a reduce-then-cancel sequence from returning more than
was taken: the two operations together return exactly the quantity the line was charged for.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.catalog.models import DiningTable, Ingredient
from app.modules.catalog.versions import (
    active_price_version,
    active_recipe,
    recipe_items,
)
from app.modules.inventory.models import IngredientLot, StockMovement
from app.modules.inventory.stock import StockChange, apply_stock_movement
from app.modules.sales.models import DemOrder, KitchenTicket, Order, OrderLine
from app.modules.sales.tickets import render_ticket
from app.shared import business_date
from app.shared.audit import SystemAuditLog
from app.shared.enums import StockMovementType

OPEN_ORDER_STATUSES: frozenset[str] = frozenset({"Đang mở"})
LINE_WAITING = "Chờ"
LINE_CONFIRMED = "Đã xác nhận xong"
LINE_SERVED = "Đã phục vụ"
LINE_CANCELLED = "Đã hủy"
LINE_FORWARD = {LINE_WAITING: LINE_CONFIRMED, LINE_CONFIRMED: LINE_SERVED}


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
) -> tuple[OrderLine, bool]:
    """Snapshot price/recipe for a dish; the flag reports whether stock can cover it."""
    price_version = await active_price_version(session, dish_id, bd)
    recipe = await active_recipe(session, dish_id, bd)
    line = OrderLine(
        dish_id=dish_id,
        quantity=quantity,
        unit_price=Decimal(str(price_version.price)) if price_version else Decimal("0"),
        price_version_id=price_version.id if price_version else None,
        recipe_id=recipe.id if recipe else None,
        status=LINE_WAITING,
    )
    if recipe is None:
        return line, True
    for item in await recipe_items(session, recipe.id):
        ingredient = await session.get(Ingredient, item.ingredient_id)
        needed = Decimal(str(item.quantity)) * quantity
        if ingredient is None or Decimal(str(ingredient.stock_qty)) < needed:
            return line, False
    return line, True


async def _draw_line_stock(
    session: AsyncSession, line: OrderLine, quantity: int, bd: date, *, actor_id: int | None
) -> None:
    if line.recipe_id is None:
        return
    for item in await recipe_items(session, line.recipe_id):
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

    now = business_date.now()
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
                    business_date=_bd_of(now),
                    order_line_id=line.id,
                    performed_by=actor_id,
                )
            )
            returned[movement.lot_id] = returned.get(movement.lot_id, Decimal(0)) + take
            remaining -= take
    await session.flush()


def _bd_of(moment: datetime) -> date:
    return business_date.business_date_of(moment)


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
    now = business_date.now()
    bd = _bd_of(now)
    order_type = payload.get("order_type") or "Tại chỗ"
    table_id = payload.get("table_id")
    lines_in: list[dict] = payload.get("lines") or []

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
        line, in_stock = await _resolve_line_inputs(session, int(dish_id), quantity, bd)
        if not in_stock:
            rejected.append({"MaMon": int(dish_id), "reason": "không đủ tồn kho"})
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
    order = await session.get(Order, order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    ensure_order_is_open(order)

    line, in_stock = await _resolve_line_inputs(session, dish_id, quantity, order.business_date)
    if not in_stock:
        raise BusinessRuleError("Không đủ tồn kho.")
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
    order = await session.get(Order, order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    ensure_order_is_open(order)
    line = await session.get(OrderLine, line_id)
    if line is None or line.order_id != order_id:
        raise NotFoundError("Dòng món không tồn tại.")
    if line.status != LINE_WAITING:
        raise BusinessRuleError("Chỉ sửa món ở trạng thái Chờ.")

    delta = quantity - int(line.quantity)
    if delta > 0:
        _, in_stock = await _resolve_line_inputs(session, line.dish_id, delta, order.business_date)
        if not in_stock:
            raise BusinessRuleError("Không đủ tồn kho.")
        await _draw_line_stock(session, line, delta, order.business_date, actor_id=actor_id)
        line.quantity = int(line.quantity) + delta
    elif delta < 0:
        await _return_line_stock(session, line, Decimal(-delta), actor_id=actor_id)
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

    await _return_line_stock(session, line, Decimal(line.quantity), actor_id=actor_id)
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
    order = await session.get(Order, order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    if order.status == "Chờ đối soát":
        raise BusinessRuleError("Order đang chờ đối soát QR, không thể hủy.")
    ensure_order_is_open(order)
    if not reason or not reason.strip():
        raise BusinessRuleError("Cần lý do hủy order.")

    lines = list(
        (await session.execute(select(OrderLine).where(OrderLine.order_id == order.id)))
        .scalars()
        .all()
    )
    for line in lines:
        if line.status == LINE_WAITING:
            await _return_line_stock(session, line, Decimal(line.quantity), actor_id=actor_id)
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
