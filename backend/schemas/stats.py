from pydantic import BaseModel


class Stats(BaseModel):
    total_buses: int
    total_stops: int


class DBStats(BaseModel):
    lines: int
    stops: int
    operators: int
