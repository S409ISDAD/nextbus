from typing import Optional
from pydantic import BaseModel

from backend.schemas.stop import StopTime


class Journey(BaseModel):
    route_name: str
    destination: str
    service_id: int
    stops: list[StopTime]


class Trip(BaseModel):
    vehicle_journey_code: str
    ticket_machine_code: str
    block: Optional[str] = None
    service_id: int
    stops: list[StopTime]
