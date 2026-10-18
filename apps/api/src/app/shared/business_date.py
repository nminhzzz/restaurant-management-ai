"""Business Date arithmetic.

A Business Date runs from 06:00 to 06:00 the next day (business rule 13). It is
the effective-date anchor for price and recipe versions, and the grouping unit
of every report.
"""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.errors import BusinessRuleError

BUSINESS_DAY_START_HOUR = 6


def business_date_of(moment: datetime, start_hour: int = BUSINESS_DAY_START_HOUR) -> date:
    shifted = moment - timedelta(hours=start_hour)
    return shifted.date()


def business_date_start(business_date: date, start_hour: int = BUSINESS_DAY_START_HOUR) -> datetime:
    return datetime.combine(business_date, time(hour=start_hour))


def business_date_range(
    business_date: date, start_hour: int = BUSINESS_DAY_START_HOUR
) -> tuple[datetime, datetime]:
    start = business_date_start(business_date, start_hour)
    return start, start + timedelta(days=1)


def business_month_range(
    month: int, start_hour: int = BUSINESS_DAY_START_HOUR
) -> tuple[datetime, datetime]:
    """Return the half-open timestamp window for a YYYYMM business month.

    December 9999 cannot have a representable exclusive endpoint, so it is
    rejected along with malformed keys before any database work begins.
    """
    year, mon = divmod(month, 100)
    if not 1000 <= year <= 9999 or not 1 <= mon <= 12 or month == 999912:
        raise BusinessRuleError("Tháng không hợp lệ (YYYYMM).")
    next_year, next_month = (year + 1, 1) if mon == 12 else (year, mon + 1)
    return (
        business_date_start(date(year, mon, 1), start_hour),
        business_date_start(date(next_year, next_month, 1), start_hour),
    )


def next_business_date(moment: datetime, start_hour: int = BUSINESS_DAY_START_HOUR) -> date:
    """Default effective date proposed when scheduling a price/recipe change."""
    return business_date_of(moment, start_hour) + timedelta(days=1)


VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def now() -> datetime:
    """Single clock seam — timezone-aware Asia/Ho_Chi_Minh."""
    return datetime.now(UTC).astimezone(VN_TZ)
