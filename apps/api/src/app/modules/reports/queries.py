"""Read-only aggregate queries for the reporting module.

Revenue is `SUM(HOA_DON.TongTien)` plus transactions still awaiting reconciliation
(counted provisionally, FR-REP-02) minus disputed transactions (deducted, FR-REP-02).
Every grouping keys on the denormalised `BusinessDate`, never on the calendar date of
the timestamp column.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Integer, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError
from app.modules.catalog.models import Dish, RecipeItem
from app.modules.inventory.models import MonthlyAverageCost, StockIssue, StockIssueLine
from app.modules.reports.periods import BusinessPeriod, resolve_period
from app.modules.sales.models import Invoice, Order, OrderLine, PaymentTransaction

STATUS_PENDING = "Chờ đối soát"
STATUS_DISPUTED = "Tranh chấp"
STATUS_PAID = "Thành công"
UNKNOWN_METHOD = "Chưa xác định"
GROUP_BY_VALUES = ("period", "table", "payment_method")
CANCELLED_ORDER_STATUSES = ("Đã hủy", "Tự động đóng")
LINE_CANCELLED = "Đã hủy"


@dataclass(frozen=True)
class RevenueBucket:
    key: str | int | None
    DoanhThu: Decimal
    SoDon: int


@dataclass(frozen=True)
class RevenueSummary:
    total: Decimal
    provisional: Decimal
    SoDon: int
    items: list[RevenueBucket] = field(default_factory=list)


def _tuples(rows) -> list[tuple[Any, Any, Any]]:
    return [(row[0], row[1], row[2]) for row in rows]


def _check_group_by(group_by: str) -> None:
    if group_by not in GROUP_BY_VALUES:
        raise BusinessRuleError("group_by phải là period/table/payment_method.")


def _normalise_key(key: object, group_by: str) -> str | int | None:
    if group_by == "period":
        return key.isoformat() if isinstance(key, date) else str(key)
    if group_by == "payment_method":
        return UNKNOWN_METHOD if key is None else str(key)
    return key if key is None else int(str(key))


def _sort_buckets(items: list[RevenueBucket], group_by: str) -> list[RevenueBucket]:
    if group_by == "table":
        return sorted(items, key=lambda b: (b.key is None, b.key or 0))
    return sorted(items, key=lambda b: str(b.key))


async def _invoice_groups(
    session: AsyncSession, period: BusinessPeriod, group_by: str
) -> list[tuple[Any, Any, Any]]:
    window = (Invoice.business_date >= period.start, Invoice.business_date <= period.end)
    if group_by == "period":
        period_stmt = (
            select(Invoice.business_date, func.sum(Invoice.total), func.count(Invoice.id))
            .where(*window)
            .group_by(Invoice.business_date)
        )
        return _tuples((await session.execute(period_stmt)).all())
    if group_by == "table":
        table_stmt = (
            select(Order.table_id, func.sum(Invoice.total), func.count(Invoice.id))
            .join(Order, Order.id == Invoice.order_id)
            .where(*window)
            .group_by(Order.table_id)
        )
        return _tuples((await session.execute(table_stmt)).all())
    method_stmt = (
        select(PaymentTransaction.method, func.sum(Invoice.total), func.count(Invoice.id))
        .outerjoin(
            PaymentTransaction,
            and_(
                PaymentTransaction.order_id == Invoice.order_id,
                PaymentTransaction.status == STATUS_PAID,
            ),
        )
        .where(*window)
        .group_by(PaymentTransaction.method)
    )
    return _tuples((await session.execute(method_stmt)).all())


async def _payment_groups(
    session: AsyncSession, period: BusinessPeriod, status: str, group_by: str
) -> list[tuple[Any, Any, Any]]:
    window = (
        PaymentTransaction.status == status,
        PaymentTransaction.business_date >= period.start,
        PaymentTransaction.business_date <= period.end,
    )
    if group_by == "period":
        period_stmt = (
            select(
                PaymentTransaction.business_date,
                func.sum(PaymentTransaction.amount),
                func.count(PaymentTransaction.id),
            )
            .where(*window)
            .group_by(PaymentTransaction.business_date)
        )
        return _tuples((await session.execute(period_stmt)).all())
    if group_by == "table":
        table_stmt = (
            select(
                Order.table_id,
                func.sum(PaymentTransaction.amount),
                func.count(PaymentTransaction.id),
            )
            .join(Order, Order.id == PaymentTransaction.order_id)
            .where(*window)
            .group_by(Order.table_id)
        )
        return _tuples((await session.execute(table_stmt)).all())
    method_stmt = (
        select(
            PaymentTransaction.method,
            func.sum(PaymentTransaction.amount),
            func.count(PaymentTransaction.id),
        )
        .where(*window)
        .group_by(PaymentTransaction.method)
    )
    return _tuples((await session.execute(method_stmt)).all())


async def revenue_by_period(
    session: AsyncSession, period: BusinessPeriod, group_by: str = "period"
) -> list[RevenueBucket]:
    """Revenue split by business date, table or payment method (FR-REP-01)."""
    _check_group_by(group_by)
    totals: dict[str | int | None, list[Decimal | int]] = {}

    def add(key: object, amount: object, count: object) -> None:
        normalised = _normalise_key(key, group_by)
        bucket = totals.setdefault(normalised, [Decimal(0), 0])
        bucket[0] = bucket[0] + Decimal(str(amount or 0))
        bucket[1] = bucket[1] + int(str(count or 0))

    for key, amount, count in await _invoice_groups(session, period, group_by):
        add(key, amount, count)
    for key, amount, count in await _payment_groups(session, period, STATUS_PENDING, group_by):
        add(key, amount, count)
    # A dispute is deducted retroactively; it carries no order of its own here.
    for key, amount, _ in await _payment_groups(session, period, STATUS_DISPUTED, group_by):
        add(key, -Decimal(str(amount or 0)), 0)

    buckets = [
        RevenueBucket(key=key, DoanhThu=Decimal(str(values[0])), SoDon=int(str(values[1])))
        for key, values in totals.items()
    ]
    return _sort_buckets(buckets, group_by)


async def _scalar_sum(session: AsyncSession, stmt) -> Decimal:
    value = (await session.execute(stmt)).scalar_one_or_none()
    return Decimal(str(value or 0))


async def _scalar_count(session: AsyncSession, stmt) -> int:
    value = (await session.execute(stmt)).scalar_one_or_none()
    return int(str(value or 0))


async def revenue_summary(session: AsyncSession, period: BusinessPeriod) -> RevenueSummary:
    def scope(column):
        return (column >= period.start, column <= period.end)

    invoices_total = await _scalar_sum(
        session, select(func.sum(Invoice.total)).where(*scope(Invoice.business_date))
    )
    pending = await _scalar_sum(
        session,
        select(func.sum(PaymentTransaction.amount)).where(
            PaymentTransaction.status == STATUS_PENDING,
            *scope(PaymentTransaction.business_date),
        ),
    )
    disputed = await _scalar_sum(
        session,
        select(func.sum(PaymentTransaction.amount)).where(
            PaymentTransaction.status == STATUS_DISPUTED,
            *scope(PaymentTransaction.business_date),
        ),
    )
    invoice_count = await _scalar_count(
        session, select(func.count(Invoice.id)).where(*scope(Invoice.business_date))
    )
    pending_count = await _scalar_count(
        session,
        select(func.count(PaymentTransaction.id)).where(
            PaymentTransaction.status == STATUS_PENDING,
            *scope(PaymentTransaction.business_date),
        ),
    )
    return RevenueSummary(
        total=invoices_total + pending - disputed,
        provisional=pending,
        SoDon=invoice_count + pending_count,
    )


# --- Task 2: dish ranking and hourly distribution (FR-REP-03, FR-REP-07) ---


@dataclass(frozen=True)
class DishRank:
    MaMon: int
    TenMon: str
    SoLuong: int
    DoanhThu: Decimal


@dataclass(frozen=True)
class HourBucket:
    ThoiDiem: int
    SoDon: int
    DoanhThu: Decimal


@dataclass(frozen=True)
class WeekdayBucket:
    Thu: int
    SoDon: int


@dataclass(frozen=True)
class HourDistribution:
    items: list[HourBucket]
    by_weekday: list[WeekdayBucket]


def _dialect_name(session: AsyncSession) -> str:
    try:
        bind = session.get_bind()
        if bind is not None:
            return bind.dialect.name
    except Exception:  # pragma: no cover - defensive, mirrors inventory.stock
        pass
    return "sqlite"


def _weekday_iso(session: AsyncSession):
    if _dialect_name(session) == "mysql":
        # WEEKDAY(): Monday=0 … Sunday=6, so +1 gives the ISO numbering.
        return func.weekday(Order.created_at) + 1
    # strftime('%w'): Sunday=0 … Saturday=6; shift it onto ISO (Monday=1).
    return (func.cast(func.strftime("%w", Order.created_at), Integer) + 6) % 7 + 1


def _sold_orders_window(period: BusinessPeriod):
    return (
        Order.business_date >= period.start,
        Order.business_date <= period.end,
        Order.status.notin_(CANCELLED_ORDER_STATUSES),
    )


async def dish_ranking(
    session: AsyncSession, period: BusinessPeriod, order_by: str = "quantity"
) -> list[DishRank]:
    """FR-REP-03: dishes ranked over the period, cancelled lines left out."""
    if order_by not in ("quantity", "revenue"):
        raise BusinessRuleError("order_by phải là quantity/revenue.")
    quantity = func.sum(OrderLine.quantity)
    revenue = func.sum(OrderLine.quantity * OrderLine.unit_price)
    stmt = (
        select(OrderLine.dish_id, Dish.name, quantity, revenue)
        .join(Order, Order.id == OrderLine.order_id)
        .join(Dish, Dish.id == OrderLine.dish_id)
        .where(*_sold_orders_window(period), OrderLine.status != LINE_CANCELLED)
        .group_by(OrderLine.dish_id, Dish.name)
    )
    stmt = stmt.order_by(
        (revenue if order_by == "revenue" else quantity).desc(), OrderLine.dish_id.asc()
    )
    rows = (await session.execute(stmt)).all()
    return [
        DishRank(
            MaMon=int(row[0]),
            TenMon=str(row[1]),
            SoLuong=int(row[2] or 0),
            DoanhThu=Decimal(str(row[3] or 0)),
        )
        for row in rows
    ]


async def hourly_distribution(session: AsyncSession, period: BusinessPeriod) -> HourDistribution:
    """FR-REP-07: orders per hour of the clock and per ISO weekday."""
    window = _sold_orders_window(period)
    line_join = and_(OrderLine.order_id == Order.id, OrderLine.status != LINE_CANCELLED)

    hour_expr = func.extract("hour", Order.created_at)
    hour_stmt = (
        select(
            hour_expr,
            func.count(func.distinct(Order.id)),
            func.coalesce(func.sum(OrderLine.quantity * OrderLine.unit_price), 0),
        )
        .outerjoin(OrderLine, line_join)
        .where(*window)
        .group_by(hour_expr)
        .order_by(hour_expr)
    )
    hour_rows = (await session.execute(hour_stmt)).all()

    weekday_expr = _weekday_iso(session)
    weekday_stmt = (
        select(weekday_expr, func.count(func.distinct(Order.id)))
        .where(*window)
        .group_by(weekday_expr)
        .order_by(weekday_expr)
    )
    weekday_rows = (await session.execute(weekday_stmt)).all()

    return HourDistribution(
        items=[
            HourBucket(ThoiDiem=int(row[0]), SoDon=int(row[1]), DoanhThu=Decimal(str(row[2] or 0)))
            for row in hour_rows
        ],
        by_weekday=[WeekdayBucket(Thu=int(row[0]), SoDon=int(row[1])) for row in weekday_rows],
    )


# --- Task 3: cost of goods, margin and per-dish cost (FR-REP-04, 05, 06) ---


@dataclass(frozen=True)
class CostBreakdown:
    NguyenLieu: Decimal
    HaoHut: Decimal
    TongGiaVon: Decimal
    TamTinh: bool
    SoDongChuaTinhGiaVon: int


@dataclass(frozen=True)
class Margin:
    DoanhThu: Decimal
    GiaVon: Decimal
    BienLoiNhuanGop: Decimal


@dataclass(frozen=True)
class DishCost:
    MaMon: int
    TenMon: str
    GiaVon: Decimal


def _month_period(month: int) -> BusinessPeriod:
    return resolve_period("month", date(month // 100, month % 100, 1))


def _month_bounds(month: int) -> tuple[datetime, datetime]:
    year, mon = month // 100, month % 100
    start = datetime(year, mon, 1)
    end = datetime(year + 1, 1, 1) if mon == 12 else datetime(year, mon + 1, 1)
    return start, end


def _consumed_amount():
    """Quantity x recipe quantity x monthly average cost, for one order line."""
    return OrderLine.quantity * RecipeItem.quantity * MonthlyAverageCost.avg_cost


def _join_recipe_cost(stmt, month: int):
    return stmt.join(RecipeItem, RecipeItem.recipe_id == OrderLine.recipe_id).join(
        MonthlyAverageCost,
        and_(
            RecipeItem.ingredient_id == MonthlyAverageCost.ingredient_id,
            MonthlyAverageCost.month == month,
        ),
    )


async def ingredient_cost(session: AsyncSession, month: int) -> Decimal:
    """FR-REP-05a: each line is costed from the recipe version pinned on it."""
    period = _month_period(month)
    stmt = (
        select(func.coalesce(func.sum(_consumed_amount()), 0))
        .select_from(OrderLine)
        .join(Order, Order.id == OrderLine.order_id)
    )
    stmt = _join_recipe_cost(stmt, month).where(
        *_sold_orders_window(period), OrderLine.status != LINE_CANCELLED
    )
    return await _scalar_sum(session, stmt)


async def dish_ingredient_cost(session: AsyncSession, month: int) -> list[DishCost]:
    """FR-REP-06: per-dish ingredient cost — no waste, no margin."""
    period = _month_period(month)
    stmt = (
        select(OrderLine.dish_id, Dish.name, func.coalesce(func.sum(_consumed_amount()), 0))
        .select_from(OrderLine)
        .join(Order, Order.id == OrderLine.order_id)
        .join(Dish, Dish.id == OrderLine.dish_id)
    )
    stmt = (
        _join_recipe_cost(stmt, month)
        .where(*_sold_orders_window(period), OrderLine.status != LINE_CANCELLED)
        .group_by(OrderLine.dish_id, Dish.name)
        .order_by(OrderLine.dish_id.asc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        DishCost(MaMon=int(row[0]), TenMon=str(row[1]), GiaVon=Decimal(str(row[2] or 0)))
        for row in rows
    ]


async def waste_cost(session: AsyncSession, month: int) -> tuple[Decimal, int]:
    """Manual write-offs of the month, plus how many still lack a costed value."""
    start, end = _month_bounds(month)
    window = (StockIssue.created_at >= start, StockIssue.created_at < end)
    waste = await _scalar_sum(
        session,
        select(func.coalesce(func.sum(StockIssueLine.estimated_cost), 0))
        .join(StockIssue, StockIssue.id == StockIssueLine.issue_id)
        .where(*window),
    )
    uncosted = await _scalar_count(
        session,
        select(func.count(StockIssueLine.id))
        .join(StockIssue, StockIssue.id == StockIssueLine.issue_id)
        .where(*window, StockIssueLine.estimated_cost == 0),
    )
    return waste, uncosted


async def cost_of_goods(session: AsyncSession, month: int) -> CostBreakdown:
    ingredients = await ingredient_cost(session, month)
    waste, uncosted = await waste_cost(session, month)
    return CostBreakdown(
        NguyenLieu=ingredients,
        HaoHut=waste,
        TongGiaVon=ingredients + waste,
        TamTinh=uncosted > 0,
        SoDongChuaTinhGiaVon=uncosted,
    )


async def gross_margin(session: AsyncSession, month: int) -> Margin:
    """FR-REP-04: margin only at the whole-restaurant, monthly level."""
    period = _month_period(month)
    revenue = (await revenue_summary(session, period)).total
    cost = (await cost_of_goods(session, month)).TongGiaVon
    return Margin(DoanhThu=revenue, GiaVon=cost, BienLoiNhuanGop=revenue - cost)
