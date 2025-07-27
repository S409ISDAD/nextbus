from pydantic import BaseModel
from typing import List, Optional, Union


class Location(BaseModel):
    name: str
    crs: str
    tiploc: Union[str, List[str]]
    country: Optional[str] = None
    system: Optional[str] = None


class OriginDestination(BaseModel):
    tiploc: Union[str, List[str]]
    description: str
    workingTime: str
    publicTime: str


class LocationDetail(BaseModel):
    realtimeActivated: Optional[bool] = None
    tiploc: Union[str, List[str]]
    crs: str
    description: str
    wttBookedArrival: Optional[str] = None
    wttBookedDeparture: Optional[str] = None
    gbttBookedArrival: Optional[str] = None
    gbttBookedDeparture: Optional[str] = None
    origin: List[OriginDestination]
    destination: List[OriginDestination]
    isCall: bool
    isPublicCall: bool
    realtimeArrival: Optional[str] = None
    realtimeArrivalActual: Optional[bool] = None
    realtimeDeparture: Optional[str] = None
    realtimeDepartureActual: Optional[bool] = None
    platform: Optional[str] = None
    platformConfirmed: Optional[bool] = None
    platformChanged: Optional[bool] = None
    displayAs: str


class Train(BaseModel):
    locationDetail: LocationDetail
    serviceUid: str
    runDate: str
    trainIdentity: str
    runningIdentity: Optional[str] = None
    atocCode: str
    atocName: str
    serviceType: str
    isPassenger: bool


class TrainResponse(BaseModel):
    location: Location
    filter: Optional[str]
    services: List[Train]
