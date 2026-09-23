"""Step 3 — SQL generation through the configured LLM.

Supports the commercial API configuration and the self-hosted Ollama fallback
(Appendix 3 configurations A/B/C), plus the daily quota and caching required by
NFR-16. NFR-06 caps this at `ai_max_sql_attempts` generations per question: the
second attempt is the retry, and there is no third.
"""

from app.shared.roles import Role


async def generate_sql(question: str, role: Role) -> str:
    """Return raw SQL text produced by the model for this question."""
    raise NotImplementedError
