"""Top up demo revenue for the most recent days on an existing database.

The full seed refuses a database that already has dishes. This script reuses the same
service-layer generator to create orders/payments for the last N business dates, so
dashboards and the assistant have recent data to show. It restocks ingredients first,
pays by cash or QR (settled, no bank call) and releases every table.

Usage:
    uv run --project apps/api python scripts/seed/demo_recent.py --days 14 --per-day 10
"""


# ruff: noqa: E402 - application imports follow the CLI path bootstrap.

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT, REPO_ROOT / "apps" / "api" / "src"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from scripts.seed.catalog import CatalogIds, Supply, build_catalogue, use_per_order
from scripts.seed.operations import _place_order, _receive
from sqlalchemy import func, select, update

from app.core.database import get_session_factory
from app.modules.catalog.models import (
    DiningTable,
    Dish,
    Ingredient,
    Recipe,
    RecipeItem,
    Supplier,
)
from app.modules.inventory.models import GoodsReceiptLine
from app.modules.sales.models import Invoice, Order, OrderLine
from app.modules.settings.models import User
from app.shared import business_date
from app.shared.enums import VersionStatus

WEIGHT_EXPONENT = 1.1
FRESH_SHELF_DAYS = 7
FALLBACK_UNIT_PRICE = 50_000


def demo_weights(count: int) -> list[float]:
    return [1.0 / ((rank + 1) ** WEIGHT_EXPONENT) for rank in range(count)]


async def load_supplies(session, usage: dict[int, float]) -> tuple[Supply, ...]:
    """Restocking terms of an existing database: the seed catalogue where the name matches,
    otherwise the ingredient's own last purchase."""
    specs = build_catalogue().ingredients
    suppliers = dict((await session.execute(select(Supplier.name, Supplier.id))).tuples().all())
    fallback_supplier = next(iter(suppliers.values()), None)
    last_prices = dict(
        (
            await session.execute(
                select(GoodsReceiptLine.ingredient_id, GoodsReceiptLine.unit_price).order_by(
                    GoodsReceiptLine.id
                )
            )
        )
        .tuples()
        .all()
    )
    supplies = []
    for ingredient_id, name, min_stock, shelf_days in await session.execute(
        select(Ingredient.id, Ingredient.name, Ingredient.min_stock, Ingredient.shelf_days).where(
            Ingredient.id.in_(usage)
        )
    ):
        spec = specs.get(name)
        supplies.append(
            Supply(
                ingredient_id=int(ingredient_id),
                supplier_id=suppliers.get(spec.category.supplier, fallback_supplier)
                if spec
                else fallback_supplier,
                unit_price=spec.unit_price
                if spec
                else int(last_prices.get(ingredient_id) or FALLBACK_UNIT_PRICE),
                min_stock_kg=float(min_stock or 0),
                restocked_daily=shelf_days is not None and shelf_days <= FRESH_SHELF_DAYS,
                use_per_order_kg=usage[int(ingredient_id)],
            )
        )
    return tuple(supplies)


async def load_ids(session) -> CatalogIds:
    dishes = (
        await session.execute(
            select(Dish.id, Dish.name)
            .where(
                Dish.is_deleted.is_(False),
                Dish.missing_recipe.is_(False),
                Dish.manual_paused.is_(False),
            )
            .order_by(Dish.id)
        )
    ).all()
    if not dishes:
        raise SystemExit("Không có món đang hoạt động để tạo dữ liệu.")

    dish_ids = [int(row[0]) for row in dishes]
    weights = demo_weights(len(dish_ids))
    recipes: dict[int, dict[int, float]] = {dish_id: {} for dish_id in dish_ids}
    for dish_id, ingredient_id, quantity in await session.execute(
        select(Recipe.dish_id, RecipeItem.ingredient_id, RecipeItem.quantity)
        .join(Recipe, Recipe.id == RecipeItem.recipe_id)
        .where(
            Recipe.dish_id.in_(dish_ids),
            Recipe.status == VersionStatus.HIEU_LUC.value,
        )
    ):
        recipes[int(dish_id)][int(ingredient_id)] = float(quantity)
    usage = use_per_order([recipes[dish_id] for dish_id in dish_ids], weights)
    if not usage:
        raise SystemExit("Không tìm thấy nguyên liệu từ công thức hiện hành.")
    supplies = await load_supplies(session, usage)

    table_ids = list(
        (
            await session.execute(
                select(DiningTable.id).where(
                    DiningTable.is_deleted.is_(False), DiningTable.status == "Trống"
                )
            )
        )
        .scalars()
        .all()
    )
    if not table_ids:
        raise SystemExit("Không còn bàn trống để tạo order tại chỗ.")

    supplier = (await session.execute(select(Supplier.id).limit(1))).scalar_one_or_none()
    manager = (
        await session.execute(
            select(User.id).where(User.role_id == "MANAGER", User.status == "Hoạt động").limit(1)
        )
    ).scalar_one_or_none()

    return CatalogIds(
        dish_names=[str(row[1]) for row in dishes],
        dish_ids=dish_ids,
        ingredient_ids=list(usage),
        table_ids=[int(t) for t in table_ids],
        supplier_ids=[supplier] if supplier is not None else [None],
        users=[],
        manager_id=manager,
        supplies=supplies,
    )


async def settle_past_lines(session, through: date) -> int:
    """Mark generated past dishes as served: a waiting line would block opening a stocktake."""
    past_orders = select(Order.id).where(Order.business_date <= through, Order.status != "Đang mở")
    result = await session.execute(
        update(OrderLine)
        .where(OrderLine.status == "Chờ làm", OrderLine.order_id.in_(past_orders))
        .values(status="Đã phục vụ")
    )
    return int(result.rowcount)


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--per-day", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args()
    if args.days < 1 or args.per_day < 1:
        raise SystemExit("--days và --per-day phải lớn hơn 0.")

    rng = random.Random(args.seed)
    factory = get_session_factory()
    async with factory() as session:
        ids = await load_ids(session)
        end = business_date.business_date_of(business_date.now())
    weights = demo_weights(len(ids.dish_ids))

    def forecast(_day: date) -> float:
        return args.per_day

    days = [end - timedelta(days=offset) for offset in range(args.days - 1, -1, -1)]
    succeeded = rejected = 0
    for index, day in enumerate(days):
        async with factory() as session:
            # Fresh goods every morning, dry goods on their delivery days, all on day one.
            await _receive(session, ids, rng, day, all_ingredients=index == 0, forecast=forecast)
            for _ in range(args.per_day):
                for _attempt in range(6):
                    outcome = await _place_order(session, ids, weights, rng, day)
                    if outcome.succeeded:
                        succeeded += 1
                        break
                    rejected += 1
                    await _receive(session, ids, rng, day, all_ingredients=True, forecast=forecast)
                else:
                    print(f"  bỏ {args.per_day} order ngày {day}: hết tồn")
            await session.commit()
        print(f"{day}: {args.per_day} order")

    async with factory() as session:
        rows = (
            await session.execute(
                select(Invoice.business_date, func.count(), func.sum(Invoice.total))
                .group_by(Invoice.business_date)
                .order_by(Invoice.business_date.desc())
                .limit(args.days)
            )
        ).all()
    async with factory() as session:
        settled = await settle_past_lines(
            session, business_date.business_date_of(business_date.now())
        )
        await session.commit()
    print(f"Đã chuyển {settled} dòng món cũ sang Đã phục vụ.")
    print("\nDoanh thu theo ngày:")
    for day, invoices, revenue in rows:
        print(f"  {day}: {invoices} hóa đơn · {Decimal(str(revenue or 0)):,.0f} đ")
    print(f"\nĐã tạo {succeeded} order ({rejected} lần bị từ chối do tồn).")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
