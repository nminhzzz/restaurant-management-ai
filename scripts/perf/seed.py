"""Dedicated, service-driven Appendix J dataset; never reads DATABASE_URL."""

import argparse
import asyncio
import calendar
import json
import random
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from scripts.perf.verify import snapshot, verify
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.modules.catalog import service as catalog
from app.modules.catalog.models import Dish
from app.modules.inventory import service as inventory
from app.modules.sales import orders as sales
from app.modules.sales import payments
from app.modules.sales.floor import release_table
from app.modules.settings import service as settings
from app.shared import business_date
from app.shared.roles import Role


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


def build_plan(seed, orders, months, now):
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
    start = shift_month(now.replace(day=1, hour=12, minute=0, second=0, microsecond=0), -months + 1)
    end = now.replace(tzinfo=None)
    seconds = int((end - start).total_seconds())
    return [
        PlannedOrder(
            start + timedelta(seconds=seconds * index // orders),
            statuses[index],
            types[index],
            tuple((dish, rng.randint(1, 3)) for dish in rng.sample(range(20), rng.randint(1, 5))),
        )
        for index in range(orders)
    ]


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
    with business_date.business_date_schedule(schedule), business_date.at_time(plan[0].moment):
        ingredients = []
        for index in range(30):
            ingredients.append(
                (
                    await catalog.create_ingredient(
                        session,
                        manager,
                        f"Nguyên liệu thử {index + 1:02}",
                        "g",
                        5,
                        1 if index == 28 else 1000,
                    )
                ).id
            )
        group = await catalog.create_group(session, manager, "Thực đơn thử nghiệm")
        dishes = []
        for index in range(40):
            dish = await catalog.create_dish(
                session, manager, f"Món thử {index + 1:02}", group.id, price=25000 + index * 1000
            )
            await catalog.assign_recipe(
                session, manager, dish.id, [(ingredients[index % 27], Decimal("10"))]
            )
            dishes.append(dish.id)
        tables = [
            (await catalog.create_table(session, manager, f"Bàn thử {index + 1:02}")).id
            for index in range(20)
        ]
        suppliers = [
            (await catalog.create_supplier(session, manager, f"NCC thử {index + 1}", None)).id
            for index in range(5)
        ]
        # One large chronological initial receipt funds all historical consumption.
        await inventory.create_receipt(
            session,
            manager,
            suppliers[0],
            plan[0].moment,
            [
                {"ingredient_id": ingredient, "quantity": orders * 200 + 10000, "unit_price": 10}
                for ingredient in ingredients[:27]
            ],
        )
        # Isolated expired and 500g/3000g FIFO lots never fund historical orders.
        await inventory.create_receipt(
            session,
            manager,
            suppliers[0],
            plan[0].moment,
            [{"ingredient_id": ingredients[28], "quantity": 100, "unit_price": 10}],
        )
        for quantity in (500, 3000):
            await inventory.create_receipt(
                session,
                manager,
                suppliers[0],
                plan[0].moment,
                [{"ingredient_id": ingredients[29], "quantity": quantity, "unit_price": 10}],
            )
    await session.commit()
    for index, row in enumerate(plan):
        with business_date.business_date_schedule(schedule), business_date.at_time(row.moment):
            result = await sales.submit_order(
                session,
                {
                    "table_id": None if row.takeaway else tables[index % 20],
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
        # Bounded transactions and identity map on the full 20,000-order run.
        if (index + 1) % 100 == 0:
            await session.commit()
    await session.commit()
    with business_date.business_date_schedule(schedule), business_date.at_time(now):
        failures = await verify(session)
        if failures:
            raise RuntimeError(str(failures))
        manifest = await snapshot(session)
    for index, account in enumerate(accounts):
        account["data"] = {
            "dish_id": dishes[index],
            "catalog_id": dishes[20 + index],
            "ingredient_id": ingredients[27],
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
    parser = argparse.ArgumentParser(description="Seed Phụ lục J vào CSDL perf_ sạch đã migrate.")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--accounts", required=True)
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument("--orders", type=int, default=20000)
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--users", type=int, default=20)
    parser.add_argument("--now", type=datetime.fromisoformat, default=datetime(2026, 10, 19, 12))
    args = parser.parse_args()
    asyncio.run(generate(args))
