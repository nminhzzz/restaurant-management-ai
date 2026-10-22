"""The three benchmark configurations of Appendix 4, and the metrics they produce.

    A — schema only (the baseline)
    B — schema + Vietnamese normalisation + few-shot examples
    C — configuration B on a second model

Accuracy is measured by **executing** what the model produced and what the reference
SQL produces, then comparing the rows — never by comparing SQL text, because two
different queries returning the same table are both correct.

Run against a seeded database with that database's read-only accounts in place:

    cd apps/api && uv run python ../../data/eval/harness.py \
        --configs A,B,C --out ../../docs/eval-results.json
"""

import argparse
import asyncio
import json
import math
import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from itertools import product
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session_factory
from app.core.errors import BusinessRuleError
from app.modules.ai import guard, llm
from app.modules.ai.errors import ClarificationNeeded, QuotaExceeded
from app.modules.ai.pipeline import executor, normalize
from app.modules.ai.pipeline.prompt import build_prompt
from app.modules.ai.scope import views_for
from app.shared.roles import Role

QUESTIONS_PATH = Path(__file__).with_name("questions.jsonl")


class Config(StrEnum):
    A = "A"
    B = "B"
    C = "C"


def uses_examples(config: Config) -> bool:
    """A is the schema-only baseline; B and C add the few-shot examples."""
    return config in (Config.B, Config.C)


def normalises(config: Config) -> bool:
    """Vietnamese normalisation is one of B's two additions over A."""
    return config in (Config.B, Config.C)


async def model_for(config: Config) -> str:
    settings = get_settings()
    if config is Config.C:
        return settings.ai_config_c_model or f"{settings.llm_model}-alt"
    return settings.llm_model


@dataclass(frozen=True)
class Failure:
    question_id: str
    reason: str


@dataclass(frozen=True)
class Outcome:
    """One question's result: status is "đúng", "sai", "lỗi" or "từ chối"."""

    question_id: str
    difficulty: str
    role: str
    status: str
    latency_ms: float
    sql: str = ""
    relaxed: bool = False


@dataclass(frozen=True)
class ConfigResult:
    config: str
    execution_accuracy: float
    error_rate: float
    refusal_rate: float
    mean_latency_ms: float
    relaxed_accuracy: float = 0.0
    p95_latency_ms: float = 0.0
    runs: int = 1
    failures: list[Failure] = field(default_factory=list)
    outcomes: list[Outcome] = field(default_factory=list)


def percentile(values: list[float], fraction: float) -> float:
    """Nearest-rank percentile; p95 with 20 samples is the 19th value."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def accuracy_by(result: ConfigResult, key: str, relaxed: bool = False) -> dict[str, float]:
    """Execution accuracy per difficulty or per role (MT5 sets per-difficulty targets)."""
    totals: dict[str, int] = {}
    correct: dict[str, int] = {}
    for outcome in result.outcomes:
        group = getattr(outcome, key)
        totals[group] = totals.get(group, 0) + 1
        hit = outcome.relaxed if relaxed else outcome.status == "đúng"
        correct[group] = correct.get(group, 0) + hit
    return {group: round(correct[group] / totals[group], 4) for group in sorted(totals)}


@dataclass(frozen=True)
class ComparisonTable:
    rows: list[dict[str, Any]]


@asynccontextmanager
async def open_session() -> AsyncIterator[AsyncSession]:
    """Session seam: tests replace this with their own in-memory session."""
    async with get_session_factory()() as session:
        yield session


def load_questions(path: Path | None = None) -> list[dict[str, Any]]:
    source = path or QUESTIONS_PATH
    lines = source.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _bind_model(client: Any, model: str) -> None:
    if hasattr(client, "model"):
        client.model = model


def _norm(value: Any) -> str:
    """Compare numbers by value (10 == 10.0000 == Decimal("10")), everything else as text."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return str(value)
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value)
    if not number.is_finite():
        return str(value)
    return format(number.normalize(), "f")


def _rows(rows: list[dict[str, Any]]) -> list[tuple[str, ...]]:
    return [tuple(_norm(value) for value in row.values()) for row in rows]


def strict_match(produced: list[dict[str, Any]], gold: list[dict[str, Any]]) -> bool:
    """Execution accuracy: the same rows with the same columns, in any row order."""
    return sorted(_rows(produced)) == sorted(_rows(gold))


def relaxed_match(produced: list[dict[str, Any]], gold: list[dict[str, Any]]) -> bool:
    """Like strict_match, but extra columns in the answer are allowed.

    Every gold column must appear among the produced columns with the same value in
    the same row, e.g. returning the unit next to the stock still answers "how much".
    """
    got, want = _rows(produced), _rows(gold)
    if len(got) != len(want):
        return False
    if not want:
        return True
    width = len(want[0])
    column = lambda rows, i: sorted(row[i] for row in rows)  # noqa: E731
    candidates = [
        [i for i in range(len(got[0])) if column(got, i) == column(want, j)] for j in range(width)
    ]
    target = sorted(want)
    for mapping in product(*candidates):
        if (
            len(set(mapping)) == width
            and sorted(tuple(row[i] for i in mapping) for row in got) == target
        ):
            return True
    return False


async def _generate(session: AsyncSession, config: Config, question: str, role: Role) -> str:
    settings = get_settings()
    examples: list[object] | None = None if uses_examples(config) else []
    prompt = await build_prompt(session, question, role, examples)
    client = llm.get_client()
    _bind_model(client, await model_for(config))
    raw = await asyncio.to_thread(client.complete, prompt) or ""
    text = raw.strip()
    if text.upper().startswith("CLARIFY:"):
        raise ClarificationNeeded(text[len("CLARIFY:") :].strip())
    return guard.validate_sql(text, allowed_views=views_for(role), max_rows=settings.ai_max_rows)


async def run_configuration(
    config: Config,
    questions: list[Any],
    session: AsyncSession | None = None,
    runs: int = 1,
) -> ConfigResult:
    """Run one configuration and report SQL execution accuracy plus latency."""
    runs = max(1, runs)
    if session is not None:
        return await _repeat(config, questions, session, runs)
    async with open_session() as opened:
        return await _repeat(config, questions, opened, runs)


async def _repeat(
    config: Config, questions: list[Any], session: AsyncSession, runs: int
) -> ConfigResult:
    results = [await _run(config, questions, session) for _ in range(runs)]
    if runs == 1:
        return results[0]
    latencies = [outcome.latency_ms for result in results for outcome in result.outcomes]
    return ConfigResult(
        config=config.value,
        execution_accuracy=sum(r.execution_accuracy for r in results) / runs,
        error_rate=sum(r.error_rate for r in results) / runs,
        refusal_rate=sum(r.refusal_rate for r in results) / runs,
        mean_latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
        relaxed_accuracy=sum(r.relaxed_accuracy for r in results) / runs,
        p95_latency_ms=percentile(latencies, 0.95),
        runs=runs,
        failures=[failure for r in results for failure in r.failures],
        outcomes=[outcome for r in results for outcome in r.outcomes],
    )


async def _run(config: Config, questions: list[Any], session: AsyncSession) -> ConfigResult:
    settings = get_settings()
    correct = errors = refusals = 0
    latencies: list[float] = []
    failures: list[Failure] = []
    outcomes: list[Outcome] = []

    def record(
        question: dict[str, Any],
        status: str,
        started: float,
        sql: str = "",
        relaxed: bool | None = None,
        overhead_ms: float = 0.0,
    ) -> None:
        # Latency measures the assistant (SQL generation + running its SQL). The
        # reference query is benchmark bookkeeping and must not inflate it.
        elapsed = (time.perf_counter() - started) * 1000 - overhead_ms
        latencies.append(elapsed)
        print(
            f"[{config.value}] {len(outcomes) + 1}/{len(questions)} {question['id']} "
            f"{status} {elapsed:.0f} ms",
            file=sys.stderr,
            flush=True,
        )
        outcomes.append(
            Outcome(
                question["id"],
                question.get("difficulty", ""),
                question["role"],
                status,
                round(elapsed, 1),
                sql,
                status == "đúng" if relaxed is None else relaxed,
            )
        )

    for question in questions:
        question_id = question["id"]
        role = Role(question["role"])
        expected_refusal = question.get("expect") == "refusal" or bool(
            question.get("notes") and "vượt quyền" in question["notes"]
        )
        text = (
            normalize.normalize_question(question["question"])
            if normalises(config)
            else question["question"]
        )

        started = time.perf_counter()
        try:
            sql = await _generate(session, config, text, role)
        except (BusinessRuleError, ClarificationNeeded, QuotaExceeded) as exc:
            refusals += 1
            if expected_refusal:
                correct += 1
                record(question, "đúng", started)
            else:
                failures.append(Failure(question_id, f"từ chối ngoài dự kiến: {exc}"))
                record(question, "từ chối", started)
            continue
        except httpx.HTTPError as exc:
            # An API outage is a measured error for this question, not a reason to
            # throw away the rest of the run.
            errors += 1
            failures.append(Failure(question_id, f"lỗi gọi LLM: {exc}"))
            record(question, "lỗi", started)
            continue

        if expected_refusal and not question.get("sql"):
            # A safety case without a reference query: producing any SQL is wrong,
            # but there is nothing safe to execute for comparison.
            failures.append(Failure(question_id, "câu không được phép nhưng vẫn trả dữ liệu"))
            record(question, "sai", started, sql)
            continue

        reference_ms = 0.0
        try:
            produced = await executor.execute(
                sql, role=role, timeout_seconds=settings.ai_sql_timeout_seconds
            )
            gold_started = time.perf_counter()
            reference = await executor.execute(
                question["sql"],
                role=role,
                timeout_seconds=settings.ai_sql_timeout_seconds,
            )
            reference_ms = (time.perf_counter() - gold_started) * 1000
        except Exception as exc:
            errors += 1
            failures.append(Failure(question_id, f"lỗi thực thi: {exc}"))
            record(question, "lỗi", started, sql)
            continue

        if expected_refusal:
            failures.append(Failure(question_id, "câu vượt quyền nhưng vẫn trả dữ liệu"))
            record(question, "sai", started, sql, overhead_ms=reference_ms)
        elif strict_match(produced, reference):
            correct += 1
            record(question, "đúng", started, sql, overhead_ms=reference_ms)
        else:
            failures.append(Failure(question_id, "kết quả khác SQL chuẩn"))
            record(
                question,
                "sai",
                started,
                sql,
                relaxed_match(produced, reference),
                overhead_ms=reference_ms,
            )

    total = len(questions) or 1
    return ConfigResult(
        config=config.value,
        execution_accuracy=correct / total,
        error_rate=errors / total,
        refusal_rate=refusals / total,
        mean_latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
        relaxed_accuracy=sum(outcome.relaxed for outcome in outcomes) / total,
        p95_latency_ms=percentile(latencies, 0.95),
        failures=failures,
        outcomes=outcomes,
    )


def compare(results: list[ConfigResult]) -> ComparisonTable:
    """One row per configuration, with the Appendix 4 metrics side by side."""
    rows = [
        {
            "config": result.config,
            "execution_accuracy": round(result.execution_accuracy, 4),
            "error_rate": round(result.error_rate, 4),
            "refusal_rate": round(result.refusal_rate, 4),
            "mean_latency_ms": round(result.mean_latency_ms, 1),
            "p95_latency_ms": round(result.p95_latency_ms, 1),
            "runs": result.runs,
            "failures": len(result.failures),
            "relaxed_accuracy": round(result.relaxed_accuracy, 4),
            "by_difficulty": accuracy_by(result, "difficulty"),
            "by_role": accuracy_by(result, "role"),
            "by_difficulty_relaxed": accuracy_by(result, "difficulty", relaxed=True),
            "by_role_relaxed": accuracy_by(result, "role", relaxed=True),
        }
        for result in results
    ]
    return ComparisonTable(rows=rows)


async def run_harness(
    config: Config, questions: list[Any], out: Path, runs: int = 1
) -> ConfigResult:
    result = await run_configuration(config, questions, runs=runs)
    out.write_text(
        json.dumps(
            {
                "config": result.config,
                "execution_accuracy": result.execution_accuracy,
                "error_rate": result.error_rate,
                "refusal_rate": result.refusal_rate,
                "mean_latency_ms": result.mean_latency_ms,
                "p95_latency_ms": result.p95_latency_ms,
                "runs": result.runs,
                "failures": [asdict(failure) for failure in result.failures],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return result


async def _main(
    configs: list[Config],
    out: Path,
    questions_path: Path | None = None,
    runs: int = 1,
) -> int:
    questions = load_questions(questions_path)
    results = [await run_configuration(config, questions, runs=runs) for config in configs]
    table = compare(results)
    detail = {
        result.config: {
            "outcomes": [asdict(outcome) for outcome in result.outcomes],
            "failures": [asdict(failure) for failure in result.failures],
        }
        for result in results
    }
    out.write_text(
        json.dumps({"rows": table.rows, "detail": detail}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for row in table.rows:
        print(
            f"{row['config']}: chính xác {row['execution_accuracy']:.2%} · "
            f"lỗi {row['error_rate']:.2%} · từ chối {row['refusal_rate']:.2%} · "
            f"{row['mean_latency_ms']:.0f} ms (p95 {row['p95_latency_ms']:.0f} ms, "
            f"{row['runs']} lần) · theo độ khó {row['by_difficulty']} · "
            f"nới lỏng {row['relaxed_accuracy']:.2%} {row['by_difficulty_relaxed']}"
        )
    print(f"Đã ghi {out}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--configs", default="A,B,C")
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Số lần chạy mỗi cấu hình (mặc định 3) để tính p95 độ trễ",
    )
    parser.add_argument("--out", default="eval-results.json")
    parser.add_argument(
        "--questions",
        default=None,
        help="Đường dẫn file JSONL; mặc định data/eval/questions.jsonl",
    )
    args = parser.parse_args()
    chosen = [Config(name.strip()) for name in args.configs.split(",") if name.strip()]
    questions_path = Path(args.questions) if args.questions else None
    raise SystemExit(asyncio.run(_main(chosen, Path(args.out), questions_path, args.runs)))
