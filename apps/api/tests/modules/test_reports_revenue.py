"""Phase 5 Task 1 — report periods and revenue (FR-REP-01, FR-REP-02)."""

from datetime import date, datetime, time
from decimal import Decimal

import pytest

from app.modules.reports.periods import resolve_period
from app.modules.reports.service import period_for
from app.modules.settings.models import SystemConfig
from app.shared import business_date

REVENUE = "/api/v1/reports/revenue"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_a_week_runs_on_business_dates_not_calendar_days() -> None:
    """A business date starts at 06:00, so the grouping boundary follows it."""
    period = resolve_period("week", date(2026, 9, 24))

    assert period.start == date(2026, 9, 21)  # Monday
    assert period.end == date(2026, 9, 27)


def test_a_month_covers_every_business_date_in_it() -> None:
    period = resolve_period("month", date(2026, 9, 24))

    assert period.start == date(2026, 9, 1)
    assert period.end == date(2026, 9, 30)


@pytest.mark.anyio
async def test_default_report_day_uses_configured_boundary(session, monkeypatch):
    cfg = await session.get(SystemConfig, 1)
    cfg.business_day_start = time(8, 30)
    monkeypatch.setattr(business_date, "now", lambda: datetime(2026, 9, 24, 8, 29))

    period = await period_for(session, "day")

    assert period.start == date(2026, 9, 23)


@pytest.mark.anyio
async def test_revenue_counts_settled_invoices(api_client, manager_token, invoices_in_september):
    body = (
        await api_client.get(
            REVENUE,
            headers=_auth(manager_token),
            params={"granularity": "month", "anchor": "2026-09-01"},
        )
    ).json()

    assert Decimal(body["total"]) == invoices_in_september.total


@pytest.mark.anyio
async def test_revenue_can_be_split_by_table_and_by_payment_method(
    api_client, manager_token, invoices_in_september
):
    """FR-REP-01."""
    by_table = (
        await api_client.get(REVENUE, headers=_auth(manager_token), params={"group_by": "table"})
    ).json()
    by_method = (
        await api_client.get(
            REVENUE, headers=_auth(manager_token), params={"group_by": "payment_method"}
        )
    ).json()

    assert {row["key"] for row in by_table["items"]} == set(invoices_in_september.table_ids)
    assert {row["key"] for row in by_method["items"]} == set(invoices_in_september.payment_methods)


@pytest.mark.anyio
async def test_the_split_by_table_sums_back_to_the_total(
    api_client, manager_token, invoices_in_september
):
    """A breakdown that does not add up is worse than no breakdown."""
    whole = (
        await api_client.get(REVENUE, headers=_auth(manager_token), params={"granularity": "month"})
    ).json()
    by_table = (
        await api_client.get(REVENUE, headers=_auth(manager_token), params={"group_by": "table"})
    ).json()

    assert sum(Decimal(row["DoanhThu"]) for row in by_table["items"]) == Decimal(whole["total"])


@pytest.mark.anyio
async def test_an_unverified_payment_is_not_revenue(
    api_client, manager_token, order_awaiting_reconciliation, invoices_in_september
):
    """FR-REP-02: an order waiting for verification has no invoice and adds no revenue."""
    body = (
        await api_client.get(REVENUE, headers=_auth(manager_token), params={"granularity": "month"})
    ).json()

    assert Decimal(body["total"]) == invoices_in_september.total
    assert Decimal(body["provisional"]) == 0
    assert body["SoDon"] == 2


@pytest.mark.anyio
async def test_a_payment_that_was_never_confirmed_changes_nothing(
    api_client, manager_token, disputed_payment, invoices_in_september
):
    """Nothing to deduct either: money that was never counted is not taken off."""
    body = (
        await api_client.get(REVENUE, headers=_auth(manager_token), params={"granularity": "month"})
    ).json()

    assert Decimal(body["total"]) == invoices_in_september.total


@pytest.mark.anyio
async def test_revenue_can_be_split_by_order_type(api_client, manager_token, invoices_in_september):
    """FR-REP-01: dine-in against takeaway, and the parts add up to the whole."""
    whole = (
        await api_client.get(REVENUE, headers=_auth(manager_token), params={"granularity": "month"})
    ).json()
    by_type = (
        await api_client.get(
            REVENUE, headers=_auth(manager_token), params={"group_by": "order_type"}
        )
    ).json()

    assert {row["key"] for row in by_type["items"]} == {"Tại chỗ"}
    assert sum(Decimal(row["DoanhThu"]) for row in by_type["items"]) == Decimal(whole["total"])


@pytest.mark.anyio
async def test_revenue_by_order_type_separates_dine_in_from_takeaway(
    api_client, manager_token, session
):
    from datetime import date

    from tests.modules.conftest import _r_dish, _r_invoice, _r_line, _r_order

    dish = await _r_dish(session, "Món mang về")
    takeaway = await _r_order(session, bd=date(2026, 9, 10), order_type="Mang về")
    await _r_line(session, takeaway, dish, 2, 30000)
    await _r_invoice(session, takeaway, bd=date(2026, 9, 10), total=60000)
    await session.commit()

    body = (
        await api_client.get(
            REVENUE,
            headers=_auth(manager_token),
            params={"group_by": "order_type", "granularity": "month", "anchor": "2026-09-01"},
        )
    ).json()

    assert [(row["key"], row["DoanhThu"], row["SoDon"]) for row in body["items"]] == [
        ("Mang về", "60000.0000", 1)
    ]


@pytest.mark.anyio
async def test_an_unknown_grouping_is_rejected(api_client, manager_token):
    response = await api_client.get(
        REVENUE, headers=_auth(manager_token), params={"group_by": "waiter"}
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_only_a_manager_may_read_revenue(api_client, cashier_token, warehouse_token):
    """Table 33."""
    cashier = await api_client.get(REVENUE, headers=_auth(cashier_token))
    warehouse = await api_client.get(REVENUE, headers=_auth(warehouse_token))

    assert cashier.status_code == 403
    assert warehouse.status_code == 403


@pytest.mark.anyio
async def test_revenue_for_an_empty_period_is_zero_not_an_error(api_client, manager_token):
    body = (
        await api_client.get(
            REVENUE,
            headers=_auth(manager_token),
            params={"granularity": "year", "anchor": "1999-01-01"},
        )
    ).json()

    assert Decimal(body["total"]) == Decimal("0")
    assert body["items"] == []
