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
from app.modules.reports.periods import BusinessPeriod
from app.modules.reports.schemas import DishRankListOut, HourlyOut, RevenueOut
from app.shared.roles import Role

router = APIRouter(prefix="/reports", tags=["Module 4 — Reports"])


def report_period(
    granularity: str = Query("month"),
    anchor: date | None = Query(None),
    month: str | None = Query(None),
) -> BusinessPeriod:
    return service.period_for(granularity, anchor, month)


@router.get("/revenue", response_model=RevenueOut)
async def revenue(
    group_by: str = Query("period"),
    period: BusinessPeriod = Depends(report_period),
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> RevenueOut:
    return await service.revenue(session, period, group_by)


@router.get("/dishes", response_model=DishRankListOut)
async def dish_ranking(
    order_by: str = Query("quantity"),
    period: BusinessPeriod = Depends(report_period),
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> DishRankListOut:
    return await service.dish_ranking(session, period, order_by)


@router.get("/hours", response_model=HourlyOut)
async def hourly(
    period: BusinessPeriod = Depends(report_period),
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> HourlyOut:
    return await service.hourly(session, period)
