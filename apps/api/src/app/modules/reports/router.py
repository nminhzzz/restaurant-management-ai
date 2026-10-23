"""HTTP layer for the reporting module.

Every endpoint is Manager-only (band 33 of the report); the cashier and the warehouse
staff receive 403.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import Principal, require_roles
from app.modules.reports import service
from app.modules.reports.periods import BusinessPeriod
from app.modules.reports.schemas import (
    CancelledReportOut,
    ClosedUnpaidReportOut,
    ComparisonOut,
    CostBreakdownOut,
    DishCostListOut,
    DishRankListOut,
    HourlyOut,
    MarginOut,
    PendingPaymentListOut,
    RevenueOut,
)
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


@router.get("/margin", response_model=MarginOut)
async def margin(
    month: str = Query(...),
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> MarginOut:
    return await service.margin(session, month)


@router.get("/costs/dishes", response_model=DishCostListOut)
async def dish_costs(
    month: str = Query(...),
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> DishCostListOut:
    return await service.dish_costs(session, month)


@router.get("/costs", response_model=CostBreakdownOut)
async def costs(
    month: str = Query(...),
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> CostBreakdownOut:
    return await service.costs(session, month)


@router.get("/comparison", response_model=ComparisonOut)
async def comparison(
    left: str | None = Query(None),
    right: str | None = Query(None),
    left_from: str | None = Query(None),
    left_to: str | None = Query(None),
    right_from: str | None = Query(None),
    right_to: str | None = Query(None),
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> ComparisonOut:
    if left_from or left_to or right_from or right_to:
        if not (left_from and left_to and right_from and right_to):
            raise HTTPException(status_code=422, detail="Thiếu mốc đầu/cuối của kỳ so sánh.")
        return await service.comparison_periods(
            session,
            service.month_span(left_from, left_to),
            service.month_span(right_from, right_to),
        )
    if not (left and right):
        raise HTTPException(status_code=422, detail="Thiếu kỳ so sánh.")
    return await service.comparison(session, left, right)


@router.get("/cancelled-orders", response_model=CancelledReportOut)
async def cancelled_orders(
    period: BusinessPeriod = Depends(report_period),
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> CancelledReportOut:
    return await service.cancelled(session, period)


@router.get("/closed-unpaid", response_model=ClosedUnpaidReportOut)
async def closed_unpaid(
    period: BusinessPeriod = Depends(report_period),
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> ClosedUnpaidReportOut:
    return await service.closed_unpaid(session, period)


@router.get("/pending-payments", response_model=PendingPaymentListOut)
async def pending_payments(
    month: str | None = Query(None),
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> PendingPaymentListOut:
    return await service.pending_payments(session, month)
