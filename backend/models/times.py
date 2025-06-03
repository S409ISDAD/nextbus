from typing import Optional
from pydantic import BaseModel


class Times(BaseModel):
    expected: Optional[int]
    scheduled: Optional[int]
    started: bool
    finished: bool
    include: bool
