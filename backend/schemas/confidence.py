from pydantic import BaseModel


class Confidence(BaseModel):
    final_confidence: float
    broken_down_confidence: float
    log_off_confidence: float
    diversion_confidence: float
    broken_tracking_confidence: float
