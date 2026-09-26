"""GET /sales/floor — tables with their open order, plus open takeaway orders."""

from decimal import Decimal

import pytest

from app.modules.catalog.models import DiningTable, Dish, DishGroup
from app.modules.sales.models import Order, OrderLine
from app.shared import business_date
from tests.modules.test_sales_payments import _headers, _make_client


async def _dish(session) -> Dish:
    group = DishGroup(name="Nhóm", display_order=1, is_deleted=False)
    session.add(group)
    await session.flush()
    dish = Dish(name="Phở bò", group_id=group.id, is_deleted=False)
    session.add(dish)
    await session.flush()
    return dish


async def _order(session, *, table_id, kind, code, lines, status="Đang mở") -> Order:
    order = Order(
        display_code=code,
        business_date=business_date.business_date_of(business_date.now()),
        table_id=table_id,
        order_type=kind,
        status=status,
        created_at=business_date.now(),
    )
    session.add(order)
    await session.flush()
    for dish_id, qty, price, line_status in lines:
        session.add(
            OrderLine(
                order_id=order.id,
                dish_id=dish_id,
                quantity=qty,
                unit_price=Decimal(price),
                status=line_status,
            )
        )
    await session.flush()
    return order


@pytest.mark.anyio
async def test_the_floor_lists_tables_open_orders_and_takeaway(session):
    dish = await _dish(session)
    free = DiningTable(name="Bàn 01", status="Trống", is_deleted=False)
    busy = DiningTable(name="Bàn 04", status="Đang phục vụ", is_deleted=False)
    gone = DiningTable(name="Bàn cũ", status="Trống", is_deleted=True)
    session.add_all([free, busy, gone])
    await session.flush()
    await _order(
        session,
        table_id=busy.id,
        kind="Tại chỗ",
        code="ORD-1",
        lines=[(dish.id, 2, "65000", "Chờ"), (dish.id, 1, "65000", "Đã hủy")],
    )
    await _order(
        session, table_id=None, kind="Mang về", code="ORD-2", lines=[(dish.id, 1, "45000", "Chờ")]
    )
    await _order(
        session,
        table_id=None,
        kind="Mang về",
        code="ORD-3",
        lines=[(dish.id, 1, "45000", "Chờ")],
        status="Đã thanh toán",
    )
    await session.commit()

    client = await _make_client(session)
    headers, _ = await _headers(session)
    resp = await client.get("/api/v1/sales/floor", headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert [t["TenBan"] for t in body["tables"]] == ["Bàn 01", "Bàn 04"]
    assert body["tables"][0]["order"] is None
    busy_order = body["tables"][1]["order"]
    assert busy_order["MaOrderHienThi"] == "ORD-1"
    assert busy_order["SoMon"] == 2
    assert busy_order["TamTinh"] == 130000
    assert [o["MaOrderHienThi"] for o in body["takeaway"]] == ["ORD-2"]


@pytest.mark.anyio
async def test_the_warehouse_role_cannot_read_the_floor(session):
    client = await _make_client(session)
    headers, _ = await _headers(session, role="WAREHOUSE", username="kho01")
    resp = await client.get("/api/v1/sales/floor", headers=headers)
    assert resp.status_code == 403
