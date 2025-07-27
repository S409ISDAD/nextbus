import inspect
import asyncio
import redis.asyncio as redis
import json

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
        # print(f"  cached: {key}")
        time_left = await r.ttl(key)
        if time_left < 15:
            # print(f"     cache expiring soon {key}, regenerating")
            if inspect.iscoroutinefunction(func):
                asyncio.create_task(func(*args))
        return json.loads(cached)["data"]

    # print(f"not cached: {key}")

    # if data is not cached
    result = await func(*args)
    if result:
        await r.set(key, value=json.dumps({"data": result}), ex=exp)
    return result
