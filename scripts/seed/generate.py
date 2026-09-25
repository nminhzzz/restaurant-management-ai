"""Entry point of `make seed`.

Reference data first — the three roles and the singleton config row are what every
foreign key in the dataset ultimately hangs from — then the catalogue, then a year of
operations, all through the module services so the data obeys the business invariants.
"""

import argparse
import asyncio

from app.core.database import get_session_factory
from app.modules.settings.service import seed_reference_data
from app.shared import business_date
from scripts.seed.catalog import seed_catalog
from scripts.seed.config import SeedConfig


async def generate(config: SeedConfig) -> None:
    print(f"[seed] seed={config.seed} months={config.months} target={config.orders_target}")
    factory = get_session_factory()
    async with factory() as session:
        await seed_reference_data(session)
        await session.commit()

        ids = await seed_catalog(session, config)
        print(
            f"[seed] danh mục: {len(ids.dish_ids)} món · "
            f"{len(ids.ingredient_ids)} nguyên liệu · {len(ids.table_ids)} bàn"
        )

        from scripts.seed.operations import seed_operations

        summary = await seed_operations(session, config, ids)
        print(
            f"[seed] vận hành: {summary.orders} order · "
            f"{summary.receipts} phiếu nhập · {summary.issues} phiếu xuất"
        )
        print(f"[seed] xong lúc {business_date.now().isoformat()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sinh dữ liệu mô phỏng 12 tháng.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--orders", type=int, default=20_000)
    args = parser.parse_args()
    asyncio.run(
        generate(
            SeedConfig(seed=args.seed, months=args.months, orders_target=args.orders)
        )
    )


if __name__ == "__main__":
    main()
