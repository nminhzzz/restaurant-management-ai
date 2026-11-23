"""AI-grade the prose answers of a harness result against each question's rubric.

Usage (from apps/api):
    uv run python ../../data/eval/ai_grade.py RESULTS.json QUESTIONS.jsonl GRADES_OUT.json
then apply the grades with `artifacts.py grade`. The judge is an AI, not a human reviewer;
every grade records that in `reviewer`.
Only runs whose SQL passed strict comparison (status 'đúng') are sent to the judge; every
other run is written as answer_correct=false, since apply_grades forbids grading them true.
"""

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import anthropic

from app.core.config import get_settings

JUDGE_MODEL = "claude-opus-5-5"
REVIEWER = "AI (claude-opus-5-5, effort=low) theo rubric"
MAX_ROWS = 60

PROMPT = """Bạn là người chấm độc lập cho một trợ lý Text-to-SQL tiếng Việt của nhà hàng.
Chấm CÂU TRẢ LỜI (diễn giải bằng lời) theo rubric. SQL đã được xác nhận cho ra bảng đúng;
chỉ chấm phần diễn giải.

Câu hỏi: {question}
Định nghĩa chỉ số: {metric}
Thời điểm tham chiếu: {now}

Rubric:
- Số liệu: {numeric}
- Phạm vi: {scope}
- Kết luận: {conclusions}

Bảng chuẩn (reference_rows{ref_note}):
{reference}

Bảng hệ thống nhận được (produced_rows{prod_note}):
{produced}

Câu trả lời của hệ thống:
<answer>
{answer}
</answer>

Quy tắc: tên cột hiển thị khác (ví dụ "So Don Hang") không phải lỗi. Đúng khi mọi số nêu ra khớp
bảng (đúng đơn vị, làm tròn hợp lý), nêu đúng kỳ/phạm vi khi câu hỏi có kỳ, và không có nhận
xét nào không suy ra được từ bảng. Sai khi có số sai, thiếu số chính câu hỏi cần, sai kỳ, hoặc
suy diễn ngoài dữ liệu.

Trả về DUY NHẤT một dòng JSON:
{{"answer_correct": true|false, "notes": "<lý do ngắn, tiếng Việt>"}}"""


def rows_text(rows):
    rows = rows or []
    note = "" if len(rows) <= MAX_ROWS else f", chỉ hiện {MAX_ROWS}/{len(rows)} dòng đầu"
    return json.dumps(rows[:MAX_ROWS], ensure_ascii=False, default=str), note


def judge(client, question, row):
    ref, ref_note = rows_text(row.get("reference_rows"))
    prod, prod_note = rows_text(row.get("produced_rows"))
    rubric = question.get("answer_rubric") or {}
    prompt = PROMPT.format(
        question=question["question"],
        metric=question.get("metric_definition", ""),
        now=question.get("reference_time") or "2026-10-23T12:00:00+07:00",
        numeric=rubric.get("numeric_values", ""),
        scope=rubric.get("scope", ""),
        conclusions=rubric.get("conclusions", ""),
        reference=ref,
        ref_note=ref_note,
        produced=prod,
        prod_note=prod_note,
        answer=row.get("answer") or "",
    )
    for attempt in range(6):
        try:
            response = client.beta.messages.create(
                model=JUDGE_MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
                output_config={"effort": "low"},
            )
            break
        except (
            anthropic.APIConnectionError,
            anthropic.RateLimitError,
            anthropic.InternalServerError,
        ):
            time.sleep(2 * (attempt + 1))
    else:
        raise RuntimeError(f"judge failed for {row['question_id']}")
    text = "".join(b.text for b in response.content if b.type == "text")
    match = re.search(r"\{.*\}", text, re.DOTALL)
    verdict = json.loads(match.group(0))
    usage = response.usage
    cost = (usage.input_tokens * 4 + usage.output_tokens * 20) / 1e6
    return bool(verdict["answer_correct"]), str(verdict.get("notes", "")), cost


def main(results_path, questions_path, out_path):
    settings = get_settings()
    client = anthropic.Anthropic(
        api_key=settings.ai_api_key or None,
        base_url=settings.llm_base_url or None,
        max_retries=0,
    )
    questions = {}
    for line in Path(questions_path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            q = json.loads(line)
            questions[q["id"]] = q
    data = json.loads(Path(results_path).read_text(encoding="utf-8"))
    jobs, grades = [], []
    for cfg, detail in data["detail"].items():
        for row in detail["outcomes"]:
            base = {
                "config": cfg,
                "question_id": row["question_id"],
                "run_index": row["run_index"],
            }
            if row["status"] == "đúng":
                jobs.append((base, row))
            else:
                grades.append(
                    {
                        **base,
                        "answer_correct": False,
                        "reviewer": REVIEWER,
                        "notes": f"Không chấm: SQL không đạt khắt khe ({row['status']}).",
                    }
                )
    total = 0.0

    def work(job):
        base, row = job
        ok, notes, cost = judge(client, questions[row["question_id"]], row)
        return {
            **base,
            "answer_correct": ok,
            "reviewer": REVIEWER,
            "notes": notes,
        }, cost

    with ThreadPoolExecutor(max_workers=8) as pool:
        for i, (grade, cost) in enumerate(pool.map(work, jobs), 1):
            grades.append(grade)
            total += cost
            if i % 50 == 0:
                print(f"{i}/{len(jobs)} graded, {total:.2f} USD", flush=True)
    Path(out_path).write_text(json.dumps(grades, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"judged {len(jobs)}, wrote {len(grades)} grades, judge cost {total:.2f} USD")


if __name__ == "__main__":
    main(*sys.argv[1:4])
