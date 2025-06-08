from pydantic import BaseModel


class Livery(BaseModel):
    name: str
    css: str
