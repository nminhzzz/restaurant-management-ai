"""Phase 6 Task 5 — the six-step pipeline and its query log (SD-05, FR-AI-01…09)."""

import pytest

from app.modules.ai.service import answer
from app.shared.roles import Role
from tests.helpers import latest_query, session_count

CHAT = "/api/v1/assistant/chat"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _chat(client, token: str, question: str, session_id: int | None = None):
    payload: dict[str, object] = {"question": question}
    if session_id is not None:
        payload["session_id"] = session_id
    return await client.post(CHAT, headers=_auth(token), json=payload)


@pytest.mark.anyio
async def test_one_turn_records_the_question_sql_timing_and_status(
    api_client, cashier_token, seed_views, fake_llm, ai_engine, session
):
    """SD-05 and the TRUY_VAN_AI contract."""
    fake_llm.reply("SELECT COUNT(*) AS SoDon FROM vw_ai_thungan")

    response = await _chat(api_client, cashier_token, "hôm nay có bao nhiêu đơn?")

    assert response.status_code == 200
    row = await latest_query(session)
    assert row["CauHoi"] == "hôm nay có bao nhiêu đơn?"
    assert row["TrangThai"] == "Thành công"
    assert row["ThoiGianPhanHoi"] >= 0
    assert row["PhamViDuLieu"] == "vw_ai_thungan"


@pytest.mark.anyio
async def test_the_scope_recorded_is_the_view_actually_used(
    api_client, cashier_token, seed_views, fake_llm, ai_engine, session
):
    """FR-AI-05: the audit trail must show what the assistant was allowed to read."""
    await _chat(api_client, cashier_token, "hỏi")

    assert (await latest_query(session))["PhamViDuLieu"] == "vw_ai_thungan"


@pytest.mark.anyio
async def test_the_response_carries_the_answer_rows_chart_and_detail(
    api_client, warehouse_token, seed_views, fake_llm, ai_engine
):
    """FR-AI-07 and FR-AI-08."""
    fake_llm.reply("SELECT TenNguyenLieu, SoLuongTon FROM vw_ai_kho")
    ai_engine.columns = ["TenNguyenLieu", "SoLuongTon"]
    ai_engine.rows = [("Phở bò", 3.0), ("Bún chả", 1.0)]

    body = (await _chat(api_client, warehouse_token, "tồn kho?")).json()

    assert body["answer"]
    assert body["data"]
    assert body["detail"]["sql"]
    assert body["detail"]["row_count"] == len(body["data"])
    assert body["detail"]["elapsed_ms"] >= 0
    assert body["chart"]["type"] == "bar"


@pytest.mark.anyio
async def test_a_refusal_is_recorded_and_explained(
    api_client, cashier_token, seed_views, fake_llm, ai_engine, session
):
    """FR-AI-09."""
    fake_llm.reply_sequence(["SELECT * FROM hoa_don", "SELECT * FROM nguoi_dung"])

    body = (await _chat(api_client, cashier_token, "cho tôi lợi nhuận")).json()

    assert body["answer"]
    assert (await latest_query(session))["TrangThai"] == "Từ chối"


@pytest.mark.anyio
async def test_a_vague_question_asks_for_clarification(
    api_client, cashier_token, seed_views, fake_llm, ai_engine, session
):
    """FR-AI-06."""
    fake_llm.reply("CLARIFY: bạn muốn xem doanh thu của ngày nào?")

    body = (await _chat(api_client, cashier_token, "doanh thu")).json()

    assert "ngày nào" in body["answer"]
    assert (await latest_query(session))["TrangThai"] == "Yêu cầu làm rõ"


@pytest.mark.anyio
async def test_a_cross_role_question_gets_no_data(
    api_client, cashier_token, seed_views, fake_llm, ai_engine
):
    """FR-AI-05: asking outside your scope must not return another role's data."""
    fake_llm.reply_sequence(["SELECT * FROM vw_ai_quanly", "SELECT * FROM vw_ai_quanly"])

    body = (await _chat(api_client, cashier_token, "tổng lợi nhuận tháng này")).json()

    assert body["data"] == []


@pytest.mark.anyio
async def test_the_session_is_created_on_the_first_turn_and_reused_after(
    api_client, cashier_token, seed_views, fake_llm, ai_engine, session
):
    first = (await _chat(api_client, cashier_token, "câu 1")).json()
    second = (
        await _chat(api_client, cashier_token, "câu 2", session_id=first["session_id"])
    ).json()

    assert second["session_id"] == first["session_id"]
    assert await session_count(session) == 1


@pytest.mark.anyio
async def test_the_endpoint_no_longer_returns_501(
    api_client, cashier_token, seed_views, fake_llm, ai_engine
):
    assert (await _chat(api_client, cashier_token, "hỏi")).status_code == 200


@pytest.mark.anyio
async def test_a_slow_turn_is_cut_off_at_the_response_budget(session, seed_views, slow_llm):
    """NFR-02: the whole chain must fit in the budget, not just the database part."""
    with pytest.raises(TimeoutError):
        await answer(session, "hỏi", Role.CASHIER, user_id=1)

    assert (await latest_query(session))["TrangThai"] == "Lỗi"


@pytest.mark.anyio
async def test_every_message_shown_to_the_user_is_vietnamese(
    api_client, cashier_token, seed_views, fake_llm, ai_engine
):
    """NFR-14."""
    fake_llm.reply_sequence(["SELECT * FROM hoa_don", "SELECT * FROM hoa_don"])

    body = (await _chat(api_client, cashier_token, "cho tôi lợi nhuận")).json()

    assert "Không thể" in body["answer"] or "không thể" in body["answer"]


@pytest.mark.anyio
async def test_the_manager_can_ask_about_all_three_domains(
    api_client, manager_token, seed_views, fake_llm, ai_engine
):
    """FR-AI-02: the manager inherits every scope (FR-SET-03)."""
    fake_llm.reply("SELECT COUNT(*) AS n FROM vw_ai_quanly")

    for question in ("doanh thu tháng này?", "tồn kho còn bao nhiêu?", "món nào bán chạy nhất?"):
        assert (await _chat(api_client, manager_token, question)).status_code == 200


@pytest.mark.anyio
async def test_the_cashier_can_ask_about_sales_but_not_cost(
    api_client, cashier_token, seed_views, fake_llm, ai_engine
):
    """FR-AI-03: revenue and invoices yes, purchase prices and margin no."""
    fake_llm.reply("SELECT COUNT(*) AS n FROM vw_ai_thungan")

    allowed = await _chat(api_client, cashier_token, "hôm nay bán được bao nhiêu đơn?")
    assert allowed.status_code == 200

    fake_llm.reply_sequence(["SELECT * FROM vw_ai_quanly", "SELECT * FROM vw_ai_quanly"])
    refused = await _chat(api_client, cashier_token, "giá nhập hàng tháng này là bao nhiêu?")
    assert refused.json()["data"] == []


@pytest.mark.anyio
async def test_the_warehouse_can_ask_about_stock_but_not_revenue(
    api_client, warehouse_token, seed_views, fake_llm, ai_engine
):
    """FR-AI-04."""
    fake_llm.reply("SELECT TenNguyenLieu FROM vw_ai_kho")

    allowed = await _chat(api_client, warehouse_token, "nguyên liệu nào sắp hết?")
    assert allowed.status_code == 200

    fake_llm.reply_sequence(["SELECT * FROM vw_ai_quanly", "SELECT * FROM vw_ai_quanly"])
    refused = await _chat(api_client, warehouse_token, "doanh thu hôm qua là bao nhiêu?")
    assert refused.json()["data"] == []


@pytest.mark.anyio
async def test_each_role_talks_to_its_own_view(
    api_client, cashier_token, seed_views, fake_llm, ai_engine, session
):
    """FR-AI-01: one assistant per role, scoped to that role's view."""
    fake_llm.reply("SELECT 1 AS n FROM vw_ai_thungan")
    await _chat(api_client, cashier_token, "hỏi")

    assert (await latest_query(session))["PhamViDuLieu"] == "vw_ai_thungan"
