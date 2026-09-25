"""Seed parameters — the single place the experiment can be tuned (Appendix 4).

Every random draw in the generator goes through `random.Random(config.seed)`, never the
global `random`, so the same seed always rebuilds the same dataset.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.shared import business_date


@dataclass(frozen=True)
class SeedConfig:
    seed: int = 42
    months: int = 12
    orders_target: int = 20_000
    now: datetime = field(default_factory=lambda: business_date.now())


# The day has two peaks — lunch around 11–13h and dinner around 18–20h — with the
# 15–16h lull between them (Appendix 4).
HOUR_WEIGHTS: dict[int, float] = {
    0: 0.05,
    1: 0.03,
    2: 0.02,
    3: 0.02,
    4: 0.03,
    5: 0.10,
    6: 0.30,
    7: 0.60,
    8: 0.80,
    9: 0.90,
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
    22: 0.50,
    23: 0.20,
}

WEEKEND_MULTIPLIER = 1.6

# Seasonality of the lunar-calendar year: quiet after Tết, busy towards the holidays.
MONTH_SEASONALITY: dict[int, float] = {
    1: 1.25,
    2: 0.80,
    3: 0.95,
    4: 1.00,
    5: 1.05,
    6: 1.00,
    7: 0.95,
    8: 1.00,
    9: 1.05,
    10: 1.05,
    11: 1.10,
    12: 1.20,
}

# A few dishes carry most of the orders.
DISH_POWER_LAW_EXPONENT = 1.2

DISH_COUNT_RANGE = (60, 80)
TABLE_COUNT = 20
SUPPLIER_COUNT = 5

CASH_PAYMENT_RATIO = 0.70
RECONCILE_RATIO = 0.05
DISPUTE_RATIO = 0.03
CANCELLED_ORDER_RATIO = 0.04

RECEIPTS_PER_MONTH = 10
WRITE_OFFS_PER_MONTH = 3
