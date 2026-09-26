"""Request and response contracts of the AI Assistant endpoints."""

from datetime import datetime
from typing import Any, Literal

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


ColumnKind = Literal["text", "money", "number", "date", "datetime", "percent"]
AnswerKind = Literal["answer", "clarify", "refused", "error"]


class ColumnMeta(BaseModel):
    key: str
    label: str
    kind: ColumnKind


class ChatResponse(BaseModel):
    answer: str
    headline: str = ""
    highlights: list[str] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)
    scope_note: str | None = None
    columns: list[ColumnMeta] = Field(default_factory=list)
    kind: AnswerKind = "answer"
    data: list[dict[str, Any]] = Field(default_factory=list)
    chart: dict[str, Any] | None = None
    detail: QueryDetail | None = None
    session_id: int | None = None


class SessionSummary(BaseModel):
    id: int
    title: str
    turn_count: int
    created_at: datetime
    last_at: datetime


class TurnOut(BaseModel):
    id: int
    question: str
    headline: str
    highlights: list[str]
    status: str
    occurred_at: datetime


class SessionDetail(BaseModel):
    id: int
    title: str
    turns: list[TurnOut]
