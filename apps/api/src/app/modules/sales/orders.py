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
from app.modules.catalog.models import DiningTable, Dish, DishPriceVersion
from app.modules.catalog.versions import recipe_items
from app.modules.inventory.models import IngredientLot, StockMovement
from app.modules.inventory.stock import (
    ensure_no_open_stocktake,
    lock_ingredient,
)
from app.modules.sales import reservations
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


async def _lock_order(session: AsyncSession, order_id: int) -> Order:
    """Serialise edits/cancellations with the payment path, which locks the same row."""
    order = (
        await session.execute(
            select(Order)
            .where(Order.id == order_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    return order


async def write_kitchen_ticket(
    session: AsyncSession, order: Order, lines: list[OrderLine]
) -> KitchenTicket:
    """Build one ticket with the names a kitchen can read, not internal ids."""
    dish_ids = {line.dish_id for line in lines}
    dish_names: dict[int, str] = {}
    if dish_ids:
        rows = await session.execute(select(Dish.id, Dish.name).where(Dish.id.in_(dish_ids)))
        dish_names = {row[0]: row[1] for row in rows}
    table_name: str | None = None
    if order.table_id is not None:
        table = await session.get(DiningTable, order.table_id)
        table_name = table.name if table is not None else None
    ticket = KitchenTicket(
        order_id=order.id,
        status="Chờ in",
        print_status="Chờ in",
        print_count=0,
        content=render_ticket(order, lines, dish_names=dish_names, table_name=table_name),
    )
    session.add(ticket)
    return ticket


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
    await ensure_no_open_stocktake(session)
    needed: dict[int, Decimal] = {}
    for item in await recipe_items(session, line.recipe_id):
        needed[item.ingredient_id] = needed.get(item.ingredient_id, Decimal(0)) + (
            Decimal(str(item.quantity)) * dishes
        )
    locked_ingredients = {
        ingredient_id: await lock_ingredient(session, ingredient_id)
        for ingredient_id in sorted(needed)
    }
    drawings = list(
        (
            await session.execute(
                select(StockMovement)
                .where(StockMovement.order_line_id == line.id, StockMovement.qty < 0)
                .order_by(StockMovement.id.asc())
                .with_for_update()
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
                select(StockMovement)
                .where(StockMovement.order_line_id == line.id, StockMovement.qty > 0)
                .with_for_update()
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
            lot = await session.scalar(
                select(IngredientLot)
                .where(IngredientLot.id == movement.lot_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            if lot is not None:
                lot.quantity_remaining = Decimal(str(lot.quantity_remaining)) + take
            ingredient = locked_ingredients[ingredient_id]
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
    table = (
        await session.execute(
            select(DiningTable)
            .where(DiningTable.id == order.table_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if table is not None and table.current_order_id == order.id:
        table.status = "Trống"
        table.current_order_id = None


async def submit_order(
    session: AsyncSession,
    payload: dict,
    *,
    actor_id: int | None = None,
    confirm_expired: bool = False,
) -> dict:
    await ensure_no_open_stocktake(session)
    now = business_date.now()
    bd = _bd_of(now)
    order_type = payload.get("order_type") or "Tại chỗ"
    table_id = payload.get("table_id")
    lines_in: list[dict] = payload.get("lines") or []
    request_id = payload.get("request_id")

    if request_id:
        existing_order = (
            await session.execute(select(Order).where(Order.request_id == str(request_id)))
        ).scalar_one_or_none()
        if existing_order is not None:
            existing_lines = list(
                (
                    await session.execute(
                        select(OrderLine)
                        .where(OrderLine.order_id == existing_order.id)
                        .order_by(OrderLine.id)
                    )
                )
                .scalars()
                .all()
            )
            return {"order": existing_order, "lines": existing_lines, "rejected": []}

    if order_type == "Mang về":
        table_id = None
    elif table_id is not None:
        table = (
            await session.execute(
                select(DiningTable)
                .where(DiningTable.id == table_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalar_one_or_none()
        if table is None or table.is_deleted:
            raise BusinessRuleError("Bàn không tồn tại.")
        if table.status != "Trống" or table.current_order_id is not None:
            raise BusinessRuleError("Bàn đang phục vụ. Hãy giải phóng bàn trước khi mở order mới.")

    # Validate the whole submission before writing anything (FR-SALE-03/NFR-10).
    # Every line goes through a hold. A client that does not create one gets a hold
    # created here, bound to this selection, so no send can skip stock reservation
    # or the expired-hold re-check.
    if actor_id is None:
        raise BusinessRuleError("Cần người thực hiện để giữ nguyên liệu.")
    prepared: list[dict] = []
    for line_input in lines_in:
        dish_id = line_input.get("dish_id") or line_input.get("MaMon")
        if dish_id is None:
            raise BusinessRuleError("Thiếu món trong danh sách gửi.")
        quantity = int(line_input.get("quantity") or line_input.get("SoLuong") or 1)
        if quantity < 1:
            raise BusinessRuleError("Số lượng món phải lớn hơn 0.")
        note = line_input.get("note") or line_input.get("GhiChu")
        hold_id = line_input.get("hold_id")

        if hold_id is not None:
            hold = await reservations.get_hold_for_submit(
                session, int(hold_id), actor_id, confirm_expired=confirm_expired
            )
        else:
            hold = await reservations.create_hold(
                session,
                user_id=actor_id,
                selection_code=request_id,
                table_id=table_id,
                order_id=None,
                dish_id=int(dish_id),
                quantity=quantity,
                note=note,
            )
        if hold.dish_id != int(dish_id) or int(hold.quantity) != quantity:
            raise BusinessRuleError("Lượt giữ chỗ không khớp món/số lượng.")
        if hold.table_id != table_id:
            raise BusinessRuleError("Lượt giữ chỗ khác bàn.")
        prepared.append(
            {
                "hold": hold,
                "dish_id": int(dish_id),
                "quantity": quantity,
                "note": note,
            }
        )

    if not prepared:
        raise BusinessRuleError("Không có món nào để gửi.")

    display_code = await next_display_code(session, bd)
    async with session.begin_nested():
        order = Order(
            business_date=bd,
            table_id=table_id,
            order_type=order_type,
            status="Đang mở",
            created_by=actor_id,
            display_code=display_code,
            request_id=str(request_id) if request_id else None,
            created_at=now,
        )
        session.add(order)
        await session.flush()

        created_lines: list[OrderLine] = []
        for item in prepared:
            hold = item["hold"]
            price = (
                await session.get(DishPriceVersion, hold.price_version_id)
                if hold.price_version_id is not None
                else None
            )
            if price is None:
                raise BusinessRuleError("Món chưa có giá")
            unit_price = Decimal(str(price.price))
            line = OrderLine(
                order_id=order.id,
                dish_id=item["dish_id"],
                quantity=item["quantity"],
                unit_price=unit_price,
                total=unit_price * item["quantity"],
                price_version_id=hold.price_version_id,
                recipe_id=hold.recipe_id,
                note=item["note"] or hold.note,
                status=LINE_WAITING,
            )
            session.add(line)
            await session.flush()
            hold.order_id = order.id
            await reservations.consume_hold(
                session,
                hold,
                order_line_id=line.id,
                business_date_value=bd,
                actor_id=actor_id,
            )
            created_lines.append(line)

        if table_id is not None:
            table = await session.get(DiningTable, table_id)
            assert table is not None
            table.status = "Đang phục vụ"
            table.current_order_id = order.id
        await write_kitchen_ticket(session, order, created_lines)
        await session.flush()
    return {"order": order, "lines": created_lines, "rejected": []}


async def add_lines(
    session: AsyncSession,
    order_id: int,
    lines: list[dict],
    *,
    actor_id: int | None = None,
    confirm_expired: bool = False,
) -> list[OrderLine]:
    """Validate and append all confirmed lines atomically (FR-SALE-03)."""
    await ensure_no_open_stocktake(session)
    created: list[OrderLine] = []
    async with session.begin_nested():
        for line in lines:
            dish_id = line.get("dish_id") or line.get("MaMon")
            quantity = int(line.get("quantity") or line.get("SoLuong") or 1)
            if dish_id is None:
                raise BusinessRuleError("Thiếu món trong danh sách gửi.")
            created.append(
                await add_line(
                    session,
                    order_id,
                    int(dish_id),
                    quantity,
                    line.get("note") or line.get("GhiChu"),
                    actor_id=actor_id,
                    hold_id=line.get("hold_id"),
                    request_line_id=line.get("request_line_id") or line.get("MaYeuCauDong"),
                    confirm_expired=confirm_expired,
                )
            )
    return created


async def add_line(
    session: AsyncSession,
    order_id: int,
    dish_id: int,
    quantity: int,
    note: str | None = None,
    *,
    actor_id: int | None = None,
    hold_id: int | None = None,
    request_line_id: str | None = None,
    confirm_expired: bool = False,
) -> OrderLine:
    await ensure_no_open_stocktake(session)
    if request_line_id:
        existing = (
            await session.execute(
                select(OrderLine).where(OrderLine.request_line_id == str(request_line_id))
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing
    order = await _lock_order(session, order_id)
    ensure_order_is_open(order)
    if quantity < 1:
        raise BusinessRuleError("Số lượng món phải lớn hơn 0.")

    if order.table_id is not None:
        table = (
            await session.execute(
                select(DiningTable)
                .where(DiningTable.id == order.table_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalar_one_or_none()
        if table is None or table.current_order_id != order.id:
            raise BusinessRuleError("Order đã được giải phóng khỏi bàn, không thể gọi thêm.")

    if actor_id is None:
        raise BusinessRuleError("Cần người thực hiện để giữ nguyên liệu.")
    if hold_id is not None:
        hold = await reservations.get_hold_for_submit(
            session,
            hold_id,
            actor_id,
            confirm_expired=confirm_expired,
            expected_order_id=order.id,
        )
    else:
        hold = await reservations.create_hold(
            session,
            user_id=actor_id,
            selection_code=request_line_id,
            table_id=order.table_id,
            order_id=order.id,
            dish_id=dish_id,
            quantity=quantity,
            note=note,
        )
    if hold.dish_id != dish_id or int(hold.quantity) != quantity:
        raise BusinessRuleError("Lượt giữ chỗ không khớp món/số lượng.")
    if hold.table_id != order.table_id:
        raise BusinessRuleError("Lượt giữ chỗ khác bàn.")
    price = (
        await session.get(DishPriceVersion, hold.price_version_id)
        if hold.price_version_id is not None
        else None
    )
    if price is None:
        raise BusinessRuleError("Món chưa có giá.")
    unit_price = Decimal(str(price.price))
    line = OrderLine(
        order_id=order.id,
        dish_id=dish_id,
        quantity=quantity,
        unit_price=unit_price,
        total=unit_price * quantity,
        price_version_id=hold.price_version_id,
        recipe_id=hold.recipe_id,
        note=note or hold.note,
        status=LINE_WAITING,
        request_line_id=str(request_line_id) if request_line_id else None,
    )
    session.add(line)
    await session.flush()
    hold.order_id = order.id
    await reservations.consume_hold(
        session,
        hold,
        order_line_id=line.id,
        business_date_value=_bd_of(business_date.now()),
        actor_id=actor_id,
    )
    await write_kitchen_ticket(session, order, [line])
    await session.flush()
    return line


async def update_line(
    session: AsyncSession,
    order_id: int,
    line_id: int,
    quantity: int,
    *,
    actor_id: int | None = None,
    request_line_id: str | None = None,
) -> OrderLine:
    await ensure_no_open_stocktake(session)
    order = await _lock_order(session, order_id)
    line = await session.get(OrderLine, line_id)
    if line is None or line.order_id != order_id:
        raise NotFoundError("Dòng món không tồn tại.")
    if request_line_id:
        existing = (
            await session.execute(
                select(OrderLine).where(OrderLine.request_line_id == request_line_id)
            )
        ).scalar_one_or_none()
        if existing is not None:
            if existing.order_id != order_id or existing.dish_id != line.dish_id:
                raise BusinessRuleError("Mã yêu cầu đã được sử dụng cho dòng món khác.")
            return existing
    ensure_order_is_open(order)
    if quantity < 1:
        raise BusinessRuleError("Số lượng món phải lớn hơn 0.")
    delta = quantity - int(line.quantity)
    if delta > 0:
        if not request_line_id or actor_id is None:
            raise BusinessRuleError(
                "Tăng số lượng phải dùng luồng gọi thêm hoặc cung cấp request_line_id "
                "để tạo dòng món mới."
            )
        if line.status == LINE_CANCELLED:
            raise BusinessRuleError("Không thể gọi thêm từ dòng món đã hủy.")
        hold = await reservations.create_hold(
            session,
            user_id=actor_id,
            selection_code=None,
            table_id=order.table_id,
            order_id=order.id,
            dish_id=line.dish_id,
            quantity=delta,
            note=line.note,
        )
        return await add_line(
            session,
            order_id,
            line.dish_id,
            delta,
            line.note,
            actor_id=actor_id,
            hold_id=hold.id,
            request_line_id=request_line_id,
        )
    if line.status != LINE_WAITING:
        raise BusinessRuleError("Chỉ sửa món ở trạng thái Chờ.")
    if delta < 0:
        await _return_line_stock(session, line, Decimal(-delta), actor_id=actor_id)
        line.quantity = quantity
    line.total = Decimal(str(line.unit_price)) * int(line.quantity)
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
    await ensure_no_open_stocktake(session)
    line = await session.get(OrderLine, line_id)
    if line is None:
        raise NotFoundError("Dòng món không tồn tại.")
    if line.status != LINE_WAITING:
        raise BusinessRuleError("Chỉ hủy món ở trạng thái Chờ.")
    order = await _lock_order(session, line.order_id)
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
    # Cancelling the last line keeps the order open so the table can order again.
    # Closing the whole order is still an explicit manager action (FR-SALE-10/11).
    return line


async def move_table(
    session: AsyncSession, order_id: int, to_table_id: int, *, actor_id: int | None = None
) -> Order:
    order = await _lock_order(session, order_id)
    ensure_order_is_open(order)
    table_ids = sorted({tid for tid in (order.table_id, to_table_id) if tid is not None})
    locked = (
        (
            await session.execute(
                select(DiningTable)
                .where(DiningTable.id.in_(table_ids))
                .order_by(DiningTable.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        )
        .scalars()
        .all()
    )
    tables = {t.id: t for t in locked}
    destination = tables.get(to_table_id)
    if destination is None or destination.is_deleted:
        raise BusinessRuleError("Bàn đích không tồn tại.")
    if destination.status != "Trống" or destination.current_order_id is not None:
        raise BusinessRuleError("Bàn đích đang bận.")

    source_id = order.table_id
    if source_id is not None:
        source = tables.get(source_id)
        if source is None or source.current_order_id != order.id:
            raise BusinessRuleError("Order không còn gắn với bàn đang phục vụ.")
        source.status = "Trống"
        source.current_order_id = None
        # Release the unique order pointer before assigning it to a lower-ID table.
        await session.flush()
    destination.status = "Đang phục vụ"
    destination.current_order_id = order.id
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
    await ensure_no_open_stocktake(session)
    from app.modules.sales.payments import QR_PENDING, PaymentTransaction, expire_stale_qr

    await expire_stale_qr(session)
    order = await _lock_order(session, order_id)
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
    for line in lines:
        if line.status == LINE_WAITING:
            await _return_line_stock(session, line, Decimal(line.quantity), actor_id=actor_id)
        if line.status != LINE_CANCELLED:
            line.status = LINE_CANCELLED
    await reservations.release_active_holds(session, order_id=order.id, table_id=order.table_id)
    await _set_order_status(session, order, "Đã hủy")
    order.cancel_reason = reason
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
