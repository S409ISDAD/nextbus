import asyncio
import json

import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect

from backend.tasks.publisher import start_publishing, stop_publishing
from backend.websockets.manager import manager


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
                data = json.loads(message["data"])
            except Exception:
                continue

            for ws in list(manager.get_connections("stop", stop_id)):
                try:
                    await ws.send_json(data)
                except Exception:
                    manager.disconnect("stop", stop_id, ws)
    except asyncio.CancelledError:
        if pubsub:
            await pubsub.unsubscribe(f"stop:departures:{stop_id}")
    except Exception as e:
        print(f"[Redis subscriber error] {e}")


async def handle_departures(channel: str, key: str, websocket: WebSocket, redis):
    await manager.connect(
        channel, key, websocket, redis, background_func=stop_subscribe
    )
    await start_publishing(channel, key, redis)

    try:
        cached = await redis.get(f"stop:departures:{key}")

        if cached:
            print(f"sending cached on first conn {key}")
            await websocket.send_json(json.loads(cached))
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(channel, key, websocket)
        if not manager.get_connections(channel, key):
            await stop_publishing(key)
