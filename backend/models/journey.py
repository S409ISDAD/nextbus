from typing import Optional
from pydantic import BaseModel

from backend.models.stop import StopTime


class Journey(BaseModel):
    route_name: str
    destination: str
    service_id: int
    stops: list[StopTime]


class Trip(BaseModel):
    service_id: int
    stops: list[StopTime]
