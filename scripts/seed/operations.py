"""Order, payment and stock generation for the two-month dataset (Appendix B.1).

Every order goes through `submit_order`/`pay_cash`/`start_qr`, so stock is drawn FIFO
and the movement ledger stays consistent with the ingredient and lot totals. The
generator never writes a row the services would refuse — that is the whole point of
building the dataset through the service layer.

The clock is the seam in `app.shared.business_date`: each simulated moment points that
seam at itself for the duration of the call, so historical orders land on the right
business dates instead of today's.
"""

import math
import random
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from scripts.seed.catalog import CatalogIds, build_catalogue, dish_weights
from scripts.seed.config import (
    CANCELLED_ORDER_RATIO,
    CASH_PAYMENT_RATIO,
    DAILY_ORDER_JITTER,
    DISPUTE_RATIO,
    DRY_RESTOCK_WEEKDAYS,
    HOUR_WEIGHTS,
    MAX_LINES_PER_ORDER,
    MAX_RECEIPT_LINE_KG,
    MAX_SERVINGS_PER_LINE,
    MAX_STOCK_KG,
    OPENING_STOCK_DAYS,
    PRICE_JITTER,
    RECONCILE_RATIO,
    RESTOCK_HOUR,
    RESTOCK_STEP_KG,
    TAKEAWAY_RATIO,
    WEEKDAY_ORDERS,
    WEEKEND_ORDERS,
    WRITE_OFF_CHANCE,
    WRITE_OFF_RANGE_KG,
    SeedConfig,
    frozen_clock,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError
from app.modules.catalog.models import Ingredient
from app.modules.inventory import service as inventory_service
from app.modules.inventory.models import IngredientLot, StockMovement
from app.modules.sales import orders as orders_service
from app.modules.sales import payments as payments_service
from app.modules.sales.models import Order, PaymentTransaction
from app.shared import business_date

ATTEMPTS_PER_ORDER = 6
UNIT_PRICE_STEP = 500


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
    pending_verification: int
    closed_unpaid_orders: int
    expired_issues: int = 0


@dataclass(frozen=True)
class AttemptResult:
    succeeded: bool
    reason: str | None = None


def hour_weight(hour: int) -> float:
    return HOUR_WEIGHTS.get(hour % 24, 0.0)


def base_order_count(day: date) -> int:
    return WEEKEND_ORDERS if day.weekday() >= 5 else WEEKDAY_ORDERS


def seed_days(config: SeedConfig) -> list[date]:
    """The business dates before the reference moment, oldest first."""
    end = business_date.business_date_of(config.now)
    return [end - timedelta(days=offset) for offset in range(config.days, 0, -1)]


def daily_order_count(config: SeedConfig, day: date) -> float:
    """Expected orders of one business date, before the random daily fluctuation."""
    base = base_order_count(day)
    if config.orders_target is None:
        return base
    return base * config.orders_target / sum(base_order_count(d) for d in seed_days(config))


def daily_volumes(config: SeedConfig, days: list[date], rng: random.Random) -> list[int]:
    """Orders to place on each day; a forced target is split exactly over the same shape."""
    bases = [base_order_count(day) for day in days]
    if config.orders_target is None:
        return [
            round(base * rng.uniform(1 - DAILY_ORDER_JITTER, 1 + DAILY_ORDER_JITTER))
            for base in bases
        ]
    volumes: list[int] = []
    cumulative = placed = 0
    for base in bases:
        cumulative += base
        target_so_far = config.orders_target * cumulative // sum(bases)
        volumes.append(target_so_far - placed)
        placed = target_so_far
    return volumes


def dish_order_counts(config: SeedConfig, days: int) -> dict[str, int]:
    """Power-law distribution of orders across dishes over the last `days` days."""
    plan = build_catalogue()
    end = business_date.business_date_of(config.now)
    total = sum(
        daily_order_count(config, end - timedelta(days=offset)) for offset in range(1, days + 1)
    )
    weights = dish_weights(len(plan.dish_names))
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


def _pick_dishes(
    rng: random.Random, dish_ids: list[int], weights: list[float], count: int
) -> list[int]:
    """Weighted draw without replacement: a guest does not order the same dish on two lines."""
    pool = list(zip(dish_ids, weights, strict=True))
    picked: list[int] = []
    for _ in range(min(count, len(pool))):
        index = rng.choices(range(len(pool)), weights=[weight for _, weight in pool], k=1)[0]
        picked.append(pool.pop(index)[0])
    return picked


def _days_until_next_dry_restock(day: date) -> int:
    return next(
        ahead
        for ahead in range(1, 8)
        if (day + timedelta(days=ahead)).weekday() in DRY_RESTOCK_WEEKDAYS
    )


def _round_up(quantity: float) -> float:
    return math.ceil(quantity / RESTOCK_STEP_KG - 1e-9) * RESTOCK_STEP_KG


def _round_down(quantity: float) -> float:
    return math.floor(quantity / RESTOCK_STEP_KG + 1e-9) * RESTOCK_STEP_KG


def receipt_unit_price(rng: random.Random, base: int) -> int:
    """Supplier price of one delivery: the usual price give or take the market swing."""
    price = base * rng.uniform(1 - PRICE_JITTER, 1 + PRICE_JITTER)
    return round(price / UNIT_PRICE_STEP) * UNIT_PRICE_STEP


async def _stock_levels(session: AsyncSession, day: date) -> dict[int, tuple[float, float]]:
    """(usable, on the books) per ingredient; an expired lot is on the books but unusable."""
    usable = {
        ingredient_id: float(quantity)
        for ingredient_id, quantity in await session.execute(
            select(IngredientLot.ingredient_id, func.sum(IngredientLot.quantity_remaining))
            .where(
                IngredientLot.expiry_date.is_(None) | (IngredientLot.expiry_date >= day),
            )
            .group_by(IngredientLot.ingredient_id)
        )
    }
    return {
        ingredient_id: (usable.get(ingredient_id, 0.0), float(stock))
        for ingredient_id, stock in await session.execute(
            select(Ingredient.id, Ingredient.stock_qty)
        )
    }


async def _receive(
    session: AsyncSession,
    ids: CatalogIds,
    rng: random.Random,
    day: date,
    *,
    all_ingredients: bool = False,
    forecast: Callable[[date], float] = base_order_count,
    horizon_days: int | None = None,
    moment: datetime | None = None,
) -> int:
    """Buy what the kitchen needs until each ingredient's next delivery; returns the receipts.

    The bought quantity covers the expected use plus the minimum stock, less what is
    still usable, and never lifts an ingredient above the storage ceiling.
    """
    dry_day = day.weekday() in DRY_RESTOCK_WEEKDAYS
    levels = await _stock_levels(session, day)
    lines_by_supplier: dict[int | None, list[dict]] = defaultdict(list)
    for supply in ids.supplies:
        if not (all_ingredients or supply.restocked_daily or dry_day):
            continue
        days_ahead = horizon_days or (
            1 if supply.restocked_daily else _days_until_next_dry_restock(day)
        )
        need = supply.use_per_order_kg * sum(
            forecast(day + timedelta(days=offset)) for offset in range(days_ahead)
        )
        usable, on_books = levels.get(supply.ingredient_id, (0.0, 0.0))
        quantity = min(
            _round_up(need + supply.min_stock_kg - usable),
            MAX_RECEIPT_LINE_KG,
            _round_down(MAX_STOCK_KG - on_books),
        )
        if quantity <= 0:
            continue
        lines_by_supplier[supply.supplier_id].append(
            {
                "ingredient_id": supply.ingredient_id,
                "quantity": quantity,
                "unit_price": receipt_unit_price(rng, supply.unit_price),
            }
        )
    received_at = moment or _moment(day, RESTOCK_HOUR)
    for supplier_id, lines in lines_by_supplier.items():
        try:
            async with session.begin_nested():
                await inventory_service.create_receipt(
                    session, ids.manager_id, supplier_id, received_at, lines
                )
        except Exception as exc:
            raise RuntimeError(
                f"Seed receipt failed: day={day} supplier={supplier_id} lines={len(lines)}"
            ) from exc
    return len(lines_by_supplier)


async def _write_off(session: AsyncSession, ids: CatalogIds, rng: random.Random) -> AttemptResult:
    """Spoilage of one fresh ingredient; the entire issue is rejected atomically when short."""
    fresh = [supply.ingredient_id for supply in ids.supplies if supply.restocked_daily]
    ingredient_id = rng.choice(fresh or ids.ingredient_ids)
    try:
        async with session.begin_nested():
            await inventory_service.create_issue(
                session,
                ids.manager_id,
                "Hao hụt",
                [
                    {
                        "ingredient_id": ingredient_id,
                        "quantity": round(rng.uniform(*WRITE_OFF_RANGE_KG), 2),
                    }
                ],
            )
    except BusinessRuleError as exc:
        return AttemptResult(False, f"writeoff: {exc.message}")
    except Exception as exc:
        raise RuntimeError(f"Seed writeoff failed: ingredient={ingredient_id}") from exc
    return AttemptResult(True)


async def _discard_expired(session: AsyncSession, ids: CatalogIds, day: date) -> bool:
    """The morning check: lots past their date leave the books instead of piling up."""
    lots = (
        await session.execute(
            select(IngredientLot.id, IngredientLot.ingredient_id, IngredientLot.quantity_remaining)
            .where(IngredientLot.quantity_remaining > 0, IngredientLot.expiry_date < day)
            .order_by(IngredientLot.id)
        )
    ).all()
    if not lots:
        return False
    try:
        async with session.begin_nested():
            await inventory_service.create_issue(
                session,
                ids.manager_id,
                "Hết hạn",
                [
                    {"ingredient_id": ingredient_id, "quantity": quantity, "lot_id": lot_id}
                    for lot_id, ingredient_id, quantity in lots
                ],
            )
    except Exception as exc:
        raise RuntimeError(f"Seed expired write-off failed: day={day} lots={len(lots)}") from exc
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
    await payments_service.request_verification(session, payment.id, actor_id=None)
    if roll >= 1 - DISPUTE_RATIO:
        # The manager gave up chasing the money (FR-SALE-35): the order closes unpaid.
        await payments_service.close_unpaid_order(
            session, order_id, reason="Không thu được tiền sau tra soát", actor_id=None
        )


async def _place_order(
    session: AsyncSession,
    ids: CatalogIds,
    weights: list[float],
    rng: random.Random,
    day: date,
    moment: datetime | None = None,
) -> AttemptResult:
    """Submit and settle atomically; rejected attempts leave no partial mutations."""
    from app.modules.catalog.models import DiningTable
    from app.modules.sales.floor import release_table

    moment = moment or _moment(day, _pick_hour(rng), rng.randrange(0, 60))
    with frozen_clock(moment):
        lines = [
            {"MaMon": dish_id, "SoLuong": rng.randint(1, MAX_SERVINGS_PER_LINE), "GhiChu": None}
            for dish_id in _pick_dishes(
                rng, ids.dish_ids, weights, rng.randint(1, MAX_LINES_PER_ORDER)
            )
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
                else:
                    # The kitchen cooks and serves before the guest pays: a finished order
                    # must not keep dishes waiting, which would also block every stocktake.
                    for line in result["lines"]:
                        for status in (orders_service.LINE_CONFIRMED, orders_service.LINE_SERVED):
                            await orders_service.advance_line_status(session, line.id, status)
                    if roll < CANCELLED_ORDER_RATIO + CASH_PAYMENT_RATIO:
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
    allowed = {
        "Đã thanh toán",
        "Chờ xác minh thanh toán",
        "Đóng \u2013 chưa thu được tiền",
        "Đã hủy",
    }
    unexpected = set(statuses) - allowed
    if unexpected:
        raise RuntimeError(f"Seed has unintended open orders: {sorted(unexpected)}")
    pending_without_payment = await session.scalar(
        select(func.count())
        .select_from(Order)
        .where(
            Order.status == "Chờ xác minh thanh toán",
            ~select(PaymentTransaction.id)
            .where(
                PaymentTransaction.order_id == Order.id,
                PaymentTransaction.status == "Chờ xác minh thanh toán",
            )
            .exists(),
        )
    )
    if pending_without_payment:
        raise RuntimeError("Seed pending verification has no matching payment")
    return statuses


async def validate_stock_ceiling(session: AsyncSession) -> None:
    """No ingredient may ever have held more than the storage ceiling (Appendix B.1)."""
    running: dict[int, Decimal] = defaultdict(Decimal)
    for ingredient_id, quantity in await session.execute(
        select(StockMovement.ingredient_id, StockMovement.qty).order_by(StockMovement.id)
    ):
        running[ingredient_id] += quantity
        if running[ingredient_id] > MAX_STOCK_KG:
            raise RuntimeError(
                f"Seed stock ceiling failed: ingredient={ingredient_id} "
                f"stock={running[ingredient_id]} limit={MAX_STOCK_KG}"
            )


async def seed_operations(
    session: AsyncSession, config: SeedConfig, ids: CatalogIds
) -> SeedSummary:
    """Generate the exact planned volume with a bounded, visible rejection budget."""
    rng = random.Random(config.seed + 1)
    weights = dish_weights(len(ids.dish_ids))
    days = seed_days(config)
    volumes = daily_volumes(config, days, rng)

    def forecast(day: date) -> float:
        return daily_order_count(config, day)

    opening_day = days[0] - timedelta(days=1)
    with frozen_clock(_moment(opening_day, RESTOCK_HOUR)):
        receipts = await _receive(
            session,
            ids,
            rng,
            days[0],
            all_ingredients=True,
            forecast=forecast,
            horizon_days=OPENING_STOCK_DAYS,
            moment=_moment(opening_day, RESTOCK_HOUR),
        )
    await session.commit()

    requested = orders = issues = expired_issues = order_attempts = issue_attempts = 0
    reasons: Counter[str] = Counter()
    issue_rejected = 0
    for day, volume in zip(days, volumes, strict=True):
        with frozen_clock(_moment(day, RESTOCK_HOUR)):
            if await _discard_expired(session, ids, day):
                expired_issues += 1
            receipts += await _receive(session, ids, rng, day, forecast=forecast)
        if rng.random() < WRITE_OFF_CHANCE:
            issue_attempts += 1
            with frozen_clock(_moment(day, RESTOCK_HOUR + 1)):
                outcome = await _write_off(session, ids, rng)
            if outcome.succeeded:
                issues += 1
            else:
                issue_rejected += 1
                reasons[outcome.reason or "writeoff: unspecified"] += 1
        requested += volume
        # Placed in clock order, so order numbers rise with the time of day.
        moments = sorted(_moment(day, _pick_hour(rng), rng.randrange(0, 60)) for _ in range(volume))
        for moment in moments:
            for _ in range(ATTEMPTS_PER_ORDER):
                order_attempts += 1
                outcome = await _place_order(session, ids, weights, rng, day, moment)
                if outcome.succeeded:
                    orders += 1
                    break
                reasons[outcome.reason or "order: unspecified"] += 1
                # The kitchen ran short: buy the missing ingredients and take the order.
                with frozen_clock(moment):
                    receipts += await _receive(
                        session,
                        ids,
                        rng,
                        day,
                        all_ingredients=True,
                        forecast=forecast,
                        moment=moment,
                    )
            else:
                raise RuntimeError(
                    f"Seed order target failed: day={day} requested={requested} "
                    f"succeeded={orders} attempted={order_attempts} reasons={dict(reasons)}"
                )
        await session.commit()
    session.expire_all()
    statuses = await validate_seed_integrity(session)
    await validate_stock_ceiling(session)
    return SeedSummary(
        orders=orders,
        receipts=receipts,
        issues=issues,
        order_attempts=order_attempts,
        order_rejected=order_attempts - orders,
        issue_attempts=issue_attempts,
        issue_rejected=issue_rejected,
        rejection_reasons=dict(sorted(reasons.items())),
        pending_verification=statuses.get("Chờ xác minh thanh toán", 0),
        closed_unpaid_orders=statuses.get("Đóng \u2013 chưa thu được tiền", 0),
        expired_issues=expired_issues,
    )
