from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from backend.schemas.journey import Journey
from backend.schemas.livery import Livery
from backend.schemas.prediction import Prediction
from backend.schemas.service import Service
from .confidence import Confidence
from .progress import Progress


class VehicleType(BaseModel):
    id: int
    name: str
    style: Optional[str]
    fuel: str
    double_decker: bool
    coach: bool
    electric: bool


class Vehicle(BaseModel):
    id: int
    reg: str  # vehicle license plate
    fleet_num: str
    vehicle_type: Optional[VehicleType]
    livery: Optional[Livery]
    name: Optional[str]
    special_features: Optional[list[str]]


class ScheduledBus(BaseModel):
    type: str = "scheduled"
    destination: str
    line: str
    scheduled: datetime
    expected: datetime
    started: bool
    trip: Optional[int]  # link to bustimes trip if exists
    db_journey: Optional[int]  # link to scheduled journey if exists
    status: str
    source: str  # "api" or "db"


class TrackedBus(BaseModel):
    type: str = "tracked"
    id: int
    trip: Optional[int] = None  # link to bustimes trip if exists
    db_journey: Optional[int] = None  # link to scheduled journey if exists
    timestamp: Optional[datetime]
    service: Optional[Service]
    destination: str
    vehicle: Optional[Vehicle]
    bus_type: str
    journey_id: int
    delay: int  # how many seconds behind/ahead e.g. 120 = 2 min late, -60 = 1 min early
    expected: Optional[datetime]  # expected arrival time at stop (iso string)
    min_expected: Optional[
        datetime
    ]  # earliest expected arrival time at stop (iso string)
    max_expected: Optional[datetime]  # latest expected arrival time at stop (iso string
    scheduled: Optional[datetime]  # scheduled arrival time at stop (iso string)
    started: bool  # if the bus has started the route or is waiting at the first stop
    finished: bool  # if the bus has finished the route
    target_seq: Optional[int]  # the sequence number of the stop requested
    speed: Optional[float]  # how fast the bus is going
    progress: Progress
    predictions: list[Prediction]
    journey: Optional[Journey]
    confidence: Confidence
    coords: list[float]
    status: str
    source: str  # "api" or "db"
