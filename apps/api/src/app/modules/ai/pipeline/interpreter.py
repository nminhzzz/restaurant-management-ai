"""Step 6 — result interpretation (FR-AI-07, FR-AI-08, FR-AI-09).

The model writes the prose, but the data-scope note is appended in code (business
rule 16): the sentence that tells the reader which view the numbers came from must not
depend on the model choosing to mention it.
"""

import asyncio
import hashlib
import json
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date
from time import monotonic
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai import llm
from app.modules.ai.pipeline.answer_format import (
    StructuredAnswer,
    compose_answer,
    parse_model_answer,
)
from app.modules.ai.pipeline.generator import cache_context_key, is_volatile_question
from app.modules.ai.pipeline.prompt import ROLE_SCOPE_NOTE
from app.modules.ai.scope import ROLE_VIEWS
from app.shared.roles import Role

EMPTY_ANSWER = "Không có dữ liệu nào phù hợp với câu hỏi trong phạm vi được phép."
FALLBACK_ANSWER = "Kết quả đã được truy vấn nhưng chưa diễn giải được thành câu trả lời."
INTERPRETATION_CACHE_TTL_SECONDS = 30.0
INTERPRETATION_CACHE_MAX_ENTRIES = 256

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


_InterpretationKey = tuple[object, ...]
_interpretation_cache: OrderedDict[_InterpretationKey, tuple[Interpretation, float]] = OrderedDict()


def reset_state() -> None:
    """Clear the process-local interpretation cache (used between tests)."""
    _interpretation_cache.clear()


def _rows_digest(rows: list[dict[str, Any]]) -> str:
    encoded = json.dumps(
        rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _cached_interpretation(key: _InterpretationKey) -> Interpretation | None:
    entry = _interpretation_cache.get(key)
    if entry is None:
        return None
    interpretation, expires_at = entry
    if expires_at <= monotonic():
        del _interpretation_cache[key]
        return None
    _interpretation_cache.move_to_end(key)
    return interpretation


def _store_interpretation(key: _InterpretationKey, interpretation: Interpretation) -> None:
    if INTERPRETATION_CACHE_TTL_SECONDS <= 0 or INTERPRETATION_CACHE_MAX_ENTRIES <= 0:
        return
    now = monotonic()
    for expired_key, (_, expires_at) in list(_interpretation_cache.items()):
        if expires_at <= now:
            del _interpretation_cache[expired_key]
    _interpretation_cache[key] = (interpretation, now + INTERPRETATION_CACHE_TTL_SECONDS)
    _interpretation_cache.move_to_end(key)
    while len(_interpretation_cache) > INTERPRETATION_CACHE_MAX_ENTRIES:
        _interpretation_cache.popitem(last=False)


async def interpret(
    session: AsyncSession,
    question: str,
    sql: str,
    rows: list[dict[str, Any]],
    role: Role,
    user_id: int,
    effective_business_date: date,
) -> Interpretation:
    """A structured Vietnamese answer; the scope note is always appended by code."""
    note = scope_note(role)
    if not rows:
        answer = StructuredAnswer(headline=EMPTY_ANSWER)
        return Interpretation(answer, compose_answer(answer, note), note)

    volatile = is_volatile_question(question)
    key = (
        *cache_context_key(user_id, question, role, effective_business_date),
        sql,
        _rows_digest(rows),
    )
    if not volatile:
        cached = _cached_interpretation(key)
        if cached is not None:
            return cached

    prompt = PROMPT.format(question=question, sql=sql, count=len(rows), rows=rows[:20])
    raw = await asyncio.to_thread(llm.get_client().complete, prompt) or ""
    answer = parse_model_answer(raw)
    if not answer.headline:
        answer = StructuredAnswer(headline=FALLBACK_ANSWER)
    interpretation = Interpretation(answer, compose_answer(answer, note), note)
    if not volatile:
        _store_interpretation(key, interpretation)
    return interpretation
