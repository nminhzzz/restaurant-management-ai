"""HTTP layer of the AI Assistant.

`POST /assistant/chat` is the single entry point: one turn in, one answer out, with
every turn logged in `TRUY_VAN_AI` by the service.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import CurrentUser
from app.modules.ai import service
from app.modules.ai.schemas import ChatRequest, ChatResponse

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
