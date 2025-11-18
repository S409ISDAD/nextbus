import asyncio
from fastapi import WebSocket
from typing import Callable, Dict, List
import json

from backend.deps import get_logger

log = get_logger(__name__)


class MultiChannelManager:
    """tracks local WebSocket connections per worker only."""

    def __init__(self):
        self.connections: Dict[str, Dict[str, List[WebSocket]]] = {}

    async def connect(self, channel: str, key: str, ws: WebSocket):
        await ws.accept()
        self.connections.setdefault(channel, {}).setdefault(key, []).append(ws)

    def disconnect(self, channel: str, key: str, ws: WebSocket):
        conns = self.connections.get(channel, {}).get(key)
        if conns and ws in conns:
            conns.remove(ws)
        if conns and len(conns) == 0:
            del self.connections[channel][key]

    def get_connections(self, channel: str, key: str) -> List[WebSocket]:
        return self.connections.get(channel, {}).get(key, [])


manager = MultiChannelManager()
