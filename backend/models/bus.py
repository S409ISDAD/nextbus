from typing import Optional
from pydantic import BaseModel

from backend.models.journey import Journey
from backend.models.livery import Livery
from backend.models.prediction import Prediction
from backend.models.service import Service
from .progress import Progress


class ScheduledBus(BaseModel):
    type: str = "scheduled"
    destination: str
    line: str
    scheduled: int
    expected: int
    started: bool
    trip: int
    status: str


class TrackedBus(BaseModel):
    type: str = "tracked"
    id: int
    service: Optional[Service]
    destination: str
    reg: str  # vehicle license plate
    fleet_num: str
    journey_id: int
    delay: int  # how many seconds behind/ahead e.g. 120 = 2 min late, -60 = 1 min early
    expected: Optional[int]  # expected arrival time at stop (unix timestamp)
    scheduled: Optional[int]  # scheduled arrival time at stop (unix timestamp)
    started: bool  # if the bus has started the route or is waiting at the first stop
    finished: bool  # if the bus has finished the route
    speed: Optional[float]  # how fast the bus is going
    progress: Progress
    predictions: list[Prediction]
    livery: Optional[Livery]
    journey: Journey
    coords: list[float]
    status: str
