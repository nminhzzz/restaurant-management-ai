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
async def test_a_month_with_unvalued_waste_rows_is_flagged_as_provisional(
    api_client, manager_token, write_off_without_unit_cost
):
    """FR-REP-12: an unknown value is reported as unknown, not as a cost of 0."""
    body = (
        await api_client.get(COSTS, headers=_auth(manager_token), params={"month": "2026-09"})
    ).json()

    assert body["TamTinh"] is True
    assert body["SoDongChuaTinhGiaVon"] == 1


@pytest.mark.anyio
async def test_the_first_receipt_values_what_was_written_off_before_it(
    api_client, manager_token, write_off_priced_by_first_receipt
):
    """Document 04 G.1: the first unit cost prices the movements that had none."""
    body = (
        await api_client.get(COSTS, headers=_auth(manager_token), params={"month": "2026-09"})
    ).json()

    assert body["TamTinh"] is False
    assert body["SoDongChuaTinhGiaVon"] == 0
    assert Decimal(body["HaoHut"]) == write_off_priced_by_first_receipt.value


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
    """FR-REP-11: cost follows collected revenue, not merely a placed order."""
    from datetime import date

    from app.modules.catalog.models import Dish, Ingredient, Recipe, RecipeItem
    from app.modules.inventory.models import StockMovement
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
    order = Order(
        business_date=date(2026, 9, 20),
        status="Đang mở",
        order_type="Mang về",
        display_code="ORD-OPEN-COST",
    )
    session.add(order)
    await session.flush()
    line = OrderLine(
        order_id=order.id,
        dish_id=dish.id,
        quantity=4,
        unit_price=Decimal("125000"),
        recipe_id=recipe.id,
        status="Chờ làm",
    )
    session.add(line)
    await session.flush()
    session.add(
        StockMovement(
            ingredient_id=ingredient.id,
            kind="Trừ tự động",
            qty=Decimal("-2"),
            business_date=date(2026, 9, 20),
            order_line_id=line.id,
            value=Decimal("-20000"),
        )
    )
    await session.commit()

    assert await queries.ingredient_cost(session, 202609) == Decimal("0")

    order.status = "Đã thanh toán"
    await session.commit()
    assert await queries.ingredient_cost(session, 202609) == Decimal("20000")


@pytest.mark.anyio
async def test_a_negative_stocktake_adjustment_is_part_of_waste(session):
    """FR-REP-12: a stocktake shortage is a cost, at the value written on its adjustment."""
    from datetime import date

    from app.modules.catalog.models import Ingredient
    from app.modules.inventory.models import (
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
    stocktake = Stocktake(status="Đang kiểm kê")
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
            value=Decimal("-30000"),
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
            estimated_cost=Decimal("30000"),
        )
    )
    await session.commit()

    waste, uncosted = await queries.waste_cost(session, 202609)

    assert waste == Decimal("30000")
    assert uncosted == 0


@pytest.mark.anyio
async def test_prepared_dish_write_off_is_not_double_counted_in_05b(session):
    """P1: 05c already carries the consumption; the classification doc adds no cost."""
    from app.modules.catalog.models import Dish, DishGroup, Ingredient
    from app.modules.inventory.models import StockIssue, StockIssueLine
    from app.modules.reports import queries
    from app.modules.sales.models import Order, OrderLine
    from app.shared import business_date

    moment = business_date.now()
    ingredient = Ingredient(name="NL", unit="kg", min_stock=0, stock_qty=0, is_deleted=False)
    group = DishGroup(name="Nhóm", display_order=1, is_deleted=False)
    session.add_all([ingredient, group])
    await session.flush()
    dish = Dish(name="Món", group_id=group.id, is_deleted=False)
    session.add(dish)
    await session.flush()
    order = Order(business_date=business_date.business_date_of(moment), order_type="Mang về")
    session.add(order)
    await session.flush()
    line = OrderLine(
        order_id=order.id, dish_id=dish.id, quantity=2, unit_price=50000, status="Đã phục vụ"
    )
    session.add(line)
    await session.flush()

    normal = StockIssue(created_at=moment, issue_date=moment)
    prepared = StockIssue(created_at=moment, issue_date=moment)
    session.add_all([normal, prepared])
    await session.flush()
    session.add_all(
        [
            StockIssueLine(
                issue_id=normal.id,
                ingredient_id=ingredient.id,
                quantity=1,
                estimated_cost=Decimal("1000"),
            ),
            StockIssueLine(
                issue_id=prepared.id,
                ingredient_id=ingredient.id,
                quantity=1,
                estimated_cost=Decimal("2000"),
                order_line_id=line.id,
                servings=1,
            ),
        ]
    )
    await session.commit()

    month = moment.year * 100 + moment.month
    waste, uncosted = await queries.waste_cost(session, month)

    assert waste == Decimal("1000")
    assert uncosted == 0


@pytest.mark.anyio
async def test_changing_the_business_day_start_does_not_move_recorded_history(
    api_client, session, manager_token, september_data, order_at_0130
):
    """TC-REP-15: stored Business Dates are kept, so past revenue and cost stay in their period."""
    from sqlalchemy import select

    from app.modules.inventory.models import StockMovement
    from app.modules.sales.models import Invoice, Order
    from app.modules.settings.service import seed_reference_data

    async def recorded():
        session.expire_all()
        return {
            "orders": sorted((await session.execute(select(Order.id, Order.business_date))).all()),
            "invoices": sorted(
                (await session.execute(select(Invoice.id, Invoice.business_date))).all()
            ),
            "movements": sorted(
                (await session.execute(select(StockMovement.id, StockMovement.business_date))).all()
            ),
            "margin": (
                await api_client.get(
                    MARGIN, headers=_auth(manager_token), params={"month": "2026-09"}
                )
            ).json(),
            "costs": (
                await api_client.get(
                    COSTS, headers=_auth(manager_token), params={"month": "2026-09"}
                )
            ).json(),
        }

    await seed_reference_data(session)
    await session.commit()
    before = await recorded()
    changed = await api_client.put(
        "/api/v1/settings/config",
        json={"GioBatDauBusinessDate": "04:00"},
        headers=_auth(manager_token),
    )

    assert changed.status_code == 200, changed.text
    after = await recorded()
    assert after == before
    assert Decimal(after["margin"]["DoanhThu"]) == september_data.revenue
    # The 01:30 order stays on the evening it was booked to, not on the next day.
    assert (order_at_0130.business_date.isoformat()) in {
        day.isoformat() for _, day in after["orders"]
    }
