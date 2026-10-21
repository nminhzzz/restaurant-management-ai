"""Monthly costing and reports share the 06:00 business-date boundary."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from app.core.errors import BusinessRuleError
from app.modules.inventory.costing import backfill_issue_costs, close_month
from app.modules.inventory.models import (
    GoodsReceipt,
    GoodsReceiptLine,
    IngredientLot,
    MonthlyAverageCost,
    StockIssue,
    StockIssueLine,
    StockMovement,
)
from app.modules.reports.queries import waste_cost
from tests.modules.test_inventory_costing import _headers, _ingredient, _make_client


@pytest.mark.anyio
@pytest.mark.parametrize("month,next_year,next_month", [(202609, 2026, 10), (202612, 2027, 1)])
async def test_month_close_and_waste_follow_business_date_boundaries(
    session, month, next_year, next_month
):
    ingredient = await _ingredient(session)
    year, mon = divmod(month, 100)
    moments = [
        datetime(year, mon, 1, 5, 59),
        datetime(year, mon, 1, 6),
        datetime(next_year, next_month, 1, 5, 59),
        datetime(next_year, next_month, 1, 6),
    ]
    lines = []
    for moment, price, quantity in zip(
        moments, [9000, 1000, 3000, 8000], [1, 2, 3, 4], strict=True
    ):
        receipt = GoodsReceipt(receipt_date=moment)
        issue = StockIssue(created_at=moment, issue_date=moments[0])
        session.add_all([receipt, issue])
        await session.flush()
        line = StockIssueLine(
            issue_id=issue.id, ingredient_id=ingredient.id, quantity=quantity, estimated_cost=0
        )
        session.add_all(
            [
                GoodsReceiptLine(
                    receipt_id=receipt.id, ingredient_id=ingredient.id, quantity=1, unit_price=price
                ),
                line,
            ]
        )
        lines.append(line)
    await session.commit()
    client = await _make_client(session)
    headers, _ = await _headers(session)
    assert await waste_cost(session, month) == (Decimal(0), 2)
    async with client:
        response = await client.post(f"/api/v1/inventory/costing/{month}/close", headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()[0]["GiaBinhQuan"] == 2000
        assert response.json()[0]["TongSoLuongNhap"] == 2
        for line in lines:
            await session.refresh(line)
        assert [line.estimated_cost for line in lines] == [0, 4000, 6000, 0]
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
        await close_month(session, month)
    with pytest.raises(BusinessRuleError):
        await backfill_issue_costs(session, month)
    with pytest.raises(BusinessRuleError):
        await waste_cost(session, month)


@pytest.mark.anyio
@pytest.mark.parametrize("month", ["2026-13", "9999-12"])
async def test_invalid_month_returns_domain_error_through_endpoints(session, month):
    client = await _make_client(session)
    headers, _ = await _headers(session)
    async with client:
        closed = await client.post(
            f"/api/v1/inventory/costing/{month.replace('-', '')}/close", headers=headers
        )
        assert closed.status_code == 422
        reported = await client.get(
            "/api/v1/reports/costs", params={"month": month}, headers=headers
        )
        assert reported.status_code == 422


@pytest.mark.anyio
async def test_backfill_rounds_fractional_cost_to_database_scale(session):
    ingredient = await _ingredient(session)
    issue = StockIssue(created_at=datetime(2026, 9, 10, 10))
    session.add(issue)
    await session.flush()
    line = StockIssueLine(
        issue_id=issue.id,
        ingredient_id=ingredient.id,
        quantity=Decimal("0.3333"),
        estimated_cost=0,
    )
    session.add_all(
        [
            line,
            MonthlyAverageCost(
                ingredient_id=ingredient.id,
                month=202609,
                avg_cost=Decimal("1234.5678"),
                total_qty=1,
            ),
        ]
    )
    await session.flush()
    assert await backfill_issue_costs(session, 202609) == 1
    assert line.estimated_cost == Decimal("411.4814")


@pytest.mark.anyio
async def test_average_cost_includes_opening_stock_and_carries_forward(session):
    ingredient = await _ingredient(session)
    # Opening: 1 kg received in August at 1.000/kg.
    opening_receipt = GoodsReceipt(receipt_date=datetime(2026, 8, 31, 9))
    session.add(opening_receipt)
    await session.flush()
    opening_line = GoodsReceiptLine(
        receipt_id=opening_receipt.id,
        ingredient_id=ingredient.id,
        quantity=Decimal("1"),
        unit_price=Decimal("1000"),
    )
    session.add(opening_line)
    await session.flush()
    session.add(
        IngredientLot(
            ingredient_id=ingredient.id,
            receipt_line_id=opening_line.id,
            quantity_remaining=Decimal("1"),
            received_quantity=Decimal("1"),
            unit_price=Decimal("1000"),
            received_at=datetime(2026, 8, 31, 9),
            status="Còn hạn",
            is_adjustment=False,
        )
    )
    session.add(
        StockMovement(
            ingredient_id=ingredient.id,
            kind="Nhập",
            qty=Decimal("1"),
            business_date=date(2026, 8, 31),
            receipt_line_id=opening_line.id,
        )
    )
    receipt = GoodsReceipt(receipt_date=datetime(2026, 9, 10, 9))
    session.add(receipt)
    await session.flush()
    session.add(
        GoodsReceiptLine(
            receipt_id=receipt.id,
            ingredient_id=ingredient.id,
            quantity=Decimal("2"),
            unit_price=Decimal("2000"),
        )
    )
    await session.commit()

    rows = await close_month(session, 202609)
    ingredient_rows = [row for row in rows if row.ingredient_id == ingredient.id]
    assert len(ingredient_rows) == 1
    # (1.000 opening value + 4.000 purchase) / (1 + 2) = 1.666,6667
    assert Decimal(str(ingredient_rows[0].avg_cost)) == Decimal("1666.6667")

    # October has no purchase; the September unit cost must carry over.
    october_rows = await close_month(session, 202610)
    october = [row for row in october_rows if row.ingredient_id == ingredient.id]
    assert len(october) == 1
    assert Decimal(str(october[0].avg_cost)) == Decimal("1666.6667")
    assert Decimal(str(october[0].total_qty)) == 0
