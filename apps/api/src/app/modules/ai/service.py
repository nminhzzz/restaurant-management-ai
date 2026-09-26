"""Orchestration of one assistant turn (FR-AI-01 … FR-AI-09).

Steps: normalise → build prompt → generate → validate through the guard → execute on
the role's read-only account → interpret. Every outcome — success, refusal,
clarification, error — writes one `TRUY_VAN_AI` row, so the evaluation harness and the
audit trail see the same thing the user saw.

The whole chain runs inside `ai_response_budget_seconds` (NFR-02); `ai_sql_timeout_seconds`
is the narrower budget for the database part alone. The model call is dispatched to a
worker thread so a stalled provider cannot hold the event loop and dodge the budget.
"""

import asyncio
import time
from dataclasses import asdict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.ai import charts, labels
from app.modules.ai.errors import ClarificationNeeded, QuotaExceeded
from app.modules.ai.models import AssistantQuery, ChatSession
from app.modules.ai.pipeline import executor, generator, interpreter, normalize
from app.modules.ai.pipeline.answer_format import split_answer
from app.modules.ai.schemas import (
    ChatResponse,
    ColumnMeta,
    QueryDetail,
    SessionDetail,
    SessionSummary,
    TurnOut,
)
from app.modules.ai.scope import ROLE_VIEWS
from app.shared.roles import Role

TITLE_LIMIT = 120

REFUSED_ANSWER = (
    "Không thể tạo truy vấn an toàn cho câu hỏi này trong phạm vi của bạn. "
    "Vui lòng diễn đạt lại câu hỏi."
)
TIMEOUT_ANSWER = "Trợ lý phản hồi quá lâu. Vui lòng thử lại với câu hỏi ngắn gọn hơn."
SCOPE_REFUSED_ANSWER = "Câu hỏi này nằm ngoài phạm vi dữ liệu mà vai trò của bạn được phép xem."


async def _resolve_session(
    session: AsyncSession, user_id: int, session_id: int | None
) -> ChatSession:
    if session_id is not None:
        existing = await session.get(ChatSession, session_id)
        if existing is not None and existing.user_id == user_id:
            return existing
    chat_session = ChatSession(user_id=user_id)
    session.add(chat_session)
    await session.flush()
    return chat_session


async def _record(
    session: AsyncSession,
    chat_session: ChatSession,
    *,
    question: str,
    sql_text: str | None,
    status: str,
    summary: str,
    role: Role,
    elapsed_ms: int,
) -> None:
    session.add(
        AssistantQuery(
            session_id=chat_session.id,
            scope=ROLE_VIEWS[role],
            question=question,
            sql_text=sql_text,
            status=status,
            summary=summary,
            latency_ms=elapsed_ms,
        )
    )
    await session.flush()


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


async def answer(
    session: AsyncSession,
    question: str,
    role: Role,
    user_id: int,
    session_id: int | None = None,
) -> ChatResponse:
    """Answer one question within the caller's role scope, and log the turn."""
    settings = get_settings()
    started = time.perf_counter()
    chat_session = await _resolve_session(session, user_id, session_id)
    normalized = normalize.normalize_question(question)
    sql_text: str | None = None

    try:
        async with asyncio.timeout(settings.ai_response_budget_seconds):
            sql_text = await generator.generate_sql(session, normalized, role)
            rows = await executor.execute(
                sql_text, role=role, timeout_seconds=settings.ai_sql_timeout_seconds
            )
            columns = list(rows[0].keys()) if rows else []
            spec = charts.choose_chart(columns, rows)
            columns_meta = labels.describe_columns(columns, rows)
            interpretation = await interpreter.interpret(session, normalized, sql_text, rows, role)
    except ClarificationNeeded as exc:
        await _record(
            session,
            chat_session,
            question=question,
            sql_text=None,
            status="Yêu cầu làm rõ",
            summary=exc.message,
            role=role,
            elapsed_ms=_elapsed_ms(started),
        )
        await session.commit()
        return ChatResponse(
            answer=exc.message, headline=exc.message, kind="clarify", session_id=chat_session.id
        )
    except QuotaExceeded as exc:
        await _record(
            session,
            chat_session,
            question=question,
            sql_text=None,
            status="Từ chối",
            summary=exc.message,
            role=role,
            elapsed_ms=_elapsed_ms(started),
        )
        await session.commit()
        return ChatResponse(
            answer=exc.message, headline=exc.message, kind="refused", session_id=chat_session.id
        )
    except BusinessRuleError:
        await _record(
            session,
            chat_session,
            question=question,
            sql_text=sql_text,
            status="Từ chối",
            summary=REFUSED_ANSWER,
            role=role,
            elapsed_ms=_elapsed_ms(started),
        )
        await session.commit()
        return ChatResponse(
            answer=REFUSED_ANSWER,
            headline=REFUSED_ANSWER,
            kind="refused",
            session_id=chat_session.id,
        )
    except TimeoutError:
        await _record(
            session,
            chat_session,
            question=question,
            sql_text=sql_text,
            status="Lỗi",
            summary=TIMEOUT_ANSWER,
            role=role,
            elapsed_ms=_elapsed_ms(started),
        )
        await session.commit()
        return ChatResponse(
            answer=TIMEOUT_ANSWER,
            headline=TIMEOUT_ANSWER,
            kind="error",
            session_id=chat_session.id,
        )
    except Exception:
        await _record(
            session,
            chat_session,
            question=question,
            sql_text=sql_text,
            status="Lỗi",
            summary=SCOPE_REFUSED_ANSWER,
            role=role,
            elapsed_ms=_elapsed_ms(started),
        )
        await session.commit()
        raise

    elapsed_ms = _elapsed_ms(started)
    await _record(
        session,
        chat_session,
        question=question,
        sql_text=sql_text,
        status="Thành công",
        summary=interpretation.text,
        role=role,
        elapsed_ms=elapsed_ms,
    )
    await session.commit()
    return ChatResponse(
        answer=interpretation.text,
        headline=interpretation.answer.headline,
        highlights=interpretation.answer.highlights,
        follow_ups=interpretation.answer.follow_ups,
        scope_note=interpretation.scope_note,
        columns=[ColumnMeta(**meta) for meta in columns_meta],
        kind="answer",
        data=rows,
        chart=asdict(spec) if spec is not None else None,
        detail=QueryDetail(
            sql=sql_text,
            row_count=len(rows),
            view=ROLE_VIEWS[role],
            elapsed_ms=elapsed_ms,
        ),
        session_id=chat_session.id,
    )


def _title(question: str) -> str:
    text = " ".join(question.split())
    return text if len(text) <= TITLE_LIMIT else text[: TITLE_LIMIT - 1] + "…"


async def list_sessions(
    session: AsyncSession, user_id: int, page: int, size: int
) -> tuple[list[SessionSummary], int]:
    """The caller's sessions that hold at least one turn, most recent activity first."""
    stats = (
        select(
            AssistantQuery.session_id.label("sid"),
            func.count(AssistantQuery.id).label("turns"),
            func.min(AssistantQuery.id).label("first_id"),
            func.max(AssistantQuery.occurred_at).label("last_at"),
        )
        .group_by(AssistantQuery.session_id)
        .subquery()
    )
    base = (
        select(ChatSession, stats.c.turns, stats.c.first_id, stats.c.last_at)
        .join(stats, stats.c.sid == ChatSession.id)
        .where(ChatSession.user_id == user_id)
    )
    total = (await session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        await session.execute(
            base.order_by(stats.c.last_at.desc(), ChatSession.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
    ).all()
    first_ids = [row.first_id for row in rows]
    questions: dict[int, str] = {}
    if first_ids:
        question_rows = await session.execute(
            select(AssistantQuery.id, AssistantQuery.question).where(
                AssistantQuery.id.in_(first_ids)
            )
        )
        questions = {row.id: row.question for row in question_rows}
    items = [
        SessionSummary(
            id=row.ChatSession.id,
            title=_title(questions.get(row.first_id, "")),
            turn_count=row.turns,
            created_at=row.ChatSession.created_at,
            last_at=row.last_at,
        )
        for row in rows
    ]
    return items, total


async def session_detail(session: AsyncSession, user_id: int, session_id: int) -> SessionDetail:
    chat = await session.get(ChatSession, session_id)
    # Someone else's session answers exactly like a missing one.
    if chat is None or chat.user_id != user_id:
        raise NotFoundError("Không tìm thấy cuộc trò chuyện.")
    turns = (
        (
            await session.execute(
                select(AssistantQuery)
                .where(AssistantQuery.session_id == chat.id)
                .order_by(AssistantQuery.occurred_at, AssistantQuery.id)
            )
        )
        .scalars()
        .all()
    )
    out = []
    for turn in turns:
        headline, highlights = split_answer(turn.summary or "")
        out.append(
            TurnOut(
                id=turn.id,
                question=turn.question,
                headline=headline,
                highlights=highlights,
                status=turn.status,
                occurred_at=turn.occurred_at,
            )
        )
    return SessionDetail(id=chat.id, title=_title(turns[0].question) if turns else "", turns=out)
