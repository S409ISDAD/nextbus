from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from backend.schemas.service import Service


class Stop(BaseModel):
    stop_id: str
    name: str
    long_name: str
    indicator: Optional[str]
    bearing: Optional[int | str]
    active: bool
    coords: list[float]
    services: Optional[list[Service]]


class StopTime(BaseModel):
    stop_id: str
    name: str
    aimed_time: datetime
    expt_time: Optional[datetime]
    departed: bool = False
    coords: list[float]
    track: Optional[list[list[float]]]
    set_down: bool
