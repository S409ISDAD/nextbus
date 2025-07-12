import redis.asyncio as redis
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


def get_redis_url() -> str:
    redis_host = os.getenv("REDIS_HOST", "redis://localhost:6379")
    if not redis_host:
        return "redis://localhost:6379"
    return redis_host


def get_redis_client() -> redis.Redis:
    redis_host = get_redis_url()
    if not redis_host:
        print(
            "Warning: REDIS_HOST environment variable not set. Using default 'localhost:6379'."
        )
        return redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

    else:
        return redis.Redis.from_url(redis_host, decode_responses=True)


async def get_redis() -> redis.Redis:
    return get_redis_client()


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=get_redis_url(),
    default_limits=["100/minute"],
)
