import asyncio
import json
from fastapi.encoders import jsonable_encoder
from time import time
from redis.asyncio import Redis
from typing import Set
from datetime import datetime, timezone
from .get_departures import get_departures
from backend.deps import DateTimeEncoder
import logging
import sentry_sdk

log = logging.getLogger(__name__)

active: dict[str, Set[str]] = {}
publish_tasks: dict[str, asyncio.Task] = {}


async def publish_loop(channel: str, key: str, redis: Redis):
    try:
        times = []
        while key in active[channel]:
            with sentry_sdk.start_span(op="start_publishing", description=key):
                start = time()
                departures = await get_departures(key, redis)
                duration = round(time() - start, 2)

                times.append(duration)

                avg = round(sum(times) / len(times), 2)

                if len(times) > 5:
                    times.pop()

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

            await asyncio.sleep(20 - avg)
    except asyncio.CancelledError:
        pass
    finally:
        publish_tasks.pop(key, None)
        active[channel].discard(key)


async def start_publishing(channel: str, key: str, redis: Redis):
    active.setdefault(channel, set())
    if key not in active[channel]:
        active[channel].add(key)
        log.debug(f"starting pub task for {key}")
        task = asyncio.create_task(publish_loop(channel, key, redis))
        publish_tasks[key] = task
    else:
        log.warning("task already started")


async def stop_publishing(key: str):
    task = publish_tasks.get(key)
    if task:
        log.debug(f"stopping pub task for {key}")

        task.cancel()
