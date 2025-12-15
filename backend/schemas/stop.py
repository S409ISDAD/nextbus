from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

from backend.schemas.service import Service


class Stop(BaseModel):
    stop_id: str
    name: Optional[str]
    long_name: Optional[str]
    indicator: Optional[str]
    bearing: Optional[int | str]
    active: bool
    coords: list[float]
    services: Optional[list[Service]]
    dist: Optional[float]  # distance from user (if needed)


class StopTime(BaseModel):
    stop_id: str
    name: str
    aimed_time: datetime
    expt_time: Optional[datetime]
    departed: bool = False
    coords: list[float]
    track: Optional[list[list[float]]]
    set_down: bool
    pick_up: bool
    timing_status: Literal["OTH", "PTP", "TIP"] = (
        "OTH"  # PTP: Principal Timing Point, OTH: Other, TIP: Timing Information Point
    )
    call_condition: Optional[str] = None  # "notStopping" means cancelled
    track_distance: Optional[float] = (
        0.0  # distance in metres along track to this stop from previous stop
    )
