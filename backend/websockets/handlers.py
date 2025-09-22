import asyncio
import datetime
import json

import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect

from backend.deps import datetime_decoder
from backend.tasks.publisher import start_publishing, stop_publishing
from backend.websockets.manager import manager
import logging

log = logging.getLogger(__name__)


def convert(obj):
    if isinstance(obj, dict):
        return {k: convert(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert(i) for i in obj]
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return obj


async def stop_subscribe(stop_id: str, redis: redis.Redis):
    pubsub = None
    try:
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"stop:departures:{stop_id}")

        async for message in pubsub.listen():
            if message is None:
                continue
            if message["type"] != "message":
                continue

            try:
                data = json.loads(message["data"], object_hook=datetime_decoder)
            except Exception:
                continue

            data_serializable = convert(data)

            for ws in list(manager.get_connections("stop", stop_id)):
                try:
                    await ws.send_json(data_serializable)
                except Exception:
                    await manager.disconnect("stop", stop_id, ws, redis)
    except asyncio.CancelledError:
        if pubsub:
            await pubsub.unsubscribe(f"stop:departures:{stop_id}")
    except Exception as e:
        log.debug(f"[Redis subscriber error] {e}")


async def handle_departures(channel: str, key: str, websocket: WebSocket, redis):
    await manager.connect(
        channel, key, websocket, redis, background_func=stop_subscribe
    )
    await start_publishing(channel, key, redis)

    try:
        cached = await redis.get(f"stop:departures:{key}")

        if cached:
            log.debug(f"sending cached on first conn {key}")
            data = json.loads(cached, object_hook=datetime_decoder)
            data_serializable = convert(data)

            await websocket.send_json(data_serializable)
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        await manager.disconnect(channel, key, websocket, redis)
        if not manager.get_connections(channel, key):
            await stop_publishing(key)
