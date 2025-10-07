from datetime import date

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
        block_id="WI30", sequence=1, start_time="08:00", end_time="09:00"
    )
    j2 = journey_factory(
        block_id="WI30", sequence=2, start_time="10:00", end_time="11:00"
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

    cal_exception = CalendarException(
        calendar_id=cal.id,
        start_date=date(2025, 10, 19),
        end_date=date(2025, 10, 19),
        operating=True,
    )  # operate on a sunday
    db_session.add(cal_exception)
    db_session.flush()

    j1 = journey_factory(
        block_id="WI30", sequence=1, start_time="08:00", end_time="09:00", calendar=cal
    )

    db_session.commit()

    assert j1.is_valid(date(2025, 10, 7))  # tuesday
    assert j1.is_valid(date(2025, 10, 6))  # monday
    assert j1.is_valid(date(2025, 10, 19))  # exception sunday
    assert not j1.is_valid(date(2025, 12, 25))  # bank holiday
    assert not j1.is_valid(date(2024, 10, 7))  # wrong year
    assert not j1.is_valid(date(2025, 10, 5))  # sunday

    valid_cal_ids = [
        c.id
        for c in db_session.query(Calendar)
        .filter(journey_is_valid_filter(date(2025, 10, 7)))
        .all()
    ]
    assert cal.id in valid_cal_ids  # tuesday

    valid_cal_ids = [
        c.id
        for c in db_session.query(Calendar)
        .filter(journey_is_valid_filter(date(2025, 10, 6)))
        .all()
    ]
    assert cal.id in valid_cal_ids  # monday

    valid_cal_ids = [
        c.id
        for c in db_session.query(Calendar)
        .filter(journey_is_valid_filter(date(2025, 10, 19)))
        .all()
    ]
    assert cal.id in valid_cal_ids  # exception sunday

    valid_cal_ids = [
        c.id
        for c in db_session.query(Calendar)
        .filter(journey_is_valid_filter(date(2025, 12, 25)))
        .all()
    ]
    assert cal.id not in valid_cal_ids  # bank holiday

    valid_cal_ids = [
        c.id
        for c in db_session.query(Calendar)
        .filter(journey_is_valid_filter(date(2025, 10, 5)))
        .all()
    ]
    assert cal.id not in valid_cal_ids  # sunday

    valid_cal_ids = [
        c.id
        for c in db_session.query(Calendar)
        .filter(journey_is_valid_filter(date(2024, 10, 7)))
        .all()
    ]
    assert cal.id not in valid_cal_ids  # wrong year
