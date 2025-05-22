import threading
import redis.asyncio as redis
import json


SERVICES_CACHE = 120
VEHICLES_CACHE = 30
TRIPS_CACHE = 300
TRIP_CACHE = 60
JOURNEY_CACHE = 300
SERVICE_CACHE = 300
STOPS_CACHE = 600


async def get_cached(key: str, func, args, exp: int, r: redis.Redis):
    cached = await r.get(key)

    if cached:
        time_left = await r.ttl(key)
        if time_left < 5:
            threading.Thread(target=func, args=args)
        return cached["data"]

    # if data is not cached
    result = await func(**args)
    if result:
        r.set(key, value=json.dumps(result), ex=exp)
    return result
