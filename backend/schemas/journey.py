from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from backend.schemas.stop import StopTime


class Location(BaseModel):
    coords: list[float]
    direction: int
    timestamp: datetime


class BaseJourney(BaseModel):
    route_name: str
    destination: str
    service_id: int
    stops: list[StopTime]


class Journey(BaseJourney):
    """basic journey representation"""

    pass


class LiveJourney(BaseJourney):
    vehicle_id: int
    trip_id: int
    start_time: datetime
    current: bool
    locations: list["Location"]

    def generate_location_history(self, exclude_start=False):
        full_track = []

        for location in self.locations:
            if exclude_start:
                if location.timestamp > self.start_time:
                    full_track.append(location.coords)
            else:
                full_track.append(location.coords)
        return full_track


class Trip(BaseJourney):
    vehicle_journey_code: str
    ticket_machine_code: str
    block: Optional[str] = None

    def generate_full_track(self):
        full_track = []

        for stop in self.stops:
            if stop.track:
                full_track.extend(stop.track)
        return full_track
