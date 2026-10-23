"""Sales tickets — Task 3."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError
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


async def request_reprint(session: AsyncSession, order_id: int, ticket_id: int) -> KitchenTicket:
    """Enqueue the immutable original content; repeated pending clicks coalesce."""
    ticket = await lock_ticket(session, order_id, ticket_id)
    if ticket.print_status == "Đang in":
        raise BusinessRuleError("Máy in đang xử lý phiếu; vui lòng chờ kết quả.")
    if ticket.print_status != "Chờ in":
        ticket.print_status = ticket.status = "Chờ in"
        ticket.print_cycle_attempts = 0
        ticket.print_next_attempt_at = None
        ticket.print_error = None
        ticket.print_lease_token = None
        ticket.print_lease_until = None
    return ticket


async def lock_ticket(session: AsyncSession, order_id: int, ticket_id: int) -> KitchenTicket:
    ticket = (
        await session.execute(
            select(KitchenTicket)
            .where(
                KitchenTicket.id == ticket_id,
                KitchenTicket.order_id == order_id,
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if ticket is None:
        raise NotFoundError("Phiếu bếp không tồn tại.")
    return ticket


async def report_print_problem(
    session: AsyncSession, order_id: int, ticket_id: int
) -> KitchenTicket:
    ticket = await lock_ticket(session, order_id, ticket_id)
    if ticket.print_status == "Đang in":
        raise BusinessRuleError("Máy in đang xử lý phiếu; vui lòng chờ kết quả.")
    ticket.print_status = ticket.status = "Thất bại"
    ticket.print_error = "Nhân viên báo lỗi in; cần kiểm tra máy in rồi in lại."
    return ticket
