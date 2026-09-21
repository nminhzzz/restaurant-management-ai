"""Step 5 — Execution of validated SQL.

Runs on a read-only database account against the role's view, with a statement
timeout and the row ceiling enforced by the guard. Nothing reaches the database
without passing `app.modules.ai.guard.validate_sql` first.
"""

from typing import Any


async def execute(sql: str, *, timeout_seconds: float) -> list[dict[str, Any]]:
    """Execute validated SQL and return the raw rows."""
    raise NotImplementedError
