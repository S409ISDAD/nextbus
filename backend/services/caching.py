import inspect
import asyncio
import redis.asyncio as redis
import json


SERVICES_CACHE = 600
VEHICLES_CACHE = 30
TRIPS_CACHE = 300
BUS_CACHE = 60
JOURNEY_CACHE = 60
SERVICE_CACHE = 300
STOPS_CACHE = 600


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
