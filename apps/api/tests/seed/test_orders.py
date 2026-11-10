"""Two months of orders with realistic patterns (Appendix B.1).

The DB-backed half is marked `slow`: it builds the dataset through the services, which
is far too much work for every `make gate`. Run it explicitly:

    cd apps/api && ./.venv/bin/pytest tests/seed/test_orders.py -m slow
"""

from datetime import date, time

import pytest
from scripts.seed.catalog import build_catalogue
from scripts.seed.config import MAX_RECEIPT_LINE_KG, MAX_STOCK_KG, SeedConfig
from scripts.seed.operations import (
    daily_order_count,
    dish_order_counts,
    hour_weight,
    seed_days,
    validate_stock_ceiling,
)
from sqlalchemy import func, select
from tests.helpers import (
    FIXED_NOW,
    order_count_between,
    order_status_counts,
)

from app.modules.catalog.models import Ingredient
from app.modules.inventory.models import (
    GoodsReceipt,
    GoodsReceiptLine,
    IngredientLot,
    StockIssue,
    StockMovement,
)

pytestmark = pytest.mark.slow

config = SeedConfig(seed=42, now=FIXED_NOW)


def test_the_day_has_two_peaks():
    """Appendix B.1: lunch and dinner peaks."""
    lunch = hour_weight(12) + hour_weight(13)
    afternoon = hour_weight(15) + hour_weight(16)

    assert lunch > afternoon
    assert hour_weight(19) > afternoon


def test_weekends_are_busier_than_weekdays():
    saturday = daily_order_count(config, date(2026, 9, 26))  # Saturday
    tuesday = daily_order_count(config, date(2026, 9, 22))  # Tuesday

    assert saturday > tuesday


def test_nothing_is_ordered_while_the_restaurant_is_closed():
    """Appendix B.1: open from 10:00 to 22:00."""
    assert all(hour_weight(hour) == 0 for hour in (*range(0, 10), 22, 23))
    assert all(hour_weight(hour) > 0 for hour in range(10, 22))


def test_two_months_hold_about_4800_orders():
    """Appendix B.1: 70 orders on a weekday, 110 at the weekend, 60 business dates."""
    days = seed_days(config)

    assert len(days) == 60
    assert days[-1] < FIXED_NOW.date()
    assert 4_600 <= sum(daily_order_count(config, day) for day in days) <= 5_000


def test_a_few_dishes_take_most_of_the_orders():
    """Appendix B.1: a power-law distribution, not a flat one."""
    counts = dish_order_counts(config, days=30)

    top_ten = sum(sorted(counts.values(), reverse=True)[:10])
    assert top_ten > sum(counts.values()) * 0.5


async def test_generated_orders_respect_business_invariants(session, seeded_months):
    """The generator must not invent states the services would refuse."""
    assert (
        await session.scalar(
            select(func.count()).select_from(Ingredient).where(Ingredient.stock_qty < 0)
        )
        == 0
    )
    assert (
        await session.scalar(
            select(func.count())
            .select_from(IngredientLot)
            .where(IngredientLot.quantity_remaining < 0)
        )
        == 0
    )


async def test_the_three_tiers_agree_after_the_whole_period(session, seeded_months):
    for ingredient_id, total in await session.execute(select(Ingredient.id, Ingredient.stock_qty)):
        lots = await session.scalar(
            select(func.coalesce(func.sum(IngredientLot.quantity_remaining), 0)).where(
                IngredientLot.ingredient_id == ingredient_id
            )
        )
        ledger = await session.scalar(
            select(func.coalesce(func.sum(StockMovement.qty), 0)).where(
                StockMovement.ingredient_id == ingredient_id
            )
        )
        assert total == lots == ledger


async def test_every_order_has_a_plausible_final_state(session, seeded_months):
    statuses = await order_status_counts(session)

    assert statuses
    assert set(statuses) <= {
        "Đã thanh toán",
        "Chờ xác minh thanh toán",
        "Đóng \u2013 chưa thu được tiền",
        "Đã hủy",
    }


async def test_orders_are_placed_only_during_opening_hours(session, seeded_months):
    assert await order_count_between(session, time(22, 0), time(23, 59)) == 0
    assert await order_count_between(session, time(0, 0), time(9, 59)) == 0
    assert await order_count_between(session, time(10, 0), time(21, 59)) == seeded_months.orders


async def test_the_storeroom_never_holds_more_than_a_small_kitchen_can(session, seeded_months):
    """Appendix B.1: at most 30 kg on a receipt line and 40 kg of one ingredient in stock."""
    assert (
        await session.scalar(select(func.max(GoodsReceiptLine.quantity)))
    ) <= MAX_RECEIPT_LINE_KG
    assert (await session.scalar(select(func.max(Ingredient.stock_qty)))) <= MAX_STOCK_KG
    await validate_stock_ceiling(session)


async def test_every_delivery_is_priced_inside_the_band_of_its_ingredient(session, seeded_months):
    specs = build_catalogue().ingredients
    rows = await session.execute(
        select(Ingredient.name, GoodsReceiptLine.unit_price).join(
            Ingredient, Ingredient.id == GoodsReceiptLine.ingredient_id
        )
    )

    for name, unit_price in rows:
        low, high = specs[name].category.price_range
        assert low <= unit_price <= high, name


async def test_each_supplier_delivers_only_its_own_kind_of_goods(session, seeded_months):
    specs = build_catalogue().ingredients
    from app.modules.catalog.models import Supplier

    rows = await session.execute(
        select(Supplier.name, Ingredient.name)
        .select_from(GoodsReceiptLine)
        .join(GoodsReceipt, GoodsReceipt.id == GoodsReceiptLine.receipt_id)
        .join(Supplier, Supplier.id == GoodsReceipt.supplier_id)
        .join(Ingredient, Ingredient.id == GoodsReceiptLine.ingredient_id)
        .distinct()
    )

    for supplier, ingredient in rows:
        assert specs[ingredient].category.supplier == supplier


async def test_expired_stock_does_not_pile_up_on_the_books(session, seeded_months):
    """A kitchen throws out what has passed its date; only yesterday's leftovers remain."""
    last_day = seed_days(SeedConfig(seed=42, months=2, orders_target=600, now=FIXED_NOW))[-1]

    stale = await session.scalar(
        select(func.count())
        .select_from(IngredientLot)
        .where(IngredientLot.quantity_remaining > 0, IngredientLot.expiry_date < last_day)
    )

    assert stale == 0
    assert seeded_months.expired_issues == await session.scalar(
        select(func.count()).select_from(StockIssue).where(StockIssue.reason == "Hết hạn")
    )
