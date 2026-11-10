"""Estimated dish cost and the cost-ratio warning (FR-CAT-29, TC-CAT-49..51)."""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.modules.catalog.costing import (
    COMPLETE,
    MISSING_COST,
    NO_RECIPE,
    IngredientCost,
    estimate,
)
from app.modules.catalog.models import (
    Dish,
    DishGroup,
    DishPriceVersion,
    Ingredient,
    Recipe,
    RecipeItem,
)
from app.modules.inventory.models import AverageCostHistory
from app.shared import business_date
from app.shared.enums import VersionStatus
from tests.modules.test_inventory_costing import _headers, _make_client, _receive

pytestmark = pytest.mark.anyio

COSTS = "/api/v1/catalog/dishes/costs"


def _line(name, quantity, unit_cost):
    cost = None if unit_cost is None else Decimal(str(unit_cost))
    quantity = Decimal(str(quantity))
    return IngredientCost(1, name, "kg", quantity, cost, None if cost is None else quantity * cost)


BEEF_STIR_FRY = [_line("Bò", "0.15", 230_000), _line("Hành", "0.05", 40_000)]


def test_the_estimate_of_the_handoff_example():
    """Bò xào 80.000 đ: 36.500 đ of ingredients, 45,6 %, 43.500 đ gross, flagged at 40 %."""
    result = estimate(1, Decimal(80_000), BEEF_STIR_FRY, Decimal(40))

    assert result.status == COMPLETE
    assert result.cost == 36_500
    assert result.ratio == Decimal("45.63")
    assert result.margin == 43_500
    assert result.warning is True


@pytest.mark.parametrize(
    "price,threshold,warned",
    [
        (80_000, 40, True),
        (80_000, 50, False),
        (91_250, 40, False),  # exactly 40 %: only a ratio above the threshold is flagged
        (91_249, 40, True),
    ],
)
def test_only_a_ratio_above_the_threshold_is_flagged(price, threshold, warned):
    result = estimate(1, Decimal(price), BEEF_STIR_FRY, Decimal(threshold))

    assert result.warning is warned


def test_a_dish_without_a_recipe_has_no_estimate():
    for lines in (None, []):
        result = estimate(1, Decimal(80_000), lines, Decimal(40))

        assert (result.status, result.cost, result.ratio, result.warning) == (
            NO_RECIPE,
            None,
            None,
            False,
        )


def test_a_missing_unit_cost_is_unknown_not_zero():
    """TC-CAT-51: no total, no ratio and no warning; the ingredient is named."""
    lines = [_line("Gà", "0.1", 140_000), _line("Sả", "0.02", None)]

    result = estimate(1, Decimal(20_000), lines, Decimal(40))

    assert result.status == MISSING_COST
    assert result.missing == ["Sả"]
    assert (result.cost, result.ratio, result.margin, result.warning) == (None, None, None, False)


def test_a_dish_without_a_price_has_a_cost_but_no_ratio():
    result = estimate(1, None, BEEF_STIR_FRY, Decimal(40))

    assert (result.cost, result.ratio, result.margin, result.warning) == (36_500, None, None, False)


async def _ingredient(session, name, unit_cost=None):
    ingredient = Ingredient(name=name, unit="kg", min_stock=0, stock_qty=0, is_deleted=False)
    session.add(ingredient)
    await session.flush()
    if unit_cost is not None:
        session.add(
            AverageCostHistory(
                ingredient_id=ingredient.id,
                effective_at=datetime(2026, 1, 1),
                avg_cost=unit_cost,
                stock_qty=0,
            )
        )
    return ingredient.id


async def _dish(session, name, price, recipe: dict[int, str] | None):
    group = await session.scalar(select(DishGroup).limit(1))
    if group is None:
        group = DishGroup(name="Món chính", display_order=1, is_deleted=False)
        session.add(group)
        await session.flush()
    dish = Dish(name=name, group_id=group.id, is_deleted=False)
    session.add(dish)
    await session.flush()
    today = business_date.business_date_of(business_date.now())
    if price is not None:
        session.add(
            DishPriceVersion(
                dish_id=dish.id,
                price=price,
                business_date=today,
                status=VersionStatus.HIEU_LUC.value,
                change_type="Tạo mới",
            )
        )
    if recipe is not None:
        version = Recipe(
            dish_id=dish.id,
            business_date=today,
            status=VersionStatus.HIEU_LUC.value,
            change_type="Tạo mới",
        )
        session.add(version)
        await session.flush()
        for ingredient_id, quantity in recipe.items():
            session.add(
                RecipeItem(
                    recipe_id=version.id, ingredient_id=ingredient_id, quantity=Decimal(quantity)
                )
            )
    await session.commit()
    return dish.id


async def _manager(session):
    client = await _make_client(session)
    headers, _ = await _headers(session)
    return client, headers


async def test_the_manager_sees_cost_ratio_margin_and_the_warning(session):
    """TC-CAT-49."""
    beef = await _ingredient(session, "Bò", 230_000)
    onion = await _ingredient(session, "Hành", 40_000)
    dish_id = await _dish(session, "Bò xào", 80_000, {beef: "0.15", onion: "0.05"})
    client, h = await _manager(session)

    listed = await client.get(COSTS, headers=h)
    detail = await client.get(f"/api/v1/catalog/dishes/{dish_id}/cost", headers=h)

    assert listed.status_code == 200, listed.text
    (row,) = listed.json()["items"]
    assert row == {
        "MaMon": dish_id,
        "TinhTrang": "Đủ dữ liệu",
        "GiaBan": 80_000,
        "GiaVonUocTinh": 36_500,
        "TyLeGiaVon": 45.63,
        "LaiGop": 43_500,
        "CanhBao": True,
        "NguongCanhBao": 40,
        "NguyenLieuThieuGia": [],
    }
    assert detail.status_code == 200, detail.text
    assert [
        (line["TenNguyenLieu"], line["DinhLuong"], line["DonGiaBinhQuan"], line["ThanhTien"])
        for line in detail.json()["ChiTiet"]
    ] == [("Bò", 0.15, 230_000, 34_500), ("Hành", 0.05, 40_000, 2_000)]


async def test_a_dearer_receipt_raises_the_estimate_but_never_the_price(session):
    """TC-CAT-50: 180.000 gives 36,25 % and no flag; 230.000 gives 45,6 % and a flag."""
    beef = await _ingredient(session, "Bò")
    onion = await _ingredient(session, "Hành", 40_000)
    dish_id = await _dish(session, "Bò xào", 80_000, {beef: "0.15", onion: "0.05"})
    client, h = await _manager(session)
    await _receive(client, h, beef, 10, 180_000)

    before = (await client.get(COSTS, headers=h)).json()["items"][0]
    await _receive(client, h, beef, 10, 280_000)  # (10 x 180.000 + 10 x 280.000) / 20
    after = (await client.get(COSTS, headers=h)).json()["items"][0]

    assert (before["GiaVonUocTinh"], before["TyLeGiaVon"], before["CanhBao"]) == (
        29_000,
        36.25,
        False,
    )
    assert (after["GiaVonUocTinh"], after["TyLeGiaVon"], after["CanhBao"]) == (36_500, 45.63, True)
    assert after["GiaBan"] == 80_000
    prices = list(
        await session.scalars(
            select(DishPriceVersion.price).where(DishPriceVersion.dish_id == dish_id)
        )
    )
    assert prices == [80_000]


async def test_an_ingredient_without_a_unit_cost_makes_the_estimate_incomplete(session):
    """TC-CAT-51."""
    chicken = await _ingredient(session, "Gà", 140_000)
    lemongrass = await _ingredient(session, "Sả")
    dish_id = await _dish(session, "Gỏi gà", 65_000, {chicken: "0.1", lemongrass: "0.02"})
    client, h = await _manager(session)

    row = (await client.get(COSTS, headers=h)).json()["items"][0]
    detail = (await client.get(f"/api/v1/catalog/dishes/{dish_id}/cost", headers=h)).json()

    assert row["TinhTrang"] == "Chưa đủ dữ liệu"
    assert row["NguyenLieuThieuGia"] == ["Sả"]
    assert (row["GiaVonUocTinh"], row["TyLeGiaVon"], row["LaiGop"]) == (None, None, None)
    assert row["CanhBao"] is False
    assert [(line["TenNguyenLieu"], line["ThanhTien"]) for line in detail["ChiTiet"]] == [
        ("Gà", 14_000),
        ("Sả", None),
    ]


async def test_a_dish_without_a_recipe_is_reported_as_such(session):
    await _dish(session, "Món mới", 50_000, None)
    client, h = await _manager(session)

    row = (await client.get(COSTS, headers=h)).json()["items"][0]

    assert row["TinhTrang"] == "Chưa có công thức"
    assert row["GiaVonUocTinh"] is None
    assert row["CanhBao"] is False


async def test_the_warning_follows_the_configured_threshold(session):
    beef = await _ingredient(session, "Bò", 230_000)
    onion = await _ingredient(session, "Hành", 40_000)
    await _dish(session, "Bò xào", 80_000, {beef: "0.15", onion: "0.05"})
    client, h = await _manager(session)

    await client.put("/api/v1/settings/config", json={"TyLeGiaVonCanhBao": 50}, headers=h)
    row = (await client.get(COSTS, headers=h)).json()["items"][0]

    assert (row["NguongCanhBao"], row["CanhBao"]) == (50, False)


@pytest.mark.parametrize("role", ["CASHIER", "WAREHOUSE"])
async def test_cost_figures_are_for_the_manager_only(session, role):
    """FR-CAT-29: neither the cost endpoints nor the dish list of other roles expose them."""
    beef = await _ingredient(session, "Bò", 230_000)
    dish_id = await _dish(session, "Bò xào", 80_000, {beef: "0.15"})
    client = await _make_client(session)
    headers, _ = await _headers(session, role=role, username=f"cost_{role.lower()}")

    listed = await client.get(COSTS, headers=headers)
    detail = await client.get(f"/api/v1/catalog/dishes/{dish_id}/cost", headers=headers)
    dishes = await client.get("/api/v1/catalog/dishes", headers=headers)

    assert listed.status_code == 403
    assert detail.status_code == 403
    if dishes.status_code == 200:
        for dish in dishes.json()["items"]:
            assert not {"GiaVonUocTinh", "TyLeGiaVon", "LaiGop", "CanhBao"} & set(dish)


async def test_the_cost_of_an_unknown_dish_is_not_found(session):
    client, h = await _manager(session)

    assert (await client.get("/api/v1/catalog/dishes/999999/cost", headers=h)).status_code == 404
