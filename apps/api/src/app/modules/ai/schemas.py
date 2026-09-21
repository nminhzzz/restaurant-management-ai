"""Request and response contracts of the AI Assistant endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    session_id: int | None = None


class QueryDetail(BaseModel):
    """Payload behind the collapsed "Xem chi tiết" section (FR-AI-08)."""

    sql: str
    row_count: int
    view: str
    elapsed_ms: int


class ChatResponse(BaseModel):
    answer: str
    data: list[dict[str, Any]] = Field(default_factory=list)
    chart: dict[str, Any] | None = None
    detail: QueryDetail | None = None
