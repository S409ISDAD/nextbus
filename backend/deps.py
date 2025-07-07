import redis.asyncio as redis
import os
from functools import lru_cache


def get_redis_client() -> redis.Redis:
    redis_host = os.getenv("REDIS_HOST")
    if not redis_host:
        print(
            "Warning: REDIS_HOST environment variable not set. Using default 'localhost:6379'."
        )
        return redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

    else:
        return redis.Redis.from_url(redis_host, decode_responses=True)


async def get_redis() -> redis.Redis:
    return get_redis_client()
