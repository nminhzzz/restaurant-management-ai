"""Step 5 — execution on the asking role's read-only account (NFR-06).

The account is per role and only ever gets `SELECT` on that role's view, so a query
that slipped past the guard still cannot reach another role's data. The statement
timeout is applied as a session variable before the query runs.
"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.modules.ai.accounts import readonly_url_for
from app.shared.roles import Role


def _create_engine(url: str) -> AsyncEngine:
    """Engine factory, replaced in tests to prove which URL each role opens."""
    return create_async_engine(url, pool_pre_ping=True)


async def execute(sql: str, *, role: Role, timeout_seconds: float) -> list[dict[str, Any]]:
    """Run validated SQL on this role's account and return plain rows."""
    engine = _create_engine(readonly_url_for(role))
    try:
        async with engine.connect() as connection:
            # `timeout_seconds` comes from settings, never from the model, so the
            # interpolation cannot carry anything a caller controls.
            timeout_ms = int(timeout_seconds * 1000)
            await connection.execute(text(f"SET SESSION MAX_EXECUTION_TIME = {timeout_ms}"))
            result = await connection.execute(text(sql))
            columns = list(result.keys())
            return [dict(zip(columns, row, strict=False)) for row in result.fetchall()]
    finally:
        await engine.dispose()
