"""Independent cross-check of gold answers before the question set is locked.

Three members each answer the same 20 questions from a worksheet that never shows
the gold SQL. `check` runs every member's SQL under the question's role and
reference time, compares it with the gold rows and drafts the consensus minutes.
The tool only reports agreement; deciding which answer is right stays with people.
"""

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.config import get_settings
from app.modules.ai import guard
from app.modules.ai.pipeline import executor
from app.modules.ai.scope import views_for
from app.shared.roles import Role
from data.eval.harness import bind_reference_sql, load_questions, relaxed_match, strict_match

# 6 easy, 7 medium, 7 hard across all three roles. Prioritised: every question the
# model missed in every answered run (the gold may be what is wrong) and the
# questions whose gold SQL was rewritten on 26/10/2026.
SELECTION = (
    "Q010", "Q016", "Q018", "Q061", "Q064", "Q073",
    "Q026", "Q030", "Q036", "Q038", "Q066", "Q076", "Q080",
    "Q041", "Q045", "Q049", "Q050", "Q053", "Q057", "Q060",
)  # fmt: skip

CONVENTIONS = (
    "- 'Hôm nay' là ngày kinh doanh tham chiếu ghi ở từng câu (ngày kinh doanh bắt đầu 06:00).\n"
    "- 'N ngày qua' = N ngày kinh doanh kết thúc hôm nay.\n"
    "- 'Tuần này' = thứ Hai đến hôm nay; 'tuần trước' = thứ Hai đến Chủ nhật tuần trước.\n"
    "- 'N tháng gần đây' = N tháng dương lịch gồm tháng hiện tại.\n"
    "- Doanh thu/lượng bán của món chỉ tính order đã thanh toán.\n"
    "- 'Bán được' = order đã có hóa đơn.\n"
    "- 'Chưa thanh toán' = mọi trạng thái trừ Đã thanh toán, Đã hủy, "
    "Đóng \u2013 chưa thu được tiền.\n"
    "- Tháng ghi dạng YYYY-MM."
)

MATCH = "khớp"
MATCH_EXTRA = "khớp (thừa cột)"
MISMATCH = "lệch"
BLANK = "bỏ trống"
AGREED = "Đồng thuận với đáp án chuẩn"
DISCUSS = "Cần thảo luận"


@dataclass(frozen=True)
class MemberResult:
    member: str
    status: str
    detail: str = ""


def selected(questions: list[dict[str, Any]], ids: tuple[str, ...] = SELECTION) -> list[dict]:
    by_id = {question["id"]: question for question in questions}
    missing = [question_id for question_id in ids if question_id not in by_id]
    if missing:
        raise ValueError(f"Không có trong bộ đề: {', '.join(missing)}")
    return [by_id[question_id] for question_id in ids]


def worksheet(questions: list[dict[str, Any]]) -> str:
    """The questions as a member sees them: no gold SQL, no expected rows."""
    lines = [
        "# Phiếu kiểm tra chéo bộ đề đánh giá",
        "",
        "Tự viết SQL cho từng câu trên CSDL đánh giá, **không xem đáp án chuẩn và không "
        "trao đổi với người khác** trước khi nộp. Chỉ dùng view ghi ở từng câu "
        "(định nghĩa trong `db/views/`). Có thể ghi ngày cụ thể thay cho hàm ngày.",
        "",
        "Điền SQL vào tệp trả lời JSON (mẫu `mau-tra-loi.json`), đổi tên thành "
        "`answers.<tên>.json` và ghi tên mình vào trường `member`.",
        "",
        "## Quy ước dùng chung",
        "",
        CONVENTIONS,
        "",
    ]
    for number, question in enumerate(questions, 1):
        lines += [
            f"## {number}. {question['id']} — {question['question']}",
            "",
            f"- Độ khó: {question['difficulty']} · Vai trò: {question['role']}",
            f"- View được dùng: {', '.join(question.get('views') or [question['view']])}",
            f"- Ngày kinh doanh 'hôm nay': {question['reference_business_date']}",
        ]
        if question.get("metric_definition"):
            lines.append(f"- Định nghĩa chỉ số: {question['metric_definition']}")
        lines.append("")
    return "\n".join(lines)


def answer_template(questions: list[dict[str, Any]]) -> dict[str, Any]:
    return {"member": "", "answers": {question["id"]: "" for question in questions}}


def verdict(results: list[MemberResult]) -> str:
    agreed = results and all(result.status in (MATCH, MATCH_EXTRA) for result in results)
    return AGREED if agreed else DISCUSS


async def _rows(sql: str, question: dict[str, Any]) -> list[dict[str, Any]]:
    role = Role(question["role"])
    checked = guard.validate_sql(
        bind_reference_sql(sql, question),
        allowed_views=views_for(role),
        max_rows=get_settings().ai_max_rows,
    )
    return await executor.execute(
        checked, role=role, timeout_seconds=get_settings().ai_sql_timeout_seconds
    )


def _sample(rows: list[dict[str, Any]]) -> str:
    return json.dumps(rows[:2], ensure_ascii=False, default=str)


async def judge(sql: str, question: dict[str, Any], gold: list[dict[str, Any]]) -> tuple[str, str]:
    if not sql.strip():
        return BLANK, ""
    try:
        produced = await _rows(sql, question)
    except Exception as exc:
        return f"lỗi: {type(exc).__name__}", str(exc)[:200]
    if strict_match(produced, gold):
        return MATCH, ""
    if relaxed_match(produced, gold):
        return MATCH_EXTRA, ""
    return MISMATCH, f"{len(produced)} dòng, ví dụ {_sample(produced)}"


async def check(
    questions: list[dict[str, Any]], sheets: list[dict[str, Any]]
) -> list[tuple[dict[str, Any], list[MemberResult], list[dict[str, Any]]]]:
    report = []
    for question in questions:
        frozen = question.get("expected_result")
        gold = frozen if isinstance(frozen, list) else await _rows(question["sql"], question)
        results = []
        for sheet in sheets:
            sql = str(sheet["answers"].get(question["id"]) or "")
            status, detail = await judge(sql, question, gold)
            results.append(MemberResult(sheet["member"], status, detail))
        report.append((question, results, gold))
    return report


def minutes(report: list[tuple[dict[str, Any], list[MemberResult], list[dict[str, Any]]]]) -> str:
    """A draft for the team to complete; the decision column is left for people."""
    members = [result.member for result in report[0][1]] if report else []
    agreed = sum(verdict(results) == AGREED for _, results, _ in report)
    lines = [
        "# Biên bản kiểm tra chéo bộ đề (bản nháp)",
        "",
        f"Thành viên: {', '.join(members)}. Ngày họp: ……",
        "",
        f"{agreed}/{len(report)} câu cả {len(members)} người khớp đáp án chuẩn; "
        f"{len(report) - agreed} câu cần thảo luận.",
        "",
        "| Câu | " + " | ".join(members) + " | Kết luận | Quyết định của nhóm |",
        "|---|" + "---|" * len(members) + "---|---|",
    ]
    for question, results, _ in report:
        cells = " | ".join(result.status for result in results)
        lines.append(f"| {question['id']} | {cells} | {verdict(results)} | |")
    lines += ["", "## Chi tiết các câu cần thảo luận", ""]
    for question, results, gold in report:
        if verdict(results) == AGREED:
            continue
        lines += [
            f"### {question['id']} — {question['question']}",
            "",
            f"Đáp án chuẩn: {len(gold)} dòng, ví dụ {_sample(gold)}",
            "",
        ]
        lines += [
            f"- {result.member}: {result.status}" + (f" — {result.detail}" if result.detail else "")
            for result in results
        ]
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sheet_parser = sub.add_parser("sheet")
    sheet_parser.add_argument("--questions", type=Path)
    sheet_parser.add_argument("--out-dir", type=Path, required=True)
    check_parser = sub.add_parser("check")
    check_parser.add_argument("--questions", type=Path)
    check_parser.add_argument("--answers", type=Path, nargs="+", required=True)
    check_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    questions = selected(load_questions(args.questions))
    if args.command == "sheet":
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "phieu-kiem-tra-cheo.md").write_text(worksheet(questions), encoding="utf-8")
        (args.out_dir / "mau-tra-loi.json").write_text(
            json.dumps(answer_template(questions), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return
    sheets = [json.loads(path.read_text(encoding="utf-8")) for path in args.answers]
    for path, sheet in zip(args.answers, sheets, strict=True):
        if not str(sheet.get("member") or "").strip():
            raise ValueError(f"{path}: chưa ghi tên người làm ở trường member")
    report = asyncio.run(check(questions, sheets))
    args.out.write_text(minutes(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
