"""Time every reporting endpoint against a seeded database (NFR-01, NFR-03).

Run with the file path (same shape as `make seed`), from `apps/api`:

    cd apps/api && uv run python ../../scripts/bench_reports.py --month 2026-09

Exits non-zero if any endpoint is over budget, so the gate cannot pass silently
while a report is slow.
"""

import argparse
import asyncio
import time
from datetime import date

from app.core.database import get_session_factory
from app.modules.reports import periods, queries

BUDGET_SECONDS = 2.0

# Named entries, so a failure says which endpoint is slow instead of "a query".
BENCHMARKS = {
    "revenue": lambda session, period: queries.revenue_by_period(session, period),
    "dishes": lambda session, period: queries.dish_ranking(session, period, order_by="revenue"),
    "hours": lambda session, period: queries.hourly_distribution(session, period),
    "costs": lambda session, period: queries.cost_of_goods(
        session, int(period.start.strftime("%Y%m"))
    ),
}


async def main(month: str) -> int:
    period = periods.resolve_period("month", date.fromisoformat(f"{month}-01"))
    over_budget = 0
    async with get_session_factory()() as session:
        for name, run in BENCHMARKS.items():
            started = time.perf_counter()
            await run(session, period)
            elapsed = time.perf_counter() - started
            over_budget += elapsed > BUDGET_SECONDS
            print(f"{name:10s} {elapsed:6.3f}s {'OVER' if elapsed > BUDGET_SECONDS else 'ok'}")
    return over_budget


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", required=True, help="YYYY-MM")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.month)))
