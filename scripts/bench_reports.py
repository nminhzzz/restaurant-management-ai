"""Measure the response-time requirements over HTTP, against a running API.

NFR-03 (report performance): p95 of the revenue and dish-ranking reports under 10 s
with 5 concurrent virtual users, on the 12-month simulated data set (>= 20,000 orders).

NFR-01 (business operations): p95 of catalogue updates and stock receipts at most 1 s
with 20 concurrent virtual users. The write scenarios create and change rows, so they run
only with --write, and only against a benchmark database. Holds and order submission need
the sales fixtures and are not scripted here.

Credentials come from the environment, never the command line:

    BENCH_USERNAME=... BENCH_PASSWORD=... \\
        uv run python ../../scripts/bench_reports.py --month 2026-09 [--write]

Exit status is non-zero when any measured p95 is over its budget, so the gate cannot pass
silently while an operation is slow. Every run prints the host, the number of virtual users
and requests, because a result is only meaningful with the conditions it was measured under.
"""

import argparse
import asyncio
import math
import os
import statistics
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import httpx

REPORT_BUDGET_SECONDS = 10.0  # NFR-03
REPORT_VIRTUAL_USERS = 5
OPERATION_BUDGET_SECONDS = 1.0  # NFR-01
OPERATION_VIRTUAL_USERS = 20


@dataclass(frozen=True)
class Scenario:
    name: str
    virtual_users: int
    budget_seconds: float
    # One request of the scenario; receives the HTTP client and the virtual user's index.
    call: Callable[[httpx.AsyncClient, int], Awaitable[httpx.Response]]


def percentile(samples: list[float], fraction: float) -> float:
    """Nearest-rank percentile; an empty sample set is 0."""
    if not samples:
        return 0.0
    ordered = sorted(samples)
    rank = max(1, math.ceil(fraction * len(ordered)))
    return ordered[rank - 1]


async def login(client: httpx.AsyncClient, username: str, password: str) -> dict[str, str]:
    response = await client.post(
        "/settings/auth/login", json={"username": username, "password": password}
    )
    response.raise_for_status()
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def run_scenario(
    base_url: str, headers: dict[str, str], scenario: Scenario, requests_per_user: int
) -> tuple[list[float], int]:
    """Each virtual user issues its requests back to back; returns timings and failures."""
    timings: list[float] = []
    failures = 0

    async def virtual_user(index: int) -> None:
        nonlocal failures
        async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=60) as client:
            for _ in range(requests_per_user):
                started = time.perf_counter()
                try:
                    response = await scenario.call(client, index)
                    ok = response.status_code < 400
                except httpx.HTTPError:
                    ok = False
                timings.append(time.perf_counter() - started)
                failures += 0 if ok else 1

    await asyncio.gather(*(virtual_user(i) for i in range(scenario.virtual_users)))
    return timings, failures


def report_scenarios(month: str) -> list[Scenario]:
    return [
        Scenario(
            "revenue report",
            REPORT_VIRTUAL_USERS,
            REPORT_BUDGET_SECONDS,
            lambda client, _: client.get("/reports/revenue", params={"month": month}),
        ),
        Scenario(
            "dish ranking report",
            REPORT_VIRTUAL_USERS,
            REPORT_BUDGET_SECONDS,
            lambda client, _: client.get(
                "/reports/dishes", params={"month": month, "order_by": "revenue"}
            ),
        ),
    ]


async def write_scenarios(base_url: str, headers: dict[str, str]) -> list[Scenario]:
    """One ingredient per virtual user, so the writers do not contend on a single row."""
    async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=60) as client:
        ids: list[int] = []
        for index in range(OPERATION_VIRTUAL_USERS):
            created = await client.post(
                "/catalog/ingredients",
                json={"TenNguyenLieu": f"bench-{int(time.time())}-{index}", "DonViTinh": "kg"},
            )
            created.raise_for_status()
            ids.append(created.json()["MaNguyenLieu"])

    return [
        Scenario(
            "catalogue update",
            OPERATION_VIRTUAL_USERS,
            OPERATION_BUDGET_SECONDS,
            lambda client, i: client.patch(
                f"/catalog/ingredients/{ids[i]}", json={"MucTonToiThieu": 1 + i % 5}
            ),
        ),
        Scenario(
            "stock receipt",
            OPERATION_VIRTUAL_USERS,
            OPERATION_BUDGET_SECONDS,
            lambda client, i: client.post(
                "/inventory/receipts",
                json={"lines": [{"ingredient_id": ids[i], "quantity": 1, "unit_price": 1000}]},
            ),
        ),
    ]


async def main(args: argparse.Namespace) -> int:
    username = os.environ.get("BENCH_USERNAME")
    password = os.environ.get("BENCH_PASSWORD")
    if not username or not password:
        raise SystemExit("Set BENCH_USERNAME and BENCH_PASSWORD (a Manager account).")

    async with httpx.AsyncClient(base_url=args.base_url, timeout=30) as client:
        headers = await login(client, username, password)

    scenarios = report_scenarios(args.month)
    if args.write:
        scenarios += await write_scenarios(args.base_url, headers)

    print(f"target {args.base_url}, {args.requests} requests per virtual user")
    print(f"{'scenario':22s} {'VUs':>4s} {'n':>5s} {'p50':>8s} {'p95':>8s} {'max':>8s}  verdict")
    over_budget = 0
    for scenario in scenarios:
        timings, failures = await run_scenario(args.base_url, headers, scenario, args.requests)
        p95 = percentile(timings, 0.95)
        failed = failures > 0 or p95 > scenario.budget_seconds
        over_budget += failed
        verdict = f"FAIL ({failures} errors)" if failures else ("OVER" if failed else "ok")
        print(
            f"{scenario.name:22s} {scenario.virtual_users:4d} {len(timings):5d} "
            f"{statistics.median(timings):7.3f}s {p95:7.3f}s {max(timings):7.3f}s  {verdict} "
            f"(budget {scenario.budget_seconds:g}s)"
        )
    return over_budget


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--month", required=True, help="YYYY-MM of the report period")
    parser.add_argument("--base-url", default="http://localhost:8000/api/v1")
    parser.add_argument("--requests", type=int, default=20, help="requests per virtual user")
    parser.add_argument(
        "--write", action="store_true", help="also run the NFR-01 write scenarios (creates rows)"
    )
    raise SystemExit(asyncio.run(main(parser.parse_args())))
