"""HTTP layer of the AI Assistant.

`POST /assistant/chat` answers one turn; `GET /assistant/sessions[/{id}]` reads the
caller's own history.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import CurrentUser
from app.modules.ai import service
from app.modules.ai.schemas import ChatRequest, ChatResponse, SessionDetail, SessionSummary
from app.shared.pagination import Page

router = APIRouter(prefix="/assistant", tags=["Module 6 — AI Assistant"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    return await service.answer(
        session,
        payload.question,
        user.role,
        user.user_id,
        payload.session_id,
    )


@router.get("/sessions", response_model=Page[SessionSummary])
async def list_sessions(
    user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(30, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> Page[SessionSummary]:
    items, total = await service.list_sessions(session, user.user_id, page, size)
    return Page[SessionSummary](items=items, total=total, page=page, size=size)


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session_detail(
    session_id: int, user: CurrentUser, session: AsyncSession = Depends(get_session)
) -> SessionDetail:
    return await service.session_detail(session, user.user_id, session_id)
