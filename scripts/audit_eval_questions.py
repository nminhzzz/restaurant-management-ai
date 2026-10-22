"""Audit the Text-to-SQL question sets against the current views and database.

Checks every reference SQL with the same guard the assistant uses, executes it through
the role's read-only account, and reports empty results as warnings (data-dependent)
and real errors as failures.

Usage (from apps/api so `app` is importable):
    uv run python ../../scripts/audit_eval_questions.py --database restaurant_demo
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from collections import Counter
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.modules.ai.guard import validate_sql
from app.modules.ai.scope import ROLE_VIEWS
from app.shared.roles import Role

REPO_ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = REPO_ROOT / "data" / "eval" / "questions.jsonl"
DEV = REPO_ROOT / "data" / "eval" / "questions.dev.jsonl"
SAFETY = REPO_ROOT / "data" / "eval" / "questions.safety.jsonl"
ENV_FILE = REPO_ROOT / ".env"
ROLE_URL_KEYS = {
    Role.MANAGER: "AI_READONLY_URL_MANAGER",
    Role.CASHIER: "AI_READONLY_URL_CASHIER",
    Role.WAREHOUSE: "AI_READONLY_URL_WAREHOUSE",
}


def read_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if not ENV_FILE.is_file():
        return values
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def load(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def url_for(env: dict[str, str], role: Role, database: str) -> str:
    url = env.get(ROLE_URL_KEYS[role], "")
    if not url:
        raise SystemExit(f"Missing {ROLE_URL_KEYS[role]} in .env")
    return re.sub(r"/[^/?]+\?", f"/{database}?", url, count=1)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        default="restaurant",
        help="Database that holds the views (default: restaurant).",
    )
    args = parser.parse_args()

    official = load(QUESTIONS)
    dev = load(DEV)
    safety = load(SAFETY)
    failures: list[str] = []
    warnings: list[str] = []

    for name, rows, expected in (
        ("official", official, 80),
        ("dev", dev, 30),
        ("safety", safety, 30),
    ):
        if len(rows) != expected:
            failures.append(f"{name}: expected {expected} rows, got {len(rows)}")

    duplicates = [
        question
        for question, count in Counter(
            row["question"] for row in official + dev
        ).items()
        if count > 1
    ]
    for question in duplicates:
        failures.append(f"duplicate question: {question}")

    env = read_env()
    engines = {
        role: create_async_engine(url_for(env, role, args.database)) for role in Role
    }
    empty: list[str] = []
    try:
        for row in official + dev:
            qid, role = row["id"], Role(row["role"])
            expected_view = ROLE_VIEWS[role]
            if row["view"] != expected_view:
                failures.append(f"{qid}: view {row['view']} != {expected_view}")
                continue
            try:
                validate_sql(row["sql"], allowed_views=[expected_view], max_rows=500)
            except Exception as exc:  # noqa: BLE001 - the report is the point
                failures.append(f"{qid}: guard rejected SQL ({exc})")
                continue
            try:
                async with engines[role].connect() as connection:
                    result = await connection.execute(text(row["sql"]))
                    count = len(result.fetchall())
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{qid}: SQL failed ({str(exc).splitlines()[0]})")
                continue
            if count == 0:
                empty.append(qid)
    finally:
        for engine in engines.values():
            await engine.dispose()

    if empty:
        warnings.append(
            f"{len(empty)} reference queries return no rows: {', '.join(empty)}"
        )

    for warning in warnings:
        print(f"warning: {warning}")
    for failure in failures:
        print(f"error: {failure}")
    print(
        f"checked {len(official)} official + {len(dev)} dev + {len(safety)} safety questions "
        f"on {args.database}: {len(failures)} errors, {len(warnings)} warnings"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
