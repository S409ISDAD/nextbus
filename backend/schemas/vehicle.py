from typing import Optional
from pydantic import BaseModel
from backend.schemas.livery import Livery


class VehicleType(BaseModel):
    id: int
    name: str
    style: Optional[str] = None
    fuel: str
    double_decker: bool
    coach: bool
    electric: bool


class Vehicle(BaseModel):
    id: int
    reg: str  # vehicle license plate
    fleet_num: str
    vehicle_type: Optional[VehicleType] = None
    livery: Optional[Livery] = None
    name: Optional[str] = None
    special_features: Optional[list[str]] = None
