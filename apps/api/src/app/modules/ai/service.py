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
import logging
import time
from dataclasses import asdict
from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.ai import charts, labels, llm
from app.modules.ai.errors import ClarificationNeeded, ExecutionFailed, QuotaExceeded
from app.modules.ai.guard import OutOfScopeError, ValidatedSql
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
from app.modules.settings.models import User
from app.modules.settings.service import effective_business_day_start, get_config
from app.shared import business_date
from app.shared.roles import Role

logger = logging.getLogger(__name__)

TITLE_LIMIT = 120
FEEDBACK_LIMIT = 200

REFUSED_ANSWER = (
    "Không thể tạo truy vấn an toàn cho câu hỏi này trong phạm vi của bạn. "
    "Vui lòng diễn đạt lại câu hỏi."
)
TIMEOUT_ANSWER = "Trợ lý phản hồi quá lâu. Vui lòng thử lại với câu hỏi ngắn gọn hơn."
SCOPE_REFUSED_ANSWER = "Câu hỏi này nằm ngoài phạm vi dữ liệu mà vai trò của bạn được phép xem."
ERROR_ANSWER = "Hệ thống chưa trả lời được câu hỏi này. Vui lòng thử lại sau."
PENDING_STATUS = "Đang xử lý"
INTERRUPTED_STATUS = "Bị gián đoạn"
INTERRUPTED_ANSWER = "Câu hỏi bị gián đoạn khi hệ thống đang xử lý. Vui lòng gửi lại nếu cần."


async def _resolve_session(
    session: AsyncSession, user_id: int, session_id: int | None, role: Role
) -> ChatSession:
    if session_id is not None:
        existing = await session.get(ChatSession, session_id)
        # A session is bound to the role it was opened under (FR-AI-05): after a role
        # change the history of the old scope must not be continued under the new one.
        if existing is not None and existing.user_id == user_id and existing.role_id == role.value:
            return existing
    chat_session = ChatSession(user_id=user_id, role_id=role.value)
    session.add(chat_session)
    await session.flush()
    return chat_session


async def _reserve_question(
    session: AsyncSession,
    user_id: int,
    session_id: int | None,
    *,
    question: str,
    role: Role,
) -> tuple[ChatSession, AssistantQuery, date]:
    """Atomically reserve one persisted per-user quota slot before external calls."""
    # Lock before any consistent read. Under MySQL REPEATABLE READ, reading settings
    # before this lock would pin a snapshot that could miss the preceding reservation.
    # SQLite ignores FOR UPDATE; its concurrency test only checks committed-row visibility.
    await session.execute(select(User.id).where(User.id == user_id).with_for_update())

    moment = business_date.now()
    start = await effective_business_day_start(session, moment)
    effective_date = business_date.business_date_of(moment, start)
    config = await get_config(session)
    reserved_ids = (
        await session.execute(
            select(AssistantQuery.id)
            .join(ChatSession, AssistantQuery.session_id == ChatSession.id)
            .where(
                ChatSession.user_id == user_id,
                AssistantQuery.business_date == effective_date,
            )
            .with_for_update()
        )
    ).scalars()
    used = len(reserved_ids.all())
    if used >= config.ai_daily_question_quota:
        raise QuotaExceeded("Đã đạt hạn mức câu hỏi trong ngày. Vui lòng thử lại vào ngày mai.")

    chat_session = await _resolve_session(session, user_id, session_id, role)
    query = AssistantQuery(
        session_id=chat_session.id,
        scope=ROLE_VIEWS[role],
        question=question,
        sql_text=None,
        business_date=effective_date,
        status=PENDING_STATUS,
        summary=None,
        latency_ms=None,
    )
    session.add(query)
    await session.flush()
    # A crash after this commit leaves a counted, visible pending/interrupted row.
    await session.commit()
    return chat_session, query, effective_date


async def _update_query(
    session: AsyncSession,
    query: AssistantQuery,
    *,
    sql_text: str | None,
    status: str,
    summary: str,
    elapsed_ms: int,
    usage: llm.UsageTally | None = None,
) -> None:
    query.sql_text = sql_text
    query.status = status
    query.summary = summary
    query.latency_ms = elapsed_ms
    if usage is not None and usage.calls:
        query.model_version = usage.model_version[:100] if usage.model_version else None
        query.input_tokens = usage.input_tokens
        query.output_tokens = usage.output_tokens
        query.cost_usd = usage.priced_cost
        query.call_count = usage.calls
    await session.flush()


def _trace_suffix(query: AssistantQuery) -> str:
    return f" Mã truy vết: {query.id}."


async def _generate_and_execute(
    session: AsyncSession,
    question: str,
    role: Role,
    user_id: int,
    effective_date: date,
) -> tuple[ValidatedSql, list[dict[str, Any]]]:
    """Generate, guard and run SQL; the database rejecting it earns one regeneration.

    Syntax or execution errors may be regenerated once within the shared
    `ai_max_sql_attempts` budget (NFR-06); an out-of-scope query never reaches this loop's
    retry because the generator raises `OutOfScopeError` and the turn ends.
    """
    settings = get_settings()
    budget = generator.AttemptBudget(settings.ai_max_sql_attempts)
    feedback: str | None = None
    while True:
        sql = await generator.generate_sql(
            session, question, role, user_id, effective_date, budget=budget, feedback=feedback
        )
        try:
            rows = await executor.execute(
                sql, role=role, timeout_seconds=settings.ai_sql_timeout_seconds
            )
        except DBAPIError as exc:
            generator.invalidate_sql(user_id, question, role, effective_date)
            if budget.remaining <= 0:
                raise ExecutionFailed(sql) from exc
            feedback = str(exc.orig)[:FEEDBACK_LIMIT]
            continue
        return sql, rows


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
    with llm.track_usage() as usage:
        return await _run_turn(session, question, role, user_id, session_id, usage)


async def _run_turn(
    session: AsyncSession,
    question: str,
    role: Role,
    user_id: int,
    session_id: int | None,
    usage: llm.UsageTally,
) -> ChatResponse:
    settings = get_settings()
    started = time.perf_counter()
    normalized = normalize.normalize_question(question)
    sql_text: str | None = None

    try:
        chat_session, query, effective_date = await _reserve_question(
            session, user_id, session_id, question=question, role=role
        )
    except QuotaExceeded as exc:
        return ChatResponse(
            answer=exc.message,
            headline=exc.message,
            kind="refused",
            session_id=session_id,
        )

    try:
        async with asyncio.timeout(settings.ai_response_budget_seconds):
            sql_text, rows = await _generate_and_execute(
                session, normalized, role, user_id, effective_date
            )
            columns = list(rows[0].keys()) if rows else []
            spec = charts.choose_chart(columns, rows)
            columns_meta = labels.describe_columns(columns, rows)
            interpretation = await interpreter.interpret(
                session,
                normalized,
                sql_text,
                rows,
                role,
                user_id,
                effective_date,
            )
    except ClarificationNeeded as exc:
        await _update_query(
            session,
            query,
            sql_text=None,
            status="Yêu cầu làm rõ",
            summary=exc.message,
            elapsed_ms=_elapsed_ms(started),
            usage=usage,
        )
        await session.commit()
        return ChatResponse(
            answer=exc.message, headline=exc.message, kind="clarify", session_id=chat_session.id
        )
    except QuotaExceeded as exc:
        await _update_query(
            session,
            query,
            sql_text=None,
            status="Từ chối",
            summary=exc.message,
            elapsed_ms=_elapsed_ms(started),
            usage=usage,
        )
        await session.commit()
        return ChatResponse(
            answer=exc.message, headline=exc.message, kind="refused", session_id=chat_session.id
        )
    except OutOfScopeError:
        await _update_query(
            session,
            query,
            sql_text=None,
            status="Từ chối",
            summary=SCOPE_REFUSED_ANSWER,
            elapsed_ms=_elapsed_ms(started),
            usage=usage,
        )
        await session.commit()
        return ChatResponse(
            answer=SCOPE_REFUSED_ANSWER,
            headline=SCOPE_REFUSED_ANSWER,
            kind="refused",
            session_id=chat_session.id,
        )
    except BusinessRuleError:
        await _update_query(
            session,
            query,
            sql_text=None,
            status="Từ chối",
            summary=REFUSED_ANSWER,
            elapsed_ms=_elapsed_ms(started),
            usage=usage,
        )
        await session.commit()
        return ChatResponse(
            answer=REFUSED_ANSWER,
            headline=REFUSED_ANSWER,
            kind="refused",
            session_id=chat_session.id,
        )
    except TimeoutError:
        await _update_query(
            session,
            query,
            sql_text=sql_text,
            status="Lỗi",
            summary=TIMEOUT_ANSWER,
            elapsed_ms=_elapsed_ms(started),
            usage=usage,
        )
        await session.commit()
        return ChatResponse(
            answer=TIMEOUT_ANSWER,
            headline=TIMEOUT_ANSWER,
            kind="error",
            session_id=chat_session.id,
        )
    except Exception as exc:
        failed_sql = exc.sql if isinstance(exc, ExecutionFailed) else sql_text
        if not isinstance(exc, ExecutionFailed):
            logger.exception("ai.turn.failed query=%s", query.id)
        message = ERROR_ANSWER + _trace_suffix(query)
        await _update_query(
            session,
            query,
            sql_text=failed_sql,
            status="Lỗi",
            summary=message,
            elapsed_ms=_elapsed_ms(started),
            usage=usage,
        )
        await session.commit()
        return ChatResponse(
            answer=message,
            headline=message,
            kind="error",
            session_id=chat_session.id,
        )

    elapsed_ms = _elapsed_ms(started)
    await _update_query(
        session,
        query,
        sql_text=sql_text,
        status="Thành công",
        summary=interpretation.text,
        elapsed_ms=elapsed_ms,
        usage=usage,
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
    session: AsyncSession, user_id: int, role: Role, page: int, size: int
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
        .where(ChatSession.user_id == user_id, ChatSession.role_id == role.value)
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


async def session_detail(
    session: AsyncSession, user_id: int, role: Role, session_id: int
) -> SessionDetail:
    chat = await session.get(ChatSession, session_id)
    # Someone else's session, or one opened under a former role, answers like a missing one.
    if chat is None or chat.user_id != user_id or chat.role_id != role.value:
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
        is_interrupted = turn.status == PENDING_STATUS
        headline, highlights = (
            (INTERRUPTED_ANSWER, []) if is_interrupted else split_answer(turn.summary or "")
        )
        out.append(
            TurnOut(
                id=turn.id,
                question=turn.question,
                headline=headline,
                highlights=highlights,
                status=INTERRUPTED_STATUS if is_interrupted else turn.status,
                occurred_at=turn.occurred_at,
            )
        )
    return SessionDetail(id=chat.id, title=_title(turns[0].question) if turns else "", turns=out)
