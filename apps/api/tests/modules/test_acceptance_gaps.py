"""Acceptance cases of document 06 that had no automated test (handoff 2026-11-08 B1)."""

from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.modules.catalog.models import DiningTable, Recipe
from app.modules.inventory.models import IngredientLot, StockMovement
from app.modules.sales.models import OrderLine, Reservation
from app.shared import business_date
from app.shared.audit import SystemAuditLog
from tests.modules.test_sales_holds import _headers, _hold, _make_client, _setup
from tests.modules.test_sales_line_lifecycle import _headers as _headers_as

pytestmark = pytest.mark.anyio


async def _order(client, headers, dish, table, quantity=1):
    created = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": table.id, "lines": [{"MaMon": dish.id, "SoLuong": quantity}]},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    return created.json()["MaOrder"], created.json()["lines"][0]["MaChiTietOrder"]


async def test_editing_the_note_of_a_held_line_keeps_its_deadline(session):
    """TC-SALE-26."""
    dish, _, table = await _setup(session, stock=5)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    hold = (await _hold(client, headers, dish, table, quantity=2)).json()
    deadline = (await session.get(Reservation, hold["MaGiuCho"])).expires_at

    edited = await client.patch(
        f"/api/v1/sales/holds/{hold['MaGiuCho']}", json={"note": "không hành"}, headers=headers
    )

    assert edited.status_code == 200, edited.text
    reservation = await session.get(Reservation, hold["MaGiuCho"])
    await session.refresh(reservation)
    assert reservation.note == "không hành"
    assert reservation.quantity == 2
    assert reservation.expires_at == deadline


async def test_a_hold_update_needs_something_to_change(session):
    dish, _, table = await _setup(session, stock=5)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    hold = (await _hold(client, headers, dish, table, quantity=2)).json()

    empty = await client.patch(f"/api/v1/sales/holds/{hold['MaGiuCho']}", json={}, headers=headers)

    assert empty.status_code == 422


async def test_leaving_the_table_ends_the_unsent_add_on_selection(session):
    """TC-SALE-46: the table is free, the held ingredients are released, and it is logged."""
    dish, _, table = await _setup(session, stock=5)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    order_id, _ = await _order(client, headers, dish, table)
    hold = await _hold(client, headers, dish, table, quantity=2, order_id=order_id)
    assert hold.status_code == 201, hold.text

    released = await client.post(
        f"/api/v1/sales/tables/{table.id}/release", json={"order_id": order_id}, headers=headers
    )

    assert released.status_code == 200, released.text
    table_id = table.id
    session.expire_all()
    freed = await session.get(DiningTable, table_id)
    assert (freed.status, freed.current_order_id) == ("Trống", None)
    reservation = await session.get(Reservation, hold.json()["MaGiuCho"])
    assert reservation.status not in ("Đang giữ", "Hết hạn")
    menu = await client.get("/api/v1/catalog/dishes", headers=headers)
    assert menu.json()["items"][0]["SoSuatKhaDung"] == 4  # 5 in stock, 1 sent, none held
    logged = await session.scalar(
        select(func.count())
        .select_from(SystemAuditLog)
        .where(SystemAuditLog.target_entity == "BAN", SystemAuditLog.target_id == str(table_id))
    )
    assert logged >= 1


async def test_a_cancelled_dish_returns_to_its_lot_even_after_the_lot_expired(session):
    """TC-INV-47: book stock rises, sellable stock does not."""
    dish, ingredient, table = await _setup(session, stock=3)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    order_id, line_id = await _order(client, headers, dish, table)
    lot = (await session.execute(select(IngredientLot))).scalar_one()
    lot_id = lot.id
    lot.expiry_date = business_date.business_date_of(business_date.now()) - timedelta(days=1)
    await session.commit()

    cancelled = await client.post(
        f"/api/v1/sales/orders/{order_id}/lines/{line_id}/cancel",
        json={"reason": "bếp chưa làm"},
        headers=headers,
    )

    assert cancelled.status_code == 200, cancelled.text
    session.expire_all()
    assert (await session.get(IngredientLot, lot_id)).quantity_remaining == 3
    await session.refresh(ingredient)
    assert float(ingredient.stock_qty) == 3
    returned = (
        await session.execute(select(StockMovement).where(StockMovement.kind == "Hoàn kho"))
    ).scalar_one()
    assert (returned.lot_id, returned.qty) == (lot_id, 1)
    menu = await client.get("/api/v1/catalog/dishes", headers=headers)
    assert menu.json()["items"][0]["SoSuatKhaDung"] == 0


async def test_a_paid_order_can_still_be_served_but_not_changed(session):
    """TC-BR-07: serving goes on; dishes and money are locked; the table is not freed."""
    dish, _, table = await _setup(session, stock=5)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    order_id, line_id = await _order(client, headers, dish, table, quantity=2)
    paid = await client.post(f"/api/v1/sales/orders/{order_id}/pay/cash", headers=headers)
    assert paid.status_code == 200, paid.text
    line_url = f"/api/v1/sales/orders/{order_id}/lines/{line_id}"

    for status in ("Đã xác nhận xong", "Đã phục vụ"):
        served = await client.patch(f"{line_url}/status", json={"to": status}, headers=headers)
        assert served.status_code == 200, served.text
    added = await client.post(
        f"/api/v1/sales/orders/{order_id}/lines",
        json={"MaMon": dish.id, "SoLuong": 1},
        headers=headers,
    )
    edited = await client.patch(line_url, json={"SoLuong": 5}, headers=headers)
    cancelled = await client.post(f"{line_url}/cancel", json={"reason": "đổi ý"}, headers=headers)

    assert (added.status_code, edited.status_code, cancelled.status_code) == (422, 422, 422)
    table_id = table.id
    session.expire_all()
    line = await session.get(OrderLine, line_id)
    assert (line.status, line.quantity) == ("Đã phục vụ", 2)
    seated = await session.get(DiningTable, table_id)
    assert (seated.status, seated.current_order_id) == ("Đang phục vụ", order_id)


@pytest.mark.parametrize("days_from_today", [0, -1])
async def test_a_recipe_cannot_be_scheduled_for_a_business_date_already_begun(
    session, days_from_today
):
    """TC-CAT-31 (the date has started) and TC-CAT-32 (the date is over)."""
    dish, ingredient, _ = await _setup(session, stock=5)
    client = await _make_client(session)
    manager, _ = await _headers_as(session, role="MANAGER", username="manager_recipe")
    today = business_date.business_date_of(business_date.now())
    versions = (await session.execute(select(Recipe.id, Recipe.status))).all()

    refused = await client.post(
        f"/api/v1/catalog/dishes/{dish.id}/recipes/schedule",
        json={
            "items": [{"MaNguyenLieu": ingredient.id, "SoLuong": 2}],
            "BusinessDateApDung": (today + timedelta(days=days_from_today)).isoformat(),
        },
        headers=manager,
    )

    assert refused.status_code == 422, refused.text
    session.expire_all()
    assert (await session.execute(select(Recipe.id, Recipe.status))).all() == versions


async def test_a_failure_after_the_stock_draw_leaves_no_trace_of_the_send(session, monkeypatch):
    """TC-SALE-08: the send is one transaction; nothing of it survives a late failure."""
    from app.modules.sales import orders as orders_service
    from app.modules.sales.models import Order

    dish, ingredient, table = await _setup(session, stock=5)
    client = await _make_client(session)
    headers, user = await _headers(session)
    hold = (await _hold(client, headers, dish, table, quantity=2)).json()
    dish_id, table_id, ingredient_id, user_id = dish.id, table.id, ingredient.id, user.id

    async def state():
        session.expire_all()
        reservation = await session.get(Reservation, hold["MaGiuCho"])
        return {
            "orders": await session.scalar(select(func.count()).select_from(Order)),
            "lines": await session.scalar(select(func.count()).select_from(OrderLine)),
            "movements": await session.scalar(select(func.count()).select_from(StockMovement)),
            "stock": float((await session.get(type(ingredient), ingredient_id)).stock_qty),
            "lot": float(
                (await session.execute(select(IngredientLot))).scalar_one().quantity_remaining
            ),
            "hold": (reservation.status, reservation.quantity, reservation.order_line_id),
            "table": (await session.get(DiningTable, table_id)).current_order_id,
        }

    before = await state()

    async def printer_down(*args, **kwargs):
        raise RuntimeError("lỗi tiêm sau khi trừ kho")

    monkeypatch.setattr(orders_service, "write_kitchen_ticket", printer_down)
    with pytest.raises(RuntimeError, match="lỗi tiêm"):
        await orders_service.submit_order(
            session,
            {
                "table_id": table_id,
                "order_type": "Tại chỗ",
                "lines": [{"MaMon": dish_id, "SoLuong": 2, "hold_id": hold["MaGiuCho"]}],
            },
            actor_id=user_id,
        )
    # What the request-scoped session does when a handler raises before its commit.
    await session.rollback()

    assert await state() == before
    assert before["hold"][0] == "Đang giữ"


async def test_late_money_for_an_order_that_left_does_not_touch_the_new_order_at_its_table(
    session, monkeypatch
):
    """TC-BR-08: A is settled once; the table stays with B; A can neither grow nor move."""
    from app.core.config import get_settings
    from app.modules.sales import payments
    from app.modules.sales.models import Invoice, Order
    from tests.modules.test_payment_reality import _second_table

    for name, value in {
        "PAYMENT_GATEWAY": "sepay",
        "SEPAY_BANK_ACCOUNT": "0123499999",
        "SEPAY_BANK_CODE": "MBBank",
        "SEPAY_WEBHOOK_API_KEY": "hook-key",
        "SEPAY_API_TOKEN": "api-token",
    }.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()
    dish, _, table = await _setup(session, stock=10)
    other_table = await _second_table(session)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    dish_id, table_id, other_table_id = dish.id, table.id, other_table.id
    order_a, _ = await _order(client, headers, dish, table)
    qr = await client.post(f"/api/v1/sales/orders/{order_a}/pay/qr", headers=headers)
    assert qr.status_code == 201, qr.text
    payment_id, amount = qr.json()["MaGiaoDich"], int(qr.json()["SoTien"])
    released = await client.post(
        f"/api/v1/sales/tables/{table_id}/release", json={"order_id": order_a}, headers=headers
    )
    assert released.status_code == 200, released.text
    order_b, _ = await _order(client, headers, dish, table)

    outcome = await payments.handle_sepay_transfer(
        session,
        {
            "id": "9600",
            "transferType": "in",
            "transferAmount": amount,
            "code": f"TT{payment_id}",
            "content": f"TT{payment_id}",
        },
    )
    await session.commit()
    add_on = await client.post(
        f"/api/v1/sales/orders/{order_a}/lines",
        json={"MaMon": dish_id, "SoLuong": 1},
        headers=headers,
    )
    moved = await client.post(
        f"/api/v1/sales/orders/{order_a}/move", json={"MaBanDich": other_table_id}, headers=headers
    )
    get_settings.cache_clear()

    assert outcome == "confirmed"
    session.expire_all()
    assert (await session.get(Order, order_a)).status == "Đã thanh toán"
    invoices = await session.scalar(
        select(func.count()).select_from(Invoice).where(Invoice.order_id == order_a)
    )
    assert invoices == 1
    seated = await session.get(DiningTable, table_id)
    assert (seated.status, seated.current_order_id) == ("Đang phục vụ", order_b)
    assert (await session.get(Order, order_b)).status == "Đang mở"
    assert (add_on.status_code, moved.status_code) == (422, 422)
    assert (await session.get(DiningTable, other_table_id)).current_order_id is None
