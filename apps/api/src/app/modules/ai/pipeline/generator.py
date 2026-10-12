"""Step 3 — SQL generation through the configured LLM.

Every candidate goes straight through `guard.validate_sql`; a rejected candidate costs
one of the `ai_max_sql_attempts` (two) generations, and running out raises. The cache
key includes the role, because the same words asked by another role must never reuse
an answer produced under a different scope (FR-AI-05).

The quota is reserved and persisted by the orchestration service before this module runs.
The SQL cache remains process-local and role-scoped.
"""

import asyncio
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import BusinessRuleError
from app.modules.ai import guard, llm
from app.modules.ai.errors import ClarificationNeeded
from app.modules.ai.pipeline.normalize import normalize_question
from app.modules.ai.pipeline.prompt import build_prompt
from app.modules.ai.scope import views_for
from app.shared.roles import Role

CLARIFY_PREFIX = "CLARIFY:"

_cache: dict[tuple[str, str], str] = {}


def reset_state() -> None:
    """Clear the process-local SQL cache (used between tests)."""
    _cache.clear()


async def generate_sql(
    session: AsyncSession,
    question: str,
    role: Role,
    user_id: int,
    effective_business_date: date,
) -> str:
    """Validated SQL for this question, or a raised signal for the orchestrator."""
    settings = get_settings()
    normalized = normalize_question(question)
    cache_key = (role.value, normalized)
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    client = llm.get_client()
    allowed = views_for(role)
    last_error: BusinessRuleError | None = None

    for _ in range(settings.ai_max_sql_attempts):
        prompt = await build_prompt(session, normalized, role)
        if last_error is not None:
            prompt += f"\n\nLần trước câu SQL chưa hợp lệ: {last_error}. Hãy sửa lại."
        raw = await asyncio.to_thread(client.complete, prompt) or ""
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
