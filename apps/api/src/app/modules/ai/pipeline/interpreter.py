"""Step 6 — result interpretation (FR-AI-07, FR-AI-08, FR-AI-09).

The model writes the prose, but the data-scope note is appended in code (business
rule 16): the sentence that tells the reader which view the numbers came from must not
depend on the model choosing to mention it.
"""

import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai import llm
from app.modules.ai.pipeline.prompt import ROLE_SCOPE_NOTE
from app.modules.ai.scope import ROLE_VIEWS
from app.shared.roles import Role

EMPTY_ANSWER = "Không có dữ liệu nào phù hợp với câu hỏi trong phạm vi được phép."
FALLBACK_ANSWER = "Kết quả đã được truy vấn nhưng chưa diễn giải được thành câu trả lời."


def scope_note(role: Role) -> str:
    """Which view answered, and what that view is allowed to contain."""
    return f"Phạm vi dữ liệu: {ROLE_VIEWS[role]} — {ROLE_SCOPE_NOTE[role]}."


async def interpret(
    session: AsyncSession,
    question: str,
    sql: str,
    rows: list[dict[str, Any]],
    role: Role,
) -> str:
    """A Vietnamese answer, always followed by the scope note."""
    note = scope_note(role)
    if not rows:
        return f"{EMPTY_ANSWER} {note}"

    prompt = (
        "Bạn là trợ lý dữ liệu của một nhà hàng. Viết một câu trả lời ngắn gọn, "
        "bằng tiếng Việt, chỉ dựa trên kết quả truy vấn dưới đây.\n"
        f"Câu hỏi: {question}\n"
        f"Câu SQL đã chạy: {sql}\n"
        f"Kết quả ({len(rows)} dòng, hiển thị tối đa 20): {rows[:20]}"
    )
    text = (await asyncio.to_thread(llm.get_client().complete, prompt) or "").strip()
    if not text:
        text = FALLBACK_ANSWER
    return f"{text}\n\n{note}"
