from typing import Optional
from pydantic import BaseModel

from backend.models.stop import StopTime


class Journey(BaseModel):
    route_name: str
    destination: str
    stops: list[StopTime]
