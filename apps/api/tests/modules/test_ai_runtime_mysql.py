"""MySQL atomic reservations shared by independent AI worker stores."""

import asyncio
import os
from datetime import date

import pytest
from sqlalchemy import delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.modules.ai.errors import QuotaExceeded
from app.modules.ai.runtime import AiRuntimeStore
from app.modules.ai.runtime_models import AiDailyUsage

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_mysql_independent_workers_reserve_exact_daily_quota(mysql_engine_factory):
    url = os.environ.get("MYSQL_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set MYSQL_TEST_DATABASE_URL to a migrated, disposable MySQL database")
    database = make_url(url).database or ""
    if not database.startswith(("restaurant_test", "restaurant_acceptance")):
        pytest.fail("MYSQL_TEST_DATABASE_URL must name a restaurant_test/acceptance database")
    engine = mysql_engine_factory(url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    day = date(2099, 1, 1)
    quota = 3
    stores = (AiRuntimeStore(factory), AiRuntimeStore(factory))

    async def reserve(worker):
        try:
            await stores[worker % 2].reserve_call(day, quota)
            return True
        except QuotaExceeded:
            return False

    try:
        async with factory.begin() as session:
            await session.execute(delete(AiDailyUsage).where(AiDailyUsage.business_date == day))
        results = await asyncio.gather(*(reserve(worker) for worker in range(16)))
        assert sum(results) == quota
        # Creating a replacement store simulates another worker/restart; reservations
        # are already committed and may not be refunded or reset by that instance.
        replacement = AiRuntimeStore(factory)
        with pytest.raises(QuotaExceeded):
            await replacement.reserve_call(day, quota)
        async with factory() as session:
            row = await session.scalar(
                select(AiDailyUsage.calls).where(AiDailyUsage.business_date == day)
            )
            assert row == quota
    finally:
        async with factory.begin() as session:
            await session.execute(delete(AiDailyUsage).where(AiDailyUsage.business_date == day))
        await engine.dispose()


@pytest.mark.asyncio
async def test_mysql_concurrent_cache_writes_do_not_hold_expiry_range_locks(
    mysql_engine_factory,
):
    """Synchronize writers at the old delete/insert boundary to expose gap deadlocks."""
    from datetime import datetime
    from uuid import uuid4

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql.dml import Delete, Insert

    from app.modules.ai.runtime_models import AiSqlCache

    url = os.environ.get("MYSQL_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set MYSQL_TEST_DATABASE_URL to a migrated, disposable MySQL database")
    database = make_url(url).database or ""
    if not database.startswith(("restaurant_test", "restaurant_acceptance")):
        pytest.fail("MYSQL_TEST_DATABASE_URL must name a restaurant_test/acceptance database")
    engine = mysql_engine_factory(url)
    barrier = asyncio.Barrier(2)
    keys = (uuid4().hex * 2, uuid4().hex * 2)
    # Pick an empty expiry range below ordinary data without clearing anyone's rows.
    now = datetime(1000, 1, 1)

    class SynchronizedSession(AsyncSession):
        async def execute(self, statement, *args, **kwargs):
            if not self.info.get("synchronized"):
                self.info["synchronized"] = True
                if isinstance(statement, Delete):
                    result = await super().execute(statement, *args, **kwargs)
                    await asyncio.wait_for(barrier.wait(), timeout=10)
                    return result
                if isinstance(statement, Insert):
                    await asyncio.wait_for(barrier.wait(), timeout=10)
            return await super().execute(statement, *args, **kwargs)

    factory = async_sessionmaker(engine, class_=SynchronizedSession, expire_on_commit=False)
    cleanup_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        stores = (AiRuntimeStore(factory), AiRuntimeStore(factory))
        results = await asyncio.gather(
            *(
                store.put_sql(key, "SELECT 1", now, 60)
                for store, key in zip(stores, keys, strict=True)
            ),
            return_exceptions=True,
        )
        assert results == [None, None]
        async with cleanup_factory() as session:
            assert set(
                await session.scalars(select(AiSqlCache.key).where(AiSqlCache.key.in_(keys)))
            ) == set(keys)
    finally:
        async with cleanup_factory.begin() as session:
            await session.execute(delete(AiSqlCache).where(AiSqlCache.key.in_(keys)))
        await engine.dispose()
