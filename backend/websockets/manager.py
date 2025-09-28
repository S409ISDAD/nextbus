import asyncio
from fastapi import WebSocket
from typing import Callable, Dict, List
import json
import logging

log = logging.getLogger(__name__)


class MultiChannelManager:
    def __init__(self):
        self.connections: Dict[str, Dict[str, List[WebSocket]]] = {
            "stop": {},
            "bus": {},
            "journey": {},
        }
        self.tasks: dict[str, asyncio.Task] = {}

    async def connect(
        self,
        channel: str,
        key: str,
        websocket: WebSocket,
        redis,
        background_func: Callable,
    ):
        await websocket.accept()
        self.connections.setdefault(channel, {}).setdefault(key, []).append(websocket)
        await redis.incr("total_ws_connections")
        client_id = websocket.query_params.get("client_id")
        if client_id:
            await redis.sadd("clients", client_id)
            await redis.sadd("total_clients", client_id)
            await redis.sadd("total_users", client_id)

        if key not in self.tasks:
            self.tasks[key] = asyncio.create_task(background_func(key, redis))

    async def disconnect(self, channel: str, key: str, websocket: WebSocket, redis):
        self.connections[channel][key].remove(websocket)
        await redis.decr("total_ws_connections")
        client_id = websocket.query_params.get("client_id")
        if client_id:
            await redis.srem("clients", client_id)
        if not self.connections[channel].get(key):
            if key in self.connections[channel]:
                del self.connections[channel][key]
            task = self.tasks.pop(key, None)
            if task:
                task.cancel()

    async def send(self, channel: str, key: str, message: dict):
        if key in self.connections.get(channel, {}):
            data = json.dumps(message)
            for ws in self.connections[channel][key]:
                try:
                    await ws.send_text(data)
                except:  # noqa: E722
                    pass

    def get_connections(self, channel: str, key: str) -> List[WebSocket]:
        return self.connections.get(channel, {}).get(key, [])


manager = MultiChannelManager()
