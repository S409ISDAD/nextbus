from pydantic import BaseModel
from backend.schemas.service import ServiceWithTimetable
from backend.schemas.places import Locality


class SearchOperator(BaseModel):
    id: int
    noc: str
    name: str


class SearchStop(BaseModel):
    atco_code: str
    long_name: str
    rank: float


class SearchResponse(BaseModel):
    operators: list[SearchOperator]
    localities: list[Locality]
    services: list[ServiceWithTimetable]
    stops: list[SearchStop]
