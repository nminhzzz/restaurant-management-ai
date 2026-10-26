"""Step 6 — result interpretation (FR-AI-07, FR-AI-08, FR-AI-09).

The model writes the prose, but the data-scope note is appended in code (business
rule 16): the sentence that tells the reader which view the numbers came from must not
depend on the model choosing to mention it.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai import llm
from app.modules.ai.pipeline.answer_format import (
    StructuredAnswer,
    compose_answer,
    parse_model_answer,
)
from app.modules.ai.pipeline.prompt import ROLE_SCOPE_NOTE
from app.modules.ai.scope import ROLE_VIEWS
from app.shared.roles import Role

EMPTY_ANSWER = "Truy vấn hợp lệ nhưng không có dòng dữ liệu nào thỏa điều kiện của câu hỏi."

PROMPT = (
    "Bạn là trợ lý dữ liệu của một nhà hàng. Chỉ dựa trên kết quả truy vấn dưới đây, "
    "trả về đúng MỘT đối tượng JSON, không kèm chữ nào khác:\n"
    '{{"headline": "một câu kết luận", "highlights": ["2 đến 4 ý, mỗi ý một câu có số liệu"], '
    '"follow_ups": ["tối đa 3 câu hỏi tiếp theo về dữ liệu"]}}\n'
    "Viết tiếng Việt. Tiền viết dạng 185.000 ₫. Ngày viết dạng dd/mm/yyyy. "
    "Không nhắc tới SQL, tên bảng hay tên cột.\n"
    "Câu hỏi: {question}\n"
    "Câu SQL đã chạy: {sql}\n"
    "Kết quả ({count} dòng, hiển thị tối đa 20): {rows}"
)


def scope_note(role: Role) -> str:
    """Which view answered, and what that view is allowed to contain."""
    return f"Phạm vi dữ liệu: {ROLE_VIEWS[role]} — {ROLE_SCOPE_NOTE[role]}."


@dataclass(frozen=True)
class Interpretation:
    answer: StructuredAnswer
    text: str
    scope_note: str


FALLBACK_LABELS = {
    "DoanhThu": "doanh thu",
    "TongTien": "tổng tiền",
    "SoTien": "số tiền",
    "SoDon": "số đơn",
    "SoLuong": "số lượng",
    "SoHoaDon": "số hóa đơn",
}


def _is_number(value: Any) -> bool:
    if value is None or isinstance(value, bool):
        return False
    try:
        float(str(value))
    except (TypeError, ValueError):
        return False
    return True


def _money(value: float) -> str:
    return f"{value:,.0f} ₫".replace(",", ".")


def _day(value: Any) -> str:
    text = str(value)[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return text


def fallback(rows: list[dict[str, Any]], role: Role) -> Interpretation:
    """A truthful, numeric answer when the model cannot finish in time (NFR-02).

    The SQL and rows are already correct. Instead of "chưa diễn giải được", sum the
    main numeric column and point at the peak day, so the turn still answers.
    """
    note = scope_note(role)
    if not rows:
        answer = StructuredAnswer(headline=EMPTY_ANSWER)
        return Interpretation(answer, compose_answer(answer, note), note)

    columns = list(rows[0])
    numeric = [column for column in columns if all(_is_number(row.get(column)) for row in rows)]

    def looks_like_date(value: Any) -> bool:
        if isinstance(value, (date, datetime)):
            return True
        text = str(value)
        return len(text) >= 10 and text[4] == "-" and text[7] == "-"

    date_column = next(
        (column for column in columns if all(looks_like_date(row.get(column)) for row in rows)),
        None,
    )
    headlines: list[str] = []
    highlights: list[str] = []
    if numeric:
        key = numeric[-1]
        label = FALLBACK_LABELS.get(key, key)
        values = [float(row[key]) for row in rows]
        total = sum(values)
        if date_column is not None:
            peak = max(rows, key=lambda row: float(row[key]))
            headlines.append(f"{len(rows)} ngày có dữ liệu; tổng {label} là {_money(total)}.")
            highlights.append(f"Tổng {label}: {_money(total)}.")
            highlights.append(
                f"Cao nhất: {_money(float(peak[key]))} vào {_day(peak[date_column])}."
            )
            highlights.append(f"Trung bình mỗi ngày: {_money(total / len(rows))}.")
        else:
            headlines.append(f"{len(rows)} dòng dữ liệu; tổng {label} là {_money(total)}.")
            highlights.append(f"Tổng {label}: {_money(total)}.")
            highlights.append(f"Trung bình mỗi dòng: {_money(total / len(rows))}.")
            if len(values) > 1:
                highlights.append(f"Cao nhất: {_money(max(values))}.")
                highlights.append(f"Thấp nhất: {_money(min(values))}.")
    else:
        headlines.append(f"Có {len(rows)} dòng dữ liệu thỏa câu hỏi.")

    answer = StructuredAnswer(headline=" ".join(headlines), highlights=highlights[:4])
    return Interpretation(answer, compose_answer(answer, note), note)


async def interpret(
    session: AsyncSession,
    question: str,
    sql: str,
    rows: list[dict[str, Any]],
    role: Role,
) -> Interpretation:
    """A structured Vietnamese answer; the scope note is always appended by code."""
    note = scope_note(role)
    if not rows:
        return fallback(rows, role)

    prompt = PROMPT.format(question=question, sql=sql, count=len(rows), rows=rows[:20])
    # Interpretation stays at configuration B's effort even under configuration C.
    with llm.generation_options(reasoning_effort="low"):
        raw = await llm.complete_async(llm.get_client(), prompt) or ""
    answer = parse_model_answer(raw)
    if not answer.headline:
        # The model returned prose we cannot parse; keep the numeric summary instead.
        return fallback(rows, role)
    return Interpretation(answer, compose_answer(answer, note), note)
