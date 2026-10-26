"""Shared durable state for generation quotas and validated SQL caching."""

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import select

from app.modules.ai import runtime
from app.modules.ai.errors import QuotaExceeded


@pytest.mark.anyio
async def test_reservations_survive_new_store_and_rejected_call(session_factory):
    store = runtime.AiRuntimeStore(session_factory)
    day = date(2026, 9, 1)
    await store.reserve_call(day, 1)

    with pytest.raises(QuotaExceeded):
        await runtime.AiRuntimeStore(session_factory).reserve_call(day, 1)

    async with session_factory() as session:
        assert await session.scalar(select(runtime.AiDailyUsage.calls)) == 1
    await store.reserve_call(day + timedelta(days=1), 1)


@pytest.mark.anyio
async def test_quota_is_counted_per_user(session_factory):
    """FR-AI-10: one user exhausting the quota must not block another user."""
    store = runtime.AiRuntimeStore(session_factory)
    day = date(2026, 9, 1)
    await store.reserve_call(day, 1, user_id=1)
    await store.reserve_call(day, 1, user_id=2)

    with pytest.raises(QuotaExceeded):
        await store.reserve_call(day, 1, user_id=1)

    async with session_factory() as session:
        rows = (
            await session.execute(
                select(runtime.AiDailyUsage.user_id, runtime.AiDailyUsage.calls).order_by(
                    runtime.AiDailyUsage.user_id
                )
            )
        ).all()
    assert rows == [(1, 1), (2, 1)]


@pytest.mark.anyio
async def test_cached_sql_is_shared_and_expires(session_factory):
    now = datetime(2026, 9, 1, 10)
    store = runtime.AiRuntimeStore(session_factory)
    await store.put_sql("a" * 64, "SELECT 1", now, 60)
    other = runtime.AiRuntimeStore(session_factory)

    assert await other.get_sql("a" * 64, now) == "SELECT 1"
    assert await other.get_sql("a" * 64, now + timedelta(seconds=60)) is None


@pytest.mark.anyio
async def test_concurrent_workers_cannot_overspend(ai_runtime_store):
    import asyncio

    day = date(2026, 9, 1)

    async def reserve():
        store = runtime.AiRuntimeStore(ai_runtime_store.session_factory)
        try:
            await store.reserve_call(day, 3)
            return True
        except QuotaExceeded:
            return False

    outcomes = await asyncio.gather(*(reserve() for _ in range(12)))
    assert sum(outcomes) == 3
    async with ai_runtime_store.session_factory() as session:
        assert await session.scalar(select(runtime.AiDailyUsage.calls)) == 3


@pytest.mark.anyio
async def test_expiry_maintenance_is_explicit_bounded_and_keeps_fresh_rows(session_factory):
    now = datetime(2026, 9, 1, 10)
    store = runtime.AiRuntimeStore(session_factory)
    await store.put_sql("a" * 64, "SELECT 1", now, 60)
    await store.put_sql("b" * 64, "SELECT 2", now, 60)
    await store.put_sql("c" * 64, "SELECT 3", now, 600)
    later = now + timedelta(seconds=60)
    assert await store.prune_expired(later, batch_size=1) == 1
    assert await store.prune_expired(later, batch_size=1) == 1
    assert await store.prune_expired(later, batch_size=1) == 0
    assert await store.get_sql("c" * 64, later) == "SELECT 3"


@pytest.mark.anyio
async def test_runtime_store_runs_on_the_application_session(engine):
    """Regression: a session opened with `async_sessionmaker.begin()` skipped
    `BusinessDateSession.__aenter__`, so every AI question failed in `__aexit__`."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.core.database import BusinessDateSession

    factory = async_sessionmaker(engine, expire_on_commit=False, class_=BusinessDateSession)
    store = runtime.AiRuntimeStore(factory)
    day = date(2026, 9, 1)

    await store.reserve_call(day, 1)
    await store.put_sql("c" * 64, "SELECT 1", datetime(2026, 9, 1, 10), 60)

    with pytest.raises(QuotaExceeded):
        await store.reserve_call(day, 1)
    assert await store.get_sql("c" * 64, datetime(2026, 9, 1, 10)) == "SELECT 1"
