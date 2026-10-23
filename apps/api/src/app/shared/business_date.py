"""Effective-dated Business Date boundaries in restaurant local time.

The immutable schedule belongs to a request/session context. A transition starts
no earlier than the previously scheduled boundary, so changing the cutoff cannot
reclassify the current day or previously recorded transactions.
"""

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError

BUSINESS_DAY_START_HOUR = 6
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


@dataclass(frozen=True)
class CutoffChange:
    effective_date: date
    start_time: time
    starts_at: datetime | None = None


_clock_override: ContextVar[datetime | None] = ContextVar("business_date_clock", default=None)

_schedule: ContextVar[tuple[CutoffChange, ...]] = ContextVar("business_date_schedule", default=())


@contextmanager
def business_date_schedule(changes: Iterable[CutoffChange]) -> Iterator[None]:
    token = _schedule.set(tuple(sorted(changes, key=lambda change: change.effective_date)))
    try:
        yield
    finally:
        _schedule.reset(token)


def cutoff_for(business_date: date) -> time:
    result = time(BUSINESS_DAY_START_HOUR)
    for change in _schedule.get():
        if change.effective_date > business_date:
            break
        result = change.start_time
    return result


def business_date_start(business_date: date, start_hour: int | None = None) -> datetime:
    if start_hour is not None:
        return datetime.combine(business_date, time(hour=start_hour))
    for change in _schedule.get():
        if change.effective_date == business_date and change.starts_at is not None:
            return change.starts_at
    return datetime.combine(business_date, cutoff_for(business_date))


def business_date_of(moment: datetime, start_hour: int | None = None) -> date:
    local = moment.astimezone(VN_TZ).replace(tzinfo=None) if moment.tzinfo else moment
    day = local.date()
    if local < business_date_start(day, start_hour):
        day -= timedelta(days=1)
    return day


def business_date_range(
    business_date: date, start_hour: int | None = None
) -> tuple[datetime, datetime]:
    return (
        business_date_start(business_date, start_hour),
        business_date_start(business_date + timedelta(days=1), start_hour),
    )


def business_month_range(month: int, start_hour: int | None = None) -> tuple[datetime, datetime]:
    """Return the half-open local timestamp window for a YYYYMM month."""
    year, mon = divmod(month, 100)
    if not 1000 <= year <= 9999 or not 1 <= mon <= 12 or month == 999912:
        raise BusinessRuleError("Tháng không hợp lệ (YYYYMM).")
    next_year, next_month = (year + 1, 1) if mon == 12 else (year, mon + 1)
    return (
        business_date_start(date(year, mon, 1), start_hour),
        business_date_start(date(next_year, next_month, 1), start_hour),
    )


def next_business_date(moment: datetime, start_hour: int | None = None) -> date:
    """Default effective date proposed when scheduling a price/recipe change."""
    return business_date_of(moment, start_hour) + timedelta(days=1)


@contextmanager
def at_time(moment: datetime) -> Iterator[None]:
    """Set a task-local reference instant for deterministic evaluations and jobs."""
    token = _clock_override.set(moment)
    try:
        yield
    finally:
        _clock_override.reset(token)


def now() -> datetime:
    """Single clock seam — timezone-aware Asia/Ho_Chi_Minh in live operation."""
    reference = _clock_override.get()
    return reference if reference is not None else datetime.now(UTC).astimezone(VN_TZ)


async def load_business_date_schedule(session: AsyncSession) -> tuple[CutoffChange, ...]:
    """Read the committed/transaction-local history without process-wide state."""
    from sqlalchemy import select

    from app.modules.settings.models import BusinessDateCutoff

    rows = (
        await session.scalars(
            select(BusinessDateCutoff).order_by(BusinessDateCutoff.effective_date)
        )
    ).all()
    return tuple(CutoffChange(row.effective_date, row.start_time, row.starts_at) for row in rows)
