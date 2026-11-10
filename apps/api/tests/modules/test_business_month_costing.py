"""Cost reports share the 06:00 business-date boundary."""

from datetime import datetime
from decimal import Decimal

import pytest

from app.core.errors import BusinessRuleError
from app.modules.inventory.models import StockIssue, StockIssueLine
from app.modules.reports.queries import waste_cost
from tests.modules.test_inventory_costing import _headers, _ingredient, _make_client


@pytest.mark.anyio
@pytest.mark.parametrize("month,next_year,next_month", [(202609, 2026, 10), (202612, 2027, 1)])
async def test_waste_follows_business_month_boundaries(session, month, next_year, next_month):
    """A write-off at 05:59 on the 1st still belongs to the month before."""
    ingredient = await _ingredient(session)
    year, mon = divmod(month, 100)
    moments = [
        datetime(year, mon, 1, 5, 59),
        datetime(year, mon, 1, 6),
        datetime(next_year, next_month, 1, 5, 59),
        datetime(next_year, next_month, 1, 6),
    ]
    for moment, cost in zip(moments, [1000, 4000, 6000, 9000], strict=True):
        issue = StockIssue(created_at=moment, issue_date=moment)
        session.add(issue)
        await session.flush()
        session.add(
            StockIssueLine(
                issue_id=issue.id, ingredient_id=ingredient.id, quantity=1, estimated_cost=cost
            )
        )
    await session.commit()
    client = await _make_client(session)
    headers, _ = await _headers(session)

    assert await waste_cost(session, month) == (Decimal(10000), 0)
    async with client:
        report = await client.get(
            "/api/v1/reports/costs", params={"month": str(month)}, headers=headers
        )
    assert report.status_code == 200, report.text
    assert Decimal(report.json()["HaoHut"]) == 10000
    assert report.json()["TamTinh"] is False


@pytest.mark.anyio
@pytest.mark.parametrize("month", [202600, 202613, 99999, 1000000, 999912])
async def test_invalid_month_is_rejected_before_database_work(session, month):
    with pytest.raises(BusinessRuleError):
        await waste_cost(session, month)


@pytest.mark.anyio
@pytest.mark.parametrize("month", ["2026-13", "9999-12"])
async def test_invalid_month_returns_domain_error_through_endpoints(session, month):
    client = await _make_client(session)
    headers, _ = await _headers(session)
    async with client:
        reported = await client.get(
            "/api/v1/reports/costs", params={"month": month}, headers=headers
        )
        assert reported.status_code == 422
