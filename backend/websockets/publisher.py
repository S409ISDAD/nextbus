import asyncio
import json
from fastapi.encoders import jsonable_encoder
from time import time
from redis.asyncio import Redis
from datetime import datetime, timezone
from ..tasks.get_departures import get_departures
from backend.deps import DateTimeEncoder, get_redis
import sentry_sdk
from asyncio import to_thread

from backend.deps import get_logger

log = get_logger(__name__)

sync_redis = get_redis(sync=True)

local_publish_tasks: dict[str, asyncio.Task] = {}

REDIS_LOCK_EXPIRE = 60  # seconds


def redis_active_key(channel: str) -> str:
    return f"active:{channel}"


async def acquire_publish_lock(redis: Redis, channel: str, key: str) -> bool:
    lock_key = f"lock:publish:{channel}:{key}"
    return await redis.set(lock_key, "1", nx=True, ex=REDIS_LOCK_EXPIRE)


async def release_publish_lock(redis: Redis, channel: str, key: str):
    lock_key = f"lock:publish:{channel}:{key}"
    await redis.delete(lock_key)


async def publish_loop(channel: str, key: str, redis: Redis):
    try:
        times = []
        while await redis.sismember(redis_active_key(channel), key):
            with sentry_sdk.start_span(op="start_publishing", description=key):
                start = time()
                departures = await to_thread(get_departures, key, sync_redis)
                duration = round(time() - start, 2)

                times.append(duration)

                if len(times) > 5:
                    times.pop()

                avg = round(sum(times) / len(times), 2)

                payload = {
                    "type": "departures",
                    "data": {
                        "timestamp": datetime.now(timezone.utc),
                        "buses": jsonable_encoder(departures),
                    },
                }

                await redis.publish(
                    f"stop:departures:{key}", json.dumps(payload, cls=DateTimeEncoder)
                )
                await redis.set(
                    f"stop:departures:{key}",
                    json.dumps(payload, cls=DateTimeEncoder),
                    ex=40,
                )

            await asyncio.sleep(max(0, 20 - avg))
    except asyncio.CancelledError:
        pass
    finally:
        await release_publish_lock(redis, channel, key)
        await redis.srem(redis_active_key(channel), key)
        log.debug(f"Publish loop ended for {channel}:{key}")
        local_publish_tasks.pop(key, None)


async def start_publishing(channel: str, key: str, redis: Redis):
    got_lock = await acquire_publish_lock(redis, channel, key)
    if not got_lock:
        log.debug(f"Publish task already active in another process for {key}")
        return

    await redis.sadd(redis_active_key(channel), key)
    log.debug(f"Starting publish task for {key}")

    if key not in local_publish_tasks:
        task = asyncio.create_task(publish_loop(channel, key, redis))
        local_publish_tasks[key] = task

        def _done_callback(t: asyncio.Task):
            local_publish_tasks.pop(key, None)
            log.debug(f"Local task removed for {key}")

        task.add_done_callback(_done_callback)


async def stop_publishing(channel: str, key: str, redis: Redis):
    await redis.srem(redis_active_key(channel), key)
    task = local_publish_tasks.pop(key, None)
    if task:
        task.cancel()
        log.debug(f"Cancelled local publish task for {key}")
