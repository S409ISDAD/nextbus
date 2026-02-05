from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class TimetableService(BaseModel):
    id: int
    line_name: str
    inbound: bool


class TimetableStop(BaseModel):
    id: str
    name: str
    timing_status: str


class TimetableJourney(BaseModel):
    id: int
    start_time: str
    times: list[Optional[str]]


class TimetableResponse(BaseModel):
    service: TimetableService
    stops: list[TimetableStop]
    journeys: list[TimetableJourney]


class DBTimetable(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_code: str
    line_id: str
    line_name: str
    line_brand: Optional[str] = None
    service_id: int
    bt_service_id: Optional[int] = None
    revision_number: int
    description: Optional[str]
    outbound_description: str
    inbound_description: str
    origin: str
    destination: str
    vias: Optional[str] = None
    public_use: bool
    data_source_id: int
    created_at: datetime
    modified_at: datetime
    start_date: date
    end_date: Optional[date] = None
    journey_count: Optional[int] = None
