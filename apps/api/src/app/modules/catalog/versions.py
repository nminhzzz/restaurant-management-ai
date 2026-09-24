"""Version lookup helpers — contract for Phase 4 and Phase 3."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import DishPriceVersion, Recipe
from app.shared import business_date
from app.shared.enums import VersionStatus


async def active_price_version(
    session: AsyncSession, dish_id: int, bd: date
) -> DishPriceVersion | None:
    start = business_date.business_date_start(bd)
    # Prefer HIEU_LUC versions whose window covers bd
    r = await session.execute(
        select(DishPriceVersion)
        .where(
            DishPriceVersion.dish_id == dish_id,
            DishPriceVersion.status == VersionStatus.HIEU_LUC.value,
        )
        .order_by(DishPriceVersion.effective_from.desc(), DishPriceVersion.id.desc())
    )
    for v in r.scalars().all():
        eff_from = v.effective_from
        eff_to = v.effective_to
        # if effective_from is set, use window; else fallback to BusinessDateApDung
        if eff_from is not None:
            if eff_from <= start and (eff_to is None or eff_to > start):
                return v
        else:
            if v.business_date <= bd:
                # check if there's a newer one also <= bd, then this is older
                return v
    # fallback: latest HIEU_LUC with business_date <= bd
    r2 = await session.execute(
        select(DishPriceVersion)
        .where(
            DishPriceVersion.dish_id == dish_id,
            DishPriceVersion.status == VersionStatus.HIEU_LUC.value,
            DishPriceVersion.business_date <= bd,
        )
        .order_by(DishPriceVersion.business_date.desc(), DishPriceVersion.id.desc())
        .limit(1)
    )
    return r2.scalar_one_or_none()


async def active_price(session: AsyncSession, dish_id: int, bd: date) -> Decimal | None:
    v = await active_price_version(session, dish_id, bd)
    return Decimal(str(v.price)) if v else None


async def active_recipe(session: AsyncSession, dish_id: int, bd: date) -> Recipe | None:
    start = business_date.business_date_start(bd)
    r = await session.execute(
        select(Recipe)
        .where(Recipe.dish_id == dish_id, Recipe.status == VersionStatus.HIEU_LUC.value)
        .order_by(Recipe.effective_from.desc(), Recipe.id.desc())
    )
    for v in r.scalars().all():
        if v.effective_from is not None:
            if v.effective_from <= start and (v.effective_to is None or v.effective_to > start):
                return v
        else:
            if v.business_date <= bd:
                return v
    r2 = await session.execute(
        select(Recipe)
        .where(
            Recipe.dish_id == dish_id,
            Recipe.status == VersionStatus.HIEU_LUC.value,
            Recipe.business_date <= bd,
        )
        .order_by(Recipe.business_date.desc(), Recipe.id.desc())
        .limit(1)
    )
    return r2.scalar_one_or_none()


async def recipe_items(session: AsyncSession, recipe_id: int):
    from sqlalchemy import select as sel

    from app.modules.catalog.models import RecipeItem

    r = await session.execute(sel(RecipeItem).where(RecipeItem.recipe_id == recipe_id))
    return list(r.scalars().all())
