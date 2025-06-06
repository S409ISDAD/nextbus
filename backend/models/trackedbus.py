from typing import Optional
from pydantic import BaseModel

from backend.models.journey import Journey
from backend.models.prediction import Prediction
from backend.models.service import Service
from .progress import Progress


class TrackedBus(BaseModel):
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
    journey: Journey
    coords: list[float]


class Bus:
    def __init__(
        self,
        id,
        service,
        destination,
        reg,
        fleet_num,
        journey_id,
        times,
        delay,
        lateness,
        # speed,
        progress,
        coords,
        timestamp,
    ):
        self.id: int = id
        self.service: str = service  # bus number e.g. 64
        self.destination: str = destination
        self.reg: str = reg  # vehicle license plate
        self.fleet_num: str = fleet_num
        self.journey_id: int = journey_id
        self.delay: int = delay  # how many seconds behind/ahead e.g. 120 = 2 min late, -60 = 1 min early
        self.lateness: str = lateness  # text to display how late or early it is
        self.expected: int = times[
            "expected"
        ]  # expected arrival time at stop (unix timestamp)
        self.scheduled: int = times[
            "scheduled"
        ]  # scheduled arrival time at stop (unix timestamp)
        self.started: bool = not (times["not_started"])
        # self.speed: float = speed  # how fast the bus is going
        self.progress: float = progress  # progress between 2 stops, 0-1
        self.coords: list[float] = coords
        self.timestamp: int = timestamp  # time when the data was fetched, indicates age
