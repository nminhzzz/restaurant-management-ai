"""Orchestration of one assistant turn (FR-AI-01 … FR-AI-09).

Steps: normalise → build prompt → generate → validate through the guard →
execute on the read-only account → interpret. The resulting TRUY_VAN_AI record
keeps the question, the SQL and the timings for the evaluation harness.
"""

from app.core.config import get_settings
from app.modules.ai import guard
from app.modules.ai.pipeline import generator, normalize
from app.modules.ai.schemas import ChatResponse
from app.modules.ai.scope import views_for
from app.shared.roles import Role


async def answer(question: str, role: Role) -> ChatResponse:
    """Answer one natural-language question within the caller's role scope."""
    settings = get_settings()
    normalized = normalize.normalize_question(question)
    raw_sql = await generator.generate_sql(normalized, role)
    sql = guard.validate_sql(
        raw_sql,
        allowed_views=views_for(role),
        max_rows=settings.ai_max_rows,
    )
    raise NotImplementedError(sql)
