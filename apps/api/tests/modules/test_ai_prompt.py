"""Phase 6 Task 1 — role-scoped prompt (FR-AI-05, FR-AI-06)."""

import pytest

from app.modules.ai.pipeline.prompt import VIEW_LOAIBANGHI_VALUES, build_prompt, schema_block
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

    for value in VIEW_LOAIBANGHI_VALUES[view]:
        assert value in block


@pytest.mark.anyio
@pytest.mark.parametrize("role", list(Role))
async def test_the_prompt_names_the_sql_dialect_even_without_examples(session, seed_views, role):
    """Without it the model writes SQL Server (GETDATE, TOP) and MySQL rejects it.

    The dialect is an instruction, not an example, so the schema-only baseline
    (configuration A, no few-shot) must carry it too.
    """
    prompt = await build_prompt(session, "Hôm nay có bao nhiêu đơn?", role, examples=[])

    assert "MySQL 8.4" in prompt
    assert "CURDATE()" in prompt
    assert "BusinessDate" in prompt
