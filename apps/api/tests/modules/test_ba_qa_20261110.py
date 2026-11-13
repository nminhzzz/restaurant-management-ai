"""Regressions for the BA test run of 2026-11-10 on 6985565 (tài liệu 06, mục J.1/J.2)."""

from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.core.database import get_session
from app.core.errors import BusinessRuleError
from app.main import app
from app.modules.catalog import service as catalog
from app.modules.catalog.models import DiningTable, Dish, DishGroup, Ingredient
from app.modules.inventory import service as inventory
from app.modules.inventory.models import StockIssue, StockMovement
from app.modules.sales import orders, payments, reservations
from app.modules.sales.models import Order
from app.modules.sales.reservations import Reservation
from app.shared.audit import SystemAuditLog
from tests.modules.test_sales_orders import _setup_dish_with_stock, _setup_table


async def _ingredient(session, name="Thịt bò"):
    ing = Ingredient(name=name, unit="kg", min_stock=0, stock_qty=0, is_deleted=False)
    session.add(ing)
    await session.flush()
    return ing


async def _balances(session, ingredient_id: int) -> list[tuple[Decimal, Decimal]]:
    rows = await session.execute(
        select(StockMovement.qty, StockMovement.balance_after)
        .where(StockMovement.ingredient_id == ingredient_id)
        .order_by(StockMovement.id)
    )
    return [(Decimal(str(q)), Decimal(str(b))) for q, b in rows]


async def _last_audit(session, action: str) -> SystemAuditLog:
    entry = await session.scalar(
        select(SystemAuditLog)
        .where(SystemAuditLog.action == action)
        .order_by(SystemAuditLog.id.desc())
        .limit(1)
    )
    assert entry is not None, action
    return entry


# PH-01: TonSauGiaoDich is the ingredient's stock right after each movement.
@pytest.mark.anyio
async def test_balance_after_follows_receipts_and_a_fifo_issue_across_lots(session, active_user):
    ing = await _ingredient(session)
    await inventory.create_receipt(
        session,
        active_user.id,
        None,
        None,
        [{"ingredient_id": ing.id, "quantity": 10, "unit_price": 1000}],
    )
    await inventory.create_receipt(
        session,
        active_user.id,
        None,
        None,
        [{"ingredient_id": ing.id, "quantity": 5, "unit_price": 2000}],
    )
    await inventory.create_issue(
        session, active_user.id, "Hao hụt", [{"ingredient_id": ing.id, "quantity": 12}]
    )

    assert [b for _, b in await _balances(session, ing.id)] == [10, 15, 5, 3]


@pytest.mark.anyio
async def test_balance_after_on_cancelled_receipt(session, active_user):
    ing = await _ingredient(session)
    receipt = await inventory.create_receipt(
        session,
        active_user.id,
        None,
        None,
        [{"ingredient_id": ing.id, "quantity": 8, "unit_price": 1000}],
    )
    await inventory.cancel_receipt(session, active_user.id, receipt.id)

    assert [b for _, b in await _balances(session, ing.id)] == [8, 0]


@pytest.mark.anyio
async def test_balance_after_on_order_draw_and_return(session, active_user):
    dish, ing, _ = await _setup_dish_with_stock(session, stock_qty=10, need_per_unit=2)
    result = await orders.submit_order(
        session,
        {"order_type": "Mang về", "lines": [{"dish_id": dish.id, "quantity": 3}]},
        actor_id=active_user.id,
    )
    await orders.cancel_line(
        session, result["lines"][0].id, "Khách đổi món", actor_id=active_user.id
    )

    assert await _balances(session, ing.id) == [
        (Decimal(-6), Decimal(4)),
        (Decimal(6), Decimal(10)),
    ]


# PH-02
@pytest.mark.anyio
async def test_supplier_patch_returns_its_receipts(session, active_user, manager_token):
    supplier = await catalog.create_supplier(session, active_user.id, "NCC Rau")
    ing = await _ingredient(session)
    await inventory.create_receipt(
        session,
        active_user.id,
        supplier.id,
        None,
        [{"ingredient_id": ing.id, "quantity": 1, "unit_price": 1000}],
    )
    await session.commit()

    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/catalog/suppliers/{supplier.id}",
                json={"NguoiLienHe": "Chị Lan"},
                headers={"Authorization": f"Bearer {manager_token}"},
            )
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 200, response.text
    assert len(response.json()["PhieuNhap"]) == 1


# PH-03
@pytest.mark.anyio
async def test_soft_deleted_group_records_its_deletion_time(session, active_user):
    group = DishGroup(name="Món cũ", display_order=1, is_deleted=False)
    session.add(group)
    await session.flush()
    session.add(Dish(name="Món đã xóa", group_id=group.id, is_deleted=True))
    await session.flush()

    await catalog.delete_group(session, active_user.id, group.id)

    await session.refresh(group)
    assert group.is_deleted is True
    assert group.deleted_at is not None


# PH-05
@pytest.mark.anyio
async def test_posted_manual_issue_is_confirmed_not_draft(session, active_user):
    ing = await _ingredient(session)
    await inventory.create_receipt(
        session,
        active_user.id,
        None,
        None,
        [{"ingredient_id": ing.id, "quantity": 5, "unit_price": 1000}],
    )
    await inventory.create_issue(
        session, active_user.id, "Hao hụt", [{"ingredient_id": ing.id, "quantity": 1}]
    )

    statuses = (await session.scalars(select(StockIssue.status))).all()
    assert statuses == ["Đã xác nhận"]


# PH-07: the losing request of a concurrent duplicate send gets the winner's order, not 500.
@pytest.mark.anyio
async def test_duplicate_request_id_race_returns_the_committed_order(
    session, session_factory, active_user, monkeypatch
):
    dish, ing, _ = await _setup_dish_with_stock(session, stock_qty=10)
    payload = {
        "order_type": "Mang về",
        "request_id": "req-race-1",
        "lines": [{"dish_id": dish.id, "quantity": 1}],
    }
    first = await orders.submit_order(session, dict(payload), actor_id=active_user.id)
    await session.commit()

    # The loser read "no order yet" before the winner committed.
    real_lookup = orders._existing_submission
    calls = {"n": 0}

    async def stale_first_lookup(sess, request_id):
        calls["n"] += 1
        if calls["n"] == 1:
            return None
        return await real_lookup(sess, request_id)

    monkeypatch.setattr(orders, "_existing_submission", stale_first_lookup)
    async with session_factory() as loser:
        second = await orders.submit_order(loser, dict(payload), actor_id=active_user.id)
        await loser.commit()

        assert second["order"].id == first["order"].id
        assert await loser.scalar(select(func.count(Order.id))) == 1
        # The loser's own hold was rolled back with the rest of its attempt.
        assert await loser.scalar(select(func.count(Reservation.id))) == 1
        refreshed = await loser.get(Ingredient, ing.id)
        assert refreshed is not None
        assert Decimal(str(refreshed.stock_qty)) == 9


# PH-09
@pytest.mark.anyio
async def test_cancelled_order_records_its_close_time(session, active_user):
    dish, _, _ = await _setup_dish_with_stock(session, stock_qty=10)
    result = await orders.submit_order(
        session,
        {"order_type": "Mang về", "lines": [{"dish_id": dish.id, "quantity": 1}]},
        actor_id=active_user.id,
    )
    order = await orders.cancel_order(
        session, result["order"].id, "Khách hủy", actor_id=active_user.id
    )

    assert order.status == "Đã hủy"
    assert order.closed_at is not None


# TC-SALE-74
@pytest.mark.anyio
async def test_qr_payment_stores_its_creation_time(session, active_user):
    dish, _, _ = await _setup_dish_with_stock(session, stock_qty=10)
    result = await orders.submit_order(
        session,
        {"order_type": "Mang về", "lines": [{"dish_id": dish.id, "quantity": 1}]},
        actor_id=active_user.id,
    )
    payment = await payments.start_qr(session, result["order"].id, actor_id=active_user.id)

    assert payment.qr_created_at is not None
    assert payment.qr_created_at == payment.created_at


# TC-SALE-61: a refused send names the line to look at again.
@pytest.mark.anyio
async def test_refused_hold_names_the_dish_and_quantity(session, active_user):
    dish, _, _ = await _setup_dish_with_stock(session, stock_qty=10, dish_name="Mực xào")
    hold = await reservations.create_hold(
        session,
        user_id=active_user.id,
        selection_code="sel-61",
        table_id=None,
        dish_id=dish.id,
        quantity=2,
    )
    await reservations.release_hold(session, hold_id=hold.id, user_id=active_user.id)

    with pytest.raises(BusinessRuleError) as refused:
        await reservations.get_hold_for_submit(session, hold.id, active_user.id)

    assert "Mực xào (2 suất)" in str(refused.value.message)


@pytest.mark.anyio
async def test_out_of_stock_refusal_names_the_dish(session, active_user):
    dish, _, _ = await _setup_dish_with_stock(
        session, stock_qty=1, dish_name="Sò điệp", need_per_unit=5
    )

    with pytest.raises(BusinessRuleError) as refused:
        await catalog.ensure_dish_sellable(session, dish.id)

    assert "Sò điệp" in str(refused.value.message)


# TC-SET-09: updates keep what changed, before and after.
@pytest.mark.anyio
async def test_catalog_updates_record_before_and_after(session, active_user):
    group = await catalog.create_group(session, active_user.id, "Món chính")
    dish = await catalog.create_dish(session, active_user.id, "Phở", group.id)
    await catalog.update_dish(session, active_user.id, dish.id, name="Phở bò")
    entry = await _last_audit(session, "UPDATE_DISH")
    assert entry.before is not None and entry.before["TenMon"] == "Phở"
    assert entry.after is not None and entry.after["TenMon"] == "Phở bò"

    ing = await catalog.create_ingredient(session, active_user.id, "Hành", min_stock=1)
    await catalog.update_ingredient(session, active_user.id, ing.id, min_stock=2.5)
    entry = await _last_audit(session, "UPDATE_INGREDIENT")
    assert entry.before is not None and entry.before["MucTonToiThieu"] == 1
    assert entry.after is not None and entry.after["MucTonToiThieu"] == 2.5

    supplier = await catalog.create_supplier(session, active_user.id, "NCC A")
    await catalog.update_supplier(session, active_user.id, supplier.id, phone="0901")
    entry = await _last_audit(session, "UPDATE_SUPPLIER")
    assert entry.before is not None and entry.before["DienThoai"] is None
    assert entry.after is not None and entry.after["DienThoai"] == "0901"

    table = await catalog.create_table(session, active_user.id, "B9", capacity=4)
    await catalog.update_table(session, active_user.id, table.id, capacity=6)
    entry = await _last_audit(session, "UPDATE_TABLE")
    assert entry.before is not None and entry.before["SoChoNgoi"] == 4
    assert entry.after is not None and entry.after["SoChoNgoi"] == 6


@pytest.mark.anyio
async def test_move_table_and_cancel_receipt_record_before(session, active_user):
    dish, _, _ = await _setup_dish_with_stock(session, stock_qty=10)
    source = await _setup_table(session, "B1")
    target = await _setup_table(session, "B2")
    result = await orders.submit_order(
        session,
        {"table_id": source.id, "lines": [{"dish_id": dish.id, "quantity": 1}]},
        actor_id=active_user.id,
    )
    await orders.move_table(session, result["order"].id, target.id, actor_id=active_user.id)
    entry = await _last_audit(session, "MOVE_ORDER_TABLE")
    assert entry.before == {"MaBan": source.id}
    assert entry.after == {"MaBan": target.id}

    ing = await _ingredient(session, "Nấm")
    receipt = await inventory.create_receipt(
        session,
        active_user.id,
        None,
        None,
        [{"ingredient_id": ing.id, "quantity": 3, "unit_price": 1000}],
    )
    await inventory.cancel_receipt(session, active_user.id, receipt.id)
    entry = await _last_audit(session, "CANCEL_RECEIPT")
    assert entry.before is not None
    assert entry.before["TrangThai"] == "Hiệu lực"
    assert entry.before["ChiTiet"][0]["SoLuong"] == 3
    assert entry.after == {"TrangThai": "Đã hủy"}
    assert isinstance(await session.get(DiningTable, target.id), DiningTable)
