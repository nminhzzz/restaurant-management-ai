"""Phase 6 Task 4 — chart choice and result interpretation (FR-AI-07, FR-AI-08, FR-AI-09)."""

from datetime import date

import pytest

from app.modules.ai.charts import choose_chart
from app.modules.ai.pipeline.interpreter import interpret, scope_note
from app.shared.roles import Role

time_series_rows = [
    {"BusinessDate": "2026-09-01", "DoanhThu": 100000},
    {"BusinessDate": "2026-09-02", "DoanhThu": 120000},
]
ranking_rows = [
    {"TenMon": "Phở bò", "SoLuong": 30},
    {"TenMon": "Bún chả", "SoLuong": 12},
]
share_rows = [
    {"TenMon": "Phở bò", "TyTrong": 60},
    {"TenMon": "Bún chả", "TyTrong": 40},
]
plain_rows = [
    {"TenNguyenLieu": "Thịt bò", "DonViTinh": "kg"},
    {"TenNguyenLieu": "Bánh phở", "DonViTinh": "kg"},
]


def test_a_time_series_becomes_a_line_chart():
    """FR-AI-07: change over time is a line chart."""
    spec = choose_chart(columns=["BusinessDate", "DoanhThu"], rows=time_series_rows)

    assert spec is not None
    assert spec.type == "line"
    assert spec.x == "BusinessDate"
    assert spec.y == ["DoanhThu"]


def test_a_comparison_between_groups_becomes_a_bar_chart():
    spec = choose_chart(columns=["TenMon", "SoLuong"], rows=ranking_rows)

    assert spec is not None
    assert spec.type == "bar"


def test_a_share_of_a_whole_becomes_a_doughnut_chart():
    spec = choose_chart(columns=["TenMon", "TyTrong"], rows=share_rows)

    assert spec is not None
    assert spec.type == "doughnut"


def test_a_single_number_gets_no_chart():
    """FR-AI-07: nothing suitable, so the table stands alone."""
    assert choose_chart(columns=["SoDon"], rows=[{"SoDon": 42}]) is None


def test_two_columns_that_are_not_a_series_get_no_chart():
    assert choose_chart(columns=["TenNguyenLieu", "DonViTinh"], rows=plain_rows) is None


@pytest.mark.anyio
async def test_the_answer_is_vietnamese_and_carries_the_scope_note(session, fake_llm):
    """FR-AI-07 and business rule 16."""
    fake_llm.reply('{"headline": "Hôm qua có 42 đơn hàng.", "highlights": [], "follow_ups": []}')

    result = await interpret(
        session,
        "hôm qua bao nhiêu đơn?",
        "SELECT 1",
        [{"SoDon": 42}],
        Role.CASHIER,
        user_id=1,
        effective_business_date=date(2026, 9, 24),
    )

    assert result.answer.headline == "Hôm qua có 42 đơn hàng."
    assert "vw_ai_thungan" in result.scope_note
    assert result.text.endswith(result.scope_note)


@pytest.mark.anyio
async def test_the_scope_note_survives_a_model_that_ignores_the_format(session, fake_llm):
    fake_llm.reply("Có 42 đơn. Phạm vi: tất cả dữ liệu.")
    result = await interpret(
        session,
        "q",
        "SELECT 1",
        [{"SoDon": 42}],
        Role.CASHIER,
        user_id=1,
        effective_business_date=date(2026, 9, 24),
    )
    assert result.answer.headline == "Có 42 đơn. Phạm vi: tất cả dữ liệu."
    assert result.text.endswith(scope_note(Role.CASHIER))


@pytest.mark.anyio
async def test_the_scope_note_differs_per_role(session):
    assert scope_note(Role.WAREHOUSE) != scope_note(Role.MANAGER)
    assert "kho" in scope_note(Role.WAREHOUSE).lower()


@pytest.mark.anyio
async def test_an_empty_result_is_explained_not_left_blank(session, fake_llm):
    """FR-AI-09."""
    result = await interpret(
        session,
        "hôm qua bao nhiêu đơn?",
        "SELECT 1",
        [],
        Role.CASHIER,
        user_id=1,
        effective_business_date=date(2026, 9, 24),
    )
    assert "không có" in result.answer.headline.lower()
    assert fake_llm.calls == 0


@pytest.mark.anyio
async def test_interpretation_cache_expires_after_its_ttl(session, fake_llm, monkeypatch):
    from app.modules.ai.pipeline import interpreter

    now = 100.0
    monkeypatch.setattr(interpreter, "monotonic", lambda: now)
    args = (
        session,
        "hôm qua bao nhiêu đơn?",
        "SELECT 1",
        [{"SoDon": 42}],
        Role.CASHIER,
        1,
        date(2026, 9, 24),
    )

    await interpret(*args)
    assert fake_llm.calls == 1

    now += interpreter.INTERPRETATION_CACHE_TTL_SECONDS + 0.1
    await interpret(*args)

    assert fake_llm.calls == 2


@pytest.mark.anyio
async def test_interpretation_cache_evicts_the_least_recently_used_entry(
    session, fake_llm, monkeypatch
):
    from app.modules.ai.pipeline import interpreter

    monkeypatch.setattr(interpreter, "INTERPRETATION_CACHE_MAX_ENTRIES", 2)

    async def ask(question: str) -> None:
        await interpret(
            session,
            question,
            "SELECT 1",
            [{"SoDon": 42}],
            Role.CASHIER,
            user_id=1,
            effective_business_date=date(2026, 9, 24),
        )

    await ask("question one")
    await ask("question two")
    await ask("question one")  # Refresh the first entry; second is now least recent.
    await ask("question three")
    assert fake_llm.calls == 3

    await ask("question one")  # Still cached.
    assert fake_llm.calls == 3

    await ask("question two")  # Evicted entry must be interpreted again.
    assert fake_llm.calls == 4
