"""Step 3 — SQL generation through the configured LLM.

Every candidate goes straight through `guard.validate_sql`; a rejected candidate costs
one of the `ai_max_sql_attempts` (two) generations, and running out raises. The cache
key includes the role, because the same words asked by another role must never reuse
an answer produced under a different scope (FR-AI-05).

Daily quota and cache are process-local on purpose: NFR-16 asks for cost control, not
for durable accounting, and keeping them here avoids a table the report never mentions.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import BusinessRuleError
from app.modules.ai import guard, llm
from app.modules.ai.errors import ClarificationNeeded, QuotaExceeded
from app.modules.ai.pipeline.normalize import normalize_question
from app.modules.ai.pipeline.prompt import build_prompt
from app.modules.ai.scope import views_for
from app.shared import business_date
from app.shared.roles import Role

CLARIFY_PREFIX = "CLARIFY:"

_cache: dict[tuple[str, str], str] = {}
_daily_calls: dict[str, int] = {}


def reset_state() -> None:
    """Clear the cache and the quota counter (used between tests)."""
    _cache.clear()
    _daily_calls.clear()


def set_daily_calls(day: str, count: int) -> None:
    _daily_calls[day] = count


def _today() -> str:
    return business_date.business_date_of(business_date.now()).isoformat()


def _enforce_quota() -> None:
    if _daily_calls.get(_today(), 0) >= get_settings().ai_daily_question_quota:
        raise QuotaExceeded("Đã đạt hạn mức câu hỏi trong ngày. Vui lòng thử lại vào ngày mai.")


def _charge_quota() -> None:
    day = _today()
    _daily_calls[day] = _daily_calls.get(day, 0) + 1


async def generate_sql(session: AsyncSession, question: str, role: Role) -> str:
    """Validated SQL for this question, or a raised signal for the orchestrator."""
    settings = get_settings()
    normalized = normalize_question(question)
    cache_key = (role.value, normalized)
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    _enforce_quota()
    client = llm.get_client()
    allowed = views_for(role)
    last_error: BusinessRuleError | None = None

    for _ in range(settings.ai_max_sql_attempts):
        _charge_quota()
        prompt = await build_prompt(session, normalized, role)
        if last_error is not None:
            prompt += f"\n\nLần trước câu SQL chưa hợp lệ: {last_error}. Hãy sửa lại."
        raw = client.complete(prompt) or ""
        text = raw.strip()

        if text.upper().startswith(CLARIFY_PREFIX):
            raise ClarificationNeeded(text[len(CLARIFY_PREFIX) :].strip())

        try:
            sql = guard.validate_sql(
                text,
                allowed_views=allowed,
                max_rows=settings.ai_max_rows,
            )
        except BusinessRuleError as exc:
            last_error = exc
            continue

        _cache[cache_key] = sql
        return sql

    raise BusinessRuleError(guard.SQL_REJECTED_MESSAGE)
