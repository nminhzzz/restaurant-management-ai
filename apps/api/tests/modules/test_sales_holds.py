"""Server-side selection holds reserve FIFO lots without moving stock."""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import get_session
from app.core.errors import BusinessRuleError
from app.core.security import create_access_token
from app.main import app
from app.modules.catalog.models import (
    Dish,
    DishGroup,
    DishPriceVersion,
    Ingredient,
    Recipe,
    RecipeItem,
)
from app.modules.inventory.models import (
    GoodsReceipt,
    GoodsReceiptLine,
    IngredientLot,
    StockMovement,
    Stocktake,
)
from app.modules.inventory.service import (
    cancel_receipt,
    confirm_stocktake,
    create_issue,
    create_stocktake,
    record_counts,
    update_receipt,
)
from app.modules.sales.holds import (
    list_holds,
    reallocate_expired_hold,
    release_hold,
    upsert_hold,
)
from app.modules.sales.models import ItemHold, ItemHoldLot, Order
from app.modules.sales.orders import cancel_order, submit_order
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from app.shared import business_date
from app.shared.business_date import VN_TZ
from tests.helpers import FIXED_NOW


async def _setup(session, *, quantities=(3, 4), expiry_dates=(None, None)):
    await seed_reference_data(session)
    user = User(
        username="hold_owner",
        password_hash="unused",
        full_name="Hold owner",
        role_id="CASHIER",
        status="Hoạt động",
    )
    ingredient = Ingredient(
        name="Hold ingredient", unit="kg", min_stock=0, stock_qty=sum(quantities)
    )
    group = DishGroup(name="Held group", display_order=1)
    session.add_all([user, ingredient, group])
    await session.flush()
    dish = Dish(name="Held dish", group_id=group.id, missing_recipe=False, out_of_stock=False)
    session.add(dish)
    await session.flush()
    bd = date(2026, 9, 24)
    price = DishPriceVersion(dish_id=dish.id, price=10000, business_date=bd, status="Đang áp dụng")
    recipe = Recipe(dish_id=dish.id, business_date=bd, status="Đang áp dụng")
    session.add_all([price, recipe])
    await session.flush()
    session.add(RecipeItem(recipe_id=recipe.id, ingredient_id=ingredient.id, quantity=1))
    lots = []
    for index, (quantity, expiry) in enumerate(zip(quantities, expiry_dates, strict=True)):
        receipt = GoodsReceipt(receipt_date=FIXED_NOW - timedelta(days=2 - index), status="Nháp")
        session.add(receipt)
        await session.flush()
        line = GoodsReceiptLine(
            receipt_id=receipt.id, ingredient_id=ingredient.id, quantity=quantity, unit_price=1000
        )
        session.add(line)
        await session.flush()
        lot = IngredientLot(
            ingredient_id=ingredient.id,
            receipt_line_id=line.id,
            quantity_remaining=quantity,
            received_at=receipt.receipt_date,
            status="Còn hạn",
            expiry_date=expiry,
        )
        session.add(lot)
        lots.append(lot)
    await session.commit()
    return user, dish, ingredient, lots


async def _client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _auth(user):
    token = create_access_token(str(user.id), {"role": user.role_id, "username": user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_selection_routes_submit_exact_held_lots_once(session):
    user, dish, ingredient, lots = await _setup(session)
    client = await _client(session)
    headers = _auth(user)
    created = await client.post("/api/v1/sales/selections", json={}, headers=headers)
    assert created.status_code == 201, created.text
    selection_id = created.json()["MaLuotChon"]
    hold_response = await client.put(
        f"/api/v1/sales/selections/{selection_id}/lines/{dish.id}",
        json={"SoLuong": 5, "GhiChu": "Ít cay"},
        headers=headers,
    )
    assert hold_response.status_code == 200, hold_response.text
    hold_id = hold_response.json()["MaGiuCho"]
    submitted = await client.post(
        f"/api/v1/sales/selections/{selection_id}/submit",
        json={"MaYeuCauGui": "send-exact-lots"},
        headers=headers,
    )
    assert submitted.status_code == 200, submitted.text
    body = submitted.json()
    assert body["CanXacNhanLai"] is False
    assert len(body["lines"]) == 1
    line_id = body["lines"][0]["MaChiTietOrder"]
    movements = (
        (
            await session.execute(
                select(StockMovement)
                .where(StockMovement.order_line_id == line_id)
                .order_by(StockMovement.id)
            )
        )
        .scalars()
        .all()
    )
    assert [(row.lot_id, row.qty) for row in movements] == [
        (lots[0].id, Decimal("-3")),
        (lots[1].id, Decimal("-2")),
    ]
    hold = await session.get(ItemHold, hold_id)
    assert hold.order_line_id == line_id
    assert hold.send_request_id == "send-exact-lots"
    assert hold.status == "Đã gửi"
    await session.refresh(ingredient)
    assert ingredient.stock_qty == 2
    session.add(Stocktake(status="Đang kiểm kê", performed_by=user.id))
    await session.commit()
    retry = await client.post(
        f"/api/v1/sales/selections/{selection_id}/submit",
        json={"MaYeuCauGui": "send-exact-lots"},
        headers=headers,
    )
    assert retry.status_code == 200
    assert retry.json() == body
    assert (await session.execute(select(Order))).scalars().all().__len__() == 1
    assert (await session.execute(select(StockMovement))).scalars().all().__len__() == 2


@pytest.mark.anyio
async def test_selection_submit_uses_one_consistent_price_and_recipe_snapshot(session, monkeypatch):
    from app.modules.sales import orders

    user, dish, _, _ = await _setup(session)
    client = await _client(session)
    headers = _auth(user)
    selection_id = (await client.post("/api/v1/sales/selections", json={}, headers=headers)).json()[
        "MaLuotChon"
    ]
    held = await client.put(
        f"/api/v1/sales/selections/{selection_id}/lines/{dish.id}",
        json={"SoLuong": 1},
        headers=headers,
    )
    hold = await session.get(ItemHold, held.json()["MaGiuCho"])
    held_price = await session.get(DishPriceVersion, hold.price_version_id)
    held_recipe = await session.get(Recipe, hold.recipe_id)
    ingredient_id = (
        await session.execute(
            select(RecipeItem.ingredient_id).where(RecipeItem.recipe_id == held_recipe.id)
        )
    ).scalar_one()
    original_lock_ingredients = orders.lock_ingredients
    simulated_update_calls = 0

    async def _simulate_apply_now_after_snapshot(_session, ingredient_ids):
        nonlocal simulated_update_calls
        simulated_update_calls += 1
        held_price.status = "Hết hiệu lực"
        session.add(
            DishPriceVersion(
                dish_id=dish.id,
                price=12000,
                business_date=date(2026, 9, 24),
                status="Đang áp dụng",
            )
        )
        held_recipe.status = "Hết hiệu lực"
        concurrently_applied_recipe = Recipe(
            dish_id=dish.id,
            business_date=date(2026, 9, 24),
            status="Đang áp dụng",
        )
        session.add(concurrently_applied_recipe)
        await session.flush()
        session.add(
            RecipeItem(
                recipe_id=concurrently_applied_recipe.id,
                ingredient_id=ingredient_id,
                quantity=2,
            )
        )
        await session.commit()
        await original_lock_ingredients(_session, ingredient_ids)

    async def _unguarded_reread(*_args):
        raise AssertionError("submit must reuse the version row locked for validation")

    monkeypatch.setattr(orders, "lock_ingredients", _simulate_apply_now_after_snapshot)
    monkeypatch.setattr(orders, "active_price_version", _unguarded_reread)
    monkeypatch.setattr(orders, "active_recipe", _unguarded_reread)
    response = await client.post(
        f"/api/v1/sales/selections/{selection_id}/submit",
        json={"MaYeuCauGui": "price-snapshot-race"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    line = response.json()["lines"][0]
    assert line["MaPhienBanGia"] == held_price.id
    assert line["MaCongThuc"] == held_recipe.id
    assert line["DonGia"] == 10000
    assert simulated_update_calls == 1


@pytest.mark.anyio
async def test_selection_routes_check_roles_owner_and_release(session):
    user, dish, _, _ = await _setup(session)
    other = User(
        username="other-cashier",
        password_hash="unused",
        full_name="Other",
        role_id="CASHIER",
        status="Hoạt động",
    )
    manager = User(
        username="hold-manager",
        password_hash="unused",
        full_name="Manager",
        role_id="MANAGER",
        status="Hoạt động",
    )
    warehouse = User(
        username="hold-warehouse",
        password_hash="unused",
        full_name="Warehouse",
        role_id="WAREHOUSE",
        status="Hoạt động",
    )
    session.add_all([other, manager, warehouse])
    await session.commit()
    client = await _client(session)
    assert (
        await client.post("/api/v1/sales/selections", json={}, headers=_auth(warehouse))
    ).status_code == 403
    assert (
        await client.post("/api/v1/sales/selections", json={}, headers=_auth(manager))
    ).status_code == 201
    selected = await client.post("/api/v1/sales/selections", json={}, headers=_auth(user))
    selection_id = selected.json()["MaLuotChon"]
    held = await client.put(
        f"/api/v1/sales/selections/{selection_id}/lines/{dish.id}",
        json={"SoLuong": 1},
        headers=_auth(user),
    )
    assert held.status_code == 200
    hold_id = held.json()["MaGiuCho"]
    assert (
        await client.put(
            f"/api/v1/sales/selections/{selection_id}/lines/{dish.id}",
            json={"SoLuong": 2},
            headers=_auth(other),
        )
    ).status_code in (403, 404)
    assert (
        await client.post(
            f"/api/v1/sales/selections/{selection_id}/submit",
            json={"MaYeuCauGui": "other-send"},
            headers=_auth(other),
        )
    ).status_code in (403, 404)
    assert (
        await client.delete(f"/api/v1/sales/holds/{hold_id}", headers=_auth(other))
    ).status_code in (403, 404)
    released = await client.delete(f"/api/v1/sales/holds/{hold_id}", headers=_auth(user))
    assert released.status_code == 200
    assert (await session.get(ItemHold, hold_id)).status == "Đã hủy"


@pytest.mark.anyio
async def test_stale_price_releases_hold_and_requests_reconfirmation(session):
    user, dish, ingredient, _ = await _setup(session)
    client = await _client(session)
    headers = _auth(user)
    selection_id = (await client.post("/api/v1/sales/selections", json={}, headers=headers)).json()[
        "MaLuotChon"
    ]
    held = await client.put(
        f"/api/v1/sales/selections/{selection_id}/lines/{dish.id}",
        json={"SoLuong": 2},
        headers=headers,
    )
    hold_id = held.json()["MaGiuCho"]
    session.add(
        DishPriceVersion(
            dish_id=dish.id, price=12000, business_date=date(2026, 9, 24), status="Đang áp dụng"
        )
    )
    await session.commit()
    response = await client.post(
        f"/api/v1/sales/selections/{selection_id}/submit",
        json={"MaYeuCauGui": "stale-send"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["CanXacNhanLai"] is True
    assert response.json()["stale"][0]["MaGiuCho"] == hold_id
    assert (await session.get(ItemHold, hold_id)).status == "Đã hủy"
    await session.refresh(ingredient)
    assert ingredient.stock_qty == 7
    assert (await session.execute(select(Order))).scalars().all() == []


@pytest.mark.anyio
async def test_stale_recipe_releases_hold_and_requests_reconfirmation(session):
    user, dish, ingredient, _ = await _setup(session)
    client = await _client(session)
    headers = _auth(user)
    selection_id = (await client.post("/api/v1/sales/selections", json={}, headers=headers)).json()[
        "MaLuotChon"
    ]
    held = await client.put(
        f"/api/v1/sales/selections/{selection_id}/lines/{dish.id}",
        json={"SoLuong": 1},
        headers=headers,
    )
    hold_id = held.json()["MaGiuCho"]
    new_recipe = Recipe(dish_id=dish.id, business_date=date(2026, 9, 24), status="Đang áp dụng")
    session.add(new_recipe)
    await session.flush()
    session.add(RecipeItem(recipe_id=new_recipe.id, ingredient_id=ingredient.id, quantity=2))
    await session.commit()

    response = await client.post(
        f"/api/v1/sales/selections/{selection_id}/submit",
        json={"MaYeuCauGui": "stale-recipe"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["CanXacNhanLai"] is True
    assert response.json()["stale"] == [{"MaGiuCho": hold_id, "MaMon": dish.id}]
    assert (await session.get(ItemHold, hold_id)).status == "Đã hủy"
    assert (await session.execute(select(Order))).scalars().all() == []
    assert (await session.execute(select(StockMovement))).scalars().all() == []


@pytest.mark.anyio
async def test_selection_submit_reallocates_an_expired_hold_before_conversion(session):
    user, dish, ingredient, _ = await _setup(session)
    client = await _client(session)
    headers = _auth(user)
    selection_id = (await client.post("/api/v1/sales/selections", json={}, headers=headers)).json()[
        "MaLuotChon"
    ]
    held = await client.put(
        f"/api/v1/sales/selections/{selection_id}/lines/{dish.id}",
        json={"SoLuong": 2},
        headers=headers,
    )
    hold_id = held.json()["MaGiuCho"]
    hold = await session.get(ItemHold, hold_id)
    hold.expires_at = FIXED_NOW.replace(tzinfo=None) - timedelta(minutes=1)
    await session.commit()

    submitted = await client.post(
        f"/api/v1/sales/selections/{selection_id}/submit",
        json={"MaYeuCauGui": "expired-reallocation"},
        headers=headers,
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["CanXacNhanLai"] is False
    await session.refresh(hold)
    assert hold.status == "Đã gửi"
    movements = (
        (
            await session.execute(
                select(StockMovement).where(StockMovement.order_line_id == hold.order_line_id)
            )
        )
        .scalars()
        .all()
    )
    assert sum((Decimal(str(row.qty)) for row in movements), Decimal(0)) == Decimal("-2")
    await session.refresh(ingredient)
    assert ingredient.stock_qty == 5


@pytest.mark.anyio
async def test_selection_submit_rolls_back_all_lines_when_a_later_hold_is_invalid(session):
    user, dish, ingredient, _ = await _setup(session)
    second_dish = Dish(
        name="Second held dish", group_id=dish.group_id, missing_recipe=False, out_of_stock=False
    )
    session.add(second_dish)
    await session.flush()
    second_price = DishPriceVersion(
        dish_id=second_dish.id, price=15000, business_date=date(2026, 9, 24), status="Đang áp dụng"
    )
    second_recipe = Recipe(
        dish_id=second_dish.id, business_date=date(2026, 9, 24), status="Đang áp dụng"
    )
    session.add_all([second_price, second_recipe])
    await session.flush()
    session.add(RecipeItem(recipe_id=second_recipe.id, ingredient_id=ingredient.id, quantity=1))
    await session.commit()

    client = await _client(session)
    headers = _auth(user)
    selection_id = (await client.post("/api/v1/sales/selections", json={}, headers=headers)).json()[
        "MaLuotChon"
    ]
    first = await client.put(
        f"/api/v1/sales/selections/{selection_id}/lines/{dish.id}",
        json={"SoLuong": 1},
        headers=headers,
    )
    second = await client.put(
        f"/api/v1/sales/selections/{selection_id}/lines/{second_dish.id}",
        json={"SoLuong": 1},
        headers=headers,
    )
    assert first.status_code == second.status_code == 200
    second_hold_id = second.json()["MaGiuCho"]
    await session.execute(
        ItemHoldLot.__table__.delete().where(ItemHoldLot.hold_id == second_hold_id)
    )
    await session.commit()

    failed = await client.post(
        f"/api/v1/sales/selections/{selection_id}/submit",
        json={"MaYeuCauGui": "rollback-all-lines"},
        headers=headers,
    )
    assert failed.status_code == 422
    await session.rollback()
    assert (await session.execute(select(Order))).scalars().all() == []
    assert (await session.execute(select(StockMovement))).scalars().all() == []
    assert (await session.get(ItemHold, first.json()["MaGiuCho"])).status == "Đang giữ"


@pytest.mark.anyio
async def test_selection_submit_observes_active_stocktake_gate(session):
    user, dish, _, _ = await _setup(session)
    client = await _client(session)
    headers = _auth(user)
    selection_id = (await client.post("/api/v1/sales/selections", json={}, headers=headers)).json()[
        "MaLuotChon"
    ]
    held = await client.put(
        f"/api/v1/sales/selections/{selection_id}/lines/{dish.id}",
        json={"SoLuong": 1},
        headers=headers,
    )
    assert held.status_code == 200
    session.add(
        Stocktake(
            status="Đang kiểm kê",
            performed_by=user.id,
        )
    )
    await session.commit()
    response = await client.post(
        f"/api/v1/sales/selections/{selection_id}/submit",
        json={"MaYeuCauGui": "stocktake-blocked"},
        headers=headers,
    )
    assert response.status_code == 422
    assert "kiểm kê" in response.json()["error"]["message"]


@pytest.mark.anyio
async def test_hold_allocates_fifo_and_preserves_stock_ledger(session):
    user, dish, ingredient, lots = await _setup(session)

    hold = await upsert_hold(session, user.id, "selection-a", dish.id, 5, None, None, None)

    allocations = (
        (await session.execute(select(ItemHoldLot).where(ItemHoldLot.hold_id == hold.id)))
        .scalars()
        .all()
    )
    assert [(row.lot_id, row.quantity_held) for row in allocations] == [
        (lots[0].id, Decimal("3")),
        (lots[1].id, Decimal("2")),
    ]
    await session.refresh(ingredient)
    assert ingredient.stock_qty == 7
    assert (await session.execute(select(StockMovement))).scalars().all() == []


@pytest.mark.anyio
async def test_competing_hold_cannot_overbook_and_release_restores_availability(session):
    user, dish, _, _ = await _setup(session)
    user_id, dish_id = user.id, dish.id
    await upsert_hold(session, user.id, "selection-a", dish.id, 5, None, None, None)
    await session.commit()
    with pytest.raises(BusinessRuleError, match="Không đủ tồn kho"):
        await upsert_hold(session, user_id, "selection-b", dish_id, 3, None, None, None)
    await session.rollback()
    first = (await list_holds(session, user_id, "selection-a"))[0]
    await release_hold(session, user_id, first.id)
    second = await upsert_hold(session, user_id, "selection-b", dish_id, 3, None, None, None)
    assert second.quantity == 3


@pytest.mark.anyio
async def test_hold_ttl_is_capped_by_earliest_lot_expiry(session, monkeypatch):
    expiry = date(2026, 9, 24)
    user, dish, _, _ = await _setup(session, expiry_dates=(expiry, None))
    monkeypatch.setattr(business_date, "now", lambda: datetime(2026, 9, 24, 23, 58))
    hold = await upsert_hold(session, user.id, "selection-a", dish.id, 2, None, None, None)
    assert hold.expires_at == datetime(2026, 9, 25)


@pytest.mark.anyio
async def test_expiry_dated_hold_accepts_aware_local_clock(session, monkeypatch):
    user, dish, _, _ = await _setup(session, expiry_dates=(date(2026, 9, 24), None))
    aware_now = datetime(2026, 9, 24, 23, 58, tzinfo=VN_TZ)
    monkeypatch.setattr(business_date, "now", lambda: aware_now)

    hold = await upsert_hold(session, user.id, "selection-aware", dish.id, 2, None, None, None)
    assert hold.expires_at == datetime(2026, 9, 25)
    assert hold.expires_at.tzinfo is None
    hold_id, user_id = hold.id, user.id
    await session.commit()
    refreshed = await reallocate_expired_hold(session, user_id, hold_id)
    assert refreshed.expires_at == datetime(2026, 9, 25)


@pytest.mark.anyio
async def test_expired_hold_stays_visible_but_no_longer_reserves_stock(session, monkeypatch):
    user, dish, _, _ = await _setup(session)
    hold = await upsert_hold(session, user.id, "selection-a", dish.id, 7, None, None, None)
    await session.commit()
    monkeypatch.setattr(business_date, "now", lambda: FIXED_NOW + timedelta(minutes=6))
    listed = await list_holds(session, user.id, "selection-a")
    assert [row.id for row in listed] == [hold.id]
    other = await upsert_hold(session, user.id, "selection-b", dish.id, 7, None, None, None)
    assert other.id != hold.id


@pytest.mark.anyio
async def test_expired_hold_reallocates_at_submit_only_when_stock_is_available(
    session, monkeypatch
):
    user, dish, _, _ = await _setup(session)
    hold = await upsert_hold(session, user.id, "selection-a", dish.id, 7, None, None, None)
    await session.commit()
    monkeypatch.setattr(business_date, "now", lambda: FIXED_NOW + timedelta(minutes=6))
    other = await upsert_hold(session, user.id, "selection-b", dish.id, 7, None, None, None)
    await session.commit()
    hold_id, other_id, user_id = hold.id, other.id, user.id

    with pytest.raises(BusinessRuleError, match="Không đủ tồn kho"):
        await reallocate_expired_hold(session, user_id, hold_id)
    await session.rollback()
    await release_hold(session, user_id, other_id)
    renewed = await reallocate_expired_hold(session, user_id, hold_id)
    assert renewed.expires_at == FIXED_NOW + timedelta(minutes=11)


@pytest.mark.anyio
async def test_manual_issue_cannot_consume_quantities_reserved_by_hold(session):
    user, dish, ingredient, _ = await _setup(session)
    await upsert_hold(session, user.id, "selection-a", dish.id, 5, None, None, None)
    await session.commit()

    with pytest.raises(BusinessRuleError, match="Không đủ tồn kho"):
        await create_issue(
            session,
            user.id,
            "Hao hụt",
            [{"ingredient_id": ingredient.id, "quantity": 3}],
        )
    await session.rollback()


@pytest.mark.anyio
async def test_stock_draw_excludes_expired_lots_even_before_expiry_cleanup(session):
    user, _, ingredient, _ = await _setup(session, expiry_dates=(date(2026, 9, 23), None))
    with pytest.raises(BusinessRuleError, match="Không đủ tồn kho"):
        await create_issue(
            session,
            user.id,
            "Hao hụt",
            [{"ingredient_id": ingredient.id, "quantity": 5}],
        )


@pytest.mark.anyio
async def test_receipt_cancellation_cannot_remove_a_held_lot(session):
    user, dish, _, lots = await _setup(session)
    await upsert_hold(session, user.id, "selection-a", dish.id, 2, None, None, None)
    await session.commit()
    line = await session.get(GoodsReceiptLine, lots[0].receipt_line_id)

    with pytest.raises(BusinessRuleError, match="đang được giữ"):
        await cancel_receipt(session, user.id, line.receipt_id)


@pytest.mark.anyio
async def test_receipt_edit_cannot_shrink_below_held_quantity(session):
    user, dish, _, lots = await _setup(session)
    await upsert_hold(session, user.id, "selection-a", dish.id, 3, None, None, None)
    await session.commit()
    line = await session.get(GoodsReceiptLine, lots[0].receipt_line_id)

    with pytest.raises(BusinessRuleError, match="đang được giữ"):
        await update_receipt(
            session,
            user.id,
            line.receipt_id,
            [{"line_id": line.id, "quantity": 2, "unit_price": 1000}],
        )


async def _open_stocktake_over_live_holds(session, user_id):
    """create_stocktake refuses to open over live holds (FR-INV-08), so the defensive
    confirm-time checks are exercised on a session inserted directly."""
    stocktake = Stocktake(status="Đang kiểm kê", performed_by=user_id)
    session.add(stocktake)
    await session.flush()
    return stocktake


@pytest.mark.anyio
async def test_active_stocktake_blocks_order_reversal(session):
    user, dish, ingredient, _ = await _setup(session)
    result = await submit_order(
        session,
        {"order_type": "Mang về", "lines": [{"dish_id": dish.id, "quantity": 2}]},
        actor_id=user.id,
    )
    order_id = result["order"].id
    await session.commit()
    await create_stocktake(session, user.id)
    await session.commit()

    with pytest.raises(BusinessRuleError, match="Đang kiểm kê"):
        await cancel_order(session, order_id, "Khách hủy", actor_id=user.id)
    await session.rollback()
    await session.refresh(ingredient)
    assert ingredient.stock_qty == 5


@pytest.mark.anyio
async def test_submit_recheck_rejects_expired_hold_invalidated_by_stocktake(session, monkeypatch):
    user, dish, ingredient, _ = await _setup(session)
    hold = await upsert_hold(session, user.id, "selection-a", dish.id, 5, None, None, None)
    hold_id, user_id, ingredient_id = hold.id, user.id, ingredient.id
    await session.commit()
    monkeypatch.setattr(business_date, "now", lambda: FIXED_NOW + timedelta(minutes=6))
    stocktake = await create_stocktake(session, user_id)
    await record_counts(session, stocktake.id, [(ingredient_id, Decimal(2))])
    await confirm_stocktake(session, user_id, stocktake.id)
    await session.commit()

    with pytest.raises(BusinessRuleError, match="Không đủ tồn kho"):
        await reallocate_expired_hold(session, user_id, hold_id)


@pytest.mark.anyio
async def test_stocktake_rejects_actual_below_active_hold_quantity(session):
    user, dish, ingredient, lots = await _setup(session)
    hold = await upsert_hold(session, user.id, "selection-a", dish.id, 5, None, None, None)
    await session.commit()
    stocktake = await _open_stocktake_over_live_holds(session, user.id)
    await record_counts(session, stocktake.id, [(ingredient.id, Decimal(4))])

    with pytest.raises(BusinessRuleError, match="đang được giữ"):
        await confirm_stocktake(session, user.id, stocktake.id)

    assert [lot.quantity_remaining for lot in lots] == [3, 4]
    assert ingredient.stock_qty == 7
    assert hold.status == "Đang giữ"


@pytest.mark.anyio
async def test_stocktake_draws_only_unheld_lot_quantities(session):
    user, dish, ingredient, lots = await _setup(session)
    hold = await upsert_hold(session, user.id, "selection-a", dish.id, 5, None, None, None)
    await session.commit()
    stocktake = await _open_stocktake_over_live_holds(session, user.id)
    await record_counts(session, stocktake.id, [(ingredient.id, Decimal(5))])
    await confirm_stocktake(session, user.id, stocktake.id)
    await session.flush()

    allocations = (
        (await session.execute(select(ItemHoldLot).where(ItemHoldLot.hold_id == hold.id)))
        .scalars()
        .all()
    )
    assert [lot.quantity_remaining for lot in lots] == [3, 2]
    assert [(row.lot_id, row.quantity_held) for row in allocations] == [
        (lots[0].id, Decimal(3)),
        (lots[1].id, Decimal(2)),
    ]
    assert ingredient.stock_qty == 5


@pytest.mark.anyio
async def test_active_stocktake_blocks_hold_creation_and_release(session):
    user, dish, _, _ = await _setup(session)
    hold = await upsert_hold(session, user.id, "selection-a", dish.id, 2, None, None, None)
    hold_id, user_id, dish_id = hold.id, user.id, dish.id
    await session.commit()
    await _open_stocktake_over_live_holds(session, user_id)
    await session.commit()

    with pytest.raises(BusinessRuleError, match="Đang kiểm kê"):
        await upsert_hold(session, user_id, "selection-b", dish_id, 1, None, None, None)
    await session.rollback()
    with pytest.raises(BusinessRuleError, match="Đang kiểm kê"):
        await release_hold(session, user_id, hold_id)
