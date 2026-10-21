"""Concurrency checks against a disposable MySQL database.

The unit suite runs on SQLite, which ignores `SELECT ... FOR UPDATE`, so this script
reproduces the races that matter for real money on MySQL 8.4:

1. two cashiers pay the same order at once   → one invoice only
2. edit a line while paying it               → invoice and line stay consistent
3. the same SePay webhook delivered twice    → one settlement, no fake exception
4. two write-offs draw the same lot          → no oversell, lot matches the ledger

It creates a throw-away database, migrates it, seeds the minimum data and drops it
afterwards. Nothing touches the demo database.

Usage:
    uv run python scripts/verify_mysql_concurrency.py
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import sys
import time
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parents[1]
API = REPO / "apps" / "api"
sys.path.insert(0, str(API / "src"))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402


def env_value(name: str) -> str:
    match = re.search(rf"^{name}=(.+)$", (REPO / ".env").read_text(), re.M)
    if not match:
        raise SystemExit(f"{name} is missing from .env")
    return match.group(1).strip()


def docker_mysql(
    sql: str, *, db: str | None = None
) -> subprocess.CompletedProcess[str]:
    parsed = urlsplit(env_value("DATABASE_URL"))
    command = [
        "docker",
        "exec",
        "-e",
        f"MYSQL_PWD={parsed.password}",
        "restaurant-db",
        "mysql",
        "--default-character-set=utf8mb4",
        "-u",
        parsed.username or "root",
        "-N",
        "-B",
    ]
    if db:
        command.append(db)
    command += ["-e", sql]
    return subprocess.run(command, capture_output=True, text=True)


def create_database(name: str) -> str:
    root_password = env_value("MYSQL_ROOT_PASSWORD")
    parsed = urlsplit(env_value("DATABASE_URL"))
    subprocess.run(
        [
            "docker",
            "exec",
            "-e",
            f"MYSQL_PWD={root_password}",
            "restaurant-db",
            "mysql",
            "-uroot",
            "-e",
            f"DROP DATABASE IF EXISTS `{name}`; CREATE DATABASE `{name}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; "
            f"GRANT ALL PRIVILEGES ON `{name}`.* TO '{parsed.username}'@'%';",
        ],
        check=True,
        capture_output=True,
    )
    return (
        f"mysql+asyncmy://{parsed.username}:{parsed.password}@"
        f"{parsed.hostname}:{parsed.port or 3306}/{name}?charset=utf8mb4"
    )


def migrate(url: str) -> None:
    env = {**os.environ, "DATABASE_URL": url}
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=API,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout, result.stderr)
        raise SystemExit("migration failed")


async def run_task(fn):
    """Run one service call in its own connection; return ok/error instead of raising."""
    async with Session() as session:
        try:
            value = await fn(session)
            await session.commit()
            return "ok", value
        except Exception as exc:
            await session.rollback()
            return "err", f"{type(exc).__name__}: {exc}"


async def seed() -> dict[str, int]:
    from app.modules.catalog.models import (
        DiningTable,
        Dish,
        DishGroup,
        DishPriceVersion,
        Ingredient,
        Recipe,
        RecipeItem,
    )
    from app.modules.inventory.models import IngredientLot
    from app.modules.settings.service import seed_reference_data
    from app.shared import business_date
    from app.shared.enums import VersionStatus

    async with Session() as session:
        await seed_reference_data(session)
        group = DishGroup(name="Nhóm kiểm thử", display_order=1, is_deleted=False)
        session.add(group)
        await session.flush()
        dish = Dish(name="Món kiểm thử", group_id=group.id, is_deleted=False)
        ingredient = Ingredient(
            name="NL kiểm thử", unit="kg", min_stock=0, stock_qty=1000, is_deleted=False
        )
        session.add_all([dish, ingredient])
        await session.flush()
        bd = business_date.business_date_of(business_date.now())
        session.add(
            DishPriceVersion(
                dish_id=dish.id,
                price=50000,
                business_date=bd,
                status=VersionStatus.HIEU_LUC.value,
                change_type="Tạo mới",
            )
        )
        recipe = Recipe(
            dish_id=dish.id,
            business_date=bd,
            status=VersionStatus.HIEU_LUC.value,
            change_type="Tạo mới",
        )
        session.add(recipe)
        await session.flush()
        session.add(
            RecipeItem(recipe_id=recipe.id, ingredient_id=ingredient.id, quantity=1)
        )
        session.add(
            IngredientLot(
                ingredient_id=ingredient.id,
                quantity_remaining=1000,
                received_quantity=1000,
                unit_price=1000,
                status="Còn hạn",
                received_at=business_date.now(),
            )
        )
        session.add(DiningTable(name="Bàn KT", is_deleted=False, status="Trống"))
        await session.commit()
        return {"dish_id": dish.id, "ingredient_id": ingredient.id}


async def make_order(dish_id: int, quantity: int = 1) -> int:
    from app.modules.sales import orders
    from app.modules.catalog.models import DiningTable

    async with Session() as session:
        table = (
            await session.execute(
                select(DiningTable).where(DiningTable.is_deleted.is_(False)).limit(1)
            )
        ).scalar_one()
        table.status = "Trống"
        table.current_order_id = None
        await session.flush()
        result = await orders.submit_order(
            session,
            {
                "table_id": table.id,
                "lines": [{"dish_id": dish_id, "quantity": quantity}],
            },
        )
        await session.commit()
        return int(result["order"].id)


def check(name: str, condition: bool, detail: str = "") -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {name} {detail}")
    if not condition:
        raise SystemExit(1)


async def scenario_cash_race(dish_id: int) -> None:
    from app.modules.sales import payments
    from app.modules.sales.models import Invoice

    order_id = await make_order(dish_id)
    outcomes = await asyncio.gather(
        run_task(lambda s: payments.pay_cash(s, order_id)),
        run_task(lambda s: payments.pay_cash(s, order_id)),
    )
    ok = [o for o in outcomes if o[0] == "ok"]
    async with Session() as session:
        invoices = (
            await session.execute(
                select(func.count())
                .select_from(Invoice)
                .where(Invoice.order_id == order_id)
            )
        ).scalar_one()
    check(
        "thanh toán tiền mặt đồng thời",
        len(ok) == 1 and invoices == 1,
        f"ok={len(ok)} invoices={invoices}",
    )


async def scenario_edit_vs_pay(dish_id: int) -> None:
    from app.modules.sales import orders, payments
    from app.modules.sales.models import Invoice, Order, OrderLine

    order_id = await make_order(dish_id)
    async with Session() as session:
        line = (
            await session.execute(
                select(OrderLine).where(OrderLine.order_id == order_id)
            )
        ).scalar_one()
        line_id = line.id
    outcomes = await asyncio.gather(
        run_task(lambda s: orders.update_line(s, order_id, line_id, 3)),
        run_task(lambda s: payments.pay_cash(s, order_id)),
    )
    async with Session() as session:
        invoice = (
            await session.execute(select(Invoice).where(Invoice.order_id == order_id))
        ).scalar_one()
        order = await session.get(Order, order_id)
        line = await session.get(OrderLine, order_id and line_id)
        assert order is not None and line is not None
        line_total = Decimal(str(line.unit_price)) * int(line.quantity)
        snapshot_total = sum(
            Decimal(str(item["ThanhTien"]))
            for item in (invoice.snapshot or {}).get("lines", [])
        )
    check(
        "sửa món đồng thời với thanh toán",
        Decimal(str(invoice.total)) == line_total == snapshot_total,
        f"invoice={invoice.total} line={line_total} snapshot={snapshot_total} "
        f"outcomes={[o[0] for o in outcomes]}",
    )


async def scenario_duplicate_webhook(dish_id: int) -> None:
    from app.modules.sales import payments
    from app.modules.sales.models import Invoice, PaymentException, PaymentTransaction

    order_id = await make_order(dish_id)
    async with Session() as session:
        payment = await payments.start_qr(session, order_id)
        await session.commit()
        payment_id = payment.id
        amount = int(payment.amount)
    body = {
        "id": f"9{int(time.time() * 1000)}",
        "transferType": "in",
        "transferAmount": amount,
        "code": f"TT{payment_id}",
        "content": f"TT{payment_id}",
    }
    outcomes = await asyncio.gather(
        run_task(lambda s: payments.handle_sepay_transfer(s, body)),
        run_task(lambda s: payments.handle_sepay_transfer(s, body)),
    )
    async with Session() as session:
        invoices = (
            await session.execute(
                select(func.count())
                .select_from(Invoice)
                .where(Invoice.order_id == order_id)
            )
        ).scalar_one()
        payment = await session.get(PaymentTransaction, payment_id)
        exceptions = (
            await session.execute(
                select(func.count())
                .select_from(PaymentException)
                .where(PaymentException.bank_ref == f"sepay:{body['id']}")
            )
        ).scalar_one()
    check(
        "webhook SePay gửi lặp đồng thời",
        invoices == 1
        and payment is not None
        and payment.status == "Thành công"
        and exceptions == 0,
        f"invoices={invoices} exceptions={exceptions} results={[o[0] for o in outcomes]}",
    )


async def scenario_stock_oversell(ingredient_id: int) -> None:
    from app.modules.catalog.models import Ingredient
    from app.modules.inventory import service as inventory
    from app.modules.inventory.models import IngredientLot

    async with Session() as session:
        lot = (
            (
                await session.execute(
                    select(IngredientLot).where(
                        IngredientLot.ingredient_id == ingredient_id
                    )
                )
            )
            .scalars()
            .first()
        )
        assert lot is not None
        lot_id = lot.id
        # Use a second, isolated lot so earlier scenarios do not interfere.
        lot.quantity_remaining = 10
        lot.received_quantity = 10
        ingredient = await session.get(Ingredient, ingredient_id)
        assert ingredient is not None
        ingredient.stock_qty = 10
        await session.commit()

    def issue(session):
        return inventory.create_issue(
            session,
            actor_id=None,
            reason="Hao hụt",
            lines=[{"ingredient_id": ingredient_id, "quantity": 6, "lot_id": lot_id}],
        )

    outcomes = await asyncio.gather(
        run_task(issue),
        run_task(issue),
    )
    async with Session() as session:
        lot = await session.get(IngredientLot, lot_id)
        ingredient = await session.get(Ingredient, ingredient_id)
        assert lot is not None and ingredient is not None
        remaining = Decimal(str(lot.quantity_remaining))
        stock = Decimal(str(ingredient.stock_qty))
    ok = [o for o in outcomes if o[0] == "ok"]
    check(
        "hai phiếu xuất tranh cùng một lô",
        len(ok) == 1 and remaining == Decimal("4") and stock == Decimal("4"),
        f"ok={len(ok)} lot={remaining} stock={stock}",
    )


async def main() -> int:
    name = f"restaurant_verify_{int(time.time())}"
    url = create_database(name)
    os.environ["DATABASE_URL"] = url
    global Session
    engine = create_async_engine(url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    try:
        migrate(url)
        data = await seed()
        await scenario_cash_race(data["dish_id"])
        await scenario_edit_vs_pay(data["dish_id"])
        await scenario_duplicate_webhook(data["dish_id"])
        await scenario_stock_oversell(data["ingredient_id"])
        print("\nAll concurrency checks passed on MySQL.")
        return 0
    finally:
        await engine.dispose()
        root_password = env_value("MYSQL_ROOT_PASSWORD")
        subprocess.run(
            [
                "docker",
                "exec",
                "-e",
                f"MYSQL_PWD={root_password}",
                "restaurant-db",
                "mysql",
                "-uroot",
                "-e",
                f"DROP DATABASE IF EXISTS `{name}`;",
            ],
            check=False,
            capture_output=True,
        )


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
