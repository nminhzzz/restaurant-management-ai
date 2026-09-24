"""Version lookup helpers — contract for Phase 4 and Phase 3."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import DishPriceVersion, Recipe
from app.shared.enums import VersionStatus


async def active_price_version(
    session: AsyncSession, dish_id: int, bd: date
) -> DishPriceVersion | None:
    # Single query: latest HIEU_LUC with business_date <= bd
    r = await session.execute(
        select(DishPriceVersion)
        .where(
            DishPriceVersion.dish_id == dish_id,
            DishPriceVersion.status == VersionStatus.HIEU_LUC.value,
            DishPriceVersion.business_date <= bd,
        )
        .order_by(DishPriceVersion.business_date.desc(), DishPriceVersion.id.desc())
        .limit(1)
    )
    return r.scalar_one_or_none()


async def active_price(session: AsyncSession, dish_id: int, bd: date) -> Decimal | None:
    v = await active_price_version(session, dish_id, bd)
    return Decimal(str(v.price)) if v else None


async def active_recipe(session: AsyncSession, dish_id: int, bd: date) -> Recipe | None:
    r = await session.execute(
        select(Recipe)
        .where(
            Recipe.dish_id == dish_id,
            Recipe.status == VersionStatus.HIEU_LUC.value,
            Recipe.business_date <= bd,
        )
        .order_by(Recipe.business_date.desc(), Recipe.id.desc())
        .limit(1)
    )
    return r.scalar_one_or_none()


async def recipe_items(session: AsyncSession, recipe_id: int):
    from sqlalchemy import select as sel

    from app.modules.catalog.models import RecipeItem

    r = await session.execute(sel(RecipeItem).where(RecipeItem.recipe_id == recipe_id))
    return list(r.scalars().all())
