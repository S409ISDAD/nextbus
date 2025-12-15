from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

from backend.schemas.service import ServiceWithTimetable
from backend.schemas.timetable import DBTimetable


class DataSourceVersion(BaseModel):
    id: int
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    url: Optional[str] = None
    bods_id: Optional[int] = None
    last_modified: Optional[datetime] = None
    timetable_count: int


class DataSource(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    service_count: Optional[int] = None
    timetable_count: Optional[int] = None
    versions: Optional[list[DataSourceVersion]] = None


class ServiceGroup(BaseModel):
    service: ServiceWithTimetable
    timetables: list[DBTimetable]


class DetailedDataSource(DataSource):
    services: dict[str, dict[str, ServiceGroup]]
