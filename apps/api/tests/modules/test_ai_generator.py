"""Phase 6 Task 2 — SQL generation through the guard, with quota and cache (NFR-16)."""

import pytest

from app.core.errors import BusinessRuleError
from app.modules.ai.errors import ClarificationNeeded, QuotaExceeded
from app.modules.ai.pipeline.generator import generate_sql
from app.shared.roles import Role


@pytest.mark.anyio
async def test_generation_returns_sql_that_passed_the_guard(session, fake_llm, seed_views):
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan")

    sql = await generate_sql(session, "Hôm nay có bao nhiêu đơn?", Role.CASHIER)

    assert "vw_ai_thungan" in sql
    assert "LIMIT" in sql  # the guard added the ceiling


@pytest.mark.anyio
async def test_a_write_statement_is_never_returned(session, fake_llm, seed_views):
    """FR-AI-05 and NFR-06: the guard is not optional."""
    fake_llm.reply("DELETE FROM vw_ai_thungan")

    with pytest.raises(BusinessRuleError):
        await generate_sql(session, "xóa hết đơn đi", Role.CASHIER)


@pytest.mark.anyio
async def test_the_model_gets_a_second_attempt_after_a_bad_query(session, fake_llm, seed_views):
    """NFR-06: at most two generations per question."""
    fake_llm.reply_sequence(["SELECT * FROM hoa_don", "SELECT COUNT(*) FROM vw_ai_thungan"])

    sql = await generate_sql(session, "hỏi", Role.CASHIER)

    assert fake_llm.calls == 2
    assert "vw_ai_thungan" in sql


@pytest.mark.anyio
async def test_a_third_attempt_never_happens(session, fake_llm, seed_views):
    fake_llm.reply_sequence(
        [
            "SELECT * FROM hoa_don",
            "SELECT * FROM nguoi_dung",
            "SELECT 1 FROM vw_ai_thungan",
        ]
    )

    with pytest.raises(BusinessRuleError):
        await generate_sql(session, "hỏi", Role.CASHIER)

    assert fake_llm.calls == 2


@pytest.mark.anyio
async def test_an_out_of_scope_question_asks_for_clarification(session, fake_llm, seed_views):
    """FR-AI-06."""
    fake_llm.reply("CLARIFY: bạn muốn xem doanh thu của ngày nào?")

    with pytest.raises(ClarificationNeeded):
        await generate_sql(session, "doanh thu", Role.CASHIER)


@pytest.mark.anyio
async def test_the_daily_quota_stops_further_calls(session, seed_views, quota_reached):
    """NFR-16."""
    with pytest.raises(QuotaExceeded):
        await generate_sql(session, "hỏi", Role.CASHIER)

    assert quota_reached.calls == 0


@pytest.mark.anyio
async def test_a_repeated_question_is_served_from_cache(session, fake_llm, seed_views):
    """NFR-16."""
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan")
    await generate_sql(session, "hôm nay bao nhiêu đơn", Role.CASHIER)

    await generate_sql(session, "hôm nay bao nhiêu đơn", Role.CASHIER)

    assert fake_llm.calls == 1


@pytest.mark.anyio
async def test_the_cache_does_not_leak_across_roles(session, fake_llm, seed_views):
    """FR-AI-05: the same words asked by another role must not reuse the answer."""
    fake_llm.reply_sequence(
        ["SELECT COUNT(*) FROM vw_ai_thungan", "SELECT COUNT(*) FROM vw_ai_kho"]
    )

    await generate_sql(session, "có bao nhiêu", Role.CASHIER)
    await generate_sql(session, "có bao nhiêu", Role.WAREHOUSE)

    assert fake_llm.calls == 2
