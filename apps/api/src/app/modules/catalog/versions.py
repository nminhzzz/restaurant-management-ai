"""Version lookup helpers — contract for Phase 4 and Phase 3."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Dish, DishPriceVersion, Recipe
from app.shared import business_date as _bd
from app.shared.enums import VersionStatus


async def _promote_due_price_versions(session: AsyncSession, dish_id: int, bd: date) -> None:
    """Make every scheduled price due on or before `bd` the active one.

    Scheduling is lazy by design: the row already carries its effective Business Date,
    so the next read that needs a price closes the old version and promotes the due one.
    Without this, a scheduled change stays `Chờ áp dụng` forever.
    """
    due = (
        (
            await session.execute(
                select(DishPriceVersion)
                .where(
                    DishPriceVersion.dish_id == dish_id,
                    DishPriceVersion.status == VersionStatus.NHAP.value,
                    DishPriceVersion.business_date <= bd,
                )
                .order_by(DishPriceVersion.business_date, DishPriceVersion.id)
                .with_for_update()
            )
        )
        .scalars()
        .all()
    )
    if not due:
        return
    active = (
        (
            await session.execute(
                select(DishPriceVersion)
                .where(
                    DishPriceVersion.dish_id == dish_id,
                    DishPriceVersion.status == VersionStatus.HIEU_LUC.value,
                )
                .with_for_update()
            )
        )
        .scalars()
        .all()
    )
    for version in due:
        start = _bd.business_date_start(version.business_date)
        for current in active:
            current.status = VersionStatus.HET_HIEU_LUC.value
            current.effective_to = start
        version.status = VersionStatus.HIEU_LUC.value
        version.effective_from = start
        version.effective_to = None
        active = [version]
    await session.flush()


async def _promote_due_recipe_versions(session: AsyncSession, dish_id: int, bd: date) -> None:
    """The recipe counterpart of `_promote_due_price_versions`."""
    due = (
        (
            await session.execute(
                select(Recipe)
                .where(
                    Recipe.dish_id == dish_id,
                    Recipe.status == VersionStatus.NHAP.value,
                    Recipe.business_date <= bd,
                )
                .order_by(Recipe.business_date, Recipe.id)
                .with_for_update()
            )
        )
        .scalars()
        .all()
    )
    if not due:
        return
    active = (
        (
            await session.execute(
                select(Recipe)
                .where(
                    Recipe.dish_id == dish_id,
                    Recipe.status == VersionStatus.HIEU_LUC.value,
                )
                .with_for_update()
            )
        )
        .scalars()
        .all()
    )
    dish = await session.get(Dish, dish_id)
    for version in due:
        start = _bd.business_date_start(version.business_date)
        for current in active:
            current.status = VersionStatus.HET_HIEU_LUC.value
            current.effective_to = start
        version.status = VersionStatus.HIEU_LUC.value
        version.effective_from = start
        version.effective_to = None
        active = [version]
    if dish is not None:
        dish.missing_recipe = False
    await session.flush()


async def promote_due_versions(session: AsyncSession, dish_id: int, bd: date) -> None:
    """Promote both a due price change and a due recipe change for one dish."""
    await _promote_due_price_versions(session, dish_id, bd)
    await _promote_due_recipe_versions(session, dish_id, bd)


async def active_price_version(
    session: AsyncSession, dish_id: int, bd: date
) -> DishPriceVersion | None:
    await _promote_due_price_versions(session, dish_id, bd)
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


async def active_prices(
    session: AsyncSession, dish_ids: Sequence[int], bd: date
) -> dict[int, Decimal]:
    """`active_price_version` for many dishes; dishes without a price are absent."""
    if not dish_ids:
        return {}
    for dish_id in set(dish_ids):
        await _promote_due_price_versions(session, dish_id, bd)
    rows = await session.execute(
        select(DishPriceVersion)
        .where(
            DishPriceVersion.dish_id.in_(list(dish_ids)),
            DishPriceVersion.status == VersionStatus.HIEU_LUC.value,
            DishPriceVersion.business_date <= bd,
        )
        .order_by(
            DishPriceVersion.dish_id,
            DishPriceVersion.business_date.desc(),
            DishPriceVersion.id.desc(),
        )
    )
    prices: dict[int, Decimal] = {}
    for version in rows.scalars():
        prices.setdefault(version.dish_id, Decimal(str(version.price)))
    return prices


async def active_recipe(session: AsyncSession, dish_id: int, bd: date) -> Recipe | None:
    await _promote_due_recipe_versions(session, dish_id, bd)
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


async def list_price_versions(session: AsyncSession, dish_id: int) -> list[DishPriceVersion]:
    """Current + pending + recent history, newest first (FR-CAT-08/20/21)."""
    await _promote_due_price_versions(session, dish_id, _bd.business_date_of(_bd.now()))
    r = await session.execute(
        select(DishPriceVersion)
        .where(DishPriceVersion.dish_id == dish_id)
        .order_by(DishPriceVersion.business_date.desc(), DishPriceVersion.id.desc())
    )
    return list(r.scalars().all())


async def list_recipe_versions(session: AsyncSession, dish_id: int) -> list[Recipe]:
    """Current + pending + recent history, newest first (FR-CAT-09/10/22)."""
    await _promote_due_recipe_versions(session, dish_id, _bd.business_date_of(_bd.now()))
    r = await session.execute(
        select(Recipe)
        .where(Recipe.dish_id == dish_id)
        .order_by(Recipe.business_date.desc(), Recipe.id.desc())
    )
    return list(r.scalars().all())


async def recipe_items_detailed(session: AsyncSession, recipe_id: int) -> list[dict]:
    """Recipe lines joined with ingredient name and unit, for display."""
    from app.modules.catalog.models import Ingredient, RecipeItem

    r = await session.execute(
        select(RecipeItem, Ingredient.name, Ingredient.unit)
        .join(Ingredient, Ingredient.id == RecipeItem.ingredient_id)
        .where(RecipeItem.recipe_id == recipe_id)
    )
    return [
        {
            "MaNguyenLieu": ri.ingredient_id,
            "TenNguyenLieu": name,
            "SoLuong": float(ri.quantity),
            "DonViTinh": unit,
        }
        for ri, name, unit in r.all()
    ]
