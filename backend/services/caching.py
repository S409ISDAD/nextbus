import inspect
import asyncio
import redis.asyncio as redis
import json

from backend.deps import DateTimeEncoder, datetime_decoder

HOUR = 3600
DAY = HOUR * 24

SERVICES_CACHE = DAY
TRIPS_CACHE = 60
BUS_CACHE = 18
JOURNEY_CACHE = DAY
SERVICE_CACHE = DAY
STOPS_CACHE = DAY
TIMETABLE_CACHE = 3600
LIVERY_CACHE = DAY
TRAIN_CACHE = 29


async def get_cached(key: str, func, args: tuple, exp: int, r: redis.Redis):
    cached = await r.get(key)

    if cached:
        time_left = await r.ttl(key)
        if time_left < 15:
            if inspect.iscoroutinefunction(func):
                asyncio.create_task(func(*args))
        return json.loads(cached, object_hook=datetime_decoder)["data"]

    result = await func(*args)
    if result:
        await r.set(
            key,
            value=json.dumps(
                {"data": result},
                cls=DateTimeEncoder,
                default=lambda o: o.__dict__ if hasattr(o, "__dict__") else str(o),
            ),
            ex=exp,
        )
    return result
