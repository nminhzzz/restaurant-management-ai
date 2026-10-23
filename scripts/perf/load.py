"""Dependency-aware HTTP workload and raw evidence for Appendix J."""

import argparse
import asyncio
import csv
import json
import random
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TextIO
from uuid import UUID

import httpx
from scripts.bench_load import percentile

ROUTES = {
    "login": "/api/v1/settings/auth/login",
    "hold": "/api/v1/sales/holds",
    "adjust_hold": "/api/v1/sales/holds/{hold_id}",
    "send": "/api/v1/sales/orders",
    "read_order": "/api/v1/sales/orders/{order_id}",
    "read_menu": "/api/v1/catalog/dishes",
    "catalog": "/api/v1/catalog/dishes/{catalog_id}",
    "receipt": "/api/v1/inventory/receipts",
    "revenue_day": "/api/v1/reports/revenue",
    "revenue_month": "/api/v1/reports/revenue",
    "ranking": "/api/v1/reports/dishes",
}


@dataclass
class Sample:
    run_id: str
    timestamp: str
    role: str
    operation: str
    status: int
    latency_ms: float
    outcome: str
    vu: int
    detail: str = ""
    phase: str = "measurement"


def write_csv(samples: list[Sample], output: TextIO) -> None:
    writer = csv.DictWriter(output, fieldnames=list(Sample.__dataclass_fields__))
    writer.writeheader()
    writer.writerows(asdict(sample) for sample in samples)


def aggregate(samples: list[Sample], duration: float) -> dict:
    groups = defaultdict(list)
    for sample in samples:
        if sample.phase == "measurement":
            groups[sample.operation].append(sample)
    result = {}
    for operation, rows in groups.items():
        latencies = [s.latency_ms for s in rows if s.outcome == "ok"]
        technical = sum(s.outcome == "technical_error" for s in rows)
        result[operation] = {
            "samples": len(rows),
            "successes": len(latencies),
            "p50_ms": percentile(latencies, 0.5) if latencies else None,
            "p95_ms": percentile(latencies, 0.95) if latencies else None,
            "success_per_second": len(latencies) / duration,
            "technical_errors": technical,
            "technical_error_rate": technical / len(rows),
            "business_rejections": sum(s.outcome == "business_rejection" for s in rows),
        }
    return result


class BusinessUser:
    def __init__(self, client, tokens, data, run_id, vu, seed, *, pause=True, routes=None):
        self.client, self.tokens, self.data = client, tokens, data
        self.run_id, self.vu = run_id, vu
        self.rng = random.Random(seed)
        self.pause = pause
        self.routes = routes or ROUTES
        self.window = None

    async def request(
        self, operation, role, method, *, ids=None, body=None, params=None, required=()
    ):
        path = self.routes[operation].format(**self.data, **(ids or {}))
        started = time.perf_counter()
        detail = ""
        result = {}
        try:
            response = await self.client.request(
                method,
                path,
                json=body,
                params=params,
                headers={"Authorization": f"Bearer {self.tokens[role]}"},
            )
            status = response.status_code
            # Only the business conflict status is an expected refusal. Authentication,
            # validation and missing routes indicate a broken workload/environment.
            outcome = (
                "ok"
                if 200 <= status < 300
                else ("business_rejection" if status == 409 else "technical_error")
            )
            if outcome == "ok":
                result = response.json()
                if not isinstance(result, dict) or any(not result.get(k) for k in required):
                    outcome, detail = "technical_error", "missing_response_dependency"
                elif result.get("rejected"):
                    outcome, detail = "business_rejection", "partial_order_rejection"
        except (httpx.HTTPError, ValueError) as exc:
            status, outcome, detail = 0, "technical_error", type(exc).__name__
        sample = Sample(
            self.run_id,
            datetime.now(UTC).isoformat(),
            role,
            operation,
            status,
            (time.perf_counter() - started) * 1000,
            outcome,
            self.vu,
            detail,
        )
        if self.window is not None:
            sample.phase = (
                "measurement"
                if started >= self.window[0] and time.perf_counter() <= self.window[1]
                else "warmup_or_boundary"
            )
        if self.pause:
            await asyncio.sleep(self.rng.uniform(1, 3))
        return sample, result

    async def cycle(self):
        samples = []
        order_id = None
        for _ in range(2):
            sample, hold = await self.request(
                "hold",
                "CASHIER",
                "POST",
                body={"dish_id": self.data["dish_id"], "quantity": 1},
                required=("MaGiuCho", "MaLuotChon"),
            )
            samples.append(sample)
            if sample.outcome != "ok":
                return samples
            sample, _ = await self.request(
                "adjust_hold",
                "CASHIER",
                "PATCH",
                ids={"hold_id": hold["MaGiuCho"]},
                body={"quantity": 2},
            )
            samples.append(sample)
            if sample.outcome != "ok":
                return samples
            sample, order = await self.request(
                "send",
                "CASHIER",
                "POST",
                required=("MaOrder",),
                body={
                    "order_type": "Mang về",
                    "request_id": str(UUID(int=self.rng.getrandbits(128))),
                    "lines": [
                        {
                            "dish_id": self.data["dish_id"],
                            "quantity": 2,
                            "hold_id": hold["MaGiuCho"],
                        }
                    ],
                },
            )
            samples.append(sample)
            if sample.outcome != "ok":
                return samples
            order_id = order["MaOrder"]
        sample, _ = await self.request("read_order", "CASHIER", "GET", ids={"order_id": order_id})
        samples.append(sample)
        sample, _ = await self.request("read_menu", "CASHIER", "GET")
        samples.append(sample)
        sample, _ = await self.request(
            "catalog",
            "MANAGER",
            "PATCH",
            body={"HinhAnh": f"/images/perf-{self.rng.getrandbits(64)}.png"},
        )
        samples.append(sample)
        sample, _ = await self.request(
            "receipt",
            "WAREHOUSE",
            "POST",
            body={
                "supplier_id": self.data["supplier_id"],
                "lines": [
                    {"ingredient_id": self.data["ingredient_id"], "quantity": 1, "unit_price": 1000}
                ],
            },
        )
        samples.append(sample)
        return samples

    async def reports(self, anchor, expected):
        samples = []
        for operation in ("revenue_day", "revenue_month", "ranking"):
            params = {
                "granularity": "day" if operation == "revenue_day" else "month",
                "anchor": anchor,
            }
            sample, body = await self.request(operation, "MANAGER", "GET", params=params)
            if sample.outcome == "ok" and operation != "ranking":
                try:
                    if Decimal(str(body["total"])) != Decimal(expected[operation]):
                        sample.outcome, sample.detail = (
                            "technical_error",
                            "manifest_revenue_mismatch",
                        )
                except (KeyError, ValueError):
                    sample.outcome, sample.detail = "technical_error", "missing_revenue_total"
            samples.append(sample)
        return samples


def validate_accounts(accounts, vu, reports=False):
    if len(accounts) < vu:
        raise ValueError("Không đủ tài khoản riêng cho số VU.")
    roles = ("MANAGER",) if reports else ("CASHIER", "MANAGER", "WAREHOUSE")
    names = [account[role]["username"] for account in accounts[:vu] for role in roles]
    if len(set(names)) != len(names):
        raise ValueError("Mỗi VU/vai trò phải dùng tài khoản riêng.")


async def run(args, reports=False):
    accounts = json.loads(Path(args.accounts).read_text())
    validate_accounts(accounts, args.vu, reports)
    routes = ROUTES | (json.loads(Path(args.api_map).read_text()) if args.api_map else {})
    manifest = json.loads(Path(args.manifest).read_text()) if reports else {}
    async with httpx.AsyncClient(base_url=args.base_url, timeout=30) as client:
        users = []
        roles = ("MANAGER",) if reports else ("CASHIER", "MANAGER", "WAREHOUSE")
        for index, account in enumerate(accounts[: args.vu]):
            tokens = {}
            for role in roles:
                response = await client.post(routes["login"], json=account[role])
                response.raise_for_status()
                tokens[role] = response.json()["access_token"]
            users.append(
                BusinessUser(
                    client,
                    tokens,
                    account["data"],
                    args.run_id,
                    args.vu,
                    args.seed + index,
                    routes=routes,
                )
            )
        samples = []
        started = time.perf_counter()
        measurement_start = started + args.warmup
        deadline = measurement_start + args.duration

        async def worker(user):
            user.window = (measurement_start, deadline)
            while time.perf_counter() < deadline:
                rows = await (
                    user.reports(args.anchor, manifest["report_totals"][args.anchor])
                    if reports
                    else user.cycle()
                )
                samples.extend(rows)

        await asyncio.gather(*(worker(user) for user in users))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as stream:
        write_csv(samples, stream)
    summary = {
        "run_id": args.run_id,
        "vu": args.vu,
        "seed": args.seed,
        "warmup_seconds": args.warmup,
        "measurement_seconds": args.duration,
        "cache": args.cache,
        "operations": aggregate(samples, args.duration),
    }
    output.with_suffix(".json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    expected = (
        ("revenue_day", "revenue_month", "ranking")
        if reports
        else ("hold", "adjust_hold", "send", "catalog", "receipt")
    )
    budget = 10000 if reports else 1000
    return int(
        any(
            name not in summary["operations"]
            or summary["operations"][name]["p95_ms"] is None
            or (
                summary["operations"][name]["p95_ms"] >= budget
                if reports
                else summary["operations"][name]["p95_ms"] > budget
            )
            or summary["operations"][name]["technical_errors"]
            for name in expected
        )
    )


def main(reports=False):
    parser = argparse.ArgumentParser(description="Phát tải API theo Phụ lục J; chỉ môi trường thử.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--accounts", required=True)
    parser.add_argument("--api-map")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--vu", type=int, default=5, choices=(5, 10, 20))
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument("--warmup", type=float, default=120)
    parser.add_argument("--duration", type=float, default=600)
    parser.add_argument("--cache", required=True, help="Trạng thái cache thực tế đã quan sát.")
    if reports:
        parser.add_argument("--manifest", required=True)
        parser.add_argument("--anchor", required=True)
    args = parser.parse_args()
    if args.duration <= 0 or args.warmup < 0 or (reports and args.vu != 5):
        parser.error("Thời lượng phải dương; warmup không âm; báo cáo dùng 5 VU.")
    raise SystemExit(asyncio.run(run(args, reports)))
