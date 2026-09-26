"""Chat history: each user sees only their own sessions (AuthZ, not just AuthN)."""

from datetime import datetime, timedelta

import pytest

from app.modules.ai.models import AssistantQuery, ChatSession

BASE = datetime(2026, 9, 24, 9, 0)


async def _session_with(
    session, user_id: int, questions: list[str], start: datetime
) -> ChatSession:
    chat = ChatSession(user_id=user_id, created_at=start)
    session.add(chat)
    await session.flush()
    for i, question in enumerate(questions):
        session.add(AssistantQuery(
            session_id=chat.id, scope="vw_ai_thungan", question=question, sql_text=None,
            status="Thành công",
            summary=f"Trả lời {i}.\n- ý {i}\n\nPhạm vi dữ liệu: vw_ai_thungan — x.",
            latency_ms=5, occurred_at=start + timedelta(minutes=i),
        ))
    await session.flush()
    return chat


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_the_list_holds_only_my_non_empty_sessions_newest_first(
    api_client, cashier_token, session
):
    old = await _session_with(session, 2, ["Câu cũ"], BASE)
    new = await _session_with(session, 2, ["Câu mới", "Câu tiếp"], BASE + timedelta(hours=1))
    await _session_with(session, 1, ["Của quản lý"], BASE + timedelta(hours=2))
    session.add(ChatSession(user_id=2, created_at=BASE + timedelta(hours=3)))
    await session.commit()

    resp = await api_client.get("/api/v1/assistant/sessions", headers=_auth(cashier_token))
    body = resp.json()

    assert [item["id"] for item in body["items"]] == [new.id, old.id]
    assert body["items"][0]["title"] == "Câu mới"
    assert body["items"][0]["turn_count"] == 2
    assert body["total"] == 2


@pytest.mark.anyio
async def test_the_list_is_paginated(api_client, cashier_token, session):
    for i in range(3):
        await _session_with(session, 2, [f"Câu {i}"], BASE + timedelta(hours=i))
    await session.commit()
    resp = await api_client.get(
        "/api/v1/assistant/sessions?page=2&size=2", headers=_auth(cashier_token)
    )
    body = resp.json()
    assert [item["title"] for item in body["items"]] == ["Câu 0"]
    assert body["total"] == 3


@pytest.mark.anyio
async def test_a_session_detail_splits_each_stored_answer(api_client, cashier_token, session):
    chat = await _session_with(session, 2, ["A?", "B?"], BASE)
    await session.commit()
    resp = await api_client.get(
        f"/api/v1/assistant/sessions/{chat.id}", headers=_auth(cashier_token)
    )
    body = resp.json()
    assert body["title"] == "A?"
    assert [t["question"] for t in body["turns"]] == ["A?", "B?"]
    assert body["turns"][0]["headline"] == "Trả lời 0."
    assert body["turns"][0]["highlights"] == ["ý 0"]


@pytest.mark.anyio
async def test_someone_elses_session_is_not_found(api_client, cashier_token, session):
    chat = await _session_with(session, 1, ["Của quản lý"], BASE)
    await session.commit()
    resp = await api_client.get(
        f"/api/v1/assistant/sessions/{chat.id}", headers=_auth(cashier_token)
    )
    missing = await api_client.get(
        "/api/v1/assistant/sessions/999999", headers=_auth(cashier_token)
    )
    assert resp.status_code == 404
    assert missing.status_code == 404
    assert resp.json() == missing.json()


@pytest.mark.anyio
async def test_history_needs_a_login(api_client):
    assert (await api_client.get("/api/v1/assistant/sessions")).status_code == 401
