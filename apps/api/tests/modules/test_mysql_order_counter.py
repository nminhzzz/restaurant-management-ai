"""The MySQL order counter must not compete with requests for the main connection pool."""

import os
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.modules.sales.orders import next_display_code

pytestmark = pytest.mark.integration

BUSINESS_DATE = date(2099, 1, 1)


@pytest.mark.asyncio
async def test_a_request_holding_the_last_pooled_connection_still_gets_an_order_number(
    monkeypatch,
):
    url = os.environ.get("MYSQL_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set MYSQL_TEST_DATABASE_URL to a migrated, disposable MySQL database")
    if not (make_url(url).database or "").startswith("restaurant_test"):
        pytest.fail("MYSQL_TEST_DATABASE_URL must name a restaurant_test database")
    from app.core import database

    # One pooled connection stands in for a pool that every request has already drained.
    engine = create_async_engine(url, pool_size=1, max_overflow=0, pool_timeout=2)
    monkeypatch.setattr(database, "_engine", engine)
    monkeypatch.setattr(database, "_counter_engine", None)
    try:
        async with AsyncSession(engine) as session:
            await session.execute(text("SELECT 1"))
            first = await next_display_code(session, BUSINESS_DATE)
            second = await next_display_code(session, BUSINESS_DATE)
        assert (first, second) == ("ORD-010199-001", "ORD-010199-002")
    finally:
        async with engine.begin() as connection:
            await connection.execute(
                text("DELETE FROM DEM_ORDER WHERE BusinessDate = :bd"),
                {"bd": BUSINESS_DATE.isoformat()},
            )
        await engine.dispose()
        if database._counter_engine is not None:
            await database._counter_engine.dispose()
