"""Phase 6 Task 5 — the six-step pipeline and its query log (SD-05, FR-AI-01…09)."""

import asyncio
from datetime import date, datetime, time

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.core.errors import NotFoundError
from app.modules.ai.errors import ClarificationNeeded
from app.modules.ai.models import AssistantQuery, ChatSession
from app.modules.ai.pipeline import generator, interpreter
from app.modules.ai.service import (
    ERROR_ANSWER,
    INTERRUPTED_ANSWER,
    REFUSED_ANSWER,
    SCOPE_REFUSED_ANSWER,
    TIMEOUT_ANSWER,
    answer,
    list_sessions,
    session_detail,
)
from app.modules.settings.models import SystemConfig
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
    """NFR-02: the whole chain must fit in the budget, not just the database part.

    Running out of time is an answer the user can act on, not a server error.
    """
    response = await answer(session, "hỏi", Role.CASHIER, user_id=1)

    assert response.answer == TIMEOUT_ANSWER
    assert (await latest_query(session))["TrangThai"] == "Lỗi"


@pytest.mark.anyio
async def test_every_message_shown_to_the_user_is_vietnamese(
    api_client, cashier_token, seed_views, fake_llm, ai_engine
):
    """NFR-14."""
    fake_llm.reply_sequence(["SELECT * FROM hoa_don", "SELECT * FROM hoa_don"])

    body = (await _chat(api_client, cashier_token, "cho tôi lợi nhuận")).json()

    assert body["answer"] in {SCOPE_REFUSED_ANSWER, REFUSED_ANSWER}


@pytest.mark.anyio
async def test_quota_is_per_user_and_a_question_is_reserved_once(
    session, seed_views, fake_llm, ai_engine, monkeypatch
):
    config = (await session.execute(select(SystemConfig))).scalar_one()
    config.ai_daily_question_quota = 1
    await session.commit()
    fake_llm.reply_sequence(
        [
            "SELECT COUNT(*) AS SoDon FROM vw_ai_thungan",
            '{"headline": "Có đơn.", "highlights": [], "follow_ups": []}',
            "SELECT COUNT(*) AS SoDon FROM vw_ai_thungan",
            '{"headline": "Có đơn.", "highlights": [], "follow_ups": []}',
        ]
    )

    first = await answer(session, "hỏi A", Role.CASHIER, user_id=2)
    calls_after_first = fake_llm.calls
    rejected = await answer(session, "hỏi B", Role.CASHIER, user_id=2)
    other_user = await answer(session, "hỏi C", Role.CASHIER, user_id=3)

    assert first.kind == "answer"
    assert rejected.kind == "refused"
    assert other_user.kind == "answer"
    assert fake_llm.calls == calls_after_first + 2
    assert (await session.execute(select(func.count(AssistantQuery.id)))).scalar_one() == 2


@pytest.mark.anyio
async def test_sql_retries_consume_one_question_quota_slot(
    session, seed_views, fake_llm, ai_engine
):
    config = (await session.execute(select(SystemConfig))).scalar_one()
    config.ai_daily_question_quota = 1
    await session.commit()
    fake_llm.reply_sequence(
        [
            "SELECT ThanhTien FROM vw_ai_thungan",
            "SELECT COUNT(*) AS SoDon FROM vw_ai_thungan",
            '{"headline": "Có đơn.", "highlights": [], "follow_ups": []}',
        ]
    )

    response = await answer(session, "hỏi", Role.CASHIER, user_id=2)
    rejected = await answer(session, "hỏi thêm", Role.CASHIER, user_id=2)

    assert response.kind == "answer"
    assert rejected.kind == "refused"
    assert fake_llm.calls == 3
    assert (await session.execute(select(func.count(AssistantQuery.id)))).scalar_one() == 1


@pytest.mark.anyio
async def test_a_quota_row_keeps_its_business_date_after_the_cutoff_changes(
    session, seed_views, fake_llm, ai_engine, monkeypatch
):
    config = (await session.execute(select(SystemConfig))).scalar_one()
    config.ai_daily_question_quota = 1
    config.business_day_start = time(6)
    await session.commit()
    now = datetime(2026, 9, 25, 5, 0)
    monkeypatch.setattr("app.modules.ai.service.business_date.now", lambda: now)
    fake_llm.reply_sequence(
        [
            "SELECT COUNT(*) AS SoDon FROM vw_ai_thungan",
            '{"headline": "Có đơn.", "highlights": [], "follow_ups": []}',
            "SELECT COUNT(*) AS SoDon FROM vw_ai_thungan",
            '{"headline": "Có đơn.", "highlights": [], "follow_ups": []}',
        ]
    )

    first = await answer(session, "câu hỏi trước mốc", Role.CASHIER, user_id=2)
    config.business_day_start = time(4)
    await session.commit()
    second = await answer(session, "câu hỏi sau đổi mốc", Role.CASHIER, user_id=2)
    dates = (
        (await session.execute(select(AssistantQuery.business_date).order_by(AssistantQuery.id)))
        .scalars()
        .all()
    )

    assert first.kind == second.kind == "answer"
    assert dates == [datetime(2026, 9, 24).date(), datetime(2026, 9, 25).date()]


@pytest.mark.anyio
async def test_an_abandoned_pending_question_is_visible_as_interrupted(session):
    chat = ChatSession(user_id=2, role_id="CASHIER")
    session.add(chat)
    await session.flush()
    query = AssistantQuery(
        session_id=chat.id,
        scope="vw_ai_thungan",
        question="câu bị ngắt",
        sql_text=None,
        business_date=datetime(2026, 9, 24).date(),
        status="Đang xử lý",
        summary=None,
        latency_ms=None,
    )
    session.add(query)
    await session.commit()

    detail = await session_detail(session, user_id=2, role=Role.CASHIER, session_id=chat.id)

    assert detail.turns[0].status == "Bị gián đoạn"
    assert detail.turns[0].headline == INTERRUPTED_ANSWER


@pytest.mark.anyio
async def test_concurrent_same_user_questions_cannot_both_take_last_slot(
    session, session_factory, seed_views, monkeypatch
):
    config = (await session.execute(select(SystemConfig))).scalar_one()
    config.ai_daily_question_quota = 1
    await session.commit()
    model_started = asyncio.Event()
    release_model = asyncio.Event()
    calls = 0

    async def blocked_generation(*args, **kwargs):
        nonlocal calls
        calls += 1
        model_started.set()
        await release_model.wait()
        raise ClarificationNeeded("Bạn muốn xem ngày nào?")

    monkeypatch.setattr(generator, "generate_sql", blocked_generation)

    async with session_factory() as first_session, session_factory() as second_session:
        first_task = asyncio.create_task(
            answer(first_session, "câu thứ nhất", Role.CASHIER, user_id=2)
        )
        await model_started.wait()
        second = await answer(second_session, "câu thứ hai", Role.CASHIER, user_id=2)
        release_model.set()
        first = await first_task

        assert first.kind == "clarify"
        assert second.kind == "refused"
        assert calls == 1


@pytest.mark.anyio
async def test_interpretation_cache_requires_fresh_result_digest_and_user_scope(session, fake_llm):
    fake_llm.reply_sequence(
        [
            '{"headline": "Hai đơn.", "highlights": [], "follow_ups": []}',
            '{"headline": "Ba đơn.", "highlights": [], "follow_ups": []}',
            '{"headline": "Hai đơn.", "highlights": [], "follow_ups": []}',
        ]
    )
    rows = [{"SoDon": 2}]
    common = (session, "đếm đơn hôm nay", "SELECT COUNT(*) FROM vw_ai_thungan")
    date_value = date(2026, 9, 24)

    first = await interpreter.interpret(
        *common, rows, Role.CASHIER, user_id=2, effective_business_date=date_value
    )
    reused = await interpreter.interpret(
        *common, rows, Role.CASHIER, user_id=2, effective_business_date=date_value
    )
    changed_rows = await interpreter.interpret(
        *common,
        [{"SoDon": 3}],
        Role.CASHIER,
        user_id=2,
        effective_business_date=date_value,
    )
    other_user = await interpreter.interpret(
        *common, rows, Role.CASHIER, user_id=3, effective_business_date=date_value
    )

    assert first.text == reused.text
    assert changed_rows.answer.headline == "Ba đơn."
    assert other_user.answer.headline == "Hai đơn."
    assert fake_llm.calls == 3


@pytest.mark.anyio
@pytest.mark.parametrize(
    "question",
    [
        "nguyên liệu tồn kho còn bao nhiêu?",
        "món nào đang giữ chỗ?",
        "còn phục vụ được bao nhiêu suất?",
    ],
)
async def test_interpretation_cache_bypasses_volatile_questions(session, fake_llm, question):
    fake_llm.reply('{"headline": "Còn 5 kg.", "highlights": [], "follow_ups": []}')
    common = (
        session,
        question,
        "SELECT SoLuongTon FROM vw_ai_kho",
        [{"SoLuongTon": 5}],
        Role.WAREHOUSE,
    )
    context = {"user_id": 3, "effective_business_date": date(2026, 9, 24)}

    await interpreter.interpret(*common, **context)
    await interpreter.interpret(*common, **context)

    assert fake_llm.calls == 2


@pytest.mark.anyio
async def test_sql_cache_still_executes_the_read_query_for_every_question(
    session, seed_views, fake_llm, ai_engine
):
    fake_llm.reply_sequence(
        [
            "SELECT COUNT(*) AS SoDon FROM vw_ai_thungan",
            '{"headline": "Có đơn.", "highlights": [], "follow_ups": []}',
        ]
    )

    await answer(session, "hôm nay có bao nhiêu đơn?", Role.CASHIER, user_id=2)
    await answer(session, "hôm nay có bao nhiêu đơn?", Role.CASHIER, user_id=2)

    assert sum(statement.startswith("SELECT") for statement in ai_engine.executed) == 2
    assert fake_llm.calls == 2


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


@pytest.mark.anyio
async def test_a_successful_turn_returns_the_structured_fields(
    api_client, cashier_token, seed_views, fake_llm, ai_engine, session
):
    fake_llm.reply_sequence(
        [
            "SELECT COUNT(*) AS SoDon FROM vw_ai_thungan",
            '{"headline": "Có 2 đơn.", "highlights": ["Cả hai đã thanh toán."], '
            '"follow_ups": ["Doanh thu hôm nay?"]}',
        ]
    )

    body = (await _chat(api_client, cashier_token, "hôm nay có bao nhiêu đơn?")).json()

    assert body["kind"] == "answer"
    assert body["headline"] == "Có 2 đơn."
    assert body["highlights"] == ["Cả hai đã thanh toán."]
    assert body["follow_ups"] == ["Doanh thu hôm nay?"]
    assert "vw_ai_thungan" in body["scope_note"]
    assert body["columns"] == [{"key": "SoDon", "label": "Số đơn", "kind": "number"}]
    assert body["answer"].startswith("Có 2 đơn.\n- Cả hai đã thanh toán.")


@pytest.mark.anyio
async def test_a_refused_turn_says_so_in_kind(
    api_client, cashier_token, seed_views, fake_llm, ai_engine, session
):
    fake_llm.reply("DELETE FROM vw_ai_thungan")
    body = (await _chat(api_client, cashier_token, "xoá hết đơn")).json()
    assert body["kind"] == "refused"
    assert body["headline"] == body["answer"]
    assert body["scope_note"] is None


def _db_error(kind: type[Exception] = ProgrammingError) -> Exception:
    return kind("SELECT broken", {}, Exception("Unknown column 'ThanhTien' in 'field list'"))


@pytest.mark.anyio
async def test_a_database_error_earns_one_regeneration_that_can_succeed(
    session, seed_views, fake_llm, ai_engine
):
    """Report §4.1.3: syntax/execution errors are regenerated once, in the same scope."""
    fake_llm.reply_sequence(
        [
            "SELECT COUNT(*) AS SoDon FROM vw_ai_thungan",
            "SELECT COUNT(*) AS SoDon FROM vw_ai_thungan WHERE LoaiBanGhi = 'ORDER'",
            '{"headline": "Có đơn.", "highlights": [], "follow_ups": []}',
        ]
    )
    ai_engine.errors = [_db_error()]

    response = await answer(session, "hỏi", Role.CASHIER, user_id=2)

    assert response.kind == "answer"
    assert fake_llm.calls == 3  # generation, one regeneration, interpretation
    row = await latest_query(session)
    assert row["TrangThai"] == "Thành công"
    assert "LoaiBanGhi" in row["CauSQLSinhRa"]


@pytest.mark.anyio
async def test_a_second_database_error_ends_the_turn_with_a_trace_code(
    session, seed_views, fake_llm, ai_engine
):
    fake_llm.reply_sequence(
        ["SELECT COUNT(*) FROM vw_ai_thungan", "SELECT COUNT(1) FROM vw_ai_thungan"]
    )
    ai_engine.errors = [_db_error(), _db_error(OperationalError)]

    response = await answer(session, "hỏi", Role.CASHIER, user_id=2)

    row = await latest_query(session)
    assert response.kind == "error"
    assert response.answer.startswith(ERROR_ANSWER)
    assert f"Mã truy vết: {row['MaTruyVan']}" in response.answer
    assert SCOPE_REFUSED_ANSWER not in response.answer
    assert row["TrangThai"] == "Lỗi"
    assert row["KetQuaTomTat"] != SCOPE_REFUSED_ANSWER
    assert fake_llm.calls == 2  # NFR-06: never a third generation


@pytest.mark.anyio
async def test_a_request_beyond_the_role_is_refused_at_once_with_the_scope_message(
    session, seed_views, fake_llm, ai_engine
):
    fake_llm.reply_sequence(["SELECT * FROM hoa_don", "SELECT COUNT(*) FROM vw_ai_thungan"])

    response = await answer(session, "cho tôi lợi nhuận", Role.CASHIER, user_id=2)

    row = await latest_query(session)
    assert response.kind == "refused"
    assert response.answer == SCOPE_REFUSED_ANSWER
    assert row["TrangThai"] == "Từ chối"
    assert row["KetQuaTomTat"] == SCOPE_REFUSED_ANSWER
    assert fake_llm.calls == 1
    assert ai_engine.executed == []


@pytest.mark.anyio
async def test_an_unexpected_failure_is_logged_as_a_generic_error_not_a_scope_refusal(
    session, seed_views, fake_llm, ai_engine
):
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan")
    ai_engine.error = RuntimeError("driver exploded")

    response = await answer(session, "hỏi", Role.CASHIER, user_id=2)

    row = await latest_query(session)
    assert response.kind == "error"
    assert "driver exploded" not in response.answer
    assert row["TrangThai"] == "Lỗi"
    assert row["KetQuaTomTat"] != SCOPE_REFUSED_ANSWER


@pytest.mark.anyio
async def test_a_new_session_records_the_role_it_was_opened_under(
    session, seed_views, fake_llm, ai_engine
):
    """Report PHIEN_CHAT_AI.MaVaiTro: the role at chat time (FR-AI-05)."""
    response = await answer(session, "hỏi", Role.CASHIER, user_id=2)

    chat = await session.get(ChatSession, response.session_id)
    assert chat is not None
    assert chat.role_id == Role.CASHIER.value


@pytest.mark.anyio
async def test_a_session_is_not_continued_under_another_role(
    session, seed_views, fake_llm, ai_engine
):
    first = await answer(session, "hỏi", Role.CASHIER, user_id=2)

    second = await answer(session, "hỏi tiếp", Role.MANAGER, user_id=2, session_id=first.session_id)

    assert second.session_id != first.session_id
    chat = await session.get(ChatSession, second.session_id)
    assert chat is not None
    assert chat.role_id == Role.MANAGER.value


@pytest.mark.anyio
async def test_token_cost_and_call_count_are_persisted_on_the_query(session, seed_views, ai_engine):
    """Report TRUY_VAN_AI: ModelPhienBan, TokenDauVao/Ra, ChiPhiUSD, SoLanGoi."""
    import httpx

    from app.modules.ai import llm

    replies = iter(
        [
            "SELECT COUNT(*) AS SoDon FROM vw_ai_thungan",
            '{"headline": "Có đơn.", "highlights": [], "follow_ups": []}',
        ]
    )

    def handler(_: httpx.Request) -> httpx.Response:
        content = next(replies)
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": content}}],
                "usage": {"prompt_tokens": 1000, "completion_tokens": 100},
            },
        )

    generator.reset_state()
    interpreter.reset_state()
    llm.set_client(
        llm.CommercialClient(
            api_key="k",
            model="deepseek-flash",
            base_url="https://api.deepseek.com",
            transport=httpx.MockTransport(handler),
        )
    )
    try:
        response = await answer(session, "hôm nay có bao nhiêu đơn?", Role.CASHIER, user_id=2)
    finally:
        llm.set_client(None)
        generator.reset_state()
        interpreter.reset_state()

    assert response.kind == "answer"
    row = await latest_query(session)
    assert row["ModelPhienBan"] == "deepseek-flash"
    assert row["TokenDauVao"] == 2000
    assert row["TokenDauRa"] == 200
    assert row["SoLanGoi"] == 2
    assert float(row["ChiPhiUSD"]) == pytest.approx(0.00084)


@pytest.mark.anyio
async def test_history_of_a_former_role_is_hidden_after_a_role_change(session):
    chat = ChatSession(user_id=2, role_id="CASHIER")
    session.add(chat)
    await session.flush()
    session.add(
        AssistantQuery(
            session_id=chat.id,
            scope="vw_ai_thungan",
            question="doanh thu hôm nay",
            sql_text=None,
            business_date=datetime(2026, 9, 24).date(),
            status="Thành công",
            summary="x",
            latency_ms=1,
        )
    )
    await session.commit()

    same_role = await list_sessions(session, 2, Role.CASHIER, 1, 30)
    other_role = await list_sessions(session, 2, Role.WAREHOUSE, 1, 30)

    assert same_role[1] == 1 and other_role[1] == 0
    with pytest.raises(NotFoundError):
        await session_detail(session, user_id=2, role=Role.WAREHOUSE, session_id=chat.id)
