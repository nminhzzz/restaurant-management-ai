"""Durable SQL cache and atomic generation reservations in short transactions.

The factory is independent of the request session: rollbacks, cancellation, or a
worker restart cannot refund a provider call that has already been reserved.
"""

import asyncio
from datetime import UTC, date, datetime, timedelta
from typing import cast

from sqlalchemy import CursorResult, delete, select, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql.dml import Insert

from app.core.database import get_engine, get_session_factory, session_scope
from app.modules.ai.errors import QuotaExceeded
from app.modules.ai.runtime_models import AiDailyUsage, AiSqlCache
from app.shared import business_date


class AiRuntimeStore:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def reserve_call(self, day: date, quota: int, user_id: int = 0) -> None:
        """Commit one reservation only when this user's daily counter is below quota."""
        async with session_scope(self.session_factory) as session:
            insert_day: Insert
            dialect = session.get_bind().dialect.name
            if dialect == "mysql":
                statement = mysql_insert(AiDailyUsage).values(
                    business_date=day, user_id=user_id, calls=0
                )
                insert_day = statement.on_duplicate_key_update(SoLanGoi=AiDailyUsage.calls)
            elif dialect == "sqlite":  # SQLite is used exclusively by unit tests.
                insert_day = (
                    sqlite_insert(AiDailyUsage)
                    .values(business_date=day, user_id=user_id, calls=0)
                    .on_conflict_do_nothing()
                )
            else:
                raise RuntimeError("AI runtime state requires MySQL")
            await session.execute(insert_day)
            result = await session.execute(
                update(AiDailyUsage)
                .where(
                    AiDailyUsage.business_date == day,
                    AiDailyUsage.user_id == user_id,
                    AiDailyUsage.calls < quota,
                )
                .values(calls=AiDailyUsage.calls + 1)
            )
            if cast(CursorResult, result).rowcount != 1:
                raise QuotaExceeded(
                    "Đã đạt hạn mức câu hỏi trong ngày. Vui lòng thử lại vào ngày mai."
                )

    async def get_sql(self, key: str, now: datetime) -> str | None:
        async with self.session_factory() as session:
            cached = await session.get(AiSqlCache, key)
            if cached is None or cached.expires_at <= now:
                return None
            return cached.sql_text

    async def put_sql(self, key: str, sql: str, now: datetime, ttl_seconds: int) -> None:
        # Do not mix expiry range deletes with inserts: InnoDB REPEATABLE READ
        # gap locks can deadlock otherwise independent writers on an empty range.
        async with session_scope(self.session_factory) as session:
            values = {
                "KhoaCache": key,
                "CauSQL": sql,
                "HetHanLuc": now + timedelta(seconds=ttl_seconds),
            }
            upsert: Insert
            dialect = session.get_bind().dialect.name
            if dialect == "mysql":
                statement = mysql_insert(AiSqlCache).values(values)
                upsert = statement.on_duplicate_key_update(
                    CauSQL=statement.inserted.CauSQL,
                    HetHanLuc=statement.inserted.HetHanLuc,
                )
            elif dialect == "sqlite":
                sqlite_statement = sqlite_insert(AiSqlCache).values(values)
                upsert = sqlite_statement.on_conflict_do_update(
                    index_elements=[AiSqlCache.key],
                    set_={
                        "CauSQL": sqlite_statement.excluded.CauSQL,
                        "HetHanLuc": sqlite_statement.excluded.HetHanLuc,
                    },
                )
            else:
                raise RuntimeError("AI runtime state requires MySQL")
            await session.execute(upsert)

    async def prune_expired(self, now: datetime, batch_size: int = 100) -> int:
        """Remove a bounded batch outside requests; never lock the expiry range.

        The first transaction is a consistent read. The second deletes sorted
        primary keys individually and rechecks expiry to preserve refreshed entries.
        Run periodically via `python -m app.modules.ai.runtime`.
        """
        if not 1 <= batch_size <= 1000:
            raise ValueError("Cache pruning batch size must be between 1 and 1000")
        async with self.session_factory() as session:
            keys = list(
                await session.scalars(
                    select(AiSqlCache.key)
                    .where(AiSqlCache.expires_at <= now)
                    .order_by(AiSqlCache.key)
                    .limit(batch_size)
                )
            )
        removed = 0
        async with session_scope(self.session_factory) as session:
            for key in keys:
                result = await session.execute(
                    delete(AiSqlCache).where(AiSqlCache.key == key, AiSqlCache.expires_at <= now)
                )
                removed += cast(CursorResult, result).rowcount
        return removed


def get_runtime_store() -> AiRuntimeStore:
    return AiRuntimeStore(get_session_factory())


async def _prune_cache() -> None:
    """Command-line maintenance; intentionally separate from paid request writes."""
    now = business_date.now().astimezone(UTC).replace(tzinfo=None)
    removed = 0
    store = get_runtime_store()
    try:
        while count := await store.prune_expired(now):
            removed += count
        print(f"Đã xóa {removed} mục SQL hết hạn.")
    finally:
        await get_engine().dispose()


if __name__ == "__main__":
    asyncio.run(_prune_cache())
