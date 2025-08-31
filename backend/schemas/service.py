from typing import Optional
from pydantic import BaseModel


class Service(BaseModel):
    id: int
    line_name: str
    description: str
    detail: Optional[str]
