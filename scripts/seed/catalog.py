"""Catalogue generation.

The catalogue is a hand-written menu of a small Vietnamese eatery rather than random
draws: a recipe has to use ingredients the dish is really cooked from, and prices have to
leave a believable food-cost margin, otherwise every cost and margin figure built on the
dataset is noise. `build_catalogue` is pure — no database — and `seed_catalog` persists
that plan **through the service layer**, which is what keeps the generated rows inside
the business invariants (recipe activation, price versioning, audit rows).
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from scripts.seed.config import (
    DISH_POWER_LAW_EXPONENT,
    MAX_LINES_PER_ORDER,
    MAX_SERVINGS_PER_LINE,
    SeedConfig,
    frozen_clock,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog import service as catalog_service
from app.modules.settings import service as settings_service
from app.shared import business_date
from app.shared.roles import Role

STARTER, MAIN, DESSERT, DRINK = "Khai vị", "Món chính", "Tráng miệng", "Đồ uống"
GROUP_NAMES: tuple[str, ...] = (STARTER, MAIN, DESSERT, DRINK)

TABLE_COUNT = 12
DISH_PRICE_RANGE = (25_000, 150_000)
DISH_PRICE_STEP = 5_000
RECIPE_SIZE_RANGE = (2, 4)
RECIPE_QUANTITY_RANGE_KG = (0.02, 0.25)


@dataclass(frozen=True)
class Category:
    """Storage class of an ingredient: who supplies it, how long it keeps, how it is bought."""

    supplier: str
    shelf_days: int
    min_stock_kg: float
    restocked_daily: bool
    price_range: tuple[int, int]


MEAT = Category("Thịt và hải sản Biển Đông", 3, 2.0, True, (120_000, 350_000))
PRODUCE = Category("Rau củ quả Đà Lạt", 7, 2.0, True, (15_000, 60_000))
DRY = Category("Hàng khô Minh Long", 365, 0.5, False, (20_000, 200_000))
CATEGORIES: tuple[Category, ...] = (MEAT, PRODUCE, DRY)


@dataclass(frozen=True)
class IngredientSpec:
    name: str
    category: Category
    unit_price: int  # đ/kg at the supplier, before the per-receipt fluctuation


@dataclass(frozen=True)
class DishSpec:
    name: str
    group: str
    price: int
    recipe: dict[str, float]  # ingredient name -> kg per serving


INGREDIENTS: tuple[IngredientSpec, ...] = (
    IngredientSpec("Thịt bò thăn", MEAT, 270_000),
    IngredientSpec("Nạm bò", MEAT, 220_000),
    IngredientSpec("Ba chỉ heo", MEAT, 150_000),
    IngredientSpec("Thịt heo xay", MEAT, 135_000),
    IngredientSpec("Sườn cốt lết", MEAT, 140_000),
    IngredientSpec("Sườn non heo", MEAT, 190_000),
    IngredientSpec("Thịt gà ta", MEAT, 140_000),
    IngredientSpec("Tôm sú", MEAT, 300_000),
    IngredientSpec("Mực ống", MEAT, 280_000),
    IngredientSpec("Cá lóc phi lê", MEAT, 150_000),
    IngredientSpec("Bánh phở", PRODUCE, 18_000),
    IngredientSpec("Bún tươi", PRODUCE, 17_000),
    IngredientSpec("Xà lách", PRODUCE, 35_000),
    IngredientSpec("Rau thơm", PRODUCE, 40_000),
    IngredientSpec("Hành tây", PRODUCE, 20_000),
    IngredientSpec("Cà chua", PRODUCE, 25_000),
    IngredientSpec("Dưa leo", PRODUCE, 20_000),
    IngredientSpec("Cà rốt", PRODUCE, 20_000),
    IngredientSpec("Chuối", PRODUCE, 20_000),
    IngredientSpec("Xoài", PRODUCE, 35_000),
    IngredientSpec("Cam", PRODUCE, 30_000),
    IngredientSpec("Bơ", PRODUCE, 45_000),
    IngredientSpec("Gạo", DRY, 25_000),
    IngredientSpec("Bánh tráng", DRY, 60_000),
    IngredientSpec("Miến dong", DRY, 70_000),
    IngredientSpec("Bột chiên giòn", DRY, 40_000),
    IngredientSpec("Dầu ăn", DRY, 50_000),
    IngredientSpec("Nước mắm", DRY, 60_000),
    IngredientSpec("Đường", DRY, 25_000),
    IngredientSpec("Đậu xanh", DRY, 55_000),
    IngredientSpec("Đậu đen", DRY, 50_000),
    IngredientSpec("Đậu phộng", DRY, 60_000),
    IngredientSpec("Nước cốt dừa", DRY, 70_000),
    IngredientSpec("Sữa đặc", DRY, 70_000),
    IngredientSpec("Cà phê bột", DRY, 180_000),
)

# Listed from the best seller down: the position is the popularity rank of the dish.
# Every meat or seafood sits in a dish popular enough to use about a kilogram a day,
# otherwise its two-kilogram minimum stock would outlast the three-day shelf life.
DISHES: tuple[DishSpec, ...] = (
    DishSpec(
        "Phở bò",
        MAIN,
        55_000,
        {"Bánh phở": 0.18, "Thịt bò thăn": 0.03, "Nạm bò": 0.04, "Rau thơm": 0.02},
    ),
    DishSpec(
        "Cơm tấm sườn",
        MAIN,
        60_000,
        {"Gạo": 0.10, "Sườn cốt lết": 0.12, "Dưa leo": 0.03, "Nước mắm": 0.02},
    ),
    DishSpec("Cà phê sữa đá", DRINK, 30_000, {"Cà phê bột": 0.02, "Sữa đặc": 0.03}),
    DishSpec(
        "Bún chả",
        MAIN,
        60_000,
        {"Bún tươi": 0.20, "Ba chỉ heo": 0.07, "Thịt heo xay": 0.05, "Rau thơm": 0.03},
    ),
    DishSpec(
        "Gỏi cuốn tôm thịt",
        STARTER,
        50_000,
        {"Tôm sú": 0.03, "Ba chỉ heo": 0.03, "Bún tươi": 0.05, "Bánh tráng": 0.02},
    ),
    DishSpec(
        "Cơm gà xối mỡ",
        MAIN,
        60_000,
        {"Gạo": 0.10, "Thịt gà ta": 0.12, "Dưa leo": 0.03, "Dầu ăn": 0.02},
    ),
    DishSpec("Nước cam", DRINK, 35_000, {"Cam": 0.25, "Đường": 0.02}),
    DishSpec(
        "Chả giò",
        STARTER,
        55_000,
        {"Thịt heo xay": 0.08, "Miến dong": 0.02, "Bánh tráng": 0.03, "Cà rốt": 0.03},
    ),
    DishSpec("Cà phê đen đá", DRINK, 25_000, {"Cà phê bột": 0.02, "Đường": 0.02}),
    DishSpec(
        "Cá lóc kho tộ", MAIN, 85_000, {"Cá lóc phi lê": 0.18, "Nước mắm": 0.03, "Đường": 0.02}
    ),
    DishSpec("Sinh tố bơ", DRINK, 40_000, {"Bơ": 0.15, "Sữa đặc": 0.04, "Đường": 0.02}),
    DishSpec(
        "Chè đậu xanh", DESSERT, 25_000, {"Đậu xanh": 0.05, "Đường": 0.03, "Nước cốt dừa": 0.03}
    ),
    DishSpec(
        "Sườn xào chua ngọt",
        MAIN,
        110_000,
        {"Sườn non heo": 0.18, "Cà chua": 0.06, "Hành tây": 0.05, "Đường": 0.02},
    ),
    DishSpec(
        "Mực xào hành tây", MAIN, 120_000, {"Mực ống": 0.15, "Hành tây": 0.08, "Dầu ăn": 0.02}
    ),
    DishSpec("Sinh tố xoài", DRINK, 40_000, {"Xoài": 0.18, "Sữa đặc": 0.03, "Đường": 0.02}),
    DishSpec(
        "Mực chiên giòn",
        STARTER,
        100_000,
        {"Mực ống": 0.12, "Bột chiên giòn": 0.04, "Dầu ăn": 0.03},
    ),
    DishSpec(
        "Tôm chiên xù", STARTER, 95_000, {"Tôm sú": 0.10, "Bột chiên giòn": 0.04, "Dầu ăn": 0.03}
    ),
    DishSpec(
        "Chè thập cẩm",
        DESSERT,
        30_000,
        {"Đậu xanh": 0.03, "Đậu đen": 0.03, "Nước cốt dừa": 0.04, "Đường": 0.03},
    ),
    DishSpec(
        "Bò lúc lắc",
        MAIN,
        135_000,
        {"Thịt bò thăn": 0.15, "Hành tây": 0.06, "Cà chua": 0.05, "Xà lách": 0.03},
    ),
    DishSpec(
        "Gỏi gà hành tây",
        STARTER,
        65_000,
        {"Thịt gà ta": 0.10, "Hành tây": 0.08, "Rau thơm": 0.02, "Đậu phộng": 0.02},
    ),
    DishSpec(
        "Gà chiên nước mắm",
        STARTER,
        75_000,
        {"Thịt gà ta": 0.18, "Nước mắm": 0.02, "Đường": 0.02, "Dầu ăn": 0.03},
    ),
    DishSpec("Trái cây dĩa", DESSERT, 40_000, {"Xoài": 0.12, "Cam": 0.10, "Chuối": 0.08}),
    DishSpec("Nước ép cà rốt", DRINK, 30_000, {"Cà rốt": 0.25, "Đường": 0.02}),
    DishSpec(
        "Salad dầu giấm",
        STARTER,
        40_000,
        {"Xà lách": 0.10, "Cà chua": 0.06, "Dưa leo": 0.06, "Hành tây": 0.03},
    ),
    DishSpec(
        "Chè đậu đen", DESSERT, 25_000, {"Đậu đen": 0.05, "Đường": 0.03, "Nước cốt dừa": 0.03}
    ),
    DishSpec(
        "Gỏi xoài tôm",
        STARTER,
        60_000,
        {"Xoài": 0.12, "Tôm sú": 0.04, "Rau thơm": 0.02, "Đậu phộng": 0.02},
    ),
    DishSpec("Sinh tố chuối", DRINK, 35_000, {"Chuối": 0.15, "Sữa đặc": 0.04, "Đường": 0.02}),
    DishSpec("Bơ dầm sữa", DESSERT, 35_000, {"Bơ": 0.15, "Sữa đặc": 0.04}),
    DishSpec(
        "Chè chuối",
        DESSERT,
        30_000,
        {"Chuối": 0.10, "Nước cốt dừa": 0.05, "Đường": 0.02, "Đậu phộng": 0.02},
    ),
    DishSpec(
        "Chuối chiên", DESSERT, 25_000, {"Chuối": 0.12, "Bột chiên giòn": 0.04, "Dầu ăn": 0.03}
    ),
)


@dataclass(frozen=True)
class Supply:
    """What the restocking routine needs to know about one ingredient."""

    ingredient_id: int
    supplier_id: int | None
    unit_price: int
    min_stock_kg: float
    restocked_daily: bool
    use_per_order_kg: float


@dataclass(frozen=True)
class CataloguePlan:
    group_names: list[str]
    dish_names: list[str]
    ingredient_names: list[str]
    supplier_names: list[str]
    tables: list[str]
    recipes: dict[str, dict[str, float]]
    prices: dict[str, int]
    groups: dict[str, str]
    ingredients: dict[str, IngredientSpec]


@dataclass(frozen=True)
class CatalogIds:
    dish_names: list[str]
    dish_ids: list[int]
    ingredient_ids: list[int]
    table_ids: list[int]
    supplier_ids: list[int]
    users: list[Any]
    manager_id: int
    supplies: tuple[Supply, ...] = ()


def dish_weights(count: int) -> list[float]:
    """Power-law popularity by rank: a few dishes take most of the orders."""
    return [1.0 / ((rank + 1) ** DISH_POWER_LAW_EXPONENT) for rank in range(count)]


def use_per_order(recipes: list[dict[Any, float]], weights: list[float]) -> dict[Any, float]:
    """Expected kg of each ingredient one order consumes, given the dish popularity."""
    servings = (1 + MAX_LINES_PER_ORDER) / 2 * (1 + MAX_SERVINGS_PER_LINE) / 2
    total = sum(weights)
    usage: dict[Any, float] = {}
    for recipe, weight in zip(recipes, weights, strict=True):
        for ingredient, quantity in recipe.items():
            usage[ingredient] = usage.get(ingredient, 0.0) + servings * quantity * weight / total
    return usage


def build_catalogue() -> CataloguePlan:
    """Pure: the same plan on every call."""
    return CataloguePlan(
        group_names=list(GROUP_NAMES),
        dish_names=[dish.name for dish in DISHES],
        ingredient_names=[ingredient.name for ingredient in INGREDIENTS],
        supplier_names=[category.supplier for category in CATEGORIES],
        tables=[f"Bàn {index:02d}" for index in range(1, TABLE_COUNT + 1)],
        recipes={dish.name: dict(dish.recipe) for dish in DISHES},
        prices={dish.name: dish.price for dish in DISHES},
        groups={dish.name: dish.group for dish in DISHES},
        ingredients={ingredient.name: ingredient for ingredient in INGREDIENTS},
    )


async def seed_catalog(session: AsyncSession, config: SeedConfig) -> CatalogIds:
    """Persist the plan through the catalogue service."""
    from sqlalchemy import func, select

    from app.core.errors import BusinessRuleError
    from app.modules.catalog.models import Dish

    existing = (await session.execute(select(func.count()).select_from(Dish))).scalar_one()
    if existing:
        raise BusinessRuleError(
            "CSDL đã có dữ liệu danh mục — seed chỉ chạy trên CSDL sạch. "
            "Tạo lại CSDL rồi chạy lại (make db-down && make db-up && make migrate)."
        )

    plan = build_catalogue()

    users = []
    for username, role in (
        ("seed_manager", Role.MANAGER),
        ("seed_cashier", Role.CASHIER),  # Thu Ngân
        ("seed_warehouse", Role.WAREHOUSE),  # Bếp
    ):
        user = await settings_service.create_user(
            session, None, username, "matkhau123", username, None, role
        )
        users.append(SimpleNamespace(id=user.id, username=username, role=role.value))
    manager_id = users[0].id
    await session.commit()

    # Prices and recipes are effective-dated, so they must be stamped before the first
    # generated business date or every historical order would be priced at zero.
    window_start = business_date.business_date_of(config.now) - timedelta(days=config.days + 1)
    with frozen_clock(datetime.combine(window_start, time(8))):
        supplier_ids = {
            name: (await catalog_service.create_supplier(session, manager_id, name, None)).id
            for name in plan.supplier_names
        }

        ingredient_ids: dict[str, int] = {}
        for name, spec in plan.ingredients.items():
            ingredient = await catalog_service.create_ingredient(
                session,
                manager_id,
                name,
                "kg",
                spec.category.min_stock_kg,
                spec.category.shelf_days,
            )
            ingredient_ids[name] = ingredient.id

        group_ids: dict[str, int] = {}
        for name in plan.group_names:
            group = await catalog_service.create_group(session, manager_id, name)
            group_ids[name] = group.id

        dish_ids: list[int] = []
        for name in plan.dish_names:
            dish = await catalog_service.create_dish(
                session, manager_id, name, group_ids[plan.groups[name]], None, plan.prices[name]
            )
            dish_ids.append(dish.id)
            # `create_dish` does not persist a price; a dish without an active price
            # version would be ordered at zero and poison every revenue report.
            await catalog_service.apply_price_directly(
                session, manager_id, dish.id, Decimal(str(plan.prices[name]))
            )
            items = [
                (ingredient_ids[ingredient], Decimal(str(quantity)))
                for ingredient, quantity in plan.recipes[name].items()
            ]
            await catalog_service.assign_recipe(session, manager_id, dish.id, items)

        table_ids = [
            (await catalog_service.create_table(session, manager_id, name)).id
            for name in plan.tables
        ]

    await session.commit()
    usage = use_per_order(
        [plan.recipes[name] for name in plan.dish_names], dish_weights(len(plan.dish_names))
    )
    supplies = tuple(
        Supply(
            ingredient_id=ingredient_ids[name],
            supplier_id=supplier_ids[spec.category.supplier],
            unit_price=spec.unit_price,
            min_stock_kg=spec.category.min_stock_kg,
            restocked_daily=spec.category.restocked_daily,
            use_per_order_kg=usage.get(name, 0.0),
        )
        for name, spec in plan.ingredients.items()
    )
    return CatalogIds(
        dish_names=list(plan.dish_names),
        dish_ids=dish_ids,
        ingredient_ids=list(ingredient_ids.values()),
        table_ids=table_ids,
        supplier_ids=list(supplier_ids.values()),
        users=users,
        manager_id=manager_id,
        supplies=supplies,
    )
