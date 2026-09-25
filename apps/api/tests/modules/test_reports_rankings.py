"""Phase 5 Task 2 — dish ranking and hourly distribution (FR-REP-03, FR-REP-07)."""

from datetime import timedelta

import pytest

DISHES = "/api/v1/reports/dishes"
HOURS = "/api/v1/reports/hours"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_the_ranking_can_be_sorted_by_quantity_or_by_revenue(
    api_client, manager_token, orders_in_september
):
    """FR-REP-03."""
    by_quantity = (
        await api_client.get(DISHES, headers=_auth(manager_token), params={"order_by": "quantity"})
    ).json()["items"]
    by_revenue = (
        await api_client.get(DISHES, headers=_auth(manager_token), params={"order_by": "revenue"})
    ).json()["items"]

    assert by_quantity[0]["TenMon"] == orders_in_september.top_by_quantity
    assert by_revenue[0]["TenMon"] == orders_in_september.top_by_revenue
    assert by_quantity[0]["TenMon"] != by_revenue[0]["TenMon"]


@pytest.mark.anyio
async def test_cancelled_lines_are_left_out_of_the_ranking(
    api_client, manager_token, order_with_cancelled_line
):
    """A cancelled line never reached the guest."""
    items = (await api_client.get(DISHES, headers=_auth(manager_token))).json()["items"]

    assert all(item["TenMon"] != "Món đã hủy" for item in items)
    assert any(item["TenMon"] == "Món giữ" for item in items)


@pytest.mark.anyio
async def test_the_ranking_covers_the_selected_period_only(
    api_client, manager_token, orders_in_two_months
):
    august = (
        await api_client.get(
            DISHES,
            headers=_auth(manager_token),
            params={"month": orders_in_two_months.left_month},
        )
    ).json()
    september = (
        await api_client.get(
            DISHES,
            headers=_auth(manager_token),
            params={"month": orders_in_two_months.right_month},
        )
    ).json()

    assert {item["TenMon"] for item in august["items"]} != {
        item["TenMon"] for item in september["items"]
    }


@pytest.mark.anyio
async def test_hours_are_grouped_by_business_hour_and_by_weekday(
    api_client, manager_token, orders_in_september
):
    """FR-REP-07."""
    body = (await api_client.get(HOURS, headers=_auth(manager_token))).json()

    assert {"ThoiDiem", "SoDon", "DoanhThu"} <= set(body["items"][0])
    assert {"Thu", "SoDon"} <= set(body["by_weekday"][0])


@pytest.mark.anyio
async def test_a_late_night_order_belongs_to_the_previous_business_date(
    api_client, manager_token, order_at_0130
):
    """Business date runs 06:00 to 06:00, so 01:30 belongs to the day before."""
    body = (await api_client.get(HOURS, headers=_auth(manager_token))).json()

    assert order_at_0130.business_date == order_at_0130.placed_at.date() - timedelta(days=1)
    assert any(row["ThoiDiem"] == 1 for row in body["items"])
