"""Phase 6 Task 2 — SQL generation through the guard, with quota and cache (NFR-16)."""

import pytest

from app.core.errors import BusinessRuleError
from app.modules.ai.errors import ClarificationNeeded, QuotaExceeded
from app.modules.ai.pipeline.generator import generate_sql
from app.shared.roles import Role


@pytest.mark.anyio
async def test_generation_returns_sql_that_passed_the_guard(session, fake_llm, seed_views):
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan_order")

    sql = await generate_sql(session, "Hôm nay có bao nhiêu đơn?", Role.CASHIER)

    assert "vw_ai_thungan" in sql
    assert "LIMIT" in sql  # the guard added the ceiling


@pytest.mark.anyio
async def test_a_write_statement_is_never_returned(session, fake_llm, seed_views):
    """FR-AI-05 and NFR-06: the guard is not optional."""
    fake_llm.reply("DELETE FROM vw_ai_thungan_order")

    with pytest.raises(BusinessRuleError):
        await generate_sql(session, "xóa hết đơn đi", Role.CASHIER)


@pytest.mark.anyio
async def test_the_model_gets_a_second_attempt_after_a_bad_query(session, fake_llm, seed_views):
    """NFR-06: at most two generations per question."""
    fake_llm.reply_sequence(["SELECT * FROM hoa_don", "SELECT COUNT(*) FROM vw_ai_thungan_order"])

    sql = await generate_sql(session, "hỏi", Role.CASHIER)

    assert fake_llm.calls == 2
    assert "vw_ai_thungan" in sql


@pytest.mark.anyio
async def test_a_third_attempt_never_happens(session, fake_llm, seed_views):
    fake_llm.reply_sequence(
        [
            "SELECT * FROM hoa_don",
            "SELECT * FROM nguoi_dung",
            "SELECT 1 FROM vw_ai_thungan_order",
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
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan_order")
    await generate_sql(session, "hôm nay bao nhiêu đơn", Role.CASHIER)

    await generate_sql(session, "hôm nay bao nhiêu đơn", Role.CASHIER)

    assert fake_llm.calls == 1


@pytest.mark.anyio
async def test_the_cache_does_not_leak_across_roles(session, fake_llm, seed_views):
    """FR-AI-05: the same words asked by another role must not reuse the answer."""
    fake_llm.reply_sequence(
        ["SELECT COUNT(*) FROM vw_ai_thungan_order", "SELECT COUNT(*) FROM vw_ai_kho_ton"]
    )

    await generate_sql(session, "có bao nhiêu", Role.CASHIER)
    await generate_sql(session, "có bao nhiêu", Role.WAREHOUSE)

    assert fake_llm.calls == 2


@pytest.mark.anyio
async def test_retry_inside_one_question_uses_a_single_quota_slot(
    session, fake_llm, seed_views, monkeypatch
):
    """NFR-16: the quota counts questions, not provider attempts."""
    from app.core.config import get_settings

    monkeypatch.setenv("AI_DAILY_QUESTION_QUOTA", "1")
    get_settings.cache_clear()
    fake_llm.reply_sequence(
        ["DELETE FROM vw_ai_thungan_order", "SELECT 1 FROM vw_ai_thungan_order"]
    )

    sql = await generate_sql(session, "hỏi", Role.CASHIER)

    assert "vw_ai_thungan" in sql
    assert fake_llm.calls == 2


@pytest.mark.anyio
async def test_a_cache_hit_still_counts_as_a_question(session, fake_llm, seed_views, monkeypatch):
    """NFR-16: cache saves provider cost but the guest still asked a question."""
    from app.core.config import get_settings

    monkeypatch.setenv("AI_DAILY_QUESTION_QUOTA", "2")
    get_settings.cache_clear()
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan_order")

    await generate_sql(session, "hôm nay bao nhiêu đơn", Role.CASHIER)
    await generate_sql(session, "hôm nay bao nhiêu đơn", Role.CASHIER)
    assert fake_llm.calls == 1

    with pytest.raises(QuotaExceeded):
        await generate_sql(session, "hôm nay bao nhiêu đơn", Role.CASHIER)


@pytest.mark.anyio
async def test_cache_changes_with_model_and_business_day(
    session, fake_llm, seed_views, monkeypatch
):
    from datetime import timedelta

    from app.core.config import get_settings
    from app.shared import business_date

    fake_llm.reply("SELECT 1 FROM vw_ai_thungan_order")
    await generate_sql(session, "hỏi", Role.CASHIER)
    monkeypatch.setenv("LLM_MODEL", "another-model")
    get_settings.cache_clear()
    await generate_sql(session, "hỏi", Role.CASHIER)
    now = business_date.now()
    monkeypatch.setattr(business_date, "now", lambda: now + timedelta(days=1))
    await generate_sql(session, "hỏi", Role.CASHIER)
    assert fake_llm.calls == 3


@pytest.mark.anyio
async def test_cache_expires_and_provider_and_limits_invalidate_it(
    session, fake_llm, seed_views, monkeypatch
):
    from datetime import timedelta

    from app.core.config import get_settings
    from app.shared import business_date

    fake_llm.reply("SELECT 1 FROM vw_ai_thungan_order")
    await generate_sql(session, "hỏi", Role.CASHIER)
    now = business_date.now()
    monkeypatch.setattr(business_date, "now", lambda: now + timedelta(seconds=301))
    await generate_sql(session, "hỏi", Role.CASHIER)
    monkeypatch.setenv("AI_PROVIDER", "fake")
    get_settings.cache_clear()
    await generate_sql(session, "hỏi", Role.CASHIER)
    monkeypatch.setenv("AI_MAX_ROWS", "20")
    get_settings.cache_clear()
    sql = await generate_sql(session, "hỏi", Role.CASHIER)
    assert fake_llm.calls == 4
    assert "LIMIT 20" in sql


@pytest.mark.anyio
async def test_cache_is_revalidated_and_corrupt_sql_never_returned(
    session, fake_llm, seed_views, ai_runtime_store
):
    from sqlalchemy import update

    from app.modules.ai.runtime_models import AiSqlCache

    fake_llm.reply("SELECT 1 FROM vw_ai_thungan_order")
    await generate_sql(session, "hỏi", Role.CASHIER)
    async with ai_runtime_store.session_factory.begin() as state_session:
        await state_session.execute(
            update(AiSqlCache).values(sql_text="DELETE FROM vw_ai_thungan_order")
        )
    sql = await generate_sql(session, "hỏi", Role.CASHIER)
    assert sql.startswith("SELECT")
    assert fake_llm.calls == 2


@pytest.mark.anyio
async def test_failed_turn_usage_survives_request_rollback(
    session, fake_llm, seed_views, ai_runtime_store
):
    from sqlalchemy import select

    from app.modules.ai.runtime_models import AiDailyUsage

    fake_llm.reply("DELETE FROM vw_ai_thungan_order")
    with pytest.raises(BusinessRuleError):
        await generate_sql(session, "hỏi", Role.CASHIER)
    await session.rollback()
    async with ai_runtime_store.session_factory() as state_session:
        # One question was asked even though both SQL attempts were rejected.
        assert await state_session.scalar(select(AiDailyUsage.calls)) == 1


@pytest.mark.anyio
async def test_view_schema_change_invalidates_cache(session, fake_llm, seed_views):
    from sqlalchemy import text

    fake_llm.reply("SELECT 1 FROM vw_ai_thungan_order")
    await generate_sql(session, "hỏi", Role.CASHIER)
    await session.execute(text("DROP VIEW vw_ai_thungan_order"))
    await session.execute(text("CREATE VIEW vw_ai_thungan_order AS SELECT 1 AS NewColumn"))
    await generate_sql(session, "hỏi", Role.CASHIER)
    assert fake_llm.calls == 2


@pytest.mark.anyio
async def test_provider_failure_keeps_committed_reservation(
    session, fake_llm, seed_views, ai_runtime_store, monkeypatch
):
    from sqlalchemy import select

    from app.modules.ai.runtime_models import AiDailyUsage

    def unavailable(prompt):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(fake_llm, "complete", unavailable)
    with pytest.raises(RuntimeError, match="provider unavailable"):
        await generate_sql(session, "hỏi", Role.CASHIER)
    await session.rollback()
    async with ai_runtime_store.session_factory() as state_session:
        assert await state_session.scalar(select(AiDailyUsage.calls)) == 1


@pytest.mark.anyio
async def test_generation_prompt_includes_the_session_history(session, fake_llm, seed_views):
    """Follow-ups are resolved from prior turns instead of asking again."""
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan_order")

    await generate_sql(
        session,
        "từng ngày trong tháng",
        Role.CASHIER,
        history=[("Doanh thu 7 ngày gần nhất?", "SELECT 1", None)],
    )

    assert "Doanh thu 7 ngày gần nhất?" in (fake_llm.last_prompt or "")
    assert "Ngữ cảnh hội thoại" in (fake_llm.last_prompt or "")
