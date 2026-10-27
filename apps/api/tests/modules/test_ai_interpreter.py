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


TWO_DAYS = [
    {"BusinessDate": "2026-10-22", "SoDon": 42},
    {"BusinessDate": "2026-10-23", "SoDon": 40},
]


@pytest.mark.anyio
async def test_the_answer_is_vietnamese_and_carries_the_scope_note(session, fake_llm):
    """FR-AI-07 and business rule 16."""
    fake_llm.reply('{"headline": "Hôm qua có 42 đơn hàng.", "highlights": [], "follow_ups": []}')

    result = await interpret(session, "hôm qua bao nhiêu đơn?", "SELECT 1", TWO_DAYS, Role.CASHIER)

    assert result.answer.headline == "Hôm qua có 42 đơn hàng."
    assert "vw_ai_thungan" in result.scope_note
    assert result.text.endswith(result.scope_note)


@pytest.mark.anyio
async def test_the_scope_note_survives_a_model_that_ignores_the_format(session, fake_llm):
    fake_llm.reply("Có 42 đơn. Phạm vi: tất cả dữ liệu.")
    result = await interpret(session, "q", "SELECT 1", TWO_DAYS, Role.CASHIER)
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


def test_a_single_day_result_is_still_a_visible_chart() -> None:
    """A one-row answer used to produce a line with no drawable segment."""
    spec = choose_chart(
        columns=["BusinessDate", "DoanhThu"],
        rows=[{"BusinessDate": "2026-10-21", "DoanhThu": 170000}],
    )

    assert spec is not None
    assert spec.type == "bar"


def test_fallback_still_reports_the_numbers_when_prose_times_out():
    """A timeout must not produce a blank answer: sum and peak stay available."""
    from app.modules.ai.pipeline.interpreter import fallback

    result = fallback(time_series_rows, Role.MANAGER)

    assert "2 ngày" in result.text
    assert "220.000" in result.text
    assert "02/09/2026" in result.text


@pytest.mark.parametrize(
    ("rows", "expected", "unexpected"),
    [
        ([{"SoPhieuNhap": 12}], "là 12.", "₫"),
        ([{"SoLuongBan": 1500}], "là 1.500.", "₫"),
        ([{"TongTienMat": 185000}], "185.000 ₫", None),
        ([{"GiaBinhQuanThang": 42000}], "42.000 ₫", None),
    ],
)
def test_fallback_only_formats_money_columns_as_currency(rows, expected, unexpected):
    """A count of receipts is not an amount of money (smoke test 26/10: "0 ₫")."""
    from app.modules.ai.pipeline.interpreter import fallback

    result = fallback(rows, Role.MANAGER)

    assert expected in result.text
    if unexpected:
        assert unexpected not in result.text


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("rows", "headline"),
    [
        ([{"SoDon": 42}], "Số đơn: 42."),
        ([{"TongTienMat": 185000}], "Tong Tien Mat: 185.000 ₫."),
        ([{"DoanhThu": None}], "Doanh thu: chưa có dữ liệu."),
        ([{"HanSuDungLo": "2026-10-30"}], "Hạn sử dụng lô: 30/10/2026."),
    ],
)
async def test_a_single_value_is_answered_without_a_model_call(session, fake_llm, rows, headline):
    """NFR-02: one cell needs no prose, so the second model call is skipped."""
    result = await interpret(session, "bao nhiêu?", "SELECT 1", rows, Role.MANAGER)

    assert fake_llm.calls == 0
    assert result.answer.headline == headline
    assert result.text.endswith(scope_note(Role.MANAGER))


def test_the_interpretation_prompt_demands_vietnamese_even_for_english_columns():
    """Smoke test 26/10: Opus 5.5 answered "Range 20/10-26/10: data for ..." in English."""
    from app.modules.ai.pipeline.interpreter import PROMPT

    assert "tiếng Việt có dấu" in PROMPT


@pytest.mark.anyio
async def test_the_prose_runs_on_the_interpretation_model_without_thinking(session):
    """NFR-02: Opus 5.5 always thinks and took ~6s for this prose; the SQL stays on Opus."""
    import json

    import httpx2

    from app.core.config import get_settings
    from app.modules.ai import llm

    sent: list[dict] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        sent.append(json.loads(request.content))
        reply = '{"headline": "Hôm qua có 42 đơn hàng.", "highlights": [], "follow_ups": []}'
        return httpx2.Response(
            200,
            json={
                "id": "msg_1",
                "type": "message",
                "role": "assistant",
                "model": sent[-1]["model"],
                "content": [{"type": "text", "text": reply}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 10, "output_tokens": 5},
            },
        )

    llm.set_client(
        llm.CommercialClient(
            api_key="k",
            model="claude-opus-5-5",
            base_url="https://api.test",
            transport=httpx2.MockTransport(handler),
        )
    )
    try:
        result = await interpret(session, "q", "SELECT 1", TWO_DAYS, Role.CASHIER)
    finally:
        llm.set_client(None)

    assert result.answer.headline == "Hôm qua có 42 đơn hàng."
    assert [body["model"] for body in sent] == [get_settings().llm_interpretation_model]
    assert sent[0]["thinking"] == {"type": "disabled"}


REVENUE_BY_DAY = [
    {"BusinessDate": "2026-10-19", "DoanhThu": 27000000},
    {"BusinessDate": "2026-10-20", "DoanhThu": 31500000},
    {"BusinessDate": "2026-10-21", "DoanhThu": 24000000},
    {"BusinessDate": "2026-10-22", "DoanhThu": 35250000},
]


@pytest.mark.anyio
async def test_the_prompt_carries_precomputed_totals_and_extremes(session, fake_llm):
    """AI grading 27/10: Haiku picked the wrong lowest day and mis-added totals, so the
    arithmetic is done in code and the model only phrases it."""
    fake_llm.reply('{"headline": "ok", "highlights": [], "follow_ups": []}')

    await interpret(session, "doanh thu từng ngày?", "SELECT 1", REVENUE_BY_DAY, Role.MANAGER)

    prompt = fake_llm.last_prompt or ""
    assert "4 dòng, từ 19/10/2026 đến 22/10/2026" in prompt
    assert "Tổng Doanh thu: 117.750.000 ₫" in prompt
    assert "Cao nhất: 35.250.000 ₫ (22/10/2026)" in prompt
    assert "Thấp nhất: 24.000.000 ₫ (21/10/2026)" in prompt
    assert "Trung bình: 29.437.500 ₫" in prompt


@pytest.mark.anyio
async def test_extremes_are_labelled_by_the_first_text_column(session, fake_llm):
    fake_llm.reply('{"headline": "ok", "highlights": [], "follow_ups": []}')
    rows = [
        {"TenMon": "Phở bò", "SoLuong": 30},
        {"TenMon": "Bún chả", "SoLuong": 12},
        {"TenMon": "Cơm rang", "SoLuong": 18},
    ]

    await interpret(session, "món bán chạy?", "SELECT 1", rows, Role.MANAGER)

    prompt = fake_llm.last_prompt or ""
    assert "Cao nhất: 30 (Phở bò)" in prompt
    assert "Thấp nhất: 12 (Bún chả)" in prompt
    assert "₫" not in prompt.split("Số liệu tính sẵn")[1]
