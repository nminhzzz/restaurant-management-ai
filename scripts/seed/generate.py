"""Entry point of `make seed`.

Reference data first — the three roles and the singleton config row are what every
foreign key in the dataset ultimately hangs from — then the catalogue, then a year of
operations, all through the module services so the data obeys the business invariants.
"""

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

# `make seed` runs this file by path, so sys.path[0] is `scripts/seed/` and the
# `scripts.*` package would not resolve without the repository root on the path.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from alembic.runtime.migration import MigrationContext  # noqa: E402
from scripts.seed.catalog import seed_catalog  # noqa: E402
from scripts.seed.config import SeedConfig  # noqa: E402
from scripts.seed.operations import SeedSummary, seed_operations  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.database import get_session_factory  # noqa: E402
from app.modules.settings.service import seed_reference_data  # noqa: E402
from app.shared import business_date  # noqa: E402


def seed_report(
    config: SeedConfig, summary: SeedSummary, database_url: str, revisions: tuple[str, ...]
) -> dict:
    """Emit reproducibility metadata through an explicit credential-free allowlist."""
    url = make_url(database_url)
    end = business_date.business_date_of(config.now)
    return {
        "status": "completed",
        "config": {
            "seed": config.seed,
            "months": config.months,
            "orders_target": config.orders_target,
            "now": config.now.isoformat(),
            "business_date_start": (end - timedelta(days=config.months * 30)).isoformat(),
            "business_date_end": end.isoformat(),
        },
        "database": {
            "dialect": url.get_backend_name(),
            "schema": url.database,
            "revisions": list(revisions),
        },
        "operations": asdict(summary),
        "integrity": "passed",
    }


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

        summary = await seed_operations(session, config, ids)
        connection = await session.connection()
        revisions = await connection.run_sync(
            lambda conn: MigrationContext.configure(conn).get_current_heads()
        )
        print(
            json.dumps(
                seed_report(config, summary, get_settings().database_url, revisions),
                ensure_ascii=False,
                sort_keys=True,
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Sinh dữ liệu mô phỏng 12 tháng.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--orders", type=int, default=20_000)
    parser.add_argument(
        "--now",
        type=datetime.fromisoformat,
        help="Mốc thời gian ISO để tái lập dữ liệu (mặc định: đồng hồ hệ thống).",
    )
    args = parser.parse_args()
    asyncio.run(
        generate(
            SeedConfig(
                seed=args.seed,
                months=args.months,
                orders_target=args.orders,
                **({"now": args.now} if args.now else {}),
            )
        )
    )


if __name__ == "__main__":
    main()
