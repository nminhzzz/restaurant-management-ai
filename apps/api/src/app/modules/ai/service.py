"""Orchestration of one assistant turn (FR-AI-01 … FR-AI-09).

Steps: normalise → build prompt → generate → validate through the guard →
execute on the role's read-only account → interpret. The resulting TRUY_VAN_AI
record keeps the question, the SQL and the timings for the evaluation harness.

NFR-06 bounds the whole SQL step: at most `ai_max_sql_attempts` generations per
question, and `ai_sql_timeout_seconds` of database time per execution.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.ai.pipeline import generator, normalize
from app.modules.ai.schemas import ChatResponse
from app.shared.roles import Role


async def answer(session: AsyncSession, question: str, role: Role) -> ChatResponse:
    """Answer one natural-language question within the caller's role scope."""
    settings = get_settings()
    normalized = normalize.normalize_question(question)
    sql = await generator.generate_sql(session, normalized, role)
    raise NotImplementedError(f"{sql} ({settings.ai_max_rows})")
