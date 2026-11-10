"""Seed parameters — the single place the experiment can be tuned (Appendix B.1).

Every random draw in the generator goes through `random.Random(config.seed)`, never the
global `random`, so the same seed always rebuilds the same dataset.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime

from app.shared import business_date


@contextmanager
def frozen_clock(moment: datetime) -> Iterator[None]:
    """Point the shared clock seam at `moment` for the duration of the block.

    The whole dataset is historical, so every write that stamps a Business Date — a
    price version, a recipe, an order — must happen with the clock pinned to that
    moment, otherwise the data is dated today and reported as if nothing was sold.
    """
    original = business_date.now
    business_date.now = lambda: moment
    try:
        yield
    finally:
        business_date.now = original


@dataclass(frozen=True)
class SeedConfig:
    """`orders_target=None` follows the daily rule of Appendix B.1 (about 4.800 orders in
    two months); a number forces that exact total, spread over the same daily shape."""

    seed: int = 42
    months: int = 2
    orders_target: int | None = None
    now: datetime = field(default_factory=lambda: business_date.now())

    def __post_init__(self) -> None:
        if self.months < 1 or (self.orders_target is not None and self.orders_target < 0):
            raise ValueError("Seed months must be positive and orders must be nonnegative.")

    @property
    def days(self) -> int:
        return self.months * 30


WEEKDAY_ORDERS = 70
WEEKEND_ORDERS = 110
DAILY_ORDER_JITTER = 0.15

# Opening hours are 10:00-22:00, with a lunch peak around 11-13h, a dinner peak around
# 18-20h and the 15-16h lull between them.
HOUR_WEIGHTS: dict[int, float] = {
    10: 1.00,
    11: 2.00,
    12: 2.20,
    13: 1.60,
    14: 0.70,
    15: 0.40,
    16: 0.50,
    17: 0.90,
    18: 2.00,
    19: 2.30,
    20: 1.70,
    21: 1.00,
}

# A few dishes carry most of the orders.
DISH_POWER_LAW_EXPONENT = 1.2

MAX_LINES_PER_ORDER = 4
MAX_SERVINGS_PER_LINE = 2

CASH_PAYMENT_RATIO = 0.70
RECONCILE_RATIO = 0.05
DISPUTE_RATIO = 0.03
CANCELLED_ORDER_RATIO = 0.04
TAKEAWAY_RATIO = 0.20

RESTOCK_HOUR = 8
DRY_RESTOCK_WEEKDAYS = (0, 3)  # Monday and Thursday
OPENING_STOCK_DAYS = 3
RESTOCK_STEP_KG = 0.5
MAX_RECEIPT_LINE_KG = 30
MAX_STOCK_KG = 40
PRICE_JITTER = 0.10

WRITE_OFF_CHANCE = 0.10
WRITE_OFF_RANGE_KG = (0.2, 1.0)
