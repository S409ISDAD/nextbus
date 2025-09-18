from datetime import datetime as dt
from datetime import timedelta

from backend.deps import LONDON


def check_scheduled_time(scheduled: dt, current_time: dt) -> dt:
    time_difference = (scheduled - current_time).total_seconds()

    # time is more than 12h in the future so bus is most likely yesterday, subtract 1 day
    if time_difference / 3600 > 12:
        scheduled -= timedelta(days=1)

    # time is more than 12h in the past so bus is most likely tomorrow, add 1 day
    elif time_difference / 3600 < -12:
        scheduled += timedelta(days=1)

    return scheduled


def to_datetime(date_str):
    """Convert a date string to a datetime object."""

    if not date_str:
        return None
    try:
        return dt.strptime(date_str, "%Y-%m-%dT%H:%M:%S").astimezone(LONDON)
    except ValueError:
        try:
            return dt.strptime(date_str, "%Y-%m-%d").astimezone(LONDON).date()
        except ValueError:
            return None
