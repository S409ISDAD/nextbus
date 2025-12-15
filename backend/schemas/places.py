from pydantic import BaseModel
from typing import Optional
from backend.schemas.service import Service
from backend.schemas.stop import Stop


class Locality(BaseModel):
    id: str
    name: str
    qualifier: Optional[str] = None
    full_name: Optional[str] = None


class LocalityDetails(Locality):
    services: list[Service]
    stops: list[Stop]


class District(BaseModel):
    id: str
    name: str


class DistrictDetails(District):
    localities: list[Locality]


class AdminArea(BaseModel):
    id: str
    name: str


class AdminAreaDetails(AdminArea):
    districts: list[District]


class Region(BaseModel):
    id: str
    name: str


class RegionDetails(Region):
    admin_areas: list[AdminArea]
