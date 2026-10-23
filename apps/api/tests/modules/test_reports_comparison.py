"""Phase 5 Task 4 — period comparison and cancelled orders (FR-REP-08, FR-REP-10)."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.sales.models import Order, OrderLine

COMPARISON = "/api/v1/reports/comparison"
CANCELLED = "/api/v1/reports/cancelled-orders"
REVENUE = "/api/v1/reports/revenue"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_the_comparison_returns_the_percentage_change(api_client, manager_token, two_months):
    """FR-REP-08."""
    body = (
        await api_client.get(
            COMPARISON,
            headers=_auth(manager_token),
            params={"left": two_months.left_month, "right": two_months.right_month},
        )
    ).json()

    assert Decimal(body["left"]["DoanhThu"]) == two_months.left_revenue
    assert Decimal(body["right"]["DoanhThu"]) == two_months.right_revenue
    assert Decimal(body["left"]["GiaVon"]) == 0
    assert body["change_cost_percent"] is None
    expected = (two_months.right_revenue - two_months.left_revenue) / two_months.left_revenue * 100
    assert Decimal(body["change_percent"]).quantize(Decimal("0.01")) == expected.quantize(
        Decimal("0.01")
    )


@pytest.mark.anyio
async def test_the_comparison_includes_material_cost(api_client, manager_token, september_data):
    """FR-REP-08: revenue and cost are both compared, not revenue only."""
    body = (
        await api_client.get(
            COMPARISON,
            headers=_auth(manager_token),
            params={"left": "2026-08", "right": "2026-09"},
        )
    ).json()

    assert Decimal(body["right"]["GiaVon"]) == september_data.cogs
    assert body["change_cost_percent"] is None


@pytest.mark.anyio
async def test_comparing_against_an_empty_period_does_not_divide_by_zero(api_client, manager_token):
    body = (
        await api_client.get(
            COMPARISON,
            headers=_auth(manager_token),
            params={"left": "1999-01", "right": "2026-09"},
        )
    ).json()

    assert body["change_percent"] is None
    assert body["change_cost_percent"] is None


@pytest.mark.anyio
async def test_the_cancelled_report_lists_totals_counts_and_reasons(
    api_client, manager_token, cancelled_orders
):
    """FR-REP-10."""
    body = (
        await api_client.get(CANCELLED, headers=_auth(manager_token), params={"month": "2026-09"})
    ).json()

    assert body["SoLuong"] == len(cancelled_orders)
    assert Decimal(body["TongGiaTri"]) == sum(order.total for order in cancelled_orders)
    assert {row["LyDoHuy"] for row in body["items"]} == {order.reason for order in cancelled_orders}
    assert all(order.reason for order in cancelled_orders)  # the fixture sets them


@pytest.mark.anyio
async def test_the_cancelled_value_stays_out_of_revenue(
    api_client, manager_token, cancelled_orders, invoices_in_september
):
    """FR-REP-10: reported separately, never mixed into revenue."""
    revenue_body = (
        await api_client.get(REVENUE, headers=_auth(manager_token), params={"month": "2026-09"})
    ).json()
    cancelled_body = (
        await api_client.get(CANCELLED, headers=_auth(manager_token), params={"month": "2026-09"})
    ).json()

    assert Decimal(cancelled_body["TongGiaTri"]) > 0
    # Revenue only counts settled invoices; a cancelled order never produced one.
    assert Decimal(revenue_body["total"]) == invoices_in_september.total


@pytest.mark.anyio
async def test_the_cancelled_report_includes_consumed_ingredient_cost(
    api_client, session, manager_token, september_data
):
    """FR-REP-05c/10: a served line keeps its cost even when the order is cancelled."""
    order = Order(
        business_date=date(2026, 9, 21),
        status="Đã hủy",
        order_type="Mang về",
        display_code="ORD-CANCEL-COST",
        cancel_reason="khách bỏ về",
    )
    session.add(order)
    await session.flush()
    line = OrderLine(
        order_id=order.id,
        dish_id=september_data.dish.id,
        quantity=2,
        unit_price=Decimal("50000"),
        recipe_id=september_data.recipe.id,
        status="Đã phục vụ",
    )
    session.add(line)
    await session.flush()

    # FR-REP-05c reads the stock ledger: the served line really consumed 1 kg
    # (2 portions x 0.5 kg) and was not returned when the order was cancelled.
    from sqlalchemy import select

    from app.modules.catalog.models import RecipeItem
    from app.modules.inventory.models import StockMovement

    item = (
        await session.execute(
            select(RecipeItem).where(RecipeItem.recipe_id == september_data.recipe.id)
        )
    ).scalar_one()
    session.add(
        StockMovement(
            ingredient_id=item.ingredient_id,
            kind="Trừ tự động",
            qty=Decimal("-1"),
            business_date=date(2026, 9, 21),
            order_line_id=line.id,
        )
    )
    await session.commit()

    body = (
        await api_client.get(CANCELLED, headers=_auth(manager_token), params={"month": "2026-09"})
    ).json()
    item = next(row for row in body["items"] if row["MaOrder"] == order.id)

    assert Decimal(item["GiaVon"]) == Decimal("10000")
    assert Decimal(body["TongGiaVon"]) >= Decimal("10000")

    costs = (
        await api_client.get(
            "/api/v1/reports/costs",
            headers=_auth(manager_token),
            params={"month": "2026-09"},
        )
    ).json()
    assert Decimal(costs["DonHuyChuaThu"]) == Decimal("10000")
    assert Decimal(costs["TongGiaVon"]) >= Decimal("10000")


@pytest.mark.anyio
async def test_the_comparison_is_cached_for_repeated_reads(session, monkeypatch):
    from app.modules.reports import service

    calls = 0
    original = service.queries.compare_periods

    async def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return await original(*args, **kwargs)

    monkeypatch.setattr(service.queries, "compare_periods", counted)
    await service.comparison(session, "2026-08", "2026-09")
    await service.comparison(session, "2026-08", "2026-09")

    assert calls == 1


@pytest.mark.anyio
async def test_the_comparison_accepts_multi_month_ranges(api_client, manager_token, two_months):
    """FR-REP-08: a period can span several whole months, not just one month."""
    body = (
        await api_client.get(
            COMPARISON,
            headers=_auth(manager_token),
            params={
                "left_from": two_months.left_month,
                "left_to": two_months.left_month,
                "right_from": two_months.left_month,
                "right_to": two_months.right_month,
            },
        )
    ).json()

    assert Decimal(body["left"]["DoanhThu"]) == two_months.left_revenue
    assert Decimal(body["right"]["DoanhThu"]) == (
        two_months.left_revenue + two_months.right_revenue
    )
