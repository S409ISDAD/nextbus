import enum

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Column,
    Computed,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Interval,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy_searchable import make_searchable
from sqlalchemy_utils.types import TSVectorType
from sqlalchemy.dialects.postgresql import ARRAY, VARCHAR

Base = declarative_base()
make_searchable(Base.metadata)


class RouteType(enum.Enum):
    tram = 0
    subway = 1
    rail = 2
    bus = 3
    ferry = 4
    cable_car = 5
    gondola = 6
    funicular = 7
    trolleybus = 11
    monorail = 12
    tourist_railway = 107
    coach = 200
    rail_replacement = 714


class PickupDropOffType(enum.Enum):
    regular = 0
    none = 1
    phone_agency = 2
    driver_coordinated = 3


class ContinuousPickupDropOff(enum.Enum):
    not_available = 0
    continuous = 1
    phone_agency = 2
    driver_coordinated = 3


class ExceptionType(enum.Enum):
    addition = 1
    removal = 2


class LocationType(enum.Enum):
    stop = 0
    station = 1
    entrance_exit = 2
    generic = 3
    boarding_area = 4


class WheelchairAccessible(enum.Enum):
    unknown = 0
    accessible = 1
    not_accessible = 2


class BikesAllowed(enum.Enum):
    unknown = 0
    allowed = 1
    not_allowed = 2


class StopTypeEnum(str, enum.Enum):
    airport_entrance = "AIR"  # Airport Entrance
    airside_interchange_area = "GAT"  # Airport airside / interchange area

    ferry_terminal_entrance = "FTD"  # Ferry terminal or dock entrance
    ferry_interchange_area = "FER"  # Ferry / dock berth area (access area)
    ferry_berth = "FBT"  # Specific ferry berth / quay

    rail_station_entrance = "RSE"  # Rail station entrance
    rail_interchange_area = "RLY"  # Rail platform access / interchange area
    rail_platform = "RPL"  # Specific rail platform

    metro_tram_underground_entrance = "TMU"  # Tram, metro, or underground entrance
    metro_tram_underground_access = (
        "MET"  # Tram, metro, or underground interchange area
    )
    metro_tram_underground_platform = "PLT"  # Tram, metro, or underground platform

    bus_coach_station_entrance = "BCE"  # Bus or coach station entrance
    bus_coach_station_access = "BST"  # Bus or coach station non-specific access area
    bus_coach_variable_bay = "BCQ"
    bus_coach_bay = "BCS"
    bus_stop = "BCT"

    taxi_rank = "TXR"  # Taxi rank
    shared_taxi_rank = "STR"  # Shared taxi rank


class BusStopTypeEnum(str, enum.Enum):
    marked_stop = "MKD"  # Specific bay/stand within a station
    on_street_unmarked_stop = "CUS"  # Unmarked stop, road-only marking
    on_street_hail_and_ride_section = "HAR"  # Hail and ride route section
    on_street_flexible_zone = "FLX"  # Flexible route service zone


class StopAreaTypeEnum(str, enum.Enum):
    on_street_pair = "GPBS"
    on_street_cluster = "GCLS"
    airport_building = "GAIR"
    bus_coach_station = "GBCS"
    ferry_terminal_dock = "GFTD"
    tram_metro_station = "GTMU"
    rail_station = "GRLS"
    coach_service_coverage = "GCCH"


class DirectionType(enum.Enum):
    outbound = "outbound"
    inbound = "inbound"
    circular = "circular"
    unknown = "unknown"


class Stop(Base):
    __tablename__ = "stop"

    atco_code = Column(String, primary_key=True)  # atco_code
    naptan_code = Column(String, nullable=True)  # naptan_code
    common_name = Column(String, nullable=False)  # stop_name
    common_short_name = Column(String, nullable=True)  # stop_short_name
    landmark = Column(String, nullable=True)  # stop_landmark
    street = Column(String, nullable=True)  # stop_street
    crossing = Column(String, nullable=True)  # stop_crossing
    indicator = Column(String, nullable=True)  # stop_indicator
    point = Column(
        Geometry(geometry_type="POINT"), nullable=False
    )  # PostGIS point for (lat, lon)
    lat = Column(Float, Computed("ST_Y(point::geometry)"), nullable=False)
    lon = Column(Float, Computed("ST_X(point::geometry)"), nullable=False)
    stop_area_id = Column(String, ForeignKey("stoparea.id"), nullable=True)

    suburb = Column(String, nullable=True)
    town = Column(String, nullable=True)

    heading = Column(Integer, nullable=True)
    bearing = Column(String, nullable=True)
    stop_type = Column(Enum(StopTypeEnum), nullable=True)
    bus_stop_type = Column(Enum(BusStopTypeEnum), nullable=True)
    timing_status = Column(String, nullable=True)
    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=True)
    modified_at = Column(DateTime, nullable=True)
    revision_number = Column(Integer, nullable=True)

    stop_area = relationship("StopArea", back_populates="stops")
    stop_times = relationship("StopTime", back_populates="stop")

    __table_args__ = (Index("ix_stop_point", "point", postgresql_using="gist"),)

    search_vector = Column(
        TSVectorType(
            "atco_code",
            "naptan_code",
            "common_name",
            "common_short_name",
            "landmark",
            "street",
            "suburb",
            "town",
        )
    )


class StopArea(Base):
    __tablename__ = "stoparea"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    point = Column(
        Geometry(geometry_type="POINT"),
        nullable=True,
    )
    lat = Column(Float, Computed("ST_Y(point::geometry)"), nullable=True)
    lon = Column(Float, Computed("ST_X(point::geometry)"), nullable=True)
    type = Column(Enum(StopAreaTypeEnum), nullable=True)
    parent_id = Column(String, ForeignKey("stoparea.id"), nullable=True)
    active = Column(Boolean, nullable=False)
    revision_number = Column(Integer, nullable=True)

    parent = relationship("StopArea", remote_side=[id], backref="children")

    stops = relationship("Stop", back_populates="stop_area")

    __table_args__ = (Index("ix_stoparea_point", "point", postgresql_using="gist"),)


class Operator(Base):
    __tablename__ = "operator"

    noc = Column(String, nullable=False, primary_key=True)
    ref = Column(Integer, nullable=True)
    name = Column(String, nullable=False)

    services = relationship("Service", back_populates="operator")

    search_vector = Column(TSVectorType("name", "noc"))


class BankHoliday(Base):
    __tablename__ = "bank_holiday"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)

    dates = relationship(
        "BankHolidayDate", back_populates="bank_holiday", cascade="all, delete-orphan"
    )
    calendars = relationship(
        "Calendar", secondary="calendar_bank_holiday", back_populates="bank_holidays"
    )


class BankHolidayDate(Base):
    __tablename__ = "bank_holiday_date"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bank_holiday_id = Column(Integer, ForeignKey("bank_holiday.id"), nullable=False)
    date = Column(Date, nullable=False)

    bank_holiday = relationship("BankHoliday", back_populates="dates")

    __table_args__ = (
        UniqueConstraint(
            "bank_holiday_id",
            "date",
            name="uq_bank_holiday_date_per_holiday",
        ),
    )


class CalendarToBankHoliday(Base):
    """
    Many-to-many relationship between Calendar and BankHoliday
    """

    __tablename__ = "calendar_bank_holiday"
    operating = Column(Boolean, nullable=False, default=True)
    calendar_id = Column(
        Integer, ForeignKey("calendar.id"), primary_key=True, nullable=False
    )
    bank_holiday_id = Column(
        Integer, ForeignKey("bank_holiday.id"), primary_key=True, nullable=False
    )


class Calendar(Base):
    """
    days of operation of a journey
    """

    __tablename__ = "calendar"

    id = Column(Integer, primary_key=True, autoincrement=True)
    monday = Column(Boolean, nullable=False, default=False)
    tuesday = Column(Boolean, nullable=False, default=False)
    wednesday = Column(Boolean, nullable=False, default=False)
    thursday = Column(Boolean, nullable=False, default=False)
    friday = Column(Boolean, nullable=False, default=False)
    saturday = Column(Boolean, nullable=False, default=False)
    sunday = Column(Boolean, nullable=False, default=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # no end date means it is valid indefinitely

    bank_holidays = relationship(
        "BankHoliday", secondary="calendar_bank_holiday", back_populates="calendars"
    )
    calendar_exceptions = relationship(
        "CalendarException", back_populates="calendar", cascade="all, delete-orphan"
    )

    journeys = relationship("Journey", back_populates="calendar")

    @property
    def days_of_week(self):
        return {
            "monday": self.monday,
            "tuesday": self.tuesday,
            "wednesday": self.wednesday,
            "thursday": self.thursday,
            "friday": self.friday,
            "saturday": self.saturday,
            "sunday": self.sunday,
        }


class CalendarException(Base):
    """
    exceptions to the calendar, e.g. public holidays, school days, etc.
    """

    __tablename__ = "calendar_exception"

    id = Column(Integer, primary_key=True, autoincrement=True)
    calendar_id = Column(Integer, ForeignKey("calendar.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    operating = Column(Boolean, nullable=False, default=True)
    description = Column(String, nullable=True)

    calendar = relationship("Calendar", back_populates="calendar_exceptions")


class Service(Base):
    """
    Represents a bus service, can have multiple lines e.g 67, 667, 67X
    """

    __tablename__ = "service"
    service_code = Column(String, nullable=False, primary_key=True)
    description = Column(String)
    origin = Column(String, nullable=True)
    destination = Column(String, nullable=True)

    vias = Column(String, nullable=True)
    operator_noc = Column(String, ForeignKey("operator.noc"), nullable=True)
    line_names = Column(String, nullable=True)  # List of line names

    operator = relationship("Operator", back_populates="services")
    lines = relationship("Line", back_populates="service")
    journeys = relationship("Journey", back_populates="service")
    search_vector = Column(
        TSVectorType(
            "service_code", "description", "origin", "destination", "vias", "line_names"
        )
    )


class Line(Base):
    """
    A line is a specific route of a service, e.g. 67, 667, 67X
    """

    __tablename__ = "line"
    id = Column(String, primary_key=True)
    line_name = Column(String, nullable=False)
    inbound_description = Column(String)
    outbound_description = Column(String)
    service_code = Column(String, ForeignKey("service.service_code"), nullable=False)

    service = relationship("Service", back_populates="lines")
    journeys = relationship("Journey", back_populates="line")

    __table_args__ = (
        UniqueConstraint("line_name", "service_code", name="uq_line_per_service"),
    )

    search_vector = Column(
        TSVectorType(
            "line_name",
            "inbound_description",
            "outbound_description",
        )
    )


class TrackSection(Base):
    """
    A point in a track, used to build the geometry of a route. known as RouteLink in TXC.
    """

    __tablename__ = "track_section"
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_stop = Column(String, nullable=True)  # if null, it is the first
    to_stop = Column(String, nullable=True)  # if null, it is the last
    distance = Column(Float, nullable=False)  # distance in meters
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=False)
    route_link_ref = Column(String, nullable=True)  # Reference to the route link
    route_section_id = Column(String, ForeignKey("route_section.id"), nullable=False)

    route_section = relationship("RouteSection", back_populates="track")


class RouteSection(Base):
    """
    A section of a route, used to build the geometry of a route.
    """

    __tablename__ = "route_section"
    id = Column(String, primary_key=True)
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=True)

    track = relationship(
        "TrackSection", back_populates="route_section", cascade="all, delete-orphan"
    )
    route = relationship("Route", back_populates="route_section")


class Route(Base):
    """
    container for a route section
    """

    __tablename__ = "route"
    id = Column(String, primary_key=True)
    private_code = Column(String, nullable=True)
    description = Column(String, nullable=True)
    route_section_id = Column(String, ForeignKey("route_section.id"), nullable=True)

    route_section = relationship("RouteSection", back_populates="route")


class Journey(Base):
    """
    full scheduled trip,has a one to many relationship with stop times to generate a schedule
    """

    __tablename__ = "journey"
    id = Column(String, primary_key=True)
    service_code = Column(String, ForeignKey("service.service_code"), nullable=False)
    ticket_machine_code = Column(String, nullable=True)
    line_id = Column(String, ForeignKey("line.id"), nullable=True)
    block_id = Column(String, nullable=True)
    direction = Column(Enum(DirectionType))
    start_time = Column(Interval, nullable=False)
    end_time = Column(Interval)
    calendar_id = Column(Integer, ForeignKey("calendar.id"), nullable=True)

    calendar = relationship("Calendar", back_populates="journeys")

    service = relationship("Service", back_populates="journeys")
    line = relationship("Line", back_populates="journeys")
    stop_times = relationship(
        "StopTime", back_populates="journey", cascade="all, delete-orphan"
    )


class StopTime(Base):
    """
    every time a journey stops at a stop
    """

    __tablename__ = "stop_time"
    id = Column(Integer, primary_key=True, autoincrement=True)
    journey_id = Column(String, ForeignKey("journey.id"), nullable=False)
    stop_id = Column(String, ForeignKey("stop.atco_code"), nullable=False)
    stop_sequence = Column(Integer, nullable=False)
    arrival_time = Column(Interval, nullable=True)
    departure_time = Column(Interval, nullable=True)
    timing_status = Column(String, nullable=True)
    pick_up = Column(Boolean, nullable=True)
    drop_off = Column(Boolean, nullable=True)
    wait_time = Column(Interval, nullable=True)  # wait time in seconds
    distance_traveled = Column(Float, nullable=True)  # distance in meters

    journey = relationship("Journey", back_populates="stop_times")
    stop = relationship("Stop", back_populates="stop_times")

    @property
    def departure_time_str(self):
        if self.departure_time is None:
            return None
        total_seconds = int(self.departure_time.total_seconds())
        hours = total_seconds // 3600
        if hours > 23:
            hours = hours - 24
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"

    @property
    def arrival_time_str(self):
        if self.arrival_time is None:
            return None
        total_seconds = int(self.arrival_time.total_seconds())
        hours = total_seconds // 3600
        if hours > 23:
            hours = hours - 24
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"

    __table_args__ = (
        UniqueConstraint(
            "journey_id", "stop_sequence", name="uq_stop_time_journey_sequence"
        ),
    )
