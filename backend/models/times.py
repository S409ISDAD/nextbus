from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Times(BaseModel):
    expected: Optional[datetime]
    scheduled: Optional[datetime]
    started: bool
    finished: bool
    include: bool
