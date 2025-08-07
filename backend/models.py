from datetime import timedelta
import enum
from sqlalchemy import (
    Column,
    Computed,
    Date,
    Enum,
    Index,
    String,
    Integer,
    Float,
    Boolean,
    ForeignKey,
    Time,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry

Base = declarative_base()


class RouteType(enum.Enum):
    TRAM = 0
    SUBWAY = 1
    RAIL = 2
    BUS = 3
    FERRY = 4
    CABLE_CAR = 5
    GONDOLA = 6
    FUNICULAR = 7
    TROLLEYBUS = 11
    MONORAIL = 12
    TOURIST_RAILWAY = 107
    COACH = 200
    RAIL_REPLACEMENT = 714


class PickupDropOffType(enum.Enum):
    REGULAR = 0
    NONE = 1
    PHONE_AGENCY = 2
    DRIVER_COORDINATED = 3


class ContinuousPickupDropOff(enum.Enum):
    NOT_AVAILABLE = 0
    CONTINUOUS = 1
    PHONE_AGENCY = 2
    DRIVER_COORDINATED = 3


class ExceptionType(enum.Enum):
    ADDITION = 1
    REMOVAL = 2


class LocationType(enum.Enum):
    STOP = 0
    STATION = 1
    ENTRANCE_EXIT = 2
    GENERIC = 3
    BOARDING_AREA = 4


class WheelchairAccessible(enum.Enum):
    UNKNOWN = 0
    ACCESSIBLE = 1
    NOT_ACCESSIBLE = 2


class BikesAllowed(enum.Enum):
    UNKNOWN = 0
    ALLOWED = 1
    NOT_ALLOWED = 2


class Stop(Base):
    __tablename__ = "stop"

    id = Column(String, primary_key=True)  # stop_id
    code = Column("stop_code", String, nullable=True)  # stop_code
    name = Column("stop_name", String, nullable=False)  # stop_name
    point = Column(
        Geometry(geometry_type="POINT", srid=4326), nullable=False
    )  # PostGIS point for (lat, lon)
    lat = Column(Float, Computed("ST_Y(point::geometry)"), nullable=False)
    lon = Column(Float, Computed("ST_X(point::geometry)"), nullable=False)
    location_type = Column(
        "location_type",
        Enum(
            LocationType,
        ),
        default=LocationType.STOP,
    )  # location_type
    parent_station_id = Column(
        "parent_station", String, ForeignKey("stop.id"), nullable=True
    )  # parent_station
    wheelchair_boarding = Column(
        "wheelchair_boarding", Enum(WheelchairAccessible), nullable=True
    )  # wheelchair_boarding
    platform_code = Column("platform_code", String, nullable=True)  # platform_code
    mode_hint = Column("mode_hint", String, nullable=True)  # e.g. bus, train, mixed

    parent_station = relationship("Stop", remote_side=[id], backref="children")

    __table_args__ = (Index("ix_stop_point", "point", postgresql_using="gist"),)

    @property
    def is_station(self) -> bool:
        return getattr(self, "location_type") == LocationType.STATION

    @property
    def is_platform(self) -> bool:
        return (
            getattr(self, "location_type") == LocationType.STOP
            and self.parent_station_id is not None
        )

    @property
    def is_standalone_stop(self) -> bool:
        return (
            getattr(self, "location_type") == LocationType.STOP
            and self.parent_station_id is None
        )


class Service(Base):
    __tablename__ = "service"

    id = Column(Integer, primary_key=True)  # service_id
    calendar = relationship("Calendar", uselist=False, back_populates="service")
    calendar_dates = relationship("CalendarDate", back_populates="service")
    trips = relationship("Trip", back_populates="service")


class Route(Base):
    __tablename__ = "route"

    id = Column(Integer, primary_key=True)  # route_id
    agency_id = Column(String, ForeignKey("agency.id"), nullable=True)  # agency_id
    short_name = Column(String, nullable=False)  # route_short_name
    long_name = Column(String, nullable=False)  # route_long_name
    type = Column(
        Enum(
            RouteType,
        ),
        nullable=False,
    )  # route_type

    agency = relationship("Agency", back_populates="routes")
    trips = relationship("Trip", back_populates="route")


class Trip(Base):
    __tablename__ = "trip"

    id = Column(String, primary_key=True)  # trip_id
    route_id = Column(Integer, ForeignKey("route.id"), nullable=False)  # route_id
    service_id = Column(Integer, ForeignKey("service.id"), nullable=False)  # service_id
    headsign = Column(String, nullable=True)  # trip_headsign
    direction = Column(Integer, nullable=True)  # direction_id
    block_id = Column(String, nullable=True)  # block_id
    geometry = Column(
        Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=True),
        nullable=True,
    )
    wheelchair_accessible = Column(
        Enum(
            WheelchairAccessible,
        ),
        nullable=True,
    )  # wheelchair_accessible
    vehicle_journey_code = Column(String, nullable=True)  # vehicle_journey_code

    route = relationship("Route", back_populates="trips")
    service = relationship("Service", back_populates="trips")
    stop_times = relationship("StopTime", back_populates="trip")
    frequencies = relationship("Frequency", back_populates="trip")


class Calendar(Base):
    __tablename__ = "calendar"

    service_id = Column(
        "service_id", Integer, ForeignKey("service.id"), primary_key=True
    )  # service_id
    monday = Column("monday", Boolean, default=False)
    tuesday = Column("tuesday", Boolean, default=False)
    wednesday = Column("wednesday", Boolean, default=False)
    thursday = Column("thursday", Boolean, default=False)
    friday = Column("friday", Boolean, default=False)
    saturday = Column("saturday", Boolean, default=False)
    sunday = Column("sunday", Boolean, default=False)
    start_date = Column("start_date", Date, nullable=False)
    end_date = Column("end_date", Date, nullable=False)

    service = relationship("Service", back_populates="calendar")


class CalendarDate(Base):
    __tablename__ = "calendardate"

    service_id = Column(
        "service_id", Integer, ForeignKey("service.id"), primary_key=True
    )  # service_id
    date = Column("date", Date, primary_key=True)  # date
    exception_type = Column(
        "exception_type",
        Enum(
            ExceptionType,
        ),
        nullable=False,
    )  # exception_type

    service = relationship("Service", back_populates="calendar_dates")


class Shape(Base):
    __tablename__ = "shape"

    id = Column(String, primary_key=True)
    geometry = Column(
        Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=True),
        nullable=True,
    )

    points = relationship("ShapePoint", back_populates="shape")


class ShapePoint(Base):
    __tablename__ = "shapepoint"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shape_id = Column(
        "shape_id", String, ForeignKey("shape.id"), nullable=False
    )  # shape_id
    point = Column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=False
    )
    lat = Column(
        Float, Computed("ST_Y(point::geometry)"), nullable=False
    )  # shape_pt_lat
    lon = Column(
        Float, Computed("ST_X(point::geometry)"), nullable=False
    )  # shape_pt_lon
    sequence = Column("shape_pt_sequence", Integer, nullable=False)  # shape_pt_sequence
    distance_traveled = Column(
        "shape_dist_traveled", Float, nullable=True
    )  # shape_dist_traveled

    shape = relationship("Shape", back_populates="points")

    __table_args__ = (
        # Ensure (shape_id, sequence) is unique
        Index(
            "ix_shapepoint_shapeid_sequence",
            "shape_id",
            "shape_pt_sequence",
            unique=True,
        ),
    )


class StopTime(Base):
    __tablename__ = "stoptime"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(
        "trip_id", String, ForeignKey("trip.id"), nullable=False
    )  # trip_id
    stop_id = Column(
        "stop_id", String, ForeignKey("stop.id"), nullable=False
    )  # stop_id
    arrival_time = Column("arrival_time", Integer, nullable=True)  # arrival_time
    departure_time = Column("departure_time", Integer, nullable=True)  # departure_time
    stop_sequence = Column("stop_sequence", Integer, nullable=False)  # stop_sequence
    stop_headsign = Column("stop_headsign", String, nullable=True)  # stop_headsign
    pickup_type = Column(
        "pickup_type",
        Enum(
            PickupDropOffType,
        ),
        default=PickupDropOffType.REGULAR,
    )  # pickup_type
    drop_off_type = Column(
        "drop_off_type",
        Enum(
            PickupDropOffType,
        ),
        default=PickupDropOffType.REGULAR,
    )  # drop_off_type
    shape_dist_traveled = Column(
        "shape_dist_traveled", Float, nullable=True
    )  # shape_dist_traveled
    timepoint = Column("timepoint", Integer, nullable=True)  # timepoint

    trip = relationship("Trip", back_populates="stop_times")
    stop = relationship("Stop")

    __table_args__ = (
        Index("ix_stoptime_tripid_stopid", "trip_id", "stop_id", unique=True),
    )

    @property
    def get_arrival_time(self) -> str | None:
        """Convert arrival_time to a time string (HH:MM)."""
        if self.arrival_time is None:
            return None
        td = timedelta(seconds=self.arrival_time)
        total_minutes = td.seconds // 60
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02}:{minutes:02}"

    @property
    def get_departure_time(self) -> str | None:
        """Convert departure_time to a time string (HH:MM)."""
        if self.departure_time is None:
            return None
        # Convert seconds to HH:MM format (ignore seconds)
        td = timedelta(seconds=self.departure_time)
        total_minutes = td.seconds // 60
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02}:{minutes:02}"


class Frequency(Base):
    __tablename__ = "frequency"

    trip_id = Column(
        "trip_id", String, ForeignKey("trip.id"), primary_key=True
    )  # trip_id
    start_time = Column("start_time", String, nullable=False)  # start_time
    end_time = Column("end_time", String, nullable=False)  # end_time
    headway_secs = Column("headway_secs", Integer, nullable=False)  # headway_secs
    exact_times = Column("exact_times", Boolean, default=False)  # exact_times

    trip = relationship("Trip", back_populates="frequencies")


class Agency(Base):
    __tablename__ = "agency"

    id = Column(String, primary_key=True)
    name = Column(String)
    url = Column(String)
    timezone = Column(String)
    lang = Column(String)
    phone = Column(String)
    noc = Column(String)

    routes = relationship("Route", back_populates="agency")


class FeedInfo(Base):
    __tablename__ = "feed_info"

    id = Column(Integer, primary_key=True)
    publisher_name = Column(String, unique=True)
    publisher_url = Column(String)
    lang = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    version = Column(String)
