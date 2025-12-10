import redis
import json
from typing import Callable

from backend.deps import DateTimeEncoder, datetime_decoder

# cache time config
HOUR = 3600
DAY = HOUR * 24

SERVICES_CACHE = DAY
TRIPS_CACHE = 60
BUS_CACHE = 18
JOURNEY_CACHE = DAY
# JOURNEY_CACHE = 1
SERVICE_CACHE = DAY
STOPS_CACHE = DAY
TIMETABLE_CACHE = 3600
# TIMETABLE_CACHE = 1
LIVERY_CACHE = DAY
TRAIN_CACHE = 29


def get_cached(key: str, func: Callable, args: tuple, exp: int, r: redis.Redis):
    """a helper function for getting and storing cached data.

    Args:
        key (str): the redis key to use
        func (Callable): the data fetching function to call if no cache
        args (tuple): arguments to pass to the function
        exp (int): expiration time in seconds
        r (redis.Redis): redis instance

    """
    cached = r.get(key)

    if cached:
        time_left = r.ttl(key)
        if time_left < 15:  # type: ignore
            func(*args)
        return json.loads(cached, object_hook=datetime_decoder)["data"]  # type: ignore

    result = func(*args)
    if result:
        r.set(
            key,
            value=json.dumps(
                {"data": result},
                cls=DateTimeEncoder,
                default=lambda o: o.__dict__ if hasattr(o, "__dict__") else str(o),
            ),
            ex=exp if exp > 0 else None,
        )
    return result
