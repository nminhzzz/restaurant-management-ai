"""Phase 6 Task 2 — SQL generation through the guard, with quota and cache (NFR-16)."""

from datetime import date, timedelta

import pytest

from app.core.errors import BusinessRuleError
from app.modules.ai.errors import ClarificationNeeded
from app.modules.ai.guard import OutOfScopeError
from app.modules.ai.pipeline import generator, prompt
from app.modules.ai.pipeline.generator import AttemptBudget, generate_sql
from app.shared.roles import Role


@pytest.mark.anyio
async def test_generation_returns_sql_that_passed_the_guard(session, fake_llm, seed_views):
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan")

    sql = await generate_sql(
        session, "Hôm nay có bao nhiêu đơn?", Role.CASHIER, 1, date(2026, 9, 24)
    )

    assert "vw_ai_thungan" in sql
    assert "LIMIT" in sql  # the guard added the ceiling


@pytest.mark.anyio
async def test_generation_passes_the_effective_business_date_to_the_prompt(
    session, fake_llm, seed_views
):
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan")
    effective_business_date = date(2026, 9, 24)

    await generate_sql(
        session,
        "Hôm qua có bao nhiêu đơn?",
        Role.CASHIER,
        1,
        effective_business_date,
    )

    assert "BusinessDate = '2026-09-24'" in (fake_llm.last_prompt or "")
    assert "06:00" not in (fake_llm.last_prompt or "")
    assert "CURDATE()" not in (fake_llm.last_prompt or "")
    assert "CURRENT_DATE" not in (fake_llm.last_prompt or "")


@pytest.mark.anyio
async def test_a_write_statement_is_never_returned(session, fake_llm, seed_views):
    """FR-AI-05 and NFR-06: the guard is not optional."""
    fake_llm.reply("DELETE FROM vw_ai_thungan")

    with pytest.raises(BusinessRuleError):
        await generate_sql(session, "xóa hết đơn đi", Role.CASHIER, 1, date(2026, 9, 24))


@pytest.mark.anyio
async def test_the_model_gets_a_second_attempt_after_a_bad_query(session, fake_llm, seed_views):
    """NFR-06: at most two generations per question."""
    fake_llm.reply_sequence(
        ["SELECT ThanhTien FROM vw_ai_thungan", "SELECT COUNT(*) FROM vw_ai_thungan"]
    )

    sql = await generate_sql(session, "hỏi", Role.CASHIER, 1, date(2026, 9, 24))

    assert fake_llm.calls == 2
    assert "vw_ai_thungan" in sql


@pytest.mark.anyio
async def test_a_third_attempt_never_happens(session, fake_llm, seed_views):
    fake_llm.reply_sequence(
        [
            "SELECT ThanhTien FROM vw_ai_thungan",
            "SELECT * FROM vw_ai_thungan -- note",
            "SELECT 1 FROM vw_ai_thungan",
        ]
    )

    with pytest.raises(BusinessRuleError):
        await generate_sql(session, "hỏi", Role.CASHIER, 1, date(2026, 9, 24))

    assert fake_llm.calls == 2


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("role", "reply"),
    [
        (Role.CASHIER, "SELECT * FROM hoa_don"),
        (Role.CASHIER, "SELECT * FROM vw_ai_quanly"),
        (Role.CASHIER, "WITH nguoi_dung AS (SELECT * FROM nguoi_dung) SELECT * FROM nguoi_dung"),
        (Role.WAREHOUSE, "SELECT TongTien FROM vw_ai_kho"),
        (Role.CASHIER, "DELETE FROM vw_ai_thungan"),
    ],
)
async def test_a_request_beyond_the_callers_scope_ends_without_a_second_generation(
    session, fake_llm, seed_views, role, reply
):
    """Report §4.1.3: an out-of-scope request ends at once; only malformed SQL is retried."""
    fake_llm.reply_sequence([reply, "SELECT COUNT(*) FROM vw_ai_thungan"])

    with pytest.raises(OutOfScopeError):
        await generate_sql(session, "hỏi", role, 1, date(2026, 9, 24))

    assert fake_llm.calls == 1


@pytest.mark.anyio
async def test_a_shared_budget_is_spent_across_generations(session, fake_llm, seed_views):
    budget = AttemptBudget(1)
    fake_llm.reply("SELECT ThanhTien FROM vw_ai_thungan")

    with pytest.raises(BusinessRuleError):
        await generate_sql(session, "hỏi", Role.CASHIER, 1, date(2026, 9, 24), budget=budget)
    with pytest.raises(BusinessRuleError):
        await generate_sql(session, "hỏi", Role.CASHIER, 1, date(2026, 9, 24), budget=budget)

    assert fake_llm.calls == 1
    assert budget.remaining == 0


@pytest.mark.anyio
async def test_database_feedback_skips_the_cache_and_reaches_the_prompt(
    session, fake_llm, seed_views
):
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan")
    await generate_sql(session, "đếm đơn", Role.CASHIER, 1, date(2026, 9, 24))

    await generate_sql(
        session, "đếm đơn", Role.CASHIER, 1, date(2026, 9, 24), feedback="Unknown column 'x'"
    )

    assert fake_llm.calls == 2
    assert "Unknown column 'x'" in (fake_llm.last_prompt or "")


@pytest.mark.anyio
async def test_an_out_of_scope_question_asks_for_clarification(session, fake_llm, seed_views):
    """FR-AI-06."""
    fake_llm.reply("CLARIFY: bạn muốn xem doanh thu của ngày nào?")

    with pytest.raises(ClarificationNeeded):
        await generate_sql(session, "doanh thu", Role.CASHIER, 1, date(2026, 9, 24))


@pytest.mark.anyio
async def test_a_repeated_question_is_served_from_cache(session, fake_llm, seed_views):
    """NFR-16."""
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan")
    await generate_sql(session, "hôm nay bao nhiêu đơn", Role.CASHIER, 1, date(2026, 9, 24))

    await generate_sql(session, "hôm nay bao nhiêu đơn", Role.CASHIER, 1, date(2026, 9, 24))

    assert fake_llm.calls == 1


@pytest.mark.anyio
async def test_the_cache_does_not_leak_across_roles(session, fake_llm, seed_views):
    """FR-AI-05: the same words asked by another role must not reuse the answer."""
    fake_llm.reply_sequence(
        ["SELECT COUNT(*) FROM vw_ai_thungan", "SELECT COUNT(*) FROM vw_ai_kho"]
    )

    await generate_sql(session, "có bao nhiêu", Role.CASHIER, 1, date(2026, 9, 24))
    await generate_sql(session, "có bao nhiêu", Role.WAREHOUSE, 1, date(2026, 9, 24))

    assert fake_llm.calls == 2


@pytest.mark.anyio
async def test_sql_cache_is_scoped_to_user_role_date_temporal_meaning_and_permission(
    session, fake_llm, seed_views, monkeypatch
):
    today = date(2026, 9, 24)
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan")
    args = (session, "doanh thu hôm nay", Role.CASHIER)

    await generate_sql(*args, user_id=1, effective_business_date=today)
    await generate_sql(*args, user_id=1, effective_business_date=today)
    await generate_sql(*args, user_id=2, effective_business_date=today)
    await generate_sql(*args, user_id=1, effective_business_date=today + timedelta(days=1))
    await generate_sql(session, "doanh thu hôm qua", Role.CASHIER, 1, today)
    monkeypatch.setitem(prompt.ROLE_SCOPE_NOTE, Role.CASHIER, "phạm vi quyền mới")
    await generate_sql(*args, user_id=1, effective_business_date=today)

    assert fake_llm.calls == 5


@pytest.mark.anyio
async def test_sql_cache_key_includes_the_current_allowed_view_fingerprint(
    session, fake_llm, seed_views, monkeypatch
):
    fake_llm.reply_sequence(
        ["SELECT COUNT(*) FROM vw_ai_thungan", "SELECT COUNT(*) FROM vw_ai_quanly"]
    )
    await generate_sql(session, "đếm đơn", Role.CASHIER, 1, date(2026, 9, 24))
    changed = lambda role: frozenset({"vw_ai_quanly"})  # noqa: E731
    monkeypatch.setattr(generator, "views_for", changed)
    monkeypatch.setattr(generator.guard, "views_for", changed)
    await generate_sql(session, "đếm đơn", Role.CASHIER, 1, date(2026, 9, 24))

    assert fake_llm.calls == 2


@pytest.mark.anyio
async def test_sql_cache_expires_and_evicts_oldest_entries(
    session, fake_llm, seed_views, monkeypatch
):
    now = [0.0]
    monkeypatch.setattr(generator, "SQL_CACHE_TTL_SECONDS", 5, raising=False)
    monkeypatch.setattr(generator, "SQL_CACHE_MAX_ENTRIES", 1, raising=False)
    monkeypatch.setattr(generator, "monotonic", lambda: now[0], raising=False)
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan")
    bd = date(2026, 9, 24)

    await generate_sql(session, "câu một", Role.CASHIER, 1, bd)
    await generate_sql(session, "câu hai", Role.CASHIER, 1, bd)
    await generate_sql(session, "câu một", Role.CASHIER, 1, bd)
    now[0] = 10.0
    await generate_sql(session, "câu một", Role.CASHIER, 1, bd)

    assert fake_llm.calls == 4


@pytest.mark.anyio
async def test_cached_sql_is_revalidated_before_it_can_be_reused(
    session, fake_llm, seed_views, monkeypatch
):
    original_validate = generator.guard.validate_sql
    validations = 0

    def validate(sql, **kwargs):
        nonlocal validations
        validations += 1
        if validations == 2:
            raise BusinessRuleError("permission scope changed")
        return original_validate(sql, **kwargs)

    monkeypatch.setattr(generator.guard, "validate_sql", validate)
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan")
    bd = date(2026, 9, 24)
    await generate_sql(session, "đếm đơn", Role.CASHIER, 1, bd)
    await generate_sql(session, "đếm đơn", Role.CASHIER, 1, bd)

    assert validations == 3
    assert fake_llm.calls == 2


@pytest.mark.anyio
@pytest.mark.parametrize(
    "question",
    [
        "nguyên liệu tồn kho còn bao nhiêu?",
        "món nào đang giữ chỗ?",
        "còn phục vụ được bao nhiêu suất?",
    ],
)
async def test_sql_cache_bypasses_volatile_questions(session, fake_llm, seed_views, question):
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_kho")
    args = (session, question, Role.WAREHOUSE, 3, date(2026, 9, 24))

    await generate_sql(*args)
    await generate_sql(*args)

    assert fake_llm.calls == 2
