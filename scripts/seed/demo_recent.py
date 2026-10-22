"""Top up demo revenue for the most recent days on an existing database.

The full seed refuses a database that already has dishes. This script reuses the same
service-layer generator to create orders/payments for the last N business dates, so
dashboards and the assistant have recent data to show. It restocks ingredients first,
pays by cash or QR (settled, no bank call) and releases every table.

Usage:
    uv run --project apps/api python scripts/seed/demo_recent.py --days 14 --per-day 10
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT, REPO_ROOT / "apps" / "api" / "src"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from scripts.seed.catalog import CatalogIds  # noqa: E402
from scripts.seed.operations import _place_order, _receive  # noqa: E402
from sqlalchemy import distinct, func, select  # noqa: E402

from app.core.database import get_session_factory
from app.modules.catalog.models import DiningTable, Dish, Recipe, RecipeItem, Supplier
from app.modules.sales.models import Invoice
from app.modules.settings.models import User
from app.shared import business_date
from app.shared.enums import VersionStatus

WEIGHT_EXPONENT = 1.1


async def load_ids(session) -> CatalogIds:
    dishes = (
        await session.execute(
            select(Dish.id, Dish.name)
            .where(Dish.is_deleted.is_(False), Dish.status == "Hoạt động")
            .order_by(Dish.id)
        )
    ).all()
    if not dishes:
        raise SystemExit("Không có món đang hoạt động để tạo dữ liệu.")

    dish_ids = [int(row[0]) for row in dishes]
    ingredient_ids = list(
        (
            await session.execute(
                select(distinct(RecipeItem.ingredient_id))
                .join(Recipe, Recipe.id == RecipeItem.recipe_id)
                .where(
                    Recipe.dish_id.in_(dish_ids),
                    Recipe.status == VersionStatus.HIEU_LUC.value,
                )
            )
        )
        .scalars()
        .all()
    )
    if not ingredient_ids:
        raise SystemExit("Không tìm thấy nguyên liệu từ công thức hiện hành.")

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

    supplier = (
        await session.execute(select(Supplier.id).limit(1))
    ).scalar_one_or_none()
    manager = (
        await session.execute(
            select(User.id)
            .where(User.role_id == "MANAGER", User.status == "Hoạt động")
            .limit(1)
        )
    ).scalar_one_or_none()

    return CatalogIds(
        dish_names=[str(row[1]) for row in dishes],
        dish_ids=dish_ids,
        ingredient_ids=[int(i) for i in ingredient_ids],
        table_ids=[int(t) for t in table_ids],
        supplier_ids=[supplier] if supplier is not None else [None],
        users=[],
        manager_id=manager,
    )


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
    weights = [
        1.0 / ((rank + 1) ** WEIGHT_EXPONENT) for rank in range(len(ids.dish_ids))
    ]

    end = business_date.business_date_of(business_date.now())
    days = [end - timedelta(days=offset) for offset in range(args.days - 1, -1, -1)]
    succeeded = rejected = 0
    for index, day in enumerate(days):
        async with factory() as session:
            # Restock at the start and twice a week so popular dishes stay sellable.
            if index == 0 or day.weekday() in (0, 3):
                await _receive(session, ids, rng, day, all_ingredients=True)
            for _ in range(args.per_day):
                for _attempt in range(6):
                    outcome = await _place_order(session, ids, weights, rng, day)
                    if outcome.succeeded:
                        succeeded += 1
                        break
                    rejected += 1
                    await _receive(session, ids, rng, day, all_ingredients=True)
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
    print("\nDoanh thu theo ngày:")
    for day, invoices, revenue in rows:
        print(f"  {day}: {invoices} hóa đơn · {Decimal(str(revenue or 0)):,.0f} đ")
    print(f"\nĐã tạo {succeeded} order ({rejected} lần bị từ chối do tồn).")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
