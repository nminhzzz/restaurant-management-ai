"""Phase 6 Task 3 — execution on the role's read-only account (FR-AI-05, NFR-06)."""

import pytest

from app.core.config import get_settings
from app.modules.ai.guard import ValidatedSql, validate_for_role
from app.modules.ai.pipeline.executor import execute
from app.shared.roles import Role

_VIEWS = {
    Role.MANAGER: "vw_ai_quanly",
    Role.CASHIER: "vw_ai_thungan",
    Role.WAREHOUSE: "vw_ai_kho",
}


def valid(role: Role, sql: str | None = None) -> ValidatedSql:
    """SQL the way production gets it: through the guard."""
    return validate_for_role(sql or f"SELECT LoaiBanGhi FROM {_VIEWS[role]}", role, max_rows=500)


@pytest.mark.anyio
async def test_the_query_runs_on_the_account_of_the_asking_role(fake_engine_factory, readonly_urls):
    """NFR-06: never a shared read-only account."""
    await execute(valid(Role.WAREHOUSE), role=Role.WAREHOUSE, timeout_seconds=3.0)

    assert fake_engine_factory.urls == [get_settings().ai_readonly_url_warehouse]


@pytest.mark.anyio
async def test_the_statement_timeout_is_applied(fake_engine_factory, readonly_urls):
    """NFR-06: at most three seconds on the database."""
    await execute(valid(Role.MANAGER), role=Role.MANAGER, timeout_seconds=3.0)

    assert "MAX_EXECUTION_TIME" in fake_engine_factory.executed[0]
    assert "3000" in fake_engine_factory.executed[0]


@pytest.mark.anyio
async def test_rows_come_back_as_plain_dicts(fake_engine_factory, readonly_urls):
    fake_engine_factory.rows = [(1, "Phở bò")]

    rows = await execute(valid(Role.WAREHOUSE), role=Role.WAREHOUSE, timeout_seconds=3.0)

    assert rows == [{"MaNguyenLieu": 1, "TenNguyenLieu": "Phở bò"}]


@pytest.mark.anyio
async def test_the_account_is_never_reused_across_roles(fake_engine_factory, readonly_urls):
    await execute(valid(Role.CASHIER), role=Role.CASHIER, timeout_seconds=3.0)
    await execute(valid(Role.WAREHOUSE), role=Role.WAREHOUSE, timeout_seconds=3.0)

    assert len(set(fake_engine_factory.urls)) == 2


@pytest.mark.anyio
async def test_the_engine_is_disposed_even_when_the_query_fails(fake_engine_factory, readonly_urls):
    fake_engine_factory.error = RuntimeError("hỏng")

    with pytest.raises(RuntimeError):
        await execute(valid(Role.MANAGER), role=Role.MANAGER, timeout_seconds=3.0)

    assert fake_engine_factory.disposed == 1


@pytest.mark.anyio
async def test_text_that_skipped_the_guard_is_never_executed(fake_engine_factory, readonly_urls):
    """The "only via validate_sql" rule is structural: a plain string cannot be run."""
    with pytest.raises(TypeError):
        await execute("SELECT 1", role=Role.MANAGER, timeout_seconds=3.0)

    assert fake_engine_factory.urls == []
    assert fake_engine_factory.executed == []


def test_validated_sql_cannot_be_forged_by_a_caller() -> None:
    with pytest.raises(TypeError):
        ValidatedSql("SELECT 1", issuer=object())
    with pytest.raises(TypeError):
        ValidatedSql("SELECT 1")  # type: ignore[call-arg]
