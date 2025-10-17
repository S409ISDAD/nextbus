from datetime import datetime
from pydantic import BaseModel


class ImportMessage(BaseModel):
    time_taken: float
    timestamp: datetime
    stats: "SimpleStatistics"


class SimpleStatistics(BaseModel):
    sc: int
    su: int
    sd: int
    ss: int
    tc: int
    tu: int
    td: int
    ts: int
    jc: int
    stc: int
    stpc: int
    stpu: int

    class Config:
        arbitrary_types_allowed = True
