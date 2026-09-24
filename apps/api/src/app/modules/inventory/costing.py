"""Costing stub."""

from sqlalchemy.ext.asyncio import AsyncSession


async def close_month(session: AsyncSession, month: int):
    return []


async def backfill_issue_costs(session: AsyncSession, month: int) -> int:
    return 0
