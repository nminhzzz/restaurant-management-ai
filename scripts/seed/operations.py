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
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from scripts.seed.catalog import CatalogIds, build_catalogue
from scripts.seed.config import (
    CANCELLED_ORDER_RATIO,
    CASH_PAYMENT_RATIO,
    DISH_POWER_LAW_EXPONENT,
    DISPUTE_RATIO,
    HOUR_WEIGHTS,
    MONTH_SEASONALITY,
    RECONCILE_RATIO,
    TAKEAWAY_RATIO,
    WEEKEND_MULTIPLIER,
    SeedConfig,
    frozen_clock,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError
from app.modules.catalog.models import Ingredient
from app.modules.inventory import service as inventory_service
from app.modules.inventory.costing import backfill_issue_costs, close_month
from app.modules.inventory.models import IngredientLot, StockMovement
from app.modules.sales import orders as orders_service
from app.modules.sales import payments as payments_service
from app.modules.sales.models import Order, PaymentTransaction
from app.shared import business_date

RESTOCK_WEEKDAYS = (0, 3)  # Monday and Thursday
RESTOCK_INGREDIENTS = 20
WRITE_OFF_CHANCE = 0.10


@dataclass(frozen=True)
class SeedSummary:
    orders: int
    receipts: int
    issues: int
    order_attempts: int
    order_rejected: int
    issue_attempts: int
    issue_rejected: int
    rejection_reasons: dict[str, int]
    pending_reconciliation: int
    disputed_orders: int


@dataclass(frozen=True)
class AttemptResult:
    succeeded: bool
    reason: str | None = None


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
    total = sum(daily_order_count(config, end - timedelta(days=offset)) for offset in range(days))
    weights = _dish_weights(plan.dish_names)
    weight_total = sum(weights)
    return {
        name: round(total * weight / weight_total)
        for name, weight in zip(plan.dish_names, weights, strict=True)
    }


def _moment(day: date, hour: int, minute: int = 0) -> datetime:
    moment = datetime.combine(day, time(hour, minute))
    if business_date.business_date_of(moment) < day:
        moment += timedelta(days=1)
    # A shortened transition day may omit this wall-clock hour entirely.
    if business_date.business_date_of(moment) != day:
        moment = business_date.business_date_start(day)
    return moment


def _pick_hour(rng: random.Random) -> int:
    hours = list(HOUR_WEIGHTS)
    return rng.choices(hours, weights=[HOUR_WEIGHTS[h] for h in hours], k=1)[0]


async def _receive(
    session: AsyncSession,
    ids: CatalogIds,
    rng: random.Random,
    day: date,
    *,
    all_ingredients: bool = False,
) -> None:
    ingredients = (
        ids.ingredient_ids
        if all_ingredients
        else rng.sample(ids.ingredient_ids, k=min(RESTOCK_INGREDIENTS, len(ids.ingredient_ids)))
    )
    lines = [
        {
            "ingredient_id": ingredient_id,
            "quantity": round(rng.uniform(20, 60), 2),
            "unit_price": rng.randrange(15_000, 120_000, 1_000),
        }
        for ingredient_id in ingredients
    ]
    try:
        async with session.begin_nested():
            await inventory_service.create_receipt(
                session, ids.manager_id, ids.supplier_ids[0], _moment(day, 8), lines
            )
    except Exception as exc:
        raise RuntimeError(f"Seed receipt failed: day={day} ingredients={ingredients}") from exc


async def _write_off(session: AsyncSession, ids: CatalogIds, rng: random.Random) -> AttemptResult:
    """Reject the entire issue atomically when stock is unavailable."""
    ingredient_id = rng.choice(ids.ingredient_ids)
    try:
        async with session.begin_nested():
            await inventory_service.create_issue(
                session,
                ids.manager_id,
                "Hao hụt",
                [{"ingredient_id": ingredient_id, "quantity": round(rng.uniform(0.2, 2.0), 2)}],
            )
    except BusinessRuleError as exc:
        return AttemptResult(False, f"writeoff: {exc.message}")
    except Exception as exc:
        raise RuntimeError(f"Seed writeoff failed: ingredient={ingredient_id}") from exc
    return AttemptResult(True)


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
) -> AttemptResult:
    """Submit and settle atomically; rejected attempts leave no partial mutations."""
    from app.modules.catalog.models import DiningTable
    from app.modules.sales.floor import release_table

    moment = _moment(day, _pick_hour(rng), rng.randrange(0, 60))
    with frozen_clock(moment):
        lines = [
            {"MaMon": dish_id, "SoLuong": rng.randint(1, 3), "GhiChu": None}
            for dish_id in rng.choices(ids.dish_ids, weights=weights, k=rng.randint(1, 4))
        ]
        takeaway = rng.random() < TAKEAWAY_RATIO
        try:
            async with session.begin_nested():
                result = await orders_service.submit_order(
                    session,
                    {
                        "table_id": None if takeaway else rng.choice(ids.table_ids),
                        "order_type": "Mang về" if takeaway else "Tại chỗ",
                        "lines": lines,
                    },
                    actor_id=ids.manager_id,
                )
                if result["rejected"]:
                    reasons = sorted({item["reason"] for item in result["rejected"]})
                    raise BusinessRuleError("; ".join(reasons))
                order = result["order"]
                roll = rng.random()
                if roll < CANCELLED_ORDER_RATIO:
                    await orders_service.cancel_order(
                        session, order.id, "khách bỏ về", actor_id=ids.manager_id
                    )
                elif roll < CANCELLED_ORDER_RATIO + CASH_PAYMENT_RATIO:
                    await payments_service.pay_cash(session, order.id, actor_id=ids.manager_id)
                else:
                    await _settle_qr(session, order.id, rng)
                table = (
                    await session.get(DiningTable, order.table_id)
                    if order.table_id is not None
                    else None
                )
                if table is not None and table.current_order_id == order.id:
                    await release_table(session, table.id, order.id, actor_id=ids.manager_id)
        except BusinessRuleError as exc:
            return AttemptResult(False, f"order: {exc.message}")
        except Exception as exc:
            raise RuntimeError(f"Seed order failed: day={day} moment={moment.isoformat()}") from exc
    return AttemptResult(True)


async def validate_seed_integrity(session: AsyncSession) -> dict[str, int]:
    """Read persisted quantities and financial states rather than trusting cached objects."""
    await session.flush()
    # Separate grouped queries avoid multiplication of lots by movements in a join.
    lots = {
        ingredient_id: quantity
        for ingredient_id, quantity in await session.execute(
            select(
                IngredientLot.ingredient_id, func.sum(IngredientLot.quantity_remaining)
            ).group_by(IngredientLot.ingredient_id)
        )
    }
    ledger = {
        ingredient_id: quantity
        for ingredient_id, quantity in await session.execute(
            select(StockMovement.ingredient_id, func.sum(StockMovement.qty)).group_by(
                StockMovement.ingredient_id
            )
        )
    }
    precision = Decimal("0.0001")
    for ingredient_id, stock in await session.execute(select(Ingredient.id, Ingredient.stock_qty)):
        quantities = [
            Decimal(value).quantize(precision)
            for value in (stock, lots.get(ingredient_id, 0), ledger.get(ingredient_id, 0))
        ]
        if min(quantities) < 0 or len(set(quantities)) != 1:
            raise RuntimeError(
                f"Seed stock invariant failed: ingredient={ingredient_id} quantities={quantities}"
            )
    negative_lots = await session.scalar(
        select(func.count()).select_from(IngredientLot).where(IngredientLot.quantity_remaining < 0)
    )
    if negative_lots:
        raise RuntimeError(f"Seed stock invariant failed: {negative_lots} negative lots")
    statuses = {
        status: count
        for status, count in await session.execute(
            select(Order.status, func.count()).group_by(Order.status)
        )
    }
    allowed = {"Đã thanh toán", "Chờ đối soát", "Tranh chấp", "Đã hủy", "Tự động đóng"}
    unexpected = set(statuses) - allowed
    if unexpected:
        raise RuntimeError(f"Seed has unintended open orders: {sorted(unexpected)}")
    pending_without_payment = await session.scalar(
        select(func.count())
        .select_from(Order)
        .where(
            Order.status == "Chờ đối soát",
            ~select(PaymentTransaction.id)
            .where(
                PaymentTransaction.order_id == Order.id,
                PaymentTransaction.status == "Chờ đối soát",
            )
            .exists(),
        )
    )
    if pending_without_payment:
        raise RuntimeError("Seed pending reconciliation has no matching payment")
    return statuses


async def seed_operations(
    session: AsyncSession, config: SeedConfig, ids: CatalogIds
) -> SeedSummary:
    """Generate the exact requested volume with a bounded, visible rejection budget."""
    rng = random.Random(config.seed + 1)
    weights = _dish_weights(ids.dish_names)
    end = business_date.business_date_of(config.now)
    start = end - timedelta(days=config.months * 30)
    days = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]
    volumes = [daily_order_count(config, day) for day in days]
    total_weight = sum(volumes)
    cumulative = orders = receipts = issues = order_attempts = issue_attempts = 0
    reasons: Counter[str] = Counter()
    issue_rejected = 0
    for day, volume in zip(days, volumes, strict=True):
        if day == start or day.weekday() in RESTOCK_WEEKDAYS:
            with frozen_clock(_moment(day, 8)):
                await _receive(session, ids, rng, day, all_ingredients=day == start)
            receipts += 1
        if rng.random() < WRITE_OFF_CHANCE:
            issue_attempts += 1
            with frozen_clock(_moment(day, 9)):
                outcome = await _write_off(session, ids, rng)
            if outcome.succeeded:
                issues += 1
            else:
                issue_rejected += 1
                reasons[outcome.reason or "writeoff: unspecified"] += 1
        cumulative += volume
        target_so_far = config.orders_target * cumulative // total_weight
        budget = (target_so_far - orders) * 5 + 10
        for _ in range(budget):
            if orders >= target_so_far:
                break
            order_attempts += 1
            outcome = await _place_order(session, ids, weights, rng, day)
            if outcome.succeeded:
                orders += 1
            else:
                reasons[outcome.reason or "order: unspecified"] += 1
                # Popular dishes must remain available as their recipes deplete stock.
                with frozen_clock(_moment(day, 8)):
                    await _receive(session, ids, rng, day, all_ingredients=True)
                receipts += 1
        if orders < target_so_far:
            raise RuntimeError(
                f"Seed order target failed: day={day} requested={target_so_far} "
                f"succeeded={orders} attempted={order_attempts} reasons={dict(reasons)}"
            )
        if day.day == 1 and day > start:
            previous = day - timedelta(days=1)
            month = previous.year * 100 + previous.month
            await close_month(session, month)
            await backfill_issue_costs(session, month)
        await session.commit()
    session.expire_all()
    statuses = await validate_seed_integrity(session)
    return SeedSummary(
        orders=orders,
        receipts=receipts,
        issues=issues,
        order_attempts=order_attempts,
        order_rejected=order_attempts - orders,
        issue_attempts=issue_attempts,
        issue_rejected=issue_rejected,
        rejection_reasons=dict(sorted(reasons.items())),
        pending_reconciliation=statuses.get("Chờ đối soát", 0),
        disputed_orders=statuses.get("Tranh chấp", 0),
    )
