"""Phase 6 Task 1 — role-scoped prompt (FR-AI-05, FR-AI-06)."""

import pytest

from app.modules.ai.pipeline.prompt import build_prompt, schema_block
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
