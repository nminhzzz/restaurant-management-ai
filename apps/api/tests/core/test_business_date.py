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


def test_cutoff_history_preserves_transition_and_minute_boundaries():
    from datetime import time

    from app.shared.business_date import CutoffChange, business_date_schedule

    changes = (
        CutoffChange(date(2026, 9, 1), time(4, 30), datetime(2026, 9, 1, 6)),
        CutoffChange(date(2026, 10, 1), time(8, 15), datetime(2026, 10, 1, 8, 15)),
    )
    with business_date_schedule(changes):
        assert business_date_of(datetime(2026, 9, 1, 5, 59)) == date(2026, 8, 31)
        assert business_date_of(datetime(2026, 9, 1, 6)) == date(2026, 9, 1)
        assert business_date_range(date(2026, 9, 1)) == (
            datetime(2026, 9, 1, 6),
            datetime(2026, 9, 2, 4, 30),
        )
        assert business_date_of(datetime(2026, 9, 2, 4, 29)) == date(2026, 9, 1)
        assert business_date_of(datetime(2026, 9, 2, 4, 30)) == date(2026, 9, 2)
        assert business_date_of(datetime(2026, 10, 1, 8, 14)) == date(2026, 9, 30)
        assert business_date_of(datetime(2026, 10, 1, 8, 15)) == date(2026, 10, 1)
        assert business_date_start(date(2026, 8, 31)) == datetime(2026, 8, 31, 6)
    assert business_date_start(date(2026, 10, 1)) == datetime(2026, 10, 1, 6)


async def test_cutoff_context_is_isolated_between_concurrent_tasks():
    import asyncio
    from datetime import time

    from app.shared.business_date import CutoffChange, business_date_schedule

    async def resolve(hour):
        with business_date_schedule((CutoffChange(date(2026, 1, 1), time(hour)),)):
            await asyncio.sleep(0)
            return business_date_of(datetime(2026, 9, 1, 7))

    assert await asyncio.gather(resolve(4), resolve(8)) == [date(2026, 9, 1), date(2026, 8, 31)]


async def test_application_session_loads_and_resets_schedule_for_background_work(session):
    from datetime import time

    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.core.database import BusinessDateSession
    from app.modules.settings.models import BusinessDateCutoff

    session.add(
        BusinessDateCutoff(
            effective_date=date(2026, 1, 1),
            start_time=time(8, 15),
            starts_at=datetime(2026, 1, 1, 8, 15),
        )
    )
    await session.commit()
    factory = async_sessionmaker(session.bind, class_=BusinessDateSession)
    async with factory() as worker_session:
        assert business_date_of(datetime(2026, 9, 1, 7)) == date(2026, 8, 31)
        # Loading a schedule must not leave an implicit transaction open.
        async with worker_session.begin():
            assert business_date_start(date(2026, 9, 1)) == datetime(2026, 9, 1, 8, 15)
    assert business_date_start(date(2026, 9, 1)) == datetime(2026, 9, 1, 6)


def test_configured_month_and_timezone_boundaries():
    from datetime import UTC, time

    from app.shared.business_date import CutoffChange, business_date_schedule, business_month_range

    with business_date_schedule((CutoffChange(date(2026, 12, 1), time(8, 15)),)):
        assert business_month_range(202612) == (
            datetime(2026, 12, 1, 8, 15),
            datetime(2027, 1, 1, 8, 15),
        )
        assert business_date_of(datetime(2026, 12, 1, 1, 14, tzinfo=UTC)) == date(2026, 11, 30)
        assert business_date_of(datetime(2026, 12, 1, 1, 15, tzinfo=UTC)) == date(2026, 12, 1)


def test_reference_clock_is_nested_and_restored(monkeypatch):
    import importlib

    from app.shared import business_date

    # Restore the real clock seam replaced by the suite's default clock fixture.
    original = business_date.now
    importlib.reload(business_date)
    moment = datetime(2026, 1, 1, 7, 45)
    try:
        with business_date.at_time(moment):
            assert business_date.now() == moment
            with business_date.at_time(datetime(2027, 2, 3, 8)):
                assert business_date.now() == datetime(2027, 2, 3, 8)
            assert business_date.now() == moment
        assert business_date.now() != moment
    finally:
        monkeypatch.setattr(business_date, "now", original)
