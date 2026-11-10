"""Dedicated, service-driven load-test dataset (report Appendix B.2); never reads DATABASE_URL."""

import argparse
import asyncio
import calendar
import json
import random
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from scripts.perf.verify import snapshot, verify
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.modules.catalog import service as catalog
from app.modules.catalog.models import Dish, Ingredient
from app.modules.inventory import service as inventory
from app.modules.sales import orders as sales
from app.modules.sales import payments
from app.modules.sales.floor import release_table
from app.modules.settings import service as settings
from app.shared import business_date
from app.shared.roles import Role

WEEKDAY_ORDERS = 70
WEEKEND_ORDERS = 110
OPENING_HOUR = 10
CLOSING_HOUR = 22
DELIVERY_HOUR = 8
DELIVERY_WEEKDAYS = (0, 3)  # Monday and Thursday

INGREDIENTS = 35
DISHES = 30
HISTORY_DISHES = 20  # the other ten are only edited by the load scenario
TABLES = 12
SUPPLIERS = 3
SERVING_GRAMS = 150
MIN_STOCK_GRAMS = 500
MAX_STOCK_GRAMS = 40_000
UNIT_PRICE_RANGE = (60, 270)  # đ/g, so the 10 % swing stays inside 50-300
PRICE_JITTER = 0.10
EXPIRED_LOT_INGREDIENT = 33  # the 34th: one 100 g lot with a one-day shelf life
FIFO_LOTS_INGREDIENT = 34  # the 35th: a 500 g lot, then a 3.000 g lot
LOAD_RECEIPT_INGREDIENT = 20  # untouched by history; the load scenario receives it


@dataclass(frozen=True)
class PlannedOrder:
    moment: datetime
    status: str
    takeaway: bool
    lines: tuple[tuple[int, int], ...]


def shift_month(moment, offset):
    value = moment.year * 12 + moment.month - 1 + offset
    year, month = divmod(value, 12)
    return moment.replace(
        year=year, month=month + 1, day=min(moment.day, calendar.monthrange(year, month + 1)[1])
    )


def _open_seconds(day: date, start: datetime, end: datetime) -> tuple[datetime, int]:
    """The part of one day's opening hours that lies inside the dataset window."""
    opens = max(datetime.combine(day, time(OPENING_HOUR)), start)
    closes = min(datetime.combine(day, time(CLOSING_HOUR)), end)
    return opens, max(0, int((closes - opens).total_seconds()))


def build_plan(seed, orders, months, now):
    """Orders spread like a small eatery: weekends busier, all inside 10:00-22:00."""
    if orders < 1 or months < 1:
        raise ValueError("Số order/tháng phải dương.")
    rng = random.Random(seed)
    paid, cancelled, review = orders * 90 // 100, orders * 5 // 100, orders * 25 // 1000
    statuses = (
        ["paid"] * paid
        + ["cancelled"] * cancelled
        + ["review"] * review
        + ["closed"] * (orders - paid - cancelled - review)
    )
    types = [False] * (orders * 70 // 100) + [True] * (orders - orders * 70 // 100)
    rng.shuffle(statuses)
    rng.shuffle(types)
    end = now.replace(tzinfo=None)
    start = shift_month(end, -months)
    windows = []
    for offset in range((end.date() - start.date()).days + 1):
        day = start.date() + timedelta(days=offset)
        opens, seconds = _open_seconds(day, start, end)
        if seconds:
            base = WEEKEND_ORDERS if day.weekday() >= 5 else WEEKDAY_ORDERS
            share = base * seconds / ((CLOSING_HOUR - OPENING_HOUR) * 3600)
            windows.append((opens, seconds, share))
    total_share = sum(share for _, _, share in windows)
    moments: list[datetime] = []
    cumulative = 0.0
    for opens, seconds, share in windows:
        cumulative += share
        count = round(orders * cumulative / total_share) - len(moments)
        moments.extend(
            sorted(opens + timedelta(seconds=rng.randrange(seconds)) for _ in range(count))
        )
    return [
        PlannedOrder(
            moment,
            statuses[index],
            types[index],
            tuple(
                (dish, rng.randint(1, 2))
                for dish in rng.sample(range(HISTORY_DISHES), rng.randint(1, 4))
            ),
        )
        for index, moment in enumerate(moments)
    ]


def delivery_moments(plan: list[PlannedOrder], now: datetime) -> list[datetime]:
    """08:00 on the first day, every Monday and Thursday, and the reference day itself."""
    first, last = plan[0].moment.date(), now.replace(tzinfo=None).date()
    days = [
        first + timedelta(days=offset)
        for offset in range((last - first).days + 1)
        if offset == 0
        or (first + timedelta(days=offset)).weekday() in DELIVERY_WEEKDAYS
        or first + timedelta(days=offset) == last
    ]
    return [datetime.combine(day, time(DELIVERY_HOUR)) for day in days]


def planned_use(plan: list[PlannedOrder], start: datetime, end: datetime) -> dict[int, int]:
    """Grams of each history ingredient the orders in [start, end) draw."""
    grams: dict[int, int] = {}
    for row in plan:
        if start <= row.moment < end:
            for dish, quantity in row.lines:
                grams[dish] = grams.get(dish, 0) + quantity * SERVING_GRAMS
    return grams


def dedicated_database(url):
    parsed = make_url(url)
    name = parsed.database or ""
    if parsed.get_backend_name() not in ("mysql", "sqlite"):
        raise ValueError("Chỉ MySQL hoặc SQLite thử nghiệm.")
    if not name.startswith("perf_") and not Path(name).name.startswith("perf_"):
        raise ValueError("CSDL phải có tên bắt đầu perf_; không dùng DATABASE_URL mặc định.")
    return parsed


async def seed_dataset(session, *, seed, orders, months, now, users=20):
    if not 1 <= users <= 20:
        raise ValueError("Số VU từ 1 đến 20.")
    if await session.scalar(select(func.count()).select_from(Dish)):
        raise ValueError("Seed chỉ chạy trên CSDL thử nghiệm sạch.")
    await settings.seed_reference_data(session)
    schedule = await business_date.load_business_date_schedule(session)
    plan = build_plan(seed, orders, months, now)
    accounts = []
    manager = None
    for index in range(users):
        account = {}
        for role in Role:
            username = f"perf_{index:02}_{role.value.lower()}"
            password = f"Perf-{seed}-{index}-{role.value}!"
            user = await settings.create_user(
                session, None, username, password, username, None, role
            )
            account[role.value] = {"username": username, "password": password}
            if role == Role.MANAGER and manager is None:
                manager = user.id
        accounts.append(account)
    rng = random.Random(seed + 1)
    deliveries = delivery_moments(plan, now)
    with business_date.business_date_schedule(schedule), business_date.at_time(deliveries[0]):
        ingredients = []
        for index in range(INGREDIENTS):
            ingredients.append(
                (
                    await catalog.create_ingredient(
                        session,
                        manager,
                        f"Nguyên liệu thử {index + 1:02}",
                        "g",
                        MIN_STOCK_GRAMS,
                        1 if index == EXPIRED_LOT_INGREDIENT else 1000,
                    )
                ).id
            )
        group = await catalog.create_group(session, manager, "Thực đơn thử nghiệm")
        dishes = []
        for index in range(DISHES):
            dish = await catalog.create_dish(
                session, manager, f"Món thử {index + 1:02}", group.id, price=25000 + index * 2000
            )
            await catalog.assign_recipe(
                session,
                manager,
                dish.id,
                [(ingredients[index % HISTORY_DISHES], Decimal(SERVING_GRAMS))],
            )
            dishes.append(dish.id)
        tables = [
            (await catalog.create_table(session, manager, f"Bàn thử {index + 1:02}")).id
            for index in range(TABLES)
        ]
        suppliers = [
            (await catalog.create_supplier(session, manager, f"NCC thử {index + 1}", None)).id
            for index in range(SUPPLIERS)
        ]
        # Isolated expired and 500g/3000g FIFO lots never fund historical orders.
        for ingredient, quantity in (
            (EXPIRED_LOT_INGREDIENT, 100),
            (FIFO_LOTS_INGREDIENT, 500),
            (FIFO_LOTS_INGREDIENT, 3000),
        ):
            await inventory.create_receipt(
                session,
                manager,
                suppliers[0],
                deliveries[0],
                [
                    {
                        "ingredient_id": ingredients[ingredient],
                        "quantity": quantity,
                        "unit_price": 100,
                    }
                ],
            )
    await session.commit()
    unit_prices = [rng.randrange(*UNIT_PRICE_RANGE, 10) for _ in range(HISTORY_DISHES)]

    async def deliver(index: int) -> None:
        """What the kitchen will use until the next delivery, plus the minimum stock.

        The delivery on the reference day fills the storeroom to its ceiling instead: the
        load scenario that follows draws from it and nothing restocks these ingredients.
        """
        moment = deliveries[index]
        last = index == len(deliveries) - 1
        until = datetime.max if last else deliveries[index + 1]
        use = planned_use(plan, moment, until)
        stock = dict(
            (
                await session.execute(
                    select(Ingredient.id, Ingredient.stock_qty).where(
                        Ingredient.id.in_(ingredients[:HISTORY_DISHES])
                    )
                )
            ).all()
        )
        lines = []
        for position, ingredient_id in enumerate(ingredients[:HISTORY_DISHES]):
            on_hand = int(stock[ingredient_id])
            target = MAX_STOCK_GRAMS if last else use.get(position, 0) + MIN_STOCK_GRAMS
            quantity = min(target, MAX_STOCK_GRAMS) - on_hand
            if quantity > 0:
                swing = rng.uniform(1 - PRICE_JITTER, 1 + PRICE_JITTER)
                lines.append(
                    {
                        "ingredient_id": ingredient_id,
                        "quantity": quantity,
                        "unit_price": round(unit_prices[position] * swing),
                    }
                )
        if lines:
            with business_date.business_date_schedule(schedule), business_date.at_time(moment):
                await inventory.create_receipt(
                    session, manager, suppliers[index % SUPPLIERS], moment, lines
                )

    delivered = 0
    for index, row in enumerate(plan):
        while delivered < len(deliveries) and deliveries[delivered] <= row.moment:
            await deliver(delivered)
            delivered += 1
        with business_date.business_date_schedule(schedule), business_date.at_time(row.moment):
            result = await sales.submit_order(
                session,
                {
                    "table_id": None if row.takeaway else tables[index % TABLES],
                    "order_type": "Mang về" if row.takeaway else "Tại chỗ",
                    "lines": [
                        {"MaMon": dishes[dish], "SoLuong": quantity, "GhiChu": None}
                        for dish, quantity in row.lines
                    ],
                },
                actor_id=manager,
            )
            if result["rejected"]:
                raise RuntimeError(f"Order seed bị từ chối: {result['rejected']}")
            order = result["order"]
            if row.status == "cancelled":
                await sales.cancel_order(session, order.id, "Hủy trước chế biến", actor_id=manager)
            elif row.status == "paid":
                await payments.pay_cash(session, order.id, actor_id=manager)
            else:
                payment = await payments.start_qr(session, order.id, actor_id=manager)
                await payments.request_verification(session, payment.id, actor_id=manager)
                if row.status == "closed":
                    await payments.close_unpaid_order(
                        session, order.id, reason="Dữ liệu thử", actor_id=manager
                    )
            if order.table_id is not None:
                await release_table(session, order.table_id, order.id, actor_id=manager)
        # Bounded transactions and identity map on the full run.
        if (index + 1) % 100 == 0:
            await session.commit()
    while delivered < len(deliveries):
        await deliver(delivered)
        delivered += 1
    await session.commit()
    over = await session.scalar(
        select(func.count()).select_from(Ingredient).where(Ingredient.stock_qty > MAX_STOCK_GRAMS)
    )
    if over:
        raise RuntimeError(f"{over} nguyên liệu tồn quá {MAX_STOCK_GRAMS} g.")
    with business_date.business_date_schedule(schedule), business_date.at_time(now):
        failures = await verify(session)
        if failures:
            raise RuntimeError(str(failures))
        manifest = await snapshot(session)
    for index, account in enumerate(accounts):
        account["data"] = {
            "dish_id": dishes[index],
            "catalog_id": dishes[HISTORY_DISHES + index % (DISHES - HISTORY_DISHES)],
            "ingredient_id": ingredients[LOAD_RECEIPT_INGREDIENT],
            "supplier_id": suppliers[0],
        }
    manifest["seed"] = seed
    manifest["months"] = months
    manifest["reference_time"] = now.isoformat()
    manifest["schema_revisions"] = []
    try:
        manifest["commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        manifest["commit"] = "unknown"
    return manifest, accounts


async def generate(args):
    dedicated_database(args.database_url)
    engine = create_async_engine(args.database_url)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            manifest, accounts = await seed_dataset(
                session,
                seed=args.seed,
                orders=args.orders,
                months=args.months,
                now=args.now,
                users=args.users,
            )
            from alembic.runtime.migration import MigrationContext

            connection = await session.connection()
            manifest["schema_revisions"] = await connection.run_sync(
                lambda conn: list(MigrationContext.configure(conn).get_current_heads())
            )
        Path(args.manifest).write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        account_path = Path(args.accounts)
        account_path.touch(mode=0o600, exist_ok=True)
        account_path.chmod(0o600)
        account_path.write_text(json.dumps(accounts, ensure_ascii=False, indent=2))
    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Seed Phụ lục B.2 vào CSDL perf_ sạch đã migrate.")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--accounts", required=True)
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument("--orders", type=int, default=4800)
    parser.add_argument("--months", type=int, default=2)
    parser.add_argument("--users", type=int, default=20)
    parser.add_argument("--now", type=datetime.fromisoformat, default=datetime(2026, 10, 19, 12))
    args = parser.parse_args()
    asyncio.run(generate(args))
