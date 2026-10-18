"""Concurrent read-load benchmark with p50/p95/p99 for the reporting endpoints.

Run against a seeded MySQL instance and a running API:

    cd apps/api && uv run uvicorn app.main:app --port 8001
    cd apps/api && uv run python ../../scripts/bench_load.py --base-url http://127.0.0.1:8001

The manager account is the seeded ``seed_manager`` / ``matkhau123`` unless
``--username`` / ``--password`` override it. The script exits non-zero when a p95
exceeds ``--budget`` so a slow endpoint cannot pass silently.
"""

import argparse
import asyncio
import math
import time
from dataclasses import dataclass

import httpx

REPORTS = (
    ("revenue", "/api/v1/reports/revenue"),
    ("dishes", "/api/v1/reports/dishes"),
    ("hours", "/api/v1/reports/hours"),
    ("costs", "/api/v1/reports/costs"),
    ("comparison", "/api/v1/reports/comparison"),
)


@dataclass(frozen=True)
class Sample:
    status: int
    elapsed_ms: float


def percentile(values: list[float], fraction: float) -> float:
    """Linear-interpolated percentile; small and dependency-free."""
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


async def _login(client: httpx.AsyncClient, username: str, password: str) -> str:
    response = await client.post(
        "/api/v1/settings/auth/login",
        json={"username": username, "password": password},
    )
    response.raise_for_status()
    return str(response.json()["access_token"])


async def _measure(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    path: str,
    params: dict[str, str],
    requests: int,
    concurrency: int,
) -> list[Sample]:
    queue: asyncio.Queue[int] = asyncio.Queue()
    for index in range(requests):
        queue.put_nowait(index)
    samples: list[Sample] = []
    lock = asyncio.Lock()

    async def worker() -> None:
        while True:
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                return
            started = time.perf_counter()
            try:
                response = await client.get(path, params=params, headers=headers)
                status = response.status_code
            except httpx.HTTPError:
                status = 0
            elapsed = (time.perf_counter() - started) * 1000
            async with lock:
                samples.append(Sample(status=status, elapsed_ms=elapsed))

    await asyncio.gather(*(worker() for _ in range(min(concurrency, requests))))
    return samples


async def _run_endpoint(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    name: str,
    path: str,
    params: dict[str, str],
    requests: int,
    concurrency: int,
    budget: float,
) -> bool:
    samples = await _measure(client, headers, path, params, requests, concurrency)
    latencies = [sample.elapsed_ms for sample in samples]
    failures = sum(1 for sample in samples if sample.status != 200)
    p95 = percentile(latencies, 0.95)
    budget_ms = budget * 1000
    print(
        f"{name:10s} n={len(samples):3d} lỗi={failures:3d} "
        f"p50={percentile(latencies, 0.50):7.1f}ms "
        f"p95={p95:7.1f}ms p99={percentile(latencies, 0.99):7.1f}ms "
        f"{'OVER' if p95 > budget_ms else 'ok'}"
    )
    return p95 <= budget_ms and failures == 0


async def main(
    base_url: str,
    month: str,
    requests: int,
    concurrency: int,
    budget: float,
    username: str,
    password: str,
) -> int:
    started = time.perf_counter()
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        token = await _login(client, username, password)
        headers = {"Authorization": f"Bearer {token}"}
        params = {"month": month}
        results = []
        for name, path in REPORTS:
            if name == "comparison":
                results.append(
                    await _run_endpoint(
                        client,
                        headers,
                        name,
                        path,
                        {"left": month, "right": month},
                        requests,
                        concurrency,
                        budget,
                    )
                )
            else:
                results.append(
                    await _run_endpoint(
                        client,
                        headers,
                        name,
                        path,
                        params,
                        requests,
                        concurrency,
                        budget,
                    )
                )
    elapsed = time.perf_counter() - started
    print(f"tổng {elapsed:.1f}s; {'PASS' if all(results) else 'FAIL'}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--month", default="2026-09")
    parser.add_argument("--requests", type=int, default=40)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--budget", type=float, default=2.0, help="p95 budget in seconds")
    parser.add_argument("--username", default="seed_manager")
    parser.add_argument("--password", default="matkhau123")
    args = parser.parse_args()
    raise SystemExit(
        asyncio.run(
            main(
                args.base_url,
                args.month,
                args.requests,
                args.concurrency,
                args.budget,
                args.username,
                args.password,
            )
        )
    )
