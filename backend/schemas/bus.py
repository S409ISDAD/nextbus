from typing import Optional
from typing_extensions import Literal
from pydantic import BaseModel
from datetime import datetime

from backend.schemas.journey import Journey
from backend.schemas.prediction import Prediction
from backend.schemas.service import Service
from backend.schemas.vehicle import Vehicle
from .confidence import Confidence
from .progress import Progress


class BaseBus(BaseModel):
    destination: str
    scheduled: Optional[datetime] = None
    expected: Optional[datetime] = None
    started: bool
    trip: Optional[int] = None
    db_journey: Optional[int] = None
    status: str
    source: str


class ScheduledBus(BaseBus):
    type: Literal["scheduled"] = "scheduled"
    line: str


class TrackedBus(BaseBus):
    type: Literal["tracked"] = "tracked"
    id: int
    timestamp: Optional[datetime] = None
    service: Optional[Service] = None
    vehicle: Optional[Vehicle] = None
    bus_type: str
    journey_id: int
    delay: int
    min_expected: Optional[datetime] = None
    max_expected: Optional[datetime] = None
    finished: bool
    target_seq: Optional[int] = None
    speed: Optional[float] = None
    progress: Progress
    predictions: list[Prediction]
    journey: Optional[Journey] = None
    confidence: Confidence
    coords: list[float]
    heading: int
