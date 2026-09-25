"""Order, payment and stock generation for the twelve-month dataset (NFR-03).

Every order goes through `submit_order`/`pay_cash`/`start_qr`, so stock is drawn FIFO
and the movement ledger stays consistent with the ingredient and lot totals. The
generator never writes a row the services would refuse — that is the whole point of
building the dataset through the service layer.

The clock is the seam in `app.shared.business_date`: each simulated moment points that
seam at itself for the duration of the call, so historical orders land on the right
business dates instead of today's.
"""

import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError
from app.modules.inventory import service as inventory_service
from app.modules.inventory.costing import backfill_issue_costs, close_month
from app.modules.sales import orders as orders_service
from app.modules.sales import payments as payments_service
from app.shared import business_date
from scripts.seed.catalog import CatalogIds, build_catalogue
from scripts.seed.config import (
    CANCELLED_ORDER_RATIO,
    CASH_PAYMENT_RATIO,
    DISH_POWER_LAW_EXPONENT,
    DISPUTE_RATIO,
    HOUR_WEIGHTS,
    MONTH_SEASONALITY,
    RECONCILE_RATIO,
    WEEKEND_MULTIPLIER,
    SeedConfig,
    frozen_clock,
)

RESTOCK_WEEKDAYS = (0, 3)  # Monday and Thursday
RESTOCK_INGREDIENTS = 20
WRITE_OFF_CHANCE = 0.10


@dataclass(frozen=True)
class SeedSummary:
    orders: int
    receipts: int
    issues: int


def hour_weight(hour: int) -> float:
    return HOUR_WEIGHTS[hour % 24]


def daily_order_count(config: SeedConfig, day: date) -> int:
    """Expected orders for one business date: season, weekend and the NFR-03 floor."""
    base = config.orders_target / max(config.months * 30, 1)
    seasonal = MONTH_SEASONALITY[day.month]
    weekend = WEEKEND_MULTIPLIER if day.weekday() >= 5 else 1.0
    return max(1, round(base * seasonal * weekend))


def _dish_weights(dish_names: list[str]) -> list[float]:
    return [1.0 / ((rank + 1) ** DISH_POWER_LAW_EXPONENT) for rank in range(len(dish_names))]


def dish_order_counts(config: SeedConfig, days: int) -> dict[str, int]:
    """Power-law distribution of orders across dishes over the last `days` days."""
    plan = build_catalogue(config)
    end = business_date.business_date_of(config.now)
    total = sum(
        daily_order_count(config, end - timedelta(days=offset)) for offset in range(days)
    )
    weights = _dish_weights(plan.dish_names)
    weight_total = sum(weights)
    return {
        name: round(total * weight / weight_total)
        for name, weight in zip(plan.dish_names, weights, strict=True)
    }


def _moment(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute))


def _pick_hour(rng: random.Random) -> int:
    hours = list(HOUR_WEIGHTS)
    return rng.choices(hours, weights=[HOUR_WEIGHTS[h] for h in hours], k=1)[0]


async def _receive(session: AsyncSession, ids: CatalogIds, rng: random.Random, day: date) -> None:
    ingredients = rng.sample(ids.ingredient_ids, k=min(RESTOCK_INGREDIENTS, len(ids.ingredient_ids)))
    lines = [
        {
            "ingredient_id": ingredient_id,
            "quantity": round(rng.uniform(20, 60), 2),
            "unit_price": rng.randrange(15_000, 120_000, 1_000),
        }
        for ingredient_id in ingredients
    ]
    await inventory_service.create_receipt(
        session, ids.manager_id, ids.supplier_ids[0], _moment(day, 8), lines
    )


async def _write_off(session: AsyncSession, ids: CatalogIds, rng: random.Random) -> bool:
    """A small manual write-off; skipped when the ingredient has nothing to write off."""
    try:
        await inventory_service.create_issue(
            session,
            ids.manager_id,
            "Hao hụt",
            [
                {
                    "ingredient_id": rng.choice(ids.ingredient_ids),
                    "quantity": round(rng.uniform(0.2, 2.0), 2),
                }
            ],
        )
    except BusinessRuleError:
        return False
    return True


async def _settle_qr(session: AsyncSession, order_id: int, rng: random.Random) -> None:
    payment = await payments_service.start_qr(session, order_id, actor_id=None)
    roll = rng.random()
    if roll < 1 - RECONCILE_RATIO - DISPUTE_RATIO:
        signature = payments_service.sign_payload(f"{payment.id}:{payment.amount}")
        await payments_service.handle_webhook(
            session,
            {
                "payment_id": payment.id,
                "amount": payment.amount,
                "signature": signature,
            },
        )
        return

    payment.status = "Hết hạn"
    await session.flush()
    await payments_service.mark_for_reconciliation(session, payment.id, actor_id=None)
    if roll >= 1 - DISPUTE_RATIO:
        await payments_service.resolve_reconciliation(
            session, payment.id, "not_received", actor_id=None
        )


async def _place_order(
    session: AsyncSession,
    ids: CatalogIds,
    weights: list[float],
    rng: random.Random,
    day: date,
) -> bool:
    """One order, from submit to a final state. `False` when stock refused it."""
    moment = _moment(day, _pick_hour(rng), rng.randrange(0, 60))
    with frozen_clock(moment):
        lines = [
            {"MaMon": dish_id, "SoLuong": rng.randint(1, 3), "GhiChu": None}
            for dish_id in rng.choices(ids.dish_ids, weights=weights, k=rng.randint(1, 4))
        ]
        try:
            result = await orders_service.submit_order(
                session,
                {
                    "table_id": rng.choice(ids.table_ids),
                    "order_type": "Tại chỗ",
                    "lines": lines,
                },
                actor_id=ids.manager_id,
            )
        except BusinessRuleError:
            return False

        order = result["order"]
        try:
            roll = rng.random()
            if roll < CANCELLED_ORDER_RATIO:
                await orders_service.cancel_order(
                    session, order.id, "khách bỏ về", actor_id=ids.manager_id
                )
            elif roll < CANCELLED_ORDER_RATIO + CASH_PAYMENT_RATIO:
                await payments_service.pay_cash(session, order.id, actor_id=ids.manager_id)
            else:
                await _settle_qr(session, order.id, rng)
        except BusinessRuleError:
            # Never leave an order open: the dataset must only contain final states.
            try:
                await orders_service.cancel_order(
                    session, order.id, "không tất toán được", actor_id=ids.manager_id
                )
            except BusinessRuleError:
                pass
        return True


async def seed_operations(
    session: AsyncSession, config: SeedConfig, ids: CatalogIds
) -> SeedSummary:
    """Twelve months of orders, payments, restocks and write-offs."""
    rng = random.Random(config.seed + 1)
    plan = build_catalogue(config)
    weights = _dish_weights(plan.dish_names)

    end = business_date.business_date_of(config.now)
    start = end - timedelta(days=config.months * 30)

    orders = receipts = issues = 0
    day = start
    while day <= end:
        if day.weekday() in RESTOCK_WEEKDAYS:
            with frozen_clock(_moment(day, 8)):
                await _receive(session, ids, rng, day)
            receipts += 1

        if rng.random() < WRITE_OFF_CHANCE:
            with frozen_clock(_moment(day, 9)):
                if await _write_off(session, ids, rng):
                    issues += 1

        for _ in range(daily_order_count(config, day)):
            if await _place_order(session, ids, weights, rng, day):
                orders += 1

        if day.day == 1 and day > start:
            previous = day - timedelta(days=1)
            month = previous.year * 100 + previous.month
            await close_month(session, month)
            await backfill_issue_costs(session, month)

        await session.commit()
        day += timedelta(days=1)

    return SeedSummary(orders=orders, receipts=receipts, issues=issues)


__all__ = [
    "SeedSummary",
    "daily_order_count",
    "dish_order_counts",
    "frozen_clock",
    "hour_weight",
    "seed_operations",
]
