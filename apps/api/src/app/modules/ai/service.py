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

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import BusinessRuleError
from app.modules.ai import charts
from app.modules.ai.errors import ClarificationNeeded, QuotaExceeded
from app.modules.ai.models import AssistantQuery, ChatSession
from app.modules.ai.pipeline import executor, generator, interpreter, normalize
from app.modules.ai.schemas import ChatResponse, QueryDetail
from app.modules.ai.scope import ROLE_VIEWS
from app.shared.roles import Role

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
            answer_text = await interpreter.interpret(session, normalized, sql_text, rows, role)
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
        return ChatResponse(answer=exc.message, session_id=chat_session.id)
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
        return ChatResponse(answer=exc.message, session_id=chat_session.id)
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
        return ChatResponse(answer=REFUSED_ANSWER, session_id=chat_session.id)
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
        return ChatResponse(answer=TIMEOUT_ANSWER, session_id=chat_session.id)
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
        summary=answer_text,
        role=role,
        elapsed_ms=elapsed_ms,
    )
    await session.commit()
    return ChatResponse(
        answer=answer_text,
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
