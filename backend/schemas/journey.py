from pydantic import BaseModel

from backend.schemas.stop import StopTime


class Journey(BaseModel):
    route_name: str
    destination: str
    service_id: int
    stops: list[StopTime]


class Trip(BaseModel):
    service_id: int
    stops: list[StopTime]
