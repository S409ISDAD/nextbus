from pydantic import BaseModel


class Livery(BaseModel):
    id: int
    name: str | None = None
    left_css: str
    right_css: str | None = None
