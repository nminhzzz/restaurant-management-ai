"""Derived "Hết nguyên liệu" state of a dish (FR-CAT-27, FR-INV-10).

HetNguyenLieu is not stored in MON_AN: it is recomputed from the available quantity of every
ingredient of the dish's current recipe, so it can never go stale after a stock movement.
"""

from collections.abc import Iterable
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Recipe, RecipeItem
from app.shared.enums import VersionStatus


async def dishes_short_of_ingredients(session: AsyncSession, dish_ids: Iterable[int]) -> set[int]:
    """Dishes whose current recipe needs more of some ingredient than is available.

    A dish without a current recipe is never reported (it is a draft, not short).
    """
    from app.modules.inventory.stock import available_quantity

    ids = set(dish_ids)
    if not ids:
        return set()
    rows = (
        await session.execute(
            select(Recipe.dish_id, RecipeItem.ingredient_id, RecipeItem.quantity)
            .join(RecipeItem, RecipeItem.recipe_id == Recipe.id)
            .where(Recipe.dish_id.in_(ids), Recipe.status == VersionStatus.HIEU_LUC.value)
        )
    ).all()
    available: dict[int, Decimal] = {}
    short: set[int] = set()
    for dish_id, ingredient_id, needed in rows:
        if dish_id in short:
            continue
        if ingredient_id not in available:
            available[ingredient_id] = await available_quantity(session, ingredient_id)
        if available[ingredient_id] < Decimal(str(needed)):
            short.add(dish_id)
    return short


async def is_short_of_ingredients(session: AsyncSession, dish_id: int) -> bool:
    return dish_id in await dishes_short_of_ingredients(session, [dish_id])
