"""The seed catalogue: a believable small menu inside the ranges of Appendix B.1."""

from collections import Counter

import pytest
from scripts.seed.catalog import (
    CATEGORIES,
    DISH_PRICE_RANGE,
    DISH_PRICE_STEP,
    DRY,
    MEAT,
    PRODUCE,
    RECIPE_QUANTITY_RANGE_KG,
    RECIPE_SIZE_RANGE,
    build_catalogue,
    seed_catalog,
)
from scripts.seed.config import PRICE_JITTER, SeedConfig
from sqlalchemy import select
from tests.helpers import active_recipe, today

from app.modules.catalog.models import Dish, DishGroup, Ingredient


def food_cost(plan, dish: str) -> float:
    return sum(
        quantity * plan.ingredients[ingredient].unit_price
        for ingredient, quantity in plan.recipes[dish].items()
    )


def test_the_catalogue_is_the_same_on_every_run():
    """Repeatable experiments need repeatable data."""
    first = build_catalogue()
    second = build_catalogue()

    assert first.dish_names == second.dish_names
    assert first.recipes == second.recipes
    assert first.prices == second.prices


def test_the_catalogue_has_the_size_the_report_describes():
    """Appendix B.1: 30 dishes in 4 groups, 35 ingredients, 12 tables, 3 suppliers."""
    plan = build_catalogue()

    assert len(set(plan.dish_names)) == 30
    assert len(set(plan.ingredient_names)) == 35
    assert len(plan.tables) == 12
    assert len(set(plan.supplier_names)) == 3
    assert sorted(Counter(plan.groups.values()).values()) == [7, 7, 8, 8]
    assert set(plan.groups.values()) == set(plan.group_names)


def test_ingredients_fall_into_the_three_storage_classes():
    """Appendix B.1: 10 meat and seafood, 12 noodles and produce, 13 dry goods."""
    by_category = Counter(spec.category for spec in build_catalogue().ingredients.values())

    assert by_category == {MEAT: 10, PRODUCE: 12, DRY: 13}
    assert (MEAT.shelf_days, PRODUCE.shelf_days, DRY.shelf_days) == (3, 7, 365)
    assert (MEAT.min_stock_kg, PRODUCE.min_stock_kg, DRY.min_stock_kg) == (2, 2, 0.5)


def test_every_recipe_uses_known_ingredients_in_serving_sized_amounts():
    plan = build_catalogue()

    for dish in plan.dish_names:
        recipe = plan.recipes[dish]
        assert RECIPE_SIZE_RANGE[0] <= len(recipe) <= RECIPE_SIZE_RANGE[1], dish
        for ingredient, quantity in recipe.items():
            assert ingredient in plan.ingredients, (dish, ingredient)
            low, high = RECIPE_QUANTITY_RANGE_KG
            assert low <= quantity <= high, (dish, ingredient)


def test_no_ingredient_is_bought_without_a_dish_that_uses_it():
    plan = build_catalogue()
    used = {ingredient for recipe in plan.recipes.values() for ingredient in recipe}

    assert used == set(plan.ingredient_names)


def test_menu_prices_stay_on_the_price_ladder():
    plan = build_catalogue()

    for dish, price in plan.prices.items():
        assert DISH_PRICE_RANGE[0] <= price <= DISH_PRICE_RANGE[1], dish
        assert price % DISH_PRICE_STEP == 0, dish


def test_purchase_prices_stay_in_their_band_even_at_the_edge_of_the_swing():
    for spec in build_catalogue().ingredients.values():
        low, high = spec.category.price_range
        assert low <= spec.unit_price * (1 - PRICE_JITTER), spec.name
        assert spec.unit_price * (1 + PRICE_JITTER) <= high, spec.name


def test_every_dish_sells_above_its_ingredient_cost_with_a_plausible_margin():
    """A random recipe can cost more than the dish sells for; a real menu cannot."""
    plan = build_catalogue()

    for dish in plan.dish_names:
        ratio = food_cost(plan, dish) / plan.prices[dish]
        assert 0.10 <= ratio <= 0.45, (dish, round(ratio, 3))


def test_the_dearest_dishes_are_built_on_meat_or_seafood():
    plan = build_catalogue()
    dearest = sorted(plan.dish_names, key=plan.prices.__getitem__, reverse=True)[:5]

    for dish in dearest:
        assert any(plan.ingredients[i].category is MEAT for i in plan.recipes[dish]), dish


@pytest.mark.anyio
async def test_seeding_persists_exactly_what_was_planned(session, seeded_reference):
    """The pure plan and the database must not drift apart."""
    plan = build_catalogue()

    ids = await seed_catalog(session, SeedConfig(seed=42))

    assert ids.dish_names == plan.dish_names
    assert len(ids.dish_ids) == len(plan.dish_names)
    groups = dict(
        (
            await session.execute(
                select(Dish.name, DishGroup.name).join(DishGroup, DishGroup.id == Dish.group_id)
            )
        )
        .tuples()
        .all()
    )
    assert groups == plan.groups
    stored = {
        name: (float(min_stock), shelf_days)
        for name, min_stock, shelf_days in await session.execute(
            select(Ingredient.name, Ingredient.min_stock, Ingredient.shelf_days)
        )
    }
    assert stored == {
        name: (spec.category.min_stock_kg, spec.category.shelf_days)
        for name, spec in plan.ingredients.items()
    }


@pytest.mark.anyio
async def test_every_ingredient_has_restocking_terms_from_its_own_supplier(
    session, seeded_reference
):
    ids = await seed_catalog(session, SeedConfig(seed=42))

    assert {supply.ingredient_id for supply in ids.supplies} == set(ids.ingredient_ids)
    assert len({supply.supplier_id for supply in ids.supplies}) == len(CATEGORIES)
    assert all(supply.use_per_order_kg > 0 for supply in ids.supplies)


@pytest.mark.anyio
async def test_every_dish_has_an_active_recipe_so_it_can_be_ordered(session, seeded_reference):
    ids = await seed_catalog(session, SeedConfig(seed=42))

    for dish_id in ids.dish_ids:
        assert await active_recipe(session, dish_id, today()) is not None


@pytest.mark.anyio
async def test_three_accounts_cover_the_three_roles(session, seeded_reference):
    ids = await seed_catalog(session, SeedConfig(seed=42))

    assert {user.role for user in ids.users} == {"MANAGER", "CASHIER", "WAREHOUSE"}
