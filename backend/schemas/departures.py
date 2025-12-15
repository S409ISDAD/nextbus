from pydantic import BaseModel
from datetime import datetime
from backend.schemas.bus import ScheduledBus, TrackedBus


class DeparturesResponse(BaseModel):
    buses: list[ScheduledBus | TrackedBus]
    timestamp: datetime
