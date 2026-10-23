"""Seed timestamps follow configured Business Date intervals."""


def test_seed_moment_stays_inside_short_transition_day():
    from datetime import date, datetime, time

    from scripts.seed.operations import _moment

    from app.shared import business_date

    day = date(2026, 10, 1)
    with business_date.business_date_schedule(
        (business_date.CutoffChange(day, time(4, 30), datetime(2026, 10, 1, 6)),)
    ):
        # 05:00 exists on neither side of this shortened day's interval.
        assert business_date.business_date_of(_moment(day, 5)) == day
