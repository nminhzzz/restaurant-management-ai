"""Server-side selection holds reserve FIFO lots without moving stock."""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core.errors import BusinessRuleError
from app.modules.catalog.models import Dish, DishPriceVersion, Ingredient, Recipe, RecipeItem
from app.modules.inventory.models import (
    GoodsReceipt,
    GoodsReceiptLine,
    IngredientLot,
    StockMovement,
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
from app.modules.sales.models import ItemHoldLot
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
    dish = Dish(name="Held dish", missing_recipe=False, out_of_stock=False)
    session.add_all([user, ingredient, dish])
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
    stocktake = await create_stocktake(session, user.id)
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
    stocktake = await create_stocktake(session, user.id)
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
    await create_stocktake(session, user_id)
    await session.commit()

    with pytest.raises(BusinessRuleError, match="Đang kiểm kê"):
        await upsert_hold(session, user_id, "selection-b", dish_id, 1, None, None, None)
    await session.rollback()
    with pytest.raises(BusinessRuleError, match="Đang kiểm kê"):
        await release_hold(session, user_id, hold_id)
