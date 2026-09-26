"""Dish prices on the catalogue API match the price an order would snapshot."""

from decimal import Decimal

import pytest

from app.main import app
from app.modules.catalog.models import DishPriceVersion
from app.modules.catalog.versions import active_price_version, active_prices
from app.shared.enums import VersionStatus
from tests.helpers import today, tomorrow
from tests.modules.test_catalog_dishes import (
    _auth_headers,
    _make_client,
    create_dish,
    list_dishes,
)


def _version(dish_id: int, price: int, bd, status=VersionStatus.HIEU_LUC.value):
    return DishPriceVersion(
        dish_id=dish_id, price=price, business_date=bd, status=status, change_type="Tạo mới"
    )


async def _price_in_list(session, dish_name: str):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        resp = await list_dishes(client, headers)
    app.dependency_overrides.clear()
    return next(x["GiaHienTai"] for x in resp.json()["items"] if x["TenMon"] == dish_name)


@pytest.mark.asyncio
async def test_the_list_shows_the_active_price(session, dish):
    session.add(_version(dish.id, 65000, today()))
    await session.commit()

    assert await _price_in_list(session, "Phở bò") == 65000


@pytest.mark.asyncio
async def test_a_price_scheduled_for_tomorrow_is_not_shown_yet(session, dish):
    session.add(_version(dish.id, 65000, today()))
    session.add(_version(dish.id, 70000, tomorrow()))
    await session.commit()

    assert await _price_in_list(session, "Phở bò") == 65000


@pytest.mark.asyncio
async def test_a_dish_without_a_price_shows_none(session, dish):
    assert await _price_in_list(session, "Phở bò") is None


@pytest.mark.asyncio
async def test_batch_lookup_agrees_with_the_order_snapshot_lookup(session, three_dishes):
    first, second, _third = three_dishes
    session.add(_version(first.id, 50000, today()))
    session.add(_version(first.id, 55000, today()))
    session.add(_version(second.id, 30000, today(), status="Hết hiệu lực"))
    await session.commit()

    batch = await active_prices(session, [d.id for d in three_dishes], today())

    for d in three_dishes:
        single = await active_price_version(session, d.id, today())
        expected = Decimal(str(single.price)) if single else None
        assert batch.get(d.id) == expected


@pytest.mark.asyncio
async def test_a_price_given_on_create_is_persisted(session, group):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        created = await create_dish(
            client, headers, name="Bún chả", group_id=group.id, GiaHienTai=60000
        )
        listed = await list_dishes(client, headers)
    app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["GiaHienTai"] == 60000
    item = next(x for x in listed.json()["items"] if x["TenMon"] == "Bún chả")
    assert item["GiaHienTai"] == 60000
