import redis.asyncio as redis
import os
from functools import lru_cache


@lru_cache
def get_redis_client() -> redis.Redis:
    redis_host = os.getenv("REDIS_HOST", "localhost")
    return redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)


async def get_redis() -> redis.Redis:
    return get_redis_client()
