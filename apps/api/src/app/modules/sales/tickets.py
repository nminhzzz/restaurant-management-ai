"""Sales tickets — Task 3."""

from app.modules.sales.models import KitchenTicket, Order, OrderLine


def render_ticket(
    order: Order,
    lines: list[OrderLine],
    *,
    dish_names: dict[int, str] | None = None,
    table_name: str | None = None,
) -> str:
    """A printable ticket with human names, not internal ids.

    The caller resolves names in one query, so the ticket stays a pure function.
    """
    table = table_name or ("Mang về" if order.table_id is None else f"Bàn #{order.table_id}")
    header = f"Order {order.display_code or order.id} - {table}"
    body_lines = []
    for ln in lines:
        note = f" ({ln.note})" if ln.note else ""
        name = (dish_names or {}).get(ln.dish_id, f"Món #{ln.dish_id}")
        body_lines.append(f"{name} x{ln.quantity}{note} - {float(ln.unit_price):.0f}")
    return header + "\n" + "\n".join(body_lines)


def record_print_result(ticket: KitchenTicket, ok: bool) -> None:
    if ok:
        ticket.print_status = "Thành công"
        ticket.status = "Đã in"
    else:
        ticket.print_status = "Thất bại"
        ticket.status = "Thất bại"
    ticket.print_count = int(ticket.print_count) + 1 if ticket.print_count else 2
