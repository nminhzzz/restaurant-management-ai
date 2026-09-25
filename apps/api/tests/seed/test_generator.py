"""Phase 7 Task 1 — deterministic catalogue generation (Appendix 4)."""

import pytest
from scripts.seed.catalog import build_catalogue, seed_catalog
from scripts.seed.config import SeedConfig
from tests.helpers import active_recipe, today


def test_the_same_seed_produces_the_same_catalogue():
    """Repeatable experiments need repeatable data."""
    first = build_catalogue(SeedConfig(seed=42, months=12))
    second = build_catalogue(SeedConfig(seed=42, months=12))

    assert first.dish_names == second.dish_names
    assert first.recipes == second.recipes


def test_a_different_seed_produces_a_different_catalogue():
    first = build_catalogue(SeedConfig(seed=42, months=12))
    second = build_catalogue(SeedConfig(seed=7, months=12))

    assert first.dish_names != second.dish_names


def test_the_catalogue_lands_in_the_ranges_the_report_describes():
    """Appendix 4: 60 to 80 dishes."""
    plan = build_catalogue(SeedConfig(seed=42, months=12))

    assert 60 <= len(plan.dish_names) <= 80
    assert len(plan.ingredient_names) >= 30
    assert len(plan.tables) >= 12


@pytest.mark.anyio
async def test_seeding_persists_exactly_what_was_planned(session, seeded_reference):
    """The pure plan and the database must not drift apart."""
    plan = build_catalogue(SeedConfig(seed=42, months=12))

    ids = await seed_catalog(session, SeedConfig(seed=42, months=12))

    assert sorted(ids.dish_names) == sorted(plan.dish_names)
    assert len(ids.dish_ids) == len(plan.dish_names)


@pytest.mark.anyio
async def test_every_dish_has_an_active_recipe_so_it_can_be_ordered(session, seeded_reference):
    ids = await seed_catalog(session, SeedConfig(seed=42, months=12))

    for dish_id in ids.dish_ids:
        assert await active_recipe(session, dish_id, today()) is not None


@pytest.mark.anyio
async def test_three_accounts_cover_the_three_roles(session, seeded_reference):
    ids = await seed_catalog(session, SeedConfig(seed=42, months=12))

    assert {user.role for user in ids.users} == {"MANAGER", "CASHIER", "WAREHOUSE"}
