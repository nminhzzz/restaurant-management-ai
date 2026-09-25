"""Sales tickets — Task 3."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sales.models import KitchenTicket, Order, OrderLine


def render_ticket(order: Order, lines: list[OrderLine]) -> str:
    header = f"Order {order.display_code or order.id} - Ban {order.table_id or 'Mang ve'}"
    body_lines = []
    for ln in lines:
        note = f" ({ln.note})" if ln.note else ""
        body_lines.append(f"{ln.dish_id} x{ln.quantity}{note} - {float(ln.unit_price):.0f}")
    return header + "\n" + "\n".join(body_lines)


def record_print_result(ticket: KitchenTicket, ok: bool) -> None:
    if ok:
        ticket.print_status = "Thành công"
        ticket.status = "Đã in"
    else:
        ticket.print_status = "Thất bại"
        ticket.status = "Thất bại"
    ticket.print_count = int(ticket.print_count) + 1 if ticket.print_count else 2
