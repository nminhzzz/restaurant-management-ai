"""Cursor-free pagination envelope shared by list endpoints."""

from typing import Annotated

from pydantic import BaseModel, Field


class Page[T](BaseModel):
    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    size: int = Field(ge=1)


class PageParams(BaseModel):
    page: Annotated[int, Field(ge=1)] = 1
    size: Annotated[int, Field(ge=1, le=200)] = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
