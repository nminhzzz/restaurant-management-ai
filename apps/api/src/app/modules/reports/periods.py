"""Business-period arithmetic for the reporting module (FR-REP-01).

Grouping always follows `BusinessDate` (06:00 → 06:00), never the calendar date of
`ThoiDiem`; a request that anchors on a calendar day is resolved onto the business
dates that contain it.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from app.core.errors import BusinessRuleError

GRANULARITIES = ("day", "week", "month", "year")


@dataclass(frozen=True)
class BusinessPeriod:
    start: date
    end: date
    granularity: str

    @property
    def month_key(self) -> int:
        """`YYYYMM`, the key of GIA_BINH_QUAN_THANG."""
        return self.start.year * 100 + self.start.month


def resolve_period(granularity: str, anchor: date) -> BusinessPeriod:
    if granularity == "day":
        return BusinessPeriod(anchor, anchor, granularity)
    if granularity == "week":
        start = anchor - timedelta(days=anchor.weekday())
        return BusinessPeriod(start, start + timedelta(days=6), granularity)
    if granularity == "month":
        start = anchor.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return BusinessPeriod(start, end, granularity)
    if granularity == "year":
        return BusinessPeriod(date(anchor.year, 1, 1), date(anchor.year, 12, 31), granularity)
    raise BusinessRuleError("Kỳ báo cáo phải là day/week/month/year.")


def month_period(month: str) -> BusinessPeriod:
    """`"2026-09"` → the September business dates."""
    try:
        year_text, month_text = month.split("-")
        anchor = date(int(year_text), int(month_text), 1)
    except (ValueError, AttributeError) as exc:
        raise BusinessRuleError("Tháng phải có dạng YYYY-MM.") from exc
    return resolve_period("month", anchor)
