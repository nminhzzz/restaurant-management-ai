"""Business Date arithmetic for the configured local day boundary."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

DEFAULT_BUSINESS_DAY_START = time(6)


def business_date_of(moment: datetime, start_time: time = DEFAULT_BUSINESS_DAY_START) -> date:
    return moment.date() - timedelta(days=moment.time() < start_time)


def business_date_start(
    business_date: date, start_time: time = DEFAULT_BUSINESS_DAY_START
) -> datetime:
    return datetime.combine(business_date, start_time)


def business_date_range(
    business_date: date, start_time: time = DEFAULT_BUSINESS_DAY_START
) -> tuple[datetime, datetime]:
    start = business_date_start(business_date, start_time)
    return start, start + timedelta(days=1)


def next_business_date(moment: datetime, start_time: time = DEFAULT_BUSINESS_DAY_START) -> date:
    """Default effective date proposed when scheduling a price/recipe change."""
    return business_date_of(moment, start_time) + timedelta(days=1)


VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def now() -> datetime:
    """Single clock seam — timezone-aware Asia/Ho_Chi_Minh."""
    return datetime.now(UTC).astimezone(VN_TZ)
