from datetime import date, datetime

from app.shared.business_date import (
    business_date_of,
    business_date_range,
    business_date_start,
    next_business_date,
)


def test_evening_belongs_to_the_same_business_date() -> None:
    assert business_date_of(datetime(2026, 8, 27, 23, 30)) == date(2026, 8, 27)


def test_early_morning_belongs_to_the_previous_business_date() -> None:
    assert business_date_of(datetime(2026, 8, 28, 5, 59)) == date(2026, 8, 27)


def test_boundary_hour_starts_the_new_business_date() -> None:
    assert business_date_of(datetime(2026, 8, 28, 6, 0)) == date(2026, 8, 28)


def test_range_spans_exactly_one_business_day() -> None:
    start, end = business_date_range(date(2026, 8, 27))

    assert start == datetime(2026, 8, 27, 6, 0)
    assert end == datetime(2026, 8, 28, 6, 0)
    assert business_date_start(date(2026, 8, 27)) == start


def test_next_business_date_is_the_default_effective_date() -> None:
    assert next_business_date(datetime(2026, 8, 27, 10, 0)) == date(2026, 8, 28)


def test_month_range_uses_business_day_boundary_and_rolls_over_december() -> None:
    from app.shared.business_date import business_month_range

    assert business_month_range(202612) == (datetime(2026, 12, 1, 6), datetime(2027, 1, 1, 6))
    assert business_month_range(202609, start_hour=8) == (
        datetime(2026, 9, 1, 8),
        datetime(2026, 10, 1, 8),
    )
    assert business_month_range(999911) == (datetime(9999, 11, 1, 6), datetime(9999, 12, 1, 6))
