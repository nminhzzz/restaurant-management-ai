"""HTTP layer for the reporting module.

Every endpoint is Manager-only (band 33 of the report); the cashier and the warehouse
staff receive 403.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import Principal, require_roles
from app.modules.reports import service
from app.modules.reports.schemas import RevenueOut
from app.shared.roles import Role

router = APIRouter(prefix="/reports", tags=["Module 4 — Reports"])


@router.get("/revenue", response_model=RevenueOut)
async def revenue(
    granularity: str = Query("month"),
    anchor: date | None = Query(None),
    month: str | None = Query(None),
    group_by: str = Query("period"),
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> RevenueOut:
    period = service.period_for(granularity, anchor, month)
    return await service.revenue(session, period, group_by)
