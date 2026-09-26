"""Step 6 — result interpretation (FR-AI-07, FR-AI-08, FR-AI-09).

The model writes the prose, but the data-scope note is appended in code (business
rule 16): the sentence that tells the reader which view the numbers came from must not
depend on the model choosing to mention it.
"""

import asyncio
from dataclasses import dataclass
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

EMPTY_ANSWER = "Không có dữ liệu nào phù hợp với câu hỏi trong phạm vi được phép."
FALLBACK_ANSWER = "Kết quả đã được truy vấn nhưng chưa diễn giải được thành câu trả lời."

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
        answer = StructuredAnswer(headline=EMPTY_ANSWER)
        return Interpretation(answer, compose_answer(answer, note), note)

    prompt = PROMPT.format(question=question, sql=sql, count=len(rows), rows=rows[:20])
    raw = await asyncio.to_thread(llm.get_client().complete, prompt) or ""
    answer = parse_model_answer(raw)
    if not answer.headline:
        answer = StructuredAnswer(headline=FALLBACK_ANSWER)
    return Interpretation(answer, compose_answer(answer, note), note)
