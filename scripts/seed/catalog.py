"""Catalogue generation.

`build_catalogue` is pure — same seed, same plan, no database — so determinism is
cheap to test. `seed_catalog` persists that plan **through the service layer**, which
is what keeps the generated rows inside the business invariants (recipe activation,
price versioning, audit rows).
"""

import random
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog import service as catalog_service
from app.modules.settings import service as settings_service
from app.shared import business_date
from app.shared.roles import Role
from scripts.seed.config import (
    DISH_COUNT_RANGE,
    SUPPLIER_COUNT,
    TABLE_COUNT,
    SeedConfig,
    frozen_clock,
)

GROUP_NAMES: tuple[str, ...] = ("Khai vị", "Món chính", "Tráng miệng", "Đồ uống")

DISH_NAMES: tuple[str, ...] = (
    "Phở bò",
    "Phở gà",
    "Phở chay",
    "Bún chả",
    "Bún bò Huế",
    "Bún riêu",
    "Bún thịt nướng",
    "Bún mọc",
    "Bún ốc",
    "Bún cá",
    "Bún đậu mắm tôm",
    "Miến gà",
    "Miến trộn",
    "Mì Quảng",
    "Cao lầu",
    "Hủ tiếu Nam Vang",
    "Hủ tiếu gõ",
    "Mì xào giòn",
    "Mì xào bò",
    "Cháo lòng",
    "Cháo gà",
    "Cháo cá lóc",
    "Cơm tấm sườn",
    "Cơm tấm bì chả",
    "Cơm rang dưa bò",
    "Cơm rang hải sản",
    "Cơm gà Hội An",
    "Cơm bò lúc lắc",
    "Cơm chiên cá mặn",
    "Xôi xéo",
    "Xôi gà",
    "Xôi đậu phộng",
    "Bánh canh cua",
    "Bánh canh ghẹ",
    "Bánh cuốn",
    "Bánh xèo",
    "Bánh khọt",
    "Bánh bèo",
    "Bánh bột lọc",
    "Bánh căn",
    "Gỏi cuốn",
    "Chả giò",
    "Nem nướng",
    "Gỏi gà",
    "Gỏi ngó sen",
    "Gỏi đu đủ",
    "Nộm hoa chuối",
    "Salad trộn",
    "Tiết canh",
    "Dồi trường",
    "Lòng xào dưa",
    "Bò bít tết",
    "Bò sốt vang",
    "Bò nướng lá lốt",
    "Bò lúc lắc khoai tây",
    "Sườn nướng",
    "Sườn xào chua ngọt",
    "Heo quay",
    "Thịt kho hột vịt",
    "Gà nướng mật ong",
    "Gà chiên nước mắm",
    "Gà hấp lá chanh",
    "Gà xào sả ớt",
    "Cá lóc nướng trui",
    "Cá hồi áp chảo",
    "Cá diêu hồng chiên giòn",
    "Mực xào sa tế",
    "Mực chiên giòn",
    "Tôm hấp bia",
    "Tôm chiên xù",
    "Tôm rang muối",
    "Ghẹ hấp",
    "Ốc hấp sả",
    "Nghêu hấp thái",
    "Lẩu hải sản",
    "Lẩu thái",
    "Lẩu bò",
    "Lẩu gà lá é",
    "Chè ba màu",
    "Chè đậu đen",
    "Chè khúc bạch",
    "Chè bưởi",
    "Bánh flan",
    "Rau câu dừa",
    "Kem dừa",
    "Trái cây dĩa",
    "Sữa chua nếp cẩm",
    "Nước mía",
    "Trà đào",
    "Trà chanh",
    "Cà phê sữa đá",
    "Cà phê đen",
    "Sinh tố bơ",
    "Sinh tố xoài",
    "Nước cam",
    "Nước dừa",
    "Bia hơi",
    "Bia lon",
)

INGREDIENT_NAMES: tuple[str, ...] = (
    "Thịt bò",
    "Thịt heo",
    "Thịt heo ba chỉ",
    "Sườn heo",
    "Giò heo",
    "Thịt gà",
    "Đùi gà",
    "Cánh gà",
    "Gà ta",
    "Cá lóc",
    "Cá hồi",
    "Cá diêu hồng",
    "Cá basa",
    "Tôm sú",
    "Tôm thẻ",
    "Mực ống",
    "Nghêu",
    "Ghẹ",
    "Ốc bươu",
    "Bánh phở",
    "Bún tươi",
    "Miến khô",
    "Mì trứng",
    "Gạo tẻ",
    "Gạo nếp",
    "Bánh tráng",
    "Bột gạo",
    "Bột mì",
    "Đậu xanh",
    "Đậu đen",
    "Đậu phộng",
    "Hành lá",
    "Hành tím",
    "Tỏi",
    "Sả",
    "Ớt",
    "Gừng",
    "Nghệ",
    "Rau muống",
    "Cải ngọt",
    "Xà lách",
    "Rau thơm",
    "Giá đỗ",
    "Dưa leo",
    "Cà chua",
    "Cà rốt",
    "Củ cải trắng",
    "Nấm rơm",
    "Nấm đùi gà",
    "Đu đủ xanh",
    "Chuối",
    "Dừa",
    "Chanh",
    "Quất",
    "Đường",
    "Nước mắm",
    "Nước tương",
    "Dầu ăn",
    "Muối",
    "Tiêu",
    "Bột ngọt",
    "Sa tế",
    "Mật ong",
    "Bia",
    "Sữa đặc",
    "Cà phê",
    "Trà",
    "Đá viên",
)

SUPPLIER_NAMES: tuple[str, ...] = (
    "Chợ đầu mối",
    "Hải sản Biển Đông",
    "Rau sạch Đà Lạt",
    "Gia vị Minh Long",
    "Đồ uống Sài Gòn",
)

PRICE_RANGE = (25_000, 185_000)
PRICE_STEP = 5_000


@dataclass(frozen=True)
class CataloguePlan:
    group_names: list[str]
    dish_names: list[str]
    ingredient_names: list[str]
    supplier_names: list[str]
    tables: list[str]
    recipes: dict[str, dict[str, float]]
    prices: dict[str, int]


@dataclass(frozen=True)
class CatalogIds:
    dish_names: list[str]
    dish_ids: list[int]
    ingredient_ids: list[int]
    table_ids: list[int]
    supplier_ids: list[int]
    users: list[Any]
    manager_id: int


def build_catalogue(config: SeedConfig) -> CataloguePlan:
    """Pure: same `config.seed` in, same plan out."""
    rng = random.Random(config.seed)
    dish_count = rng.randint(*DISH_COUNT_RANGE)
    dishes = rng.sample(sorted(DISH_NAMES), dish_count)
    ingredients = list(INGREDIENT_NAMES)

    recipes: dict[str, dict[str, float]] = {}
    for dish in dishes:
        picks = rng.sample(ingredients, rng.randint(2, 4))
        recipes[dish] = {name: round(rng.uniform(0.02, 0.4), 4) for name in picks}

    prices = {
        dish: rng.randrange(PRICE_RANGE[0], PRICE_RANGE[1], PRICE_STEP) for dish in dishes
    }

    return CataloguePlan(
        group_names=list(GROUP_NAMES),
        dish_names=dishes,
        ingredient_names=ingredients,
        supplier_names=list(SUPPLIER_NAMES[:SUPPLIER_COUNT]),
        tables=[f"Bàn {index:02d}" for index in range(1, TABLE_COUNT + 1)],
        recipes=recipes,
        prices=prices,
    )


async def seed_catalog(session: AsyncSession, config: SeedConfig) -> CatalogIds:
    """Persist the plan through the catalogue service."""
    from sqlalchemy import func, select

    from app.core.errors import BusinessRuleError
    from app.modules.catalog.models import Dish

    existing = (
        await session.execute(select(func.count()).select_from(Dish))
    ).scalar_one()
    if existing:
        raise BusinessRuleError(
            "CSDL đã có dữ liệu danh mục — seed chỉ chạy trên CSDL sạch. "
            "Tạo lại CSDL rồi chạy lại (make db-down && make db-up && make migrate)."
        )

    plan = build_catalogue(config)

    users = []
    for username, role in (
        ("seed_manager", Role.MANAGER),
        ("seed_cashier", Role.CASHIER),
        ("seed_warehouse", Role.WAREHOUSE),
    ):
        user = await settings_service.create_user(
            session, None, username, "matkhau123", username, None, role
        )
        users.append(SimpleNamespace(id=user.id, username=username, role=role.value))
    manager_id = users[0].id
    await session.commit()

    # Prices and recipes are effective-dated, so they must be stamped before the first
    # generated business date or every historical order would be priced at zero.
    window_start = business_date.business_date_of(config.now) - timedelta(
        days=config.months * 30 + 1
    )
    with frozen_clock(datetime.combine(window_start, time(8))):
        ingredient_ids: dict[str, int] = {}
        for name in plan.ingredient_names:
            ingredient = await catalog_service.create_ingredient(
                session, manager_id, name, "kg", 5
            )
            ingredient_ids[name] = ingredient.id

        group_ids: dict[str, int] = {}
        for name in plan.group_names:
            group = await catalog_service.create_group(session, manager_id, name)
            group_ids[name] = group.id

        dish_ids: list[int] = []
        group_keys = list(group_ids)
        for index, name in enumerate(plan.dish_names):
            group_name = group_keys[index % len(group_keys)]
            dish = await catalog_service.create_dish(
                session, manager_id, name, group_ids[group_name], None, plan.prices[name]
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
        supplier_ids = [
            (await catalog_service.create_supplier(session, manager_id, name, None)).id
            for name in plan.supplier_names
        ]

    await session.commit()
    return CatalogIds(
        dish_names=list(plan.dish_names),
        dish_ids=dish_ids,
        ingredient_ids=list(ingredient_ids.values()),
        table_ids=table_ids,
        supplier_ids=supplier_ids,
        users=users,
        manager_id=manager_id,
    )
