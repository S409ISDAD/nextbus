import asyncio
from fastapi import WebSocket
from typing import Callable, Dict, List

from backend.deps import get_logger

log = get_logger(__name__)


class MultiChannelManager:
    """tracks local WebSocket connections per worker only."""

    def __init__(self):
        self.connections: Dict[str, Dict[str, List[WebSocket]]] = {}
        self.tasks: Dict[str, asyncio.Task] = {}

    async def connect(
        self, channel: str, key: str, ws: WebSocket, redis, background_func: Callable
    ):
        await ws.accept()
        self.connections.setdefault(channel, {}).setdefault(key, []).append(ws)

        if background_func:
            if key not in self.tasks:
                log.debug(f"Starting background task for {channel}:{key}")
                task = asyncio.create_task(background_func(key, redis))
                self.tasks[key] = task

    def disconnect(self, channel: str, key: str, ws: WebSocket):
        conns = self.connections.get(channel, {}).get(key)
        if conns and ws in conns:
            conns.remove(ws)
        if conns and len(conns) == 0:
            del self.connections[channel][key]
            task = self.tasks.pop(key, None)
            if task:
                task.cancel()
                log.debug(f"Cancelled background task for {channel}:{key}")

    def get_connections(self, channel: str, key: str) -> List[WebSocket]:
        return self.connections.get(channel, {}).get(key, [])


manager = MultiChannelManager()
