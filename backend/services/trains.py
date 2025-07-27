from backend.services.caching import TRAIN_CACHE, get_cached
from redis.asyncio import Redis

from backend.utils.fetch_json import fetch_rtt_json


async def get_departures(station_code: str, r: Redis):
    async def fetch(station_code):
        url = f"https://api.rtt.io/api/v1/json/search/{station_code}"
        trains = await fetch_rtt_json(url)

        if not trains:
            return None

        return trains

    trains = await get_cached(
        f"trains:departures:{station_code}",
        fetch,
        (station_code,),
        TRAIN_CACHE,
        r,
    )

    return trains


async def get_arrivals(station_code: str, r: Redis):
    async def fetch(station_code):
        url = f"https://api.rtt.io/api/v1/json/search/{station_code}/arrivals"
        trains = await fetch_rtt_json(url)

        if not trains:
            return None

        return trains

    trains = await get_cached(
        f"trains:arrivals:{station_code}",
        fetch,
        (station_code,),
        TRAIN_CACHE,
        r,
    )

    return trains
