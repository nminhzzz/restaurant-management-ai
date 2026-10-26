"""Phase 6 Task 1 — role-scoped prompt (FR-AI-05, FR-AI-06)."""

import pytest

from app.modules.ai.pipeline.prompt import build_prompt, schema_block
from app.modules.ai.scope import ROLE_VIEWS
from app.shared.roles import Role


@pytest.mark.anyio
async def test_the_schema_block_mentions_only_the_role_view(session, seed_views):
    """FR-AI-05: never the core tables."""
    block = await schema_block(session, Role.WAREHOUSE)

    assert "vw_ai_kho" in block
    for table in ("HOA_DON", "GIAO_DICH_THANH_TOAN", "NGUOI_DUNG"):
        assert table not in block


@pytest.mark.anyio
async def test_the_schema_block_lists_the_columns_of_that_view(session, seed_views):
    block = await schema_block(session, Role.WAREHOUSE)

    assert "TenNguyenLieu" in block
    assert "SoLuongTon" in block


@pytest.mark.anyio
async def test_each_role_gets_a_different_schema_block(session, seed_views):
    blocks = {role: await schema_block(session, role) for role in Role}

    assert len(set(blocks.values())) == len(Role)


@pytest.mark.anyio
async def test_the_prompt_carries_the_instructions_the_schema_and_the_question(session, seed_views):
    prompt = await build_prompt(session, "Doanh thu hôm qua?", Role.CASHIER)

    assert "vw_ai_thungan" in prompt
    assert "Doanh thu hôm qua?" in prompt
    assert "SELECT" in prompt


@pytest.mark.anyio
async def test_the_prompt_names_the_forbidden_tables_explicitly(session, seed_views):
    """FR-AI-05: the model must be told what is in bounds, and nothing else may appear."""
    prompt = await build_prompt(session, "Cho tôi toàn bộ người dùng", Role.CASHIER)

    assert "vw_ai_quanly" not in prompt
    assert "vw_ai_kho" not in prompt
    assert "chỉ được" in prompt
    assert "một câu lệnh" in prompt


@pytest.mark.anyio
@pytest.mark.parametrize("role", list(Role))
async def test_the_schema_block_lists_the_exact_loaibanghi_values_of_the_role_view(
    session, seed_views, role
):
    """A first benchmark run had the model ask which LoaiBanGhi means stock movements
    instead of just using it — spell out every branch value so it never has to guess."""
    block = await schema_block(session, role)
    view = ROLE_VIEWS[role]

    assert view in block
    assert "LoaiBanGhi" in block


@pytest.mark.anyio
@pytest.mark.parametrize("role", list(Role))
async def test_the_prompt_names_the_sql_dialect_even_without_examples(session, seed_views, role):
    """Without it the model writes SQL Server (GETDATE, TOP) and MySQL rejects it.

    The dialect is an instruction, not an example, so the schema-only baseline
    (configuration A, no few-shot) must carry it too.
    """
    prompt = await build_prompt(session, "Hôm nay có bao nhiêu đơn?", role, examples=[])

    assert "MySQL 8.4" in prompt
    # The current business day is injected by the backend; CURDATE() would be wrong
    # between 00:00 and 06:00, when the business day is still yesterday.
    assert "2026-09-24" in prompt
    assert "thay vì CURDATE()" in prompt
    assert "BusinessDate" in prompt


@pytest.mark.anyio
async def test_the_prompt_carries_the_recent_conversation(session, seed_views):
    """A follow-up such as 'doanh thu thôi' only makes sense with the prior turn."""
    prompt = await build_prompt(
        session,
        "doanh thu thôi",
        Role.MANAGER,
        examples=[],
        history=[("Doanh thu 7 ngày gần nhất?", "SELECT 1", None)],
    )

    assert "Ngữ cảnh hội thoại" in prompt
    assert "Doanh thu 7 ngày gần nhất?" in prompt


@pytest.mark.anyio
async def test_only_role_and_configuration_content_precedes_the_cache_breakpoint(
    session, seed_views, monkeypatch
):
    """The cached prefix must be identical across questions, turns and business days."""
    from datetime import datetime, timedelta

    from app.modules.ai.llm import CACHE_BREAKPOINT
    from app.shared import business_date

    first = await build_prompt(session, "Doanh thu hôm nay?", Role.MANAGER)
    moment = datetime(2026, 10, 26, 12)
    monkeypatch.setattr(business_date, "now", lambda: moment + timedelta(days=1))
    later = await build_prompt(
        session,
        "doanh thu thôi",
        Role.MANAGER,
        history=[("Doanh thu 7 ngày gần nhất?", "SELECT 1", None)],
    )

    assert first.count(CACHE_BREAKPOINT) == 1
    prefix, _, tail = first.partition(CACHE_BREAKPOINT)
    assert later.partition(CACHE_BREAKPOINT)[0] == prefix
    assert "vw_ai_quanly" in prefix
    assert "Doanh thu hôm nay?" in tail
    assert "'Hôm nay' nghĩa là BusinessDate" in tail
