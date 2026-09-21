"""Step 6 — Result interpretation.

Turns raw rows into a Vietnamese answer with a chart specification, always
including the source table and the scope note (FR-AI-07, business rule 16).
"""

from typing import Any

from app.shared.roles import Role


async def interpret(question: str, sql: str, rows: list[dict[str, Any]], role: Role) -> str:
    """Produce the Vietnamese answer shown to the user."""
    raise NotImplementedError
