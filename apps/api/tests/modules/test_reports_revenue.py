"""Phase 5 Task 1 — report periods and revenue (FR-REP-01, FR-REP-02)."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.reports.periods import resolve_period

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
async def test_a_transaction_awaiting_reconciliation_is_provisional_revenue(
    api_client, manager_token, order_awaiting_reconciliation
):
    """FR-REP-02: counted for now, but flagged."""
    body = (
        await api_client.get(REVENUE, headers=_auth(manager_token), params={"granularity": "month"})
    ).json()

    assert Decimal(body["provisional"]) == order_awaiting_reconciliation.total
    assert Decimal(body["total"]) >= Decimal(body["provisional"])


@pytest.mark.anyio
async def test_marking_a_dispute_subtracts_it_from_revenue(
    api_client, manager_token, disputed_payment, invoices_in_september
):
    """FR-REP-02: a dispute is deducted retroactively."""
    body = (
        await api_client.get(REVENUE, headers=_auth(manager_token), params={"granularity": "month"})
    ).json()

    assert Decimal(body["total"]) == invoices_in_september.total - disputed_payment.total


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
