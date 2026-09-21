"""HTTP layer of the AI Assistant.

`POST /assistant/chat` is the single entry point; it is wired to the service now
so the frontend can integrate against the real route shape, and returns 501
until the pipeline steps are implemented.
"""

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import CurrentUser
from app.modules.ai import service
from app.modules.ai.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/assistant", tags=["Module 6 — AI Assistant"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, user: CurrentUser) -> ChatResponse:
    try:
        return await service.answer(payload.question, user.role)
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Trợ lý AI chưa được triển khai.",
        ) from None
