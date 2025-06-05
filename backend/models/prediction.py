from pydantic import BaseModel


class Prediction(BaseModel):
    timestamp: int
    sequence: int
    progress: float
    location: list[float]
