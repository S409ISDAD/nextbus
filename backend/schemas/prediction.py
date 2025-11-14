from pydantic import BaseModel
from datetime import datetime


class Prediction(BaseModel):
    timestamp: datetime
    sequence: int
    progress: float
    location: list[float]
    heading: int
