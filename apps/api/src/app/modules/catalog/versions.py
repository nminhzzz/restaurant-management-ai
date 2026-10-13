"""Version lookup helpers — contract for Phase 4 and Phase 3."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import DishPriceVersion, Recipe
from app.modules.settings.service import effective_business_day_start
from app.shared import business_date
from app.shared.audit import record
from app.shared.enums import VersionStatus

_PROMOTED_FOR = "catalog_versions_promoted_for"


async def promote_due_versions(session: AsyncSession, *, dish_id: int | None = None) -> int:
    """FR-CAT-08/20: a pending version becomes the active one on its Business Date.

    Lazy and idempotent: it runs inside whichever transaction needs a current version,
    takes the row locks, and leaves one audit entry (no user) per promotion. Returns how
    many versions it promoted. Within one session the work is skipped once nothing is
    due for the current Business Date.
    """
    moment = business_date.now()
    start = await effective_business_day_start(session, moment)
    today = business_date.business_date_of(moment, start)
    marker = (today, dish_id)
    if session.info.get(_PROMOTED_FOR) == marker:
        return 0
    effective_at = business_date.business_date_start(today, start)
    promoted = 0
    versioned: tuple[tuple[Any, str, str], ...] = (
        (DishPriceVersion, "LICH_SU_GIA_MON", "PROMOTE_PRICE_VERSION"),
        (Recipe, "CONG_THUC", "PROMOTE_RECIPE_VERSION"),
    )
    for model, entity, action in versioned:
        due_query = (
            select(model)
            .where(model.status == VersionStatus.NHAP.value, model.business_date <= today)
            .order_by(model.dish_id, model.business_date, model.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if dish_id is not None:
            due_query = due_query.where(model.dish_id == dish_id)
        due = (await session.execute(due_query)).scalars().all()
        by_dish: dict[int, list] = {}
        for version in due:
            by_dish.setdefault(version.dish_id, []).append(version)
        for dish, versions in by_dish.items():
            *superseded, newest = versions
            for old in superseded:
                old.status = VersionStatus.HET_HIEU_LUC.value
            current = (
                (
                    await session.execute(
                        select(model)
                        .where(model.dish_id == dish, model.status == VersionStatus.HIEU_LUC.value)
                        .with_for_update()
                        .execution_options(populate_existing=True)
                    )
                )
                .scalars()
                .all()
            )
            for row in current:
                row.status = VersionStatus.HET_HIEU_LUC.value
                row.effective_to = effective_at
            newest.status = VersionStatus.HIEU_LUC.value
            newest.effective_from = effective_at
            record(
                session,
                user_id=None,
                action=action,
                target_entity=entity,
                target_id=newest.id,
                before={"TrangThai": VersionStatus.NHAP.value},
                after={
                    "TrangThai": VersionStatus.HIEU_LUC.value,
                    "ThoiDiemHieuLuc": effective_at.isoformat(),
                    "BusinessDateApDung": newest.business_date.isoformat(),
                },
            )
            promoted += 1
    if promoted:
        await session.flush()
    session.info[_PROMOTED_FOR] = marker
    return promoted


def forget_promotion_marker(session: AsyncSession) -> None:
    """A new pending version invalidates the 'nothing is due' shortcut."""
    session.info.pop(_PROMOTED_FOR, None)


async def active_price_version(
    session: AsyncSession, dish_id: int, bd: date
) -> DishPriceVersion | None:
    await promote_due_versions(session, dish_id=None)
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


async def active_price_version_for_update(
    session: AsyncSession, dish_id: int, bd: date
) -> DishPriceVersion | None:
    """Read and lock the current active price row, bypassing RR snapshot reads."""
    await promote_due_versions(session, dish_id=None)
    query = (
        select(DishPriceVersion)
        .where(
            DishPriceVersion.dish_id == dish_id,
            DishPriceVersion.status == VersionStatus.HIEU_LUC.value,
            DishPriceVersion.business_date <= bd,
        )
        .order_by(DishPriceVersion.business_date.desc(), DishPriceVersion.id.desc())
        .limit(1)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def active_price(session: AsyncSession, dish_id: int, bd: date) -> Decimal | None:
    v = await active_price_version(session, dish_id, bd)
    return Decimal(str(v.price)) if v else None


async def active_prices(
    session: AsyncSession, dish_ids: Sequence[int], bd: date
) -> dict[int, Decimal]:
    """`active_price_version` for many dishes in one query; dishes without a price are absent."""
    if not dish_ids:
        return {}
    await promote_due_versions(session, dish_id=None)
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
    await promote_due_versions(session, dish_id=None)
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


async def active_recipe_for_update(session: AsyncSession, dish_id: int, bd: date) -> Recipe | None:
    """Read and lock the current active recipe row, bypassing RR snapshot reads."""
    await promote_due_versions(session, dish_id=None)
    query = (
        select(Recipe)
        .where(
            Recipe.dish_id == dish_id,
            Recipe.status == VersionStatus.HIEU_LUC.value,
            Recipe.business_date <= bd,
        )
        .order_by(Recipe.business_date.desc(), Recipe.id.desc())
        .limit(1)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def recipe_items(session: AsyncSession, recipe_id: int):
    from sqlalchemy import select as sel

    from app.modules.catalog.models import RecipeItem

    r = await session.execute(sel(RecipeItem).where(RecipeItem.recipe_id == recipe_id))
    return list(r.scalars().all())


async def list_price_versions(session: AsyncSession, dish_id: int) -> list[DishPriceVersion]:
    """Current + pending + recent history, newest first (FR-CAT-08/20/21)."""
    r = await session.execute(
        select(DishPriceVersion)
        .where(DishPriceVersion.dish_id == dish_id)
        .order_by(DishPriceVersion.business_date.desc(), DishPriceVersion.id.desc())
    )
    return list(r.scalars().all())


async def list_recipe_versions(session: AsyncSession, dish_id: int) -> list[Recipe]:
    """Current + pending + recent history, newest first (FR-CAT-09/10/22)."""
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
