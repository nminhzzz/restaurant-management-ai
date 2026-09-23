"""Step 5 — Execution of validated SQL.

Runs on the read-only database account of the asking role (NFR-06: one account
per role, each granted SELECT on that role's view only), with a statement
timeout and the row ceiling enforced by the guard. Nothing reaches the database
without passing `app.modules.ai.guard.validate_sql` first.
"""

from typing import Any

from app.shared.roles import Role


async def execute(sql: str, *, role: Role, timeout_seconds: float) -> list[dict[str, Any]]:
    """Execute validated SQL on the role's account and return the raw rows."""
    raise NotImplementedError
