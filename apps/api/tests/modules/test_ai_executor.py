"""Phase 6 Task 3 — execution on the role's read-only account (FR-AI-05, NFR-06)."""

import pytest

from app.core.config import get_settings
from app.modules.ai.pipeline.executor import execute
from app.shared.roles import Role


@pytest.mark.anyio
async def test_the_query_runs_on_the_account_of_the_asking_role(fake_engine_factory, readonly_urls):
    """NFR-06: never a shared read-only account."""
    await execute("SELECT 1", role=Role.WAREHOUSE, timeout_seconds=3.0)

    assert fake_engine_factory.urls == [get_settings().ai_readonly_url_warehouse]


@pytest.mark.anyio
async def test_the_statement_timeout_is_applied(fake_engine_factory, readonly_urls):
    """NFR-06: at most three seconds on the database."""
    await execute("SELECT 1", role=Role.MANAGER, timeout_seconds=3.0)

    assert "MAX_EXECUTION_TIME" in fake_engine_factory.executed[0]
    assert "3000" in fake_engine_factory.executed[0]


@pytest.mark.anyio
async def test_rows_come_back_as_plain_dicts(fake_engine_factory, readonly_urls):
    fake_engine_factory.rows = [(1, "Phở bò")]

    rows = await execute("SELECT * FROM vw_ai_kho", role=Role.WAREHOUSE, timeout_seconds=3.0)

    assert rows == [{"MaNguyenLieu": 1, "TenNguyenLieu": "Phở bò"}]


@pytest.mark.anyio
async def test_the_account_is_never_reused_across_roles(fake_engine_factory, readonly_urls):
    await execute("SELECT 1", role=Role.CASHIER, timeout_seconds=3.0)
    await execute("SELECT 1", role=Role.WAREHOUSE, timeout_seconds=3.0)

    assert len(set(fake_engine_factory.urls)) == 2


@pytest.mark.anyio
async def test_the_engine_is_disposed_even_when_the_query_fails(fake_engine_factory, readonly_urls):
    fake_engine_factory.error = RuntimeError("hỏng")

    with pytest.raises(RuntimeError):
        await execute("SELECT 1", role=Role.MANAGER, timeout_seconds=3.0)

    assert fake_engine_factory.disposed == 1
