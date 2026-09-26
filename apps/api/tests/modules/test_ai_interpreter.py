"""Phase 6 Task 4 — chart choice and result interpretation (FR-AI-07, FR-AI-08, FR-AI-09)."""

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
        session, "hôm qua bao nhiêu đơn?", "SELECT 1", [{"SoDon": 42}], Role.CASHIER
    )

    assert result.answer.headline == "Hôm qua có 42 đơn hàng."
    assert "vw_ai_thungan" in result.scope_note
    assert result.text.endswith(result.scope_note)


@pytest.mark.anyio
async def test_the_scope_note_survives_a_model_that_ignores_the_format(session, fake_llm):
    fake_llm.reply("Có 42 đơn. Phạm vi: tất cả dữ liệu.")
    result = await interpret(session, "q", "SELECT 1", [{"SoDon": 42}], Role.CASHIER)
    assert result.answer.headline == "Có 42 đơn. Phạm vi: tất cả dữ liệu."
    assert result.text.endswith(scope_note(Role.CASHIER))


@pytest.mark.anyio
async def test_the_scope_note_differs_per_role(session):
    assert scope_note(Role.WAREHOUSE) != scope_note(Role.MANAGER)
    assert "kho" in scope_note(Role.WAREHOUSE).lower()


@pytest.mark.anyio
async def test_an_empty_result_is_explained_not_left_blank(session, fake_llm):
    """FR-AI-09."""
    result = await interpret(session, "hôm qua bao nhiêu đơn?", "SELECT 1", [], Role.CASHIER)
    assert "không có" in result.answer.headline.lower()
    assert fake_llm.calls == 0
