"""Fixtures for settings and catalog modules."""

import pytest_asyncio

from app.core.security import hash_password
from app.modules.catalog.models import Dish, DishGroup
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data


@pytest_asyncio.fixture
async def active_user(session):
    await seed_reference_data(session)
    user = User(
        username="thungan01",
        password_hash=hash_password("mat-khau-dung"),
        full_name="Thu Ngan 01",
        role_id="CASHIER",
        status="Hoạt động",
    )
    session.add(user)
    await session.flush()
    await session.commit()
    return user


@pytest_asyncio.fixture
async def locked_user(session):
    await seed_reference_data(session)
    user = User(
        username="thungan01",
        password_hash=hash_password("mat-khau-dung"),
        full_name="Thu Ngan 01",
        role_id="CASHIER",
        status="Đã khóa",
    )
    session.add(user)
    await session.flush()
    await session.commit()
    return user


# Catalog fixtures
@pytest_asyncio.fixture
async def group(session):
    await seed_reference_data(session)
    g = DishGroup(name="Món chính", display_order=1, is_deleted=False)
    session.add(g)
    await session.flush()
    await session.commit()
    return g


@pytest_asyncio.fixture
async def other_group(session):
    await seed_reference_data(session)
    g = DishGroup(name="Khai vị", display_order=1, is_deleted=False)
    session.add(g)
    await session.flush()
    await session.commit()
    return g


@pytest_asyncio.fixture
async def three_groups(session):
    await seed_reference_data(session)
    groups = []
    for i, name in enumerate(["Món chính", "Khai vị", "Tráng miệng"], start=1):
        g = DishGroup(name=name, display_order=i, is_deleted=False)
        session.add(g)
        await session.flush()
        groups.append(g)
    await session.commit()
    return groups


@pytest_asyncio.fixture
async def dish(session, group):
    d = Dish(
        name="Phở bò",
        group_id=group.id,
        hide_manual=False,
        out_of_stock_manual=False,
        out_of_stock_auto=False,
        is_deleted=False,
    )
    session.add(d)
    await session.flush()
    await session.commit()
    return d


@pytest_asyncio.fixture
async def draft_dish(session, group):
    d = Dish(
        name="Món nháp",
        group_id=group.id,
        hide_manual=False,
        out_of_stock_manual=False,
        out_of_stock_auto=False,
        is_deleted=False,
    )
    session.add(d)
    await session.flush()
    await session.commit()
    return d


@pytest_asyncio.fixture
async def three_dishes(session, group):
    dishes = []
    for name in ["Phở bò", "Bún chả", "Cơm tấm"]:
        d = Dish(
            name=name,
            group_id=group.id,
            hide_manual=False,
            out_of_stock_manual=False,
            out_of_stock_auto=False,
            is_deleted=False,
        )
        session.add(d)
        await session.flush()
        dishes.append(d)
    await session.commit()
    return dishes


@pytest_asyncio.fixture
async def group_with_dish(session):
    await seed_reference_data(session)
    g = DishGroup(name="Nhóm có món", display_order=1, is_deleted=False)
    session.add(g)
    await session.flush()
    d = Dish(
        name="Món trong nhóm",
        group_id=g.id,
        hide_manual=False,
        out_of_stock_manual=False,
        out_of_stock_auto=False,
        is_deleted=False,
    )
    session.add(d)
    await session.flush()
    await session.commit()
    # attach helper attrs
    g.dish_id = d.id
    return g


@pytest_asyncio.fixture
async def dish_with_pending_price(session, dish):
    from app.modules.catalog.models import DishPriceVersion
    from tests.helpers import tomorrow

    v = DishPriceVersion(
        dish_id=dish.id, price=50000, business_date=tomorrow(), status="Nháp", change_type="Tạo mới"
    )
    session.add(v)
    await session.flush()
    await session.commit()
    return dish


@pytest_asyncio.fixture
async def free_table(session):
    from app.modules.catalog.models import DiningTable

    await seed_reference_data(session)
    t = DiningTable(name="Bàn 1", is_deleted=False)
    session.add(t)
    await session.flush()
    await session.commit()
    return t


@pytest_asyncio.fixture
async def occupied_table(session):
    from app.modules.catalog.models import DiningTable

    await seed_reference_data(session)
    t = DiningTable(name="Bàn 2", is_deleted=False)
    session.add(t)
    await session.flush()
    await session.commit()
    return t


@pytest_asyncio.fixture
async def fresh_ingredient(session):
    from app.modules.catalog.models import Ingredient

    await seed_reference_data(session)
    ing = Ingredient(
        name="Bột mì", unit="kg", min_stock=5, stock_qty=0, is_deleted=False, unit_locked=False
    )
    session.add(ing)
    await session.flush()
    await session.commit()
    return ing


@pytest_asyncio.fixture
async def three_ingredients(session):
    from app.modules.catalog.models import Ingredient

    await seed_reference_data(session)
    ings = []
    for name in ["Hành lá", "Bột mì", "Cà chua"]:
        ing = Ingredient(
            name=name, unit="kg", min_stock=5, stock_qty=0, is_deleted=False, unit_locked=False
        )
        session.add(ing)
        await session.flush()
        ings.append(ing)
    await session.commit()
    return ings


@pytest_asyncio.fixture
async def ingredient_in_recipe(session, dish, fresh_ingredient):
    from app.modules.catalog.models import Recipe, RecipeItem
    from app.shared import business_date
    from app.shared.enums import VersionStatus

    r = Recipe(
        dish_id=dish.id,
        business_date=business_date.business_date_of(business_date.now()),
        status=VersionStatus.HIEU_LUC.value,
        change_type="Tạo mới",
        effective_from=business_date.now(),
    )
    session.add(r)
    await session.flush()
    session.add(RecipeItem(recipe_id=r.id, ingredient_id=fresh_ingredient.id, quantity=0.2))
    fresh_ingredient.unit_locked = True
    await session.flush()
    await session.commit()
    return fresh_ingredient


@pytest_asyncio.fixture
async def fresh_supplier(session):
    from app.modules.catalog.models import Supplier

    await seed_reference_data(session)
    s = Supplier(name="NCC A", is_deleted=False)
    session.add(s)
    await session.flush()
    await session.commit()
    return s


@pytest_asyncio.fixture
async def supplier_with_receipts(session, fresh_supplier):

    from app.modules.inventory.models import GoodsReceipt

    for _ in range(2):
        gr = GoodsReceipt(supplier_id=fresh_supplier.id, status="Đã nhập")
        session.add(gr)
        await session.flush()
    await session.commit()
    return fresh_supplier


@pytest_asyncio.fixture
async def config_with_default_threshold(session):
    await seed_reference_data(session)
    from sqlalchemy import select

    from app.modules.settings.models import SystemConfig

    cfg = (await session.execute(select(SystemConfig))).scalar_one()
    cfg.default_stock_threshold = 7
    await session.flush()
    await session.commit()
    return cfg


@pytest_asyncio.fixture
async def dish_with_recipe(session, dish, fresh_ingredient):
    from app.modules.catalog.models import Recipe, RecipeItem
    from app.shared import business_date
    from app.shared.enums import VersionStatus

    r = Recipe(
        dish_id=dish.id,
        business_date=business_date.business_date_of(business_date.now()),
        status=VersionStatus.HIEU_LUC.value,
        change_type="Tạo mới",
        effective_from=business_date.now(),
    )
    session.add(r)
    await session.flush()
    session.add(RecipeItem(recipe_id=r.id, ingredient_id=fresh_ingredient.id, quantity=0.2))
    fresh_ingredient.unit_locked = True
    await session.flush()
    await session.commit()
    return dish


@pytest_asyncio.fixture
async def flour(session, fresh_ingredient):
    return fresh_ingredient
# --- Phase 4 fixtures ---
@pytest_asyncio.fixture
async def table(session):
    from app.modules.catalog.models import DiningTable
    t = DiningTable(name="Bàn A", is_deleted=False, status="Trống")
    session.add(t)
    await session.flush()
    await session.commit()
    return t


@pytest_asyncio.fixture
async def table2(session):
    from app.modules.catalog.models import DiningTable
    t = DiningTable(name="Bàn B", is_deleted=False, status="Trống")
    session.add(t)
    await session.flush()
    await session.commit()
    return t


@pytest_asyncio.fixture
async def scarce_dish(session, group):
    """Dish with tiny stock (1 unit) so ordering 99 fails."""
    from app.modules.catalog.models import Dish, Ingredient, Recipe, RecipeItem, DishPriceVersion
    from app.shared import business_date as _bd
    from app.shared.enums import VersionStatus
    from app.modules.inventory.models import GoodsReceipt, GoodsReceiptLine, IngredientLot
    dish = Dish(name="Món hiếm", group_id=group.id, is_deleted=False)
    session.add(dish)
    await session.flush()
    ing = Ingredient(name="NL hiếm", unit="kg", min_stock=1, stock_qty=1, is_deleted=False)
    session.add(ing)
    await session.flush()
    pv = DishPriceVersion(dish_id=dish.id, price=10000, business_date=_bd.business_date_of(_bd.now()), status=VersionStatus.HIEU_LUC.value, change_type="Tạo mới")
    session.add(pv)
    await session.flush()
    r = Recipe(dish_id=dish.id, business_date=_bd.business_date_of(_bd.now()), status=VersionStatus.HIEU_LUC.value, change_type="Tạo mới")
    session.add(r)
    await session.flush()
    session.add(RecipeItem(recipe_id=r.id, ingredient_id=ing.id, quantity=1))
    # lot with 1 remaining
    gr = GoodsReceipt(supplier_id=None, status="Nháp", receipt_date=_bd.now())
    session.add(gr)
    await session.flush()
    gl = GoodsReceiptLine(receipt_id=gr.id, ingredient_id=ing.id, quantity=1, unit_price=5000)
    session.add(gl)
    await session.flush()
    lot = IngredientLot(ingredient_id=ing.id, receipt_line_id=gl.id, quantity_remaining=1, status="Còn hạn", received_at=_bd.now())
    session.add(lot)
    await session.flush()
    await session.commit()
    return dish

