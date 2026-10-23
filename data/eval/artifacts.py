"""Capture readonly gold answers and import independently reviewed answer grades."""

import argparse
import asyncio
import copy
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.config import REPO_ROOT, get_settings
from app.modules.ai import guard
from app.modules.ai.pipeline import executor
from app.modules.ai.scope import views_for
from app.shared.roles import Role
from data.eval.harness import (
    Config,
    Failure,
    Outcome,
    _summarize,
    bind_reference_sql,
    compare,
    load_questions,
)


def validated_reference(question: dict[str, Any]) -> str:
    return guard.validate_sql(
        bind_reference_sql(question["sql"], question),
        allowed_views=views_for(Role(question["role"])),
        max_rows=get_settings().ai_max_rows,
    )


async def snapshot(source: Path, output: Path, dataset_id: str) -> dict[str, Any]:
    """Read a quiescent, restored evaluation dataset; never write to the database."""
    if source.resolve() == output.resolve():
        raise ValueError("Snapshot output must be separate from the source question set")
    questions = load_questions(source)
    for question in questions:
        if not question.get("reference_time") or not question.get("answer_rubric"):
            raise ValueError(f"{question['id']}: missing reference_time/answer_rubric")
        question["expected_result"] = await executor.execute(
            validated_reference(question),
            role=Role(question["role"]),
            timeout_seconds=get_settings().ai_sql_timeout_seconds,
        )
        question["snapshot_dataset"] = dataset_id
        question["review_status"] = "Đã chụp kết quả; chờ người kiểm tra chéo đáp án."
    body = "\n".join(json.dumps(q, ensure_ascii=False, default=str) for q in questions) + "\n"
    output.write_text(body, encoding="utf-8")
    manifest = {
        "dataset_id": dataset_id,
        "captured_at": datetime.now(UTC).isoformat(),
        "question_count": len(questions),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "snapshot_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "schema_sha256": hashlib.sha256(
            b"".join(p.read_bytes() for p in sorted((REPO_ROOT / "db/views").glob("*.sql")))
        ).hexdigest(),
        "prerequisite": "CSDL đánh giá đã phục hồi và không có tác vụ ghi trong lúc chụp.",
        "human_review_complete": False,
    }
    output.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def apply_grades(result: dict[str, Any], grades: list[dict[str, Any]]) -> dict[str, Any]:
    graded = copy.deepcopy(result)
    index = {
        (config, row["question_id"], row["run_index"]): row
        for config, detail in graded["detail"].items()
        for row in detail["outcomes"]
    }
    seen: set[tuple] = set()
    for grade in grades:
        if not str(grade.get("reviewer") or "").strip():
            raise ValueError("Every grade requires reviewer identity")
        if not isinstance(grade.get("answer_correct"), bool):
            raise ValueError("answer_correct must be a boolean")
        key = (grade["config"], grade["question_id"], grade["run_index"])
        if key not in index or key in seen:
            raise ValueError(f"Unknown or duplicate grade: {key}")
        seen.add(key)
        row = index[key]
        row["answer_correct"] = bool(grade["answer_correct"] and row["status"] == "đúng")
        row["grade"] = grade
    return graded


def recompute_comparison(result: dict[str, Any]) -> None:
    configs = []
    fields = Outcome.__dataclass_fields__
    for config, detail in result["detail"].items():
        outcomes = [
            Outcome(**{k: v for k, v in row.items() if k in fields}) for row in detail["outcomes"]
        ]
        failures = [Failure(**failure) for failure in detail.get("failures", [])]
        configs.append(
            _summarize(
                Config(config), outcomes, failures, max((o.run_index for o in outcomes), default=1)
            )
        )
    result["rows"] = compare(configs).rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("snapshot")
    capture.add_argument("--questions", type=Path, required=True)
    capture.add_argument("--out", type=Path, required=True)
    capture.add_argument("--dataset-id", required=True)
    grade_parser = sub.add_parser("grade")
    grade_parser.add_argument("--results", type=Path, required=True)
    grade_parser.add_argument("--grades", type=Path, required=True)
    grade_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "snapshot":
        asyncio.run(snapshot(args.questions, args.out, args.dataset_id))
    else:
        result = apply_grades(
            json.loads(args.results.read_text()), json.loads(args.grades.read_text())
        )
        recompute_comparison(result)
        args.out.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
