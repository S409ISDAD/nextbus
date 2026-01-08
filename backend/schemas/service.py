from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class Service(BaseModel):
    id: int
    line_name: str
    description: str
    detail: Optional[str] = None


class Operator(BaseModel):
    noc: Optional[str]
    name: str


class ServiceWithTimetable(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    line_name: str
    inbound_description: Optional[str] = None
    outbound_description: Optional[str] = None
    geometry: Optional[str] = None
    bt_service_id: Optional[int] = None
    service_code: str
    description: str
    origin: Optional[str] = None
    destination: Optional[str] = None
    vias: Optional[str] = None
    operators: list[Operator]
    last_modified: Optional[datetime] = None
    rank: Optional[float] = None


class RoutePixels(BaseModel):
    route: list[tuple[int, int]]
    stops: list[tuple[int, int]]
