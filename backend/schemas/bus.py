from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from backend.schemas.journey import Journey
from backend.schemas.livery import Livery
from backend.schemas.prediction import Prediction
from backend.schemas.service import Service
from .progress import Progress


class ScheduledBus(BaseModel):
    type: str = "scheduled"
    destination: str
    line: str
    scheduled: datetime
    expected: datetime
    started: bool
    trip: int
    status: str


class TrackedBus(BaseModel):
    type: str = "tracked"
    id: int
    trip: int
    timestamp: Optional[datetime]
    service: Optional[Service]
    destination: str
    reg: str  # vehicle license plate
    fleet_num: str
    bus_type: str  # double decker
    journey_id: int
    delay: int  # how many seconds behind/ahead e.g. 120 = 2 min late, -60 = 1 min early
    expected: Optional[datetime]  # expected arrival time at stop (iso string)
    scheduled: Optional[datetime]  # scheduled arrival time at stop (iso string)
    started: bool  # if the bus has started the route or is waiting at the first stop
    finished: bool  # if the bus has finished the route
    speed: Optional[float]  # how fast the bus is going
    progress: Progress
    predictions: list[Prediction]
    livery: Optional[Livery]
    journey: Journey
    coords: list[float]
    status: str
