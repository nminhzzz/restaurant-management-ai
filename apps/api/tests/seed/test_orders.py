"""Phase 7 Task 2 — twelve months of orders with realistic patterns (NFR-03).

The DB-backed half is marked `slow`: it builds a year through the services, which is
far too much work for every `make gate`. Run it explicitly:

    cd apps/api && ./.venv/bin/pytest tests/seed/test_orders.py -m slow
"""

from datetime import date, timedelta

import pytest
from scripts.seed.config import SeedConfig
from scripts.seed.operations import daily_order_count, dish_order_counts, hour_weight
from sqlalchemy import func, select
from tests.helpers import (
    FIXED_NOW,
    order_count_between,
    order_status_counts,
)

from app.modules.catalog.models import Ingredient
from app.modules.inventory.models import IngredientLot, StockMovement

pytestmark = pytest.mark.slow

config = SeedConfig(seed=42, months=12, now=FIXED_NOW)


def test_the_day_has_two_peaks():
    """Appendix 4: lunch and dinner peaks."""
    lunch = hour_weight(12) + hour_weight(13)
    afternoon = hour_weight(15) + hour_weight(16)

    assert lunch > afternoon
    assert hour_weight(19) > afternoon


def test_weekends_are_busier_than_weekdays():
    saturday = daily_order_count(config, date(2026, 9, 26))  # Saturday
    tuesday = daily_order_count(config, date(2026, 9, 22))  # Tuesday

    assert saturday > tuesday


def test_the_monthly_volume_reaches_the_nfr_03_floor():
    """NFR-03: at least 20.000 orders a year."""
    total = sum(
        daily_order_count(config, date(2026, 1, 1) + timedelta(days=offset))
        for offset in range(365)
    )

    assert total >= 20_000


def test_a_few_dishes_take_most_of_the_orders():
    """Appendix 4: a power-law distribution, not a flat one."""
    counts = dish_order_counts(config, days=30)

    top_ten = sum(sorted(counts.values(), reverse=True)[:10])
    assert top_ten > sum(counts.values()) * 0.5


async def test_generated_orders_respect_business_invariants(session, seeded_year):
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


async def test_the_three_tiers_agree_after_a_full_year(session, seeded_year):
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


async def test_every_order_has_a_plausible_final_state(session, seeded_year):
    statuses = await order_status_counts(session)

    assert statuses
    assert set(statuses) <= {
        "Đã thanh toán",
        "Chờ đối soát",
        "Tranh chấp",
        "Đã hủy",
        "Tự động đóng",
    }


async def test_orders_land_on_both_sides_of_the_0600_boundary(session, seeded_year):
    """A generator that only emits daytime orders would hide timezone bugs."""
    from datetime import time

    early = await order_count_between(session, time(0, 0), time(5, 59))
    late = await order_count_between(session, time(18, 0), time(23, 59))

    assert early > 0
    assert late > 0
