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


class StationResponse(BaseModel):
    location: Location
    filter: Optional[str]
    services: Optional[List[Train]]


class ServiceLocation(BaseModel):
    realtimeActivated: bool
    tiploc: Union[str, List[str]]
    crs: str
    description: str

    gbttBookedArrival: Optional[str] = None
    gbttBookedDeparture: Optional[str] = None

    wttBookedArrival: Optional[str] = None
    wttBookedDeparture: Optional[str] = None

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

    line: Optional[str] = None
    lineConfirmed: Optional[bool] = None

    serviceLocation: Optional[str] = None
    displayAs: str


class TrainService(BaseModel):
    serviceUid: str
    runDate: str
    serviceType: str
    isPassenger: bool
    trainIdentity: str

    powerType: Optional[str] = None
    trainClass: Optional[str] = None

    atocCode: str
    atocName: str

    performanceMonitored: Optional[bool] = None

    origin: List[OriginDestination]
    destination: List[OriginDestination]

    locations: List[ServiceLocation]

    realtimeActivated: Optional[bool] = None
    runningIdentity: Optional[str] = None
