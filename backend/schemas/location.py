from pydantic import BaseModel


class LocationRequest(BaseModel):
    lat: float
    lon: float
