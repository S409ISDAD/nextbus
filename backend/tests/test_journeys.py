from datetime import date, timedelta

from backend.models import (
    Calendar,
    BankHoliday,
    CalendarException,
    CalendarToBankHoliday,
    BankHolidayDate,
    journey_is_valid_filter,
)


def test_previous_journey(db_session, journey_factory):
    j1 = journey_factory(
        block_id="WI30",
        sequence=1,
        start_time=timedelta(hours=8),
        end_time=timedelta(hours=9),
    )
    j2 = journey_factory(
        block_id="WI30",
        sequence=2,
        start_time=timedelta(hours=10),
        end_time=timedelta(hours=11),
    )

    prev = j2.get_previous_journey(db_session, date=date(2025, 10, 7))
    print(prev, j1, j2)
    assert prev.id == j1.id


def test_valid(db_session, journey_factory, calendar_factory):
    bh = BankHoliday(name="Test Holiday")
    db_session.add(bh)
    db_session.flush()

    bh_date = BankHolidayDate(bank_holiday_name=bh.name, date=date(2025, 12, 25))
    db_session.add(bh_date)
    db_session.flush()

    cal = calendar_factory(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        monday=True,
        tuesday=True,
        wednesday=True,
        thursday=True,
        friday=True,
        saturday=False,
        sunday=False,
    )

    cal_to_bh = CalendarToBankHoliday(
        calendar_id=cal.id, bank_holiday=bh.name, operating=False
    )  # no service on BH
    db_session.add(cal_to_bh)
    db_session.flush()

    cal_exceptions = [
        CalendarException(
            calendar_id=cal.id,
            start_date=date(2025, 10, 18),
            end_date=date(2025, 10, 19),
            operating=True,
            special=True,
        ),  # operate on a weekend, special condition only on these dates
        CalendarException(
            calendar_id=cal.id,
            start_date=date(2025, 9, 1),
            end_date=date(2025, 12, 17),
            operating=True,
            special=False,
        ),  # operate normally on weekdays in this range
        CalendarException(
            calendar_id=cal.id,
            start_date=date(2025, 10, 20),
            end_date=date(2025, 10, 20),
            operating=False,
        ),  # do not operate on this monday
        CalendarException(
            calendar_id=cal.id,
            start_date=date(2025, 11, 1),
            end_date=date(2025, 11, 1),
            operating=True,
            special=True,
        ),  # operate on this saturday only
        CalendarException(
            calendar_id=cal.id,
            start_date=date(2025, 12, 25),
            end_date=date(2025, 12, 25),
            operating=True,
            special=False,
        ),  # operate on BH as normal service
    ]
    db_session.add_all(cal_exceptions)
    db_session.flush()

    j1 = journey_factory(
        block_id="WI30", sequence=1, start_time="08:00", end_time="09:00", calendar=cal
    )

    db_session.commit()

    valid_dates = [
        date(2025, 1, 1),  # boundary
        date(2025, 12, 31),  # boundary
        date(2025, 10, 6),  # monday
        date(2025, 10, 7),  # tuesday
        date(2025, 10, 2),  # thursday
        date(2025, 10, 18),  # exception saturday
        date(2025, 10, 19),  # exception sunday
        date(2025, 11, 1),  # exception saturday
    ]

    invalid_dates = [
        date(2024, 12, 31),  # before start
        date(2026, 1, 1),  # after end
        date(2025, 12, 25),  # bank holiday
        date(2025, 10, 20),  # exception monday
        date(2024, 10, 7),  # wrong year
        date(2025, 10, 5),  # sunday
        date(2025, 12, 25),  # bank holiday wins over normal inclusion
    ]

    for d in valid_dates:
        valid_cal_ids = [
            c.id
            for c in db_session.query(Calendar).filter(journey_is_valid_filter(d)).all()
        ]
        assert j1.is_valid(d), f"Journey should be valid on {d}"
        assert (
            cal.id in valid_cal_ids
        ), f"Journey should be valid on {d}"  # make sure both functions agree
    for d in invalid_dates:
        valid_cal_ids = [
            c.id
            for c in db_session.query(Calendar).filter(journey_is_valid_filter(d)).all()
        ]
        assert not j1.is_valid(d), f"Journey should be invalid on {d}"
        assert (
            cal.id not in valid_cal_ids
        ), f"Journey should be valid on {d}"  # make sure both functions agree
