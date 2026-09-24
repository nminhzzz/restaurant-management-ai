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
