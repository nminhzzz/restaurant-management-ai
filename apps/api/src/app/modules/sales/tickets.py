"""Kitchen tickets (FR-SALE-31, FR-SALE-32): content with table and dish names, print results."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import DiningTable, Dish
from app.modules.sales.models import KitchenTicket, Order, OrderLine

TICKET_CONTENT_LIMIT = 2000  # PHIEU_BEP.NoiDung


def render_ticket(
    order: Order,
    lines: list[OrderLine],
    *,
    table_name: str | None,
    dish_names: dict[int, str],
    quantities: dict[int, int] | None = None,
) -> str:
    """The text the thermal printer receives: table or order code, then dish, quantity, note.

    `quantities` overrides a line's quantity (an increase prints only the added portions).
    """
    where = table_name if order.table_id is not None and table_name else "Mang về"
    header = f"{order.display_code or order.id} - {where}"
    rows = []
    for line in lines:
        quantity = (quantities or {}).get(line.id, int(line.quantity))
        note = f" ({line.note})" if line.note else ""
        rows.append(f"{dish_names.get(line.dish_id, line.dish_id)} x{quantity}{note}")
    return "\n".join([header, *rows])[:TICKET_CONTENT_LIMIT]


async def write_kitchen_ticket(
    session: AsyncSession,
    order: Order,
    lines: list[OrderLine],
    *,
    quantities: dict[int, int] | None = None,
) -> KitchenTicket:
    dish_ids = {line.dish_id for line in lines}
    dish_names: dict[int, str] = {}
    if dish_ids:
        rows = await session.execute(select(Dish.id, Dish.name).where(Dish.id.in_(dish_ids)))
        dish_names = {dish_id: name for dish_id, name in rows}
    table_name = None
    if order.table_id is not None:
        table_name = (
            await session.execute(select(DiningTable.name).where(DiningTable.id == order.table_id))
        ).scalar_one_or_none()
    ticket = KitchenTicket(
        order_id=order.id,
        status="Chờ in",
        print_status="Chờ in",
        print_count=1,
        content=render_ticket(
            order, lines, table_name=table_name, dish_names=dish_names, quantities=quantities
        ),
    )
    session.add(ticket)
    return ticket


def record_print_result(ticket: KitchenTicket, ok: bool) -> None:
    if ok:
        ticket.print_status = "Thành công"
        ticket.status = "Đã in"
    else:
        ticket.print_status = "Thất bại"
        ticket.status = "Thất bại"
    ticket.print_count = int(ticket.print_count) + 1 if ticket.print_count else 2
