"""Estimated cost of a dish and the cost-ratio warning (FR-CAT-29).

The estimate prices the recipe in force at each ingredient's current average unit cost. It
supports pricing decisions only: profit reports keep using the value written on each stock
movement when the dish was actually sent (FR-REP-11).
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Ingredient, RecipeItem
from app.modules.catalog.versions import active_prices, active_recipe
from app.modules.inventory.costing import current_unit_costs, money
from app.modules.settings.models import SystemConfig

NO_RECIPE = "Chưa có công thức"
MISSING_COST = "Chưa đủ dữ liệu"
COMPLETE = "Đủ dữ liệu"
DEFAULT_WARNING_RATIO = Decimal(40)


@dataclass(frozen=True)
class IngredientCost:
    ingredient_id: int
    name: str
    unit: str
    quantity: Decimal
    unit_cost: Decimal | None
    amount: Decimal | None


@dataclass(frozen=True)
class DishCostEstimate:
    dish_id: int
    status: str
    price: Decimal | None
    cost: Decimal | None
    ratio: Decimal | None
    margin: Decimal | None
    warning: bool
    threshold: Decimal
    missing: list[str] = field(default_factory=list)
    lines: list[IngredientCost] = field(default_factory=list)


def cost_ratio(cost: Decimal, price: Decimal) -> Decimal:
    """Cost as a percentage of the price, to two decimals."""
    return (cost * 100 / price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def estimate(
    dish_id: int,
    price: Decimal | None,
    lines: list[IngredientCost] | None,
    threshold: Decimal,
) -> DishCostEstimate:
    """Pure: `lines` is None when the dish has no recipe in force."""
    if not lines:
        return DishCostEstimate(dish_id, NO_RECIPE, price, None, None, None, False, threshold)
    missing = [line.name for line in lines if line.unit_cost is None]
    if missing:
        # A missing unit cost is unknown, not 0: no total, no ratio and no warning.
        return DishCostEstimate(
            dish_id, MISSING_COST, price, None, None, None, False, threshold, missing, lines
        )
    cost = money(
        sum((line.quantity * line.unit_cost for line in lines if line.unit_cost), Decimal(0))
    )
    if price is None or price <= 0:
        return DishCostEstimate(
            dish_id, COMPLETE, price, cost, None, None, False, threshold, [], lines
        )
    return DishCostEstimate(
        dish_id=dish_id,
        status=COMPLETE,
        price=price,
        cost=cost,
        ratio=cost_ratio(cost, price),
        margin=price - cost,
        # Compared before rounding, so 40,004 % is over a 40 % threshold.
        warning=cost * 100 > threshold * price,
        threshold=threshold,
        lines=lines,
    )


async def warning_threshold(session: AsyncSession) -> Decimal:
    value = await session.scalar(select(SystemConfig.cost_ratio_warning).limit(1))
    return DEFAULT_WARNING_RATIO if value is None else Decimal(str(value))


async def estimate_dish_costs(
    session: AsyncSession, dish_ids: list[int], business_day: date
) -> dict[int, DishCostEstimate]:
    threshold = await warning_threshold(session)
    prices = await active_prices(session, dish_ids, business_day)
    recipes = {dish_id: await active_recipe(session, dish_id, business_day) for dish_id in dish_ids}
    recipe_ids = [recipe.id for recipe in recipes.values() if recipe is not None]
    items: dict[int, list[tuple[RecipeItem, str, str]]] = {}
    if recipe_ids:
        for item, name, unit in await session.execute(
            select(RecipeItem, Ingredient.name, Ingredient.unit)
            .join(Ingredient, Ingredient.id == RecipeItem.ingredient_id)
            .where(RecipeItem.recipe_id.in_(recipe_ids))
            .order_by(RecipeItem.recipe_id, RecipeItem.ingredient_id)
        ):
            items.setdefault(item.recipe_id, []).append((item, name, unit))
    unit_costs = await current_unit_costs(
        session, {item.ingredient_id for rows in items.values() for item, _, _ in rows}
    )
    estimates: dict[int, DishCostEstimate] = {}
    for dish_id in dish_ids:
        recipe = recipes[dish_id]
        lines = None
        if recipe is not None:
            lines = []
            for item, name, unit in items.get(recipe.id, []):
                quantity = Decimal(str(item.quantity))
                unit_cost = unit_costs.get(item.ingredient_id)
                lines.append(
                    IngredientCost(
                        ingredient_id=item.ingredient_id,
                        name=name,
                        unit=unit,
                        quantity=quantity,
                        unit_cost=unit_cost,
                        amount=None if unit_cost is None else money(quantity * unit_cost),
                    )
                )
        price = prices.get(dish_id)
        estimates[dish_id] = estimate(
            dish_id, None if price is None else Decimal(str(price)), lines, threshold
        )
    return estimates
