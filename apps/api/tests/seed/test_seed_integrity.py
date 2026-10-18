"""Seed failures must leave auditable results and coherent persisted data."""

import random
from decimal import Decimal

import pytest
from scripts.seed import operations
from scripts.seed.catalog import seed_catalog
from scripts.seed.config import SeedConfig
from sqlalchemy import func, select

from app.core.errors import BusinessRuleError
from app.modules.catalog.models import DiningTable, Ingredient
from app.modules.inventory.models import StockIssue
from app.modules.sales.models import Order, PaymentTransaction


async def test_rejected_order_does_not_occupy_a_table(session, seeded_reference):
    ids = await seed_catalog(session, SeedConfig())
    result = await operations._place_order(
        session, ids, [1.0] * len(ids.dish_ids), random.Random(42), SeedConfig().now.date()
    )
    await session.commit()
    assert not result.succeeded
    assert result.reason
    assert await session.scalar(select(func.count()).select_from(Order)) == 0
    assert set(await session.scalars(select(DiningTable.status))) == {"Trống"}


async def test_rejected_writeoff_rolls_back_created_issue(session, seeded_reference):
    ids = await seed_catalog(session, SeedConfig())
    result = await operations._write_off(session, ids, random.Random(42))
    await session.commit()
    assert not result.succeeded
    assert result.reason
    assert await session.scalar(select(func.count()).select_from(StockIssue)) == 0


async def test_seed_reaches_requested_order_count_and_reports_attempts(session, seeded_reference):
    config = SeedConfig(seed=42, months=1, orders_target=40)
    ids = await seed_catalog(session, config)
    result = await operations.seed_operations(session, config, ids)
    assert result.orders == 40
    assert result.order_attempts == result.orders + result.order_rejected
    assert sum(result.rejection_reasons.values()) == result.order_rejected + result.issue_rejected
    assert await session.scalar(select(func.count()).select_from(Order)) == 40
    assert "Đang mở" not in set(await session.scalars(select(Order.status)))
    assert result.pending_reconciliation == await session.scalar(
        select(func.count()).select_from(Order).where(Order.status == "Chờ đối soát")
    )
    await operations.validate_seed_integrity(session)


async def test_integrity_check_rejects_persisted_stock_mismatch(session, seeded_reference):
    ids = await seed_catalog(session, SeedConfig())
    ingredient = await session.get(Ingredient, ids.ingredient_ids[0])
    ingredient.stock_qty = Decimal("1")
    await session.commit()
    with pytest.raises(RuntimeError, match="stock"):
        await operations.validate_seed_integrity(session)


async def test_unexpected_settlement_failure_aborts_with_context(
    session, seeded_reference, monkeypatch
):
    config = SeedConfig(seed=42, months=1, orders_target=1)
    ids = await seed_catalog(session, config)
    await operations._receive(
        session, ids, random.Random(42), config.now.date(), all_ingredients=True
    )

    async def broken_cash(*args, **kwargs):
        raise ValueError("broken settlement")

    monkeypatch.setattr(operations.payments_service, "pay_cash", broken_cash)
    monkeypatch.setattr(operations, "CANCELLED_ORDER_RATIO", 0)
    monkeypatch.setattr(operations, "CASH_PAYMENT_RATIO", 1)
    with pytest.raises(RuntimeError, match=r"order.*2026") as caught:
        await operations._place_order(
            session, ids, [1.0] * len(ids.dish_ids), random.Random(42), config.now.date()
        )
    assert isinstance(caught.value.__cause__, ValueError)
    await session.commit()
    assert await session.scalar(select(func.count()).select_from(Order)) == 0
    assert await session.scalar(select(func.count()).select_from(PaymentTransaction)) == 0


async def test_exhausted_rejection_budget_fails_instead_of_reporting_success(
    session, seeded_reference, monkeypatch
):
    config = SeedConfig(seed=42, months=1, orders_target=1)
    ids = await seed_catalog(session, config)

    async def no_stock(*args, **kwargs):
        return operations.AttemptResult(False, "order: unavailable")

    monkeypatch.setattr(operations, "_place_order", no_stock)
    with pytest.raises(RuntimeError, match=r"target failed.*succeeded=0.*unavailable"):
        await operations.seed_operations(session, config, ids)


async def test_rejected_settlement_rolls_back_stock_order_and_table(
    session, seeded_reference, monkeypatch
):
    config = SeedConfig()
    ids = await seed_catalog(session, config)
    await operations._receive(
        session, ids, random.Random(42), config.now.date(), all_ingredients=True
    )
    await session.commit()
    before = list((await session.execute(select(Ingredient.id, Ingredient.stock_qty))).all())

    async def refused_cash(*args, **kwargs):
        raise BusinessRuleError("settlement refused")

    monkeypatch.setattr(operations.payments_service, "pay_cash", refused_cash)
    monkeypatch.setattr(operations, "CANCELLED_ORDER_RATIO", 0)
    monkeypatch.setattr(operations, "CASH_PAYMENT_RATIO", 1)
    outcome = await operations._place_order(
        session, ids, [1.0] * len(ids.dish_ids), random.Random(42), config.now.date()
    )
    await session.commit()
    assert not outcome.succeeded
    assert "settlement refused" in outcome.reason
    assert (
        list((await session.execute(select(Ingredient.id, Ingredient.stock_qty))).all()) == before
    )
    assert await session.scalar(select(func.count()).select_from(Order)) == 0
    assert set(await session.scalars(select(DiningTable.status))) == {"Trống"}
    await operations.validate_seed_integrity(session)


def test_report_describes_effective_config_without_database_credentials():
    from scripts.seed.generate import seed_report
    from scripts.seed.operations import SeedSummary

    config = SeedConfig(seed=7, months=1, orders_target=40)
    summary = SeedSummary(40, 5, 2, 43, 3, 2, 0, {"order: stock": 3}, 1, 0)
    report = seed_report(
        config, summary, "mysql+asyncmy://alice:supersecret@db:3306/demo", ("0007",)
    )
    assert report["database"] == {"dialect": "mysql", "schema": "demo", "revisions": ["0007"]}
    assert report["config"]["now"] == config.now.isoformat()
    assert report["operations"]["orders"] == 40
    assert "supersecret" not in str(report)
    assert "alice" not in str(report)


@pytest.mark.parametrize("months,orders", [(0, 40), (-1, 40), (1, -1)])
def test_invalid_seed_size_fails_before_database_writes(months, orders):
    with pytest.raises(ValueError):
        SeedConfig(months=months, orders_target=orders)


async def test_pending_reconciliation_is_reported_and_physical_table_released(
    session, seeded_reference, monkeypatch
):
    config = SeedConfig(months=1, orders_target=2)
    ids = await seed_catalog(session, config)
    monkeypatch.setattr(operations, "CANCELLED_ORDER_RATIO", 0)
    monkeypatch.setattr(operations, "CASH_PAYMENT_RATIO", 0)
    monkeypatch.setattr(operations, "RECONCILE_RATIO", 1)
    monkeypatch.setattr(operations, "DISPUTE_RATIO", 0)
    summary = await operations.seed_operations(session, config, ids)
    assert summary.pending_reconciliation == 2
    assert summary.disputed_orders == 0
    assert set(await session.scalars(select(Order.status))) == {"Chờ đối soát"}
    assert set(await session.scalars(select(DiningTable.status))) == {"Trống"}
    assert set(await session.scalars(select(DiningTable.current_order_id))) == {None}


async def test_receipt_failure_aborts_with_business_date_context(
    session, seeded_reference, monkeypatch
):
    config = SeedConfig()
    ids = await seed_catalog(session, config)

    async def broken_receipt(*args, **kwargs):
        raise ValueError("broken receipt")

    monkeypatch.setattr(operations.inventory_service, "create_receipt", broken_receipt)
    with pytest.raises(RuntimeError, match=r"receipt.*2026") as caught:
        await operations._receive(session, ids, random.Random(42), config.now.date())
    assert isinstance(caught.value.__cause__, ValueError)
