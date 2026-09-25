"""Read-only aggregate queries for the reporting module.

Revenue is `SUM(HOA_DON.TongTien)` plus transactions still awaiting reconciliation
(counted provisionally, FR-REP-02) minus disputed transactions (deducted, FR-REP-02).
Every grouping keys on the denormalised `BusinessDate`, never on the calendar date of
the timestamp column.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError
from app.modules.reports.periods import BusinessPeriod
from app.modules.sales.models import Invoice, Order, PaymentTransaction

STATUS_PENDING = "Chờ đối soát"
STATUS_DISPUTED = "Tranh chấp"
STATUS_PAID = "Thành công"
UNKNOWN_METHOD = "Chưa xác định"
GROUP_BY_VALUES = ("period", "table", "payment_method")


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
