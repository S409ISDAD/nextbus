from fastapi import APIRouter, Depends, WebSocket

from backend.deps import get_redis
from backend.websockets.handlers import handle_departures
import logging

log = logging.getLogger(__name__)
ws_router = APIRouter()


@ws_router.websocket("/ws/stop/{stop_id}")
async def ws_stop(websocket: WebSocket, stop_id: str, redis=Depends(get_redis)):
    await handle_departures("stop", stop_id, websocket, redis)


@ws_router.websocket("/ws/bus/{bus_id}")
async def ws_bus(websocket: WebSocket, bus_id: str, redis=Depends(get_redis)):
    pass
    # await _handle_ws("bus", bus_id, websocket, redis)


@ws_router.websocket("/ws/journey/{journey_id}")
async def ws_journey(websocket: WebSocket, journey_id: str, redis=Depends(get_redis)):
    pass
    # await _handle_ws("journey", journey_id, websocket, redis)
