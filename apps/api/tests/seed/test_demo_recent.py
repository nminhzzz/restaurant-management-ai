"""The demo top-up must leave a database where a stocktake can open and costs are known."""

from datetime import date
from decimal import Decimal

import pytest
from scripts.seed.demo_recent import settle_past_lines
from sqlalchemy import select

from app.modules.catalog.models import Dish, DishGroup
from app.modules.sales.models import Order, OrderLine


async def _line(session, dish_id, code, day, status="Đã thanh toán", line_status="Chờ làm"):
    order = Order(
        display_code=code,
        business_date=day,
        status=status,
        total=Decimal("1000"),
        order_type="Mang về",
    )
    session.add(order)
    await session.flush()
    line = OrderLine(order_id=order.id, dish_id=dish_id, status=line_status)
    session.add(line)
    await session.flush()
    return line.id


@pytest.mark.asyncio
async def test_only_past_waiting_lines_of_closed_orders_are_marked_served(session):
    group = DishGroup(name="Nhóm thử")
    session.add(group)
    await session.flush()
    dish = Dish(name="Món thử", group_id=group.id)
    session.add(dish)
    await session.flush()
    through = date(2026, 11, 5)
    past = await _line(session, dish.id, "ORD-1", date(2026, 11, 5))
    later = await _line(session, dish.id, "ORD-2", date(2026, 11, 6))
    still_open = await _line(session, dish.id, "ORD-3", date(2026, 11, 5), status="Đang mở")
    cancelled = await _line(session, dish.id, "ORD-4", date(2026, 11, 5), line_status="Đã hủy")

    settled = await settle_past_lines(session, through)

    session.expire_all()
    statuses = dict((await session.execute(select(OrderLine.id, OrderLine.status))).tuples().all())
    assert settled == 1
    assert statuses == {
        past: "Đã phục vụ",
        later: "Chờ làm",
        still_open: "Chờ làm",
        cancelled: "Đã hủy",
    }
