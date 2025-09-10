from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional, Union

from backend.schemas.prediction import Prediction


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
    wttBookedArrival: Optional[datetime] = None
    wttBookedDeparture: Optional[datetime] = None
    gbttBookedArrival: Optional[datetime] = None
    gbttBookedDeparture: Optional[datetime] = None
    origin: List[OriginDestination]
    destination: List[OriginDestination]
    isCall: bool
    isPublicCall: bool

    realtimeArrival: Optional[datetime] = None
    realtimeArrivalActual: Optional[bool] = None
    realtimeDeparture: Optional[datetime] = None
    realtimeDepartureActual: Optional[bool] = None
    expectedDeparture: Optional[datetime] = None
    expectedArrival: Optional[datetime] = None
    scheduledDeparture: Optional[datetime] = None
    scheduledArrival: Optional[datetime] = None
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
    atocColor: Optional[str]
    atocCode: str
    atocName: str
    serviceType: str
    delay: Optional[int] = 0
    timeTo: Optional[str] = None
    isPassenger: bool


class Filter(BaseModel):
    destination: Optional[Location] = None
    origin: Optional[Location] = None


class StationResponse(BaseModel):
    location: Location
    filter: Optional[Filter] = None
    services: Optional[List[Train]]


class ServiceLocation(BaseModel):
    realtimeActivated: bool
    tiploc: Union[str, List[str]]
    crs: str
    description: str

    gbttBookedArrival: Optional[datetime] = None
    gbttBookedDeparture: Optional[datetime] = None

    wttBookedArrival: Optional[datetime] = None
    wttBookedDeparture: Optional[datetime] = None

    origin: List[OriginDestination]
    destination: List[OriginDestination]

    isCall: bool
    isPublicCall: bool

    timeTo: Optional[str] = None

    realtimeArrival: Optional[datetime] = None
    realtimeArrivalActual: Optional[bool] = None
    realtimeDeparture: Optional[datetime] = None
    realtimeDepartureActual: Optional[bool] = None

    expectedDeparture: Optional[datetime] = None
    expectedArrival: Optional[datetime] = None

    scheduledDeparture: Optional[datetime] = None
    scheduledArrival: Optional[datetime] = None

    delay: int = 0
    departed: bool = False

    platform: Optional[str] = None
    platformConfirmed: Optional[bool] = None
    platformChanged: Optional[bool] = None

    line: Optional[str] = None
    lineConfirmed: Optional[bool] = None

    cancelReasonCode: Optional[str] = None
    cancelReasonShortText: Optional[str] = None
    cancelReasonLongText: Optional[str] = None

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

    fromStop: Optional[ServiceLocation] = None
    toStop: Optional[ServiceLocation] = None
    duration: Optional[int] = None

    atocCode: str
    atocName: str
    atocColor: str

    sequence: int = 0
    progress: float = 0

    started: bool = True
    finished: bool = False

    predictions: Optional[List[Prediction]] = None

    delay: int

    nextStation: Optional[ServiceLocation]

    performanceMonitored: Optional[bool] = None

    origin: List[OriginDestination]
    destination: List[OriginDestination]

    locations: List[ServiceLocation]

    realtimeActivated: Optional[bool] = None
    runningIdentity: Optional[str] = None
