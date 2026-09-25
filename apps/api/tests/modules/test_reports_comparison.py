"""Phase 5 Task 4 — period comparison and cancelled orders (FR-REP-08, FR-REP-10)."""

from decimal import Decimal

import pytest

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
    expected = (two_months.right_revenue - two_months.left_revenue) / two_months.left_revenue * 100
    assert Decimal(body["change_percent"]).quantize(Decimal("0.01")) == expected.quantize(
        Decimal("0.01")
    )


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
