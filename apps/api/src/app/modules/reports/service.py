"""Orchestration for the reporting module (read-only)."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.reports import queries
from app.modules.reports.periods import BusinessPeriod, month_period, resolve_period
from app.modules.reports.schemas import (
    CancelledOrderOut,
    CancelledReportOut,
    ComparisonOut,
    CostBreakdownOut,
    DishCostListOut,
    DishCostOut,
    DishRankListOut,
    DishRankOut,
    HourBucketOut,
    HourlyOut,
    MarginOut,
    PeriodOut,
    RevenueBucketOut,
    RevenueOut,
    RevenueSummaryOut,
    WeekdayBucketOut,
)
from app.shared import business_date


def period_for(
    granularity: str, anchor: date | None = None, month: str | None = None
) -> BusinessPeriod:
    """A report period comes from either an explicit `month` or an anchor day."""
    if month:
        return month_period(month)
    default_anchor = anchor or business_date.business_date_of(business_date.now())
    return resolve_period(granularity, default_anchor)


def period_out(period: BusinessPeriod) -> PeriodOut:
    return PeriodOut(start=period.start, end=period.end, granularity=period.granularity)


def month_key(month: str) -> int:
    """`"2026-09"` → `202609`, the key of GIA_BINH_QUAN_THANG."""
    return month_period(month).month_key


async def revenue(
    session: AsyncSession, period: BusinessPeriod, group_by: str = "period"
) -> RevenueOut:
    summary = await queries.revenue_summary(session, period)
    buckets = await queries.revenue_by_period(session, period, group_by)
    return RevenueOut(
        total=summary.total,
        provisional=summary.provisional,
        SoDon=summary.SoDon,
        items=[RevenueBucketOut(key=b.key, DoanhThu=b.DoanhThu, SoDon=b.SoDon) for b in buckets],
        period=period_out(period),
    )


async def dish_ranking(
    session: AsyncSession, period: BusinessPeriod, order_by: str = "quantity"
) -> DishRankListOut:
    rows = await queries.dish_ranking(session, period, order_by)
    return DishRankListOut(
        items=[
            DishRankOut(
                MaMon=row.MaMon,
                TenMon=row.TenMon,
                SoLuong=row.SoLuong,
                DoanhThu=row.DoanhThu,
            )
            for row in rows
        ],
        period=period_out(period),
    )


async def hourly(session: AsyncSession, period: BusinessPeriod) -> HourlyOut:
    distribution = await queries.hourly_distribution(session, period)
    return HourlyOut(
        items=[
            HourBucketOut(ThoiDiem=b.ThoiDiem, SoDon=b.SoDon, DoanhThu=b.DoanhThu)
            for b in distribution.items
        ],
        by_weekday=[WeekdayBucketOut(Thu=b.Thu, SoDon=b.SoDon) for b in distribution.by_weekday],
        period=period_out(period),
    )


async def margin(session: AsyncSession, month: str) -> MarginOut:
    result = await queries.gross_margin(session, month_key(month))
    return MarginOut(
        DoanhThu=result.DoanhThu,
        GiaVon=result.GiaVon,
        BienLoiNhuanGop=result.BienLoiNhuanGop,
    )


async def costs(session: AsyncSession, month: str) -> CostBreakdownOut:
    result = await queries.cost_of_goods(session, month_key(month))
    return CostBreakdownOut(
        NguyenLieu=result.NguyenLieu,
        HaoHut=result.HaoHut,
        TongGiaVon=result.TongGiaVon,
        TamTinh=result.TamTinh,
        SoDongChuaTinhGiaVon=result.SoDongChuaTinhGiaVon,
    )


async def dish_costs(session: AsyncSession, month: str) -> DishCostListOut:
    rows = await queries.dish_ingredient_cost(session, month_key(month))
    return DishCostListOut(
        items=[DishCostOut(MaMon=r.MaMon, TenMon=r.TenMon, GiaVon=r.GiaVon) for r in rows]
    )


async def comparison(session: AsyncSession, left: str, right: str) -> ComparisonOut:
    result = await queries.compare_periods(session, month_period(left), month_period(right))
    return ComparisonOut(
        left=RevenueSummaryOut(DoanhThu=result.left.DoanhThu, SoDon=result.left.SoDon),
        right=RevenueSummaryOut(DoanhThu=result.right.DoanhThu, SoDon=result.right.SoDon),
        change_percent=result.change_percent,
    )


async def cancelled(session: AsyncSession, month: str) -> CancelledReportOut:
    result = await queries.cancelled_orders(session, month_period(month))
    return CancelledReportOut(
        SoLuong=result.SoLuong,
        TongGiaTri=result.TongGiaTri,
        items=[
            CancelledOrderOut(
                MaOrder=item.MaOrder,
                MaOrderHienThi=item.MaOrderHienThi,
                TongTien=item.TongTien,
                LyDoHuy=item.LyDoHuy,
            )
            for item in result.items
        ],
    )
