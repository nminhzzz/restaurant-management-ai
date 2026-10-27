"""Async SQLAlchemy engine and session plumbing.

Models stay in their module packages; this module only owns the connection.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Self

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.shared.base import Base
from app.shared.business_date import business_date_schedule, load_business_date_schedule

_engine: AsyncEngine | None = None
_counter_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


class BusinessDateSession(AsyncSession):
    """Install a private cutoff snapshot for HTTP requests, workers and seed runs."""

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        try:
            changes = await load_business_date_schedule(self)
            # The snapshot read is separate from the caller's business transaction.
            await self.rollback()
        except BaseException:
            await self.close()
            raise
        self._business_date_context = business_date_schedule(changes)
        self._business_date_context.__enter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        try:
            await super().__aexit__(*args)
        finally:
            self._business_date_context.__exit__(*args)


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    return _engine


def get_counter_engine() -> AsyncEngine:
    """A separate small pool for the self-committing order-number bump.

    The request claiming a number already holds a connection from the main pool. Taking
    the second one from that same pool deadlocks once every pooled connection belongs to
    a request waiting for another (seen at 20 VU in the 2026-10-27 performance run).
    """
    global _counter_engine
    if _counter_engine is None:
        _counter_engine = create_async_engine(
            get_engine().url, pool_pre_ping=True, pool_size=2, max_overflow=3
        )
    return _counter_engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(), class_=BusinessDateSession, expire_on_commit=False
        )
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    async with get_session_factory()() as session:
        yield session


@asynccontextmanager
async def session_scope(factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    """Open a session and a committing transaction through `__aenter__`.

    `async_sessionmaker.begin()` yields the session without entering it, so
    `BusinessDateSession` never installs the cutoff snapshot and its `__aexit__`
    fails. Short-lived background transactions must use this instead.
    """
    async with factory() as session, session.begin():
        yield session


__all__ = [
    "Base",
    "get_counter_engine",
    "get_engine",
    "get_session",
    "get_session_factory",
    "session_scope",
]
