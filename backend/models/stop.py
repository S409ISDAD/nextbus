from typing import Optional
from pydantic import BaseModel

from backend.models.service import Service


class Stop(BaseModel):
    stop_id: str
    name: str
    long_name: str
    indicator: Optional[str]
    bearing: Optional[str]
    active: bool
    coords: list[float]
    services: Optional[list[Service]]


class StopTime(BaseModel):
    stop_id: str
    name: str
    aimed_time: int
    expt_time: Optional[int]
    coords: list[float]
    track: Optional[list[list[float]]]
    set_down: bool
