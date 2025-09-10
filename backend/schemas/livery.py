from pydantic import BaseModel


class Livery(BaseModel):
    name: str
    left_css: str
    right_css: str | None = None
