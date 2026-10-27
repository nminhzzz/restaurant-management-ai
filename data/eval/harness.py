"""The three benchmark configurations of Appendix 4, and the metrics they produce.

    A — schema only (the baseline)
    B — schema + Vietnamese normalisation + few-shot examples
    C — configuration B on the same model at effort=high for SQL generation

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
from contextlib import asynccontextmanager, nullcontext
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from enum import StrEnum
from itertools import product
from pathlib import Path
from typing import Any

import anthropic
import httpx
import sqlglot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlglot import exp

from app.core.config import get_settings
from app.core.database import get_session_factory
from app.core.errors import BusinessRuleError
from app.modules.ai import guard, llm
from app.modules.ai.errors import ClarificationNeeded, QuotaExceeded
from app.modules.ai.pipeline import executor, interpreter, normalize
from app.modules.ai.pipeline.prompt import build_prompt
from app.modules.ai.scope import views_for
from app.modules.ai.usage import collect_usage
from app.shared import business_date
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
    # The independent variable is effort/prompt policy, never model identity.
    return get_settings().llm_model


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
    answer: str = ""
    answer_correct: bool | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    call_count: int = 0
    models: list[str] = field(default_factory=list)
    usage_complete: bool = False
    produced_rows: list[dict[str, Any]] | None = None
    reference_rows: list[dict[str, Any]] | None = None
    run_index: int = 1


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
    """Compare numbers by value at two decimal places, everything else as text.

    10 == 10.0000 == Decimal("10"), and an unrounded average equals the gold's
    ROUND(..., 2): the question never fixes the precision, so neither does the grade.
    """
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
    return format(number.quantize(Decimal("0.01"), ROUND_HALF_UP).normalize(), "f")


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


def bind_reference_sql(sql: str, question: dict[str, Any]) -> str:
    """Freeze MySQL clock expressions using parsed nodes, never string substitution."""
    if not question.get("reference_time"):
        return sql
    moment = datetime.fromisoformat(question["reference_time"])
    day = (
        question.get("reference_business_date")
        or business_date.business_date_of(moment).isoformat()
    )
    tree = sqlglot.parse_one(sql, read="mysql")
    # Old gold SQL used DATE(CURDATE() - INTERVAL 6 HOUR); use its intended
    # business-date anchor explicitly, including when a different cutoff is active.
    # sqlglot parses MySQL DATE(expr) as TsOrDsToDate, not exp.Date.
    for date_node in list(tree.find_all(exp.Date, exp.TsOrDsToDate)):
        if date_node.find(exp.CurrentDate) is not None and date_node.find(exp.Interval) is not None:
            date_node.replace(exp.Cast(this=exp.Literal.string(day), to=exp.DataType.build("DATE")))
    for node in list(tree.walk()):
        if isinstance(node, exp.CurrentDate):
            node.replace(
                exp.Cast(
                    this=exp.Literal.string(moment.date().isoformat()),
                    to=exp.DataType.build("DATE"),
                )
            )
        elif isinstance(node, exp.CurrentTimestamp):
            node.replace(
                exp.Cast(
                    this=exp.Literal.string(moment.replace(tzinfo=None).isoformat(sep=" ")),
                    to=exp.DataType.build("DATETIME"),
                )
            )
    return tree.sql(dialect="mysql")


async def _generate(
    session: AsyncSession, config: Config, question: str, role: Role, error: str = ""
) -> str:
    settings = get_settings()
    examples: list[object] | None = None if uses_examples(config) else []
    prompt = await build_prompt(session, question, role, examples)
    if error:
        prompt += (
            f"\nSQL trước chưa hợp lệ hoặc thực thi lỗi: {error}. Hãy sửa trong phạm vi quyền."
        )
    client = llm.get_client()
    _bind_model(client, await model_for(config))
    with llm.generation_options(
        reasoning_effort="high" if config is Config.C else "low",
        fallback=False,
    ):
        raw = await llm.complete_async(client, prompt) or ""
    text = raw.strip()
    if text.upper().startswith("CLARIFY:"):
        raise ClarificationNeeded(text[len("CLARIFY:") :].strip())
    return guard.validate_sql(text, allowed_views=views_for(role), max_rows=settings.ai_max_rows)


def _summarize(
    config: Config, outcomes: list[Outcome], failures: list[Failure], runs: int = 1
) -> ConfigResult:
    total = len(outcomes) or 1
    latencies = [outcome.latency_ms for outcome in outcomes]
    return ConfigResult(
        config=config.value,
        execution_accuracy=sum(o.status == "đúng" for o in outcomes) / total,
        error_rate=sum(o.status == "lỗi" for o in outcomes) / total,
        refusal_rate=sum(
            o.status == "từ chối" or (o.status == "đúng" and not o.sql) for o in outcomes
        )
        / total,
        mean_latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
        relaxed_accuracy=sum(o.relaxed for o in outcomes) / total,
        p95_latency_ms=percentile(latencies, 0.95),
        runs=runs,
        failures=failures,
        outcomes=outcomes,
    )


async def run_configuration(
    config: Config, questions: list[Any], session: AsyncSession | None = None, runs: int = 1
) -> ConfigResult:
    if session is None:
        async with open_session() as opened:
            return await run_configuration(config, questions, opened, runs)
    outcomes: list[Outcome] = []
    failures: list[Failure] = []
    for run_index in range(1, max(1, runs) + 1):
        result = await _run(config, questions, session)
        outcomes.extend(replace(o, run_index=run_index) for o in result.outcomes)
        failures.extend(result.failures)
    return _summarize(config, outcomes, failures, max(1, runs))


async def _run(config: Config, questions: list[Any], session: AsyncSession) -> ConfigResult:
    settings = get_settings()
    outcomes: list[Outcome] = []
    failures: list[Failure] = []
    for question in questions:
        role = Role(question["role"])
        expected_refusal = question.get("expect") == "refusal"
        text = (
            normalize.normalize_question(question["question"])
            if normalises(config)
            else question["question"]
        )
        clock = (
            business_date.at_time(datetime.fromisoformat(question["reference_time"]))
            if question.get("reference_time")
            else nullcontext()
        )
        sql, answer, status, reason = "", "", "lỗi", ""
        produced = reference = None
        relaxed = False
        elapsed = 0.0
        with (
            clock,
            collect_usage(
                input_price=settings.ai_input_usd_per_million,
                output_price=settings.ai_output_usd_per_million,
                cache_write_price=settings.ai_cache_write_usd_per_million,
                cache_read_price=settings.ai_cache_read_usd_per_million,
                model_prices={
                    settings.llm_interpretation_model: (
                        settings.ai_interpretation_input_usd_per_million,
                        settings.ai_interpretation_output_usd_per_million,
                    )
                },
            ) as usage,
        ):
            started = time.perf_counter()
            last_error = ""
            for attempt in range(settings.ai_max_sql_attempts):
                try:
                    sql = await _generate(session, config, text, role, last_error)
                    if expected_refusal:
                        status, reason = "sai", "Yêu cầu không được phép nhưng vẫn sinh SQL."
                        break  # Never run a safety-case candidate against business data.
                    sql = guard.validate_sql(
                        bind_reference_sql(sql, question),
                        allowed_views=views_for(role),
                        max_rows=settings.ai_max_rows,
                    )
                    produced = await executor.execute(
                        sql, role=role, timeout_seconds=settings.ai_sql_timeout_seconds
                    )
                    with llm.generation_options(reasoning_effort="low", fallback=False):
                        try:
                            interpreted = await interpreter.interpret(
                                session, text, sql, produced, role
                            )
                        except (httpx.HTTPError, TimeoutError, anthropic.APIError):
                            interpreted = interpreter.fallback(produced, role)
                    answer = interpreted.text
                    status = "sai"  # Execution correctness is determined below.
                    break
                except (ClarificationNeeded, QuotaExceeded) as exc:
                    status, reason = ("đúng" if expected_refusal else "từ chối"), str(exc)
                    break
                except BusinessRuleError as exc:
                    last_error = str(exc)
                    status, reason = ("đúng" if expected_refusal else "từ chối"), last_error
                    if attempt + 1 == settings.ai_max_sql_attempts:
                        break
                except (httpx.HTTPError, TimeoutError, anthropic.APIError) as exc:
                    status, reason = "lỗi", f"Lỗi gọi LLM hoặc timeout: {type(exc).__name__}"
                    break
                except Exception as exc:
                    last_error = f"Lỗi thực thi: {type(exc).__name__}"
                    status, reason = "lỗi", last_error
                    if attempt + 1 == settings.ai_max_sql_attempts:
                        break
            # Stop the end-to-end clock BEFORE executing gold SQL or human grading.
            elapsed = (time.perf_counter() - started) * 1000
            if produced is not None:
                try:
                    frozen_gold = question.get("expected_result")
                    if isinstance(frozen_gold, list):
                        reference = frozen_gold
                    else:
                        reference_sql = guard.validate_sql(
                            bind_reference_sql(question["sql"], question),
                            allowed_views=views_for(role),
                            max_rows=settings.ai_max_rows,
                        )
                        reference = await executor.execute(
                            reference_sql,
                            role=role,
                            timeout_seconds=settings.ai_sql_timeout_seconds,
                        )
                    ordered = bool(question.get("answer_rubric", {}).get("ordering_required"))
                    hit = (
                        _rows(produced) == _rows(reference)
                        if ordered
                        else strict_match(produced, reference)
                    )
                    status = "đúng" if hit else "sai"
                    relaxed = hit or relaxed_match(produced, reference)
                    reason = "" if hit else "Kết quả khác SQL chuẩn."
                except Exception as exc:
                    status, reason = "lỗi", f"Lỗi đáp án chuẩn: {type(exc).__name__}"
        if reason and status != "đúng":
            failures.append(Failure(question["id"], reason))
        outcomes.append(
            Outcome(
                question_id=question["id"],
                difficulty=question.get("difficulty", ""),
                role=question["role"],
                status=status,
                latency_ms=round(elapsed, 1),
                sql=sql,
                relaxed=relaxed or status == "đúng",
                answer=answer,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cost_usd=usage.cost_usd,
                call_count=usage.call_count,
                models=usage.models,
                usage_complete=all(a.usage_reported for a in usage.attempts),
                produced_rows=produced,
                reference_rows=reference,
            )
        )
        print(
            f"[{config.value}] {question['id']} {status} {elapsed:.0f} ms",
            file=sys.stderr,
            flush=True,
        )
    return _summarize(config, outcomes, failures)


async def run_interleaved(
    configs: list[Config], questions: list[Any], runs: int = 3
) -> list[ConfigResult]:
    """Interleave configurations per question; rotate the first config each repeat."""
    buckets: dict[Config, list[Outcome]] = {config: [] for config in configs}
    failures: dict[Config, list[Failure]] = {config: [] for config in configs}
    async with open_session() as session:
        for repeat in range(max(1, runs)):
            rotation = repeat % len(configs)
            order = configs[rotation:] + configs[:rotation]
            for question in questions:
                for config in order:
                    result = await _run(config, [question], session)
                    buckets[config].extend(
                        replace(o, run_index=repeat + 1) for o in result.outcomes
                    )
                    failures[config].extend(result.failures)
    return [
        _summarize(config, buckets[config], failures[config], max(1, runs)) for config in configs
    ]


def _answer_accuracy(outcomes: list[Outcome]) -> float | None:
    if not outcomes or any(o.answer_correct is None for o in outcomes):
        return None
    return sum(o.status == "đúng" and o.answer_correct is True for o in outcomes) / len(outcomes)


def metrics_by(outcomes: list[Outcome], key: str) -> dict[str, dict[str, Any]]:
    groups = sorted({getattr(o, key) for o in outcomes})
    return {
        group: {
            "samples": len(rows := [o for o in outcomes if getattr(o, key) == group]),
            "p50_latency_ms": percentile([o.latency_ms for o in rows], 0.50),
            "p95_latency_ms": percentile([o.latency_ms for o in rows], 0.95),
            "execution_accuracy": sum(o.status == "đúng" for o in rows) / len(rows),
            "answer_accuracy": _answer_accuracy(rows),
            "cost_usd": sum(o.cost_usd for o in rows),
        }
        for group in groups
    }


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
            "answer_accuracy": _answer_accuracy(result.outcomes),
            "answer_grades_pending": sum(o.answer_correct is None for o in result.outcomes),
            "input_tokens": sum(o.input_tokens for o in result.outcomes),
            "output_tokens": sum(o.output_tokens for o in result.outcomes),
            "cost_usd": sum(o.cost_usd for o in result.outcomes),
            "usage_complete": all(o.usage_complete for o in result.outcomes),
            "metrics_by_role": metrics_by(result.outcomes, "role"),
            "metrics_by_difficulty": metrics_by(result.outcomes, "difficulty"),
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
    results = await run_interleaved(configs, questions, runs=runs)
    table = compare(results)
    detail = {
        result.config: {
            "outcomes": [asdict(outcome) for outcome in result.outcomes],
            "failures": [asdict(failure) for failure in result.failures],
        }
        for result in results
    }
    out.write_text(
        json.dumps(
            {"rows": table.rows, "detail": detail}, ensure_ascii=False, indent=2, default=str
        ),
        encoding="utf-8",
    )
    for row in table.rows:
        # Relaxed accuracy is the headline (agreed 26/10/2026): extra columns such as
        # the unit next to a stock figure still answer the question.
        print(
            f"{row['config']}: chính xác (nới lỏng) {row['relaxed_accuracy']:.2%} "
            f"{row['by_difficulty_relaxed']} · khắt khe {row['execution_accuracy']:.2%} "
            f"{row['by_difficulty']} · lỗi {row['error_rate']:.2%} · "
            f"từ chối {row['refusal_rate']:.2%} · {row['mean_latency_ms']:.0f} ms "
            f"(p95 {row['p95_latency_ms']:.0f} ms, {row['runs']} lần)"
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
