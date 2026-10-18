"""Phase 5 Task 3 — cost of goods, gross margin and provisional labels (FR-REP-04, 05, 06)."""

from decimal import Decimal

import pytest

MARGIN = "/api/v1/reports/margin"
COSTS = "/api/v1/reports/costs"
DISH_COSTS = "/api/v1/reports/costs/dishes"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_the_margin_is_revenue_minus_consumed_ingredients(
    api_client, manager_token, september_data
):
    """FR-REP-04."""
    body = (
        await api_client.get(MARGIN, headers=_auth(manager_token), params={"month": "2026-09"})
    ).json()

    assert Decimal(body["DoanhThu"]) == september_data.revenue
    assert Decimal(body["GiaVon"]) == september_data.cogs
    assert Decimal(body["BienLoiNhuanGop"]) == september_data.margin
    # The definition, not just the three numbers: margin is what is left of revenue.
    assert september_data.margin == september_data.revenue - september_data.cogs


@pytest.mark.anyio
async def test_the_cost_uses_the_recipe_version_in_force_at_order_time(
    api_client, manager_token, order_before_recipe_change, order_after_recipe_change
):
    """FR-REP-05a: the recipe snapshot on the line decides, not the current recipe."""
    body = (
        await api_client.get(COSTS, headers=_auth(manager_token), params={"month": "2026-09"})
    ).json()

    # Both orders use their own pinned recipe version, so the expected total is the
    # sum of the two snapshots.
    assert Decimal(body["NguyenLieu"]) == (
        order_before_recipe_change.expected_cost + order_after_recipe_change.expected_cost
    )


@pytest.mark.anyio
async def test_waste_is_part_of_the_cost(
    api_client, manager_token, september_data, write_off_in_september
):
    """FR-REP-05b."""
    body = (
        await api_client.get(
            COSTS, headers=_auth(manager_token), params={"month": str(september_data.month)}
        )
    ).json()

    assert Decimal(body["HaoHut"]) == write_off_in_september.value
    assert Decimal(body["TongGiaVon"]) == Decimal(body["NguyenLieu"]) + Decimal(body["HaoHut"])


@pytest.mark.anyio
async def test_a_month_with_uncosted_waste_rows_is_flagged_as_provisional(
    api_client, manager_token, write_off_before_month_close
):
    """FR-REP-05b: the manager must know the figure is not final."""
    body = (
        await api_client.get(COSTS, headers=_auth(manager_token), params={"month": "2026-09"})
    ).json()

    assert body["TamTinh"] is True
    assert body["SoDongChuaTinhGiaVon"] == 1


@pytest.mark.anyio
async def test_the_label_clears_once_the_backfill_has_run(
    api_client, manager_token, write_off_after_backfill
):
    body = (
        await api_client.get(COSTS, headers=_auth(manager_token), params={"month": "2026-09"})
    ).json()

    assert body["TamTinh"] is False
    assert body["SoDongChuaTinhGiaVon"] == 0


@pytest.mark.anyio
async def test_the_per_dish_cost_excludes_waste(api_client, manager_token, september_data):
    """FR-REP-06: reference only, waste is not attributed to a dish."""
    body = (
        await api_client.get(
            DISH_COSTS,
            headers=_auth(manager_token),
            params={"month": str(september_data.month)},
        )
    ).json()

    assert body["items"]
    assert all("HaoHut" not in item for item in body["items"])


@pytest.mark.anyio
async def test_the_per_dish_cost_is_not_turned_into_a_margin(
    api_client, manager_token, september_data
):
    """FR-REP-06: no per-dish profit figure, by design."""
    body = (
        await api_client.get(
            DISH_COSTS,
            headers=_auth(manager_token),
            params={"month": str(september_data.month)},
        )
    ).json()

    assert all("BienLoiNhuan" not in item for item in body["items"])


@pytest.mark.anyio
async def test_the_per_dish_costs_add_up_to_the_ingredient_cost(
    api_client, manager_token, september_data
):
    """Otherwise the breakdown contradicts the total on the same screen."""
    month = str(september_data.month)
    dishes = (
        await api_client.get(DISH_COSTS, headers=_auth(manager_token), params={"month": month})
    ).json()
    costs = (
        await api_client.get(COSTS, headers=_auth(manager_token), params={"month": month})
    ).json()

    assert sum(Decimal(item["GiaVon"]) for item in dishes["items"]) == Decimal(costs["NguyenLieu"])


@pytest.mark.anyio
async def test_an_open_order_is_not_costed_as_sold(session):
    """FR-REP-05a: cost follows collected revenue, not merely a placed order."""
    from datetime import date

    from app.modules.catalog.models import Dish, Ingredient, Recipe, RecipeItem
    from app.modules.inventory.models import MonthlyAverageCost
    from app.modules.reports import queries
    from app.modules.sales.models import Order, OrderLine

    ingredient = Ingredient(name="NL mở", unit="kg", min_stock=0, stock_qty=10, is_deleted=False)
    session.add(ingredient)
    await session.flush()
    dish = Dish(name="Món mở", is_deleted=False)
    session.add(dish)
    await session.flush()
    recipe = Recipe(
        dish_id=dish.id,
        business_date=date(2026, 9, 1),
        status="Đang áp dụng",
        change_type="Tạo mới",
    )
    session.add(recipe)
    await session.flush()
    session.add(
        RecipeItem(recipe_id=recipe.id, ingredient_id=ingredient.id, quantity=Decimal("0.5"))
    )
    session.add(
        MonthlyAverageCost(
            ingredient_id=ingredient.id, month=202609, avg_cost=Decimal("10000"), total_qty=10
        )
    )
    order = Order(
        business_date=date(2026, 9, 20),
        status="Đang mở",
        order_type="Mang về",
        display_code="ORD-OPEN-COST",
    )
    session.add(order)
    await session.flush()
    session.add(
        OrderLine(
            order_id=order.id,
            dish_id=dish.id,
            quantity=4,
            unit_price=Decimal("125000"),
            recipe_id=recipe.id,
            status="Chờ",
        )
    )
    await session.commit()

    assert await queries.ingredient_cost(session, 202609) == Decimal("0")

    order.status = "Đã thanh toán"
    await session.commit()
    assert await queries.ingredient_cost(session, 202609) == Decimal("20000")


@pytest.mark.anyio
async def test_a_negative_stocktake_adjustment_is_part_of_waste(session):
    """FR-REP-05b: stocktake shortages are a cost, costed from the monthly average."""
    from datetime import date

    from app.modules.catalog.models import Ingredient
    from app.modules.inventory.models import (
        MonthlyAverageCost,
        StockIssue,
        StockIssueLine,
        StockMovement,
        Stocktake,
        StocktakeLine,
    )
    from app.modules.reports import queries

    ingredient = Ingredient(
        name="NL kiểm kê", unit="kg", min_stock=0, stock_qty=10, is_deleted=False
    )
    session.add(ingredient)
    await session.flush()
    session.add(
        MonthlyAverageCost(
            ingredient_id=ingredient.id, month=202609, avg_cost=Decimal("10000"), total_qty=10
        )
    )
    stocktake = Stocktake(status="Nháp")
    session.add(stocktake)
    await session.flush()
    line = StocktakeLine(
        stocktake_id=stocktake.id,
        ingredient_id=ingredient.id,
        system_qty=Decimal("10"),
        actual_qty=Decimal("7"),
    )
    session.add(line)
    await session.flush()
    session.add(
        StockMovement(
            ingredient_id=ingredient.id,
            kind="Điều chỉnh kiểm kê",
            qty=Decimal("-3"),
            business_date=date(2026, 9, 22),
            stocktake_line_id=line.id,
        )
    )
    issue = StockIssue(reason="Hủy do kiểm kê", status="Đã xác nhận", stocktake_id=stocktake.id)
    session.add(issue)
    await session.flush()
    session.add(
        StockIssueLine(
            issue_id=issue.id,
            ingredient_id=ingredient.id,
            quantity=Decimal("3"),
            estimated_cost=Decimal("0"),
        )
    )
    await session.commit()

    waste, uncosted = await queries.waste_cost(session, 202609)

    assert waste == Decimal("30000")
    assert uncosted == 0
