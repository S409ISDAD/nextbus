import enum
from datetime import date, datetime, timedelta

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
    Integer,
    Interval,
    String,
    UniqueConstraint,
    func,
    Index,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session, joinedload, deferred, aliased
from sqlalchemy_searchable import make_searchable
from sqlalchemy_utils.types import TSVectorType

from backend.config import API_BASE
from backend.db.db import SessionLocal
from backend.deps import LONDON
from backend.utils.fetch_json import fetch_json
import logging

log = logging.getLogger(__name__)

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


class BotStatusEnum(enum.Enum):
    up = "up"
    down = "down"
    degraded = "degraded"
    restarting = "restarting"


class BotStatus(Base):
    __tablename__ = "bot_status"
    channel_id = Column(Integer, nullable=False, primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    last_status = Column(Enum(BotStatusEnum), nullable=False)


class BotConfig(Base):
    __tablename__ = "bot_dashboard"
    id = Column(Integer, primary_key=True)
    channel_id = Column(String, nullable=False)
    message_id = Column(String, nullable=True)


class ActiveUsersSnapshot(Base):
    __tablename__ = "active_users_snapshot"

    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), index=True, primary_key=True
    )
    total_connections = Column(Integer, nullable=False)
    unique_connections = Column(Integer, nullable=False)


class DataSource(Base):
    __tablename__ = "data_source"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    url = Column(String, nullable=True)
    last_modified = Column(DateTime(timezone=True), nullable=True)

    services = relationship(
        "Service",
        back_populates="data_source",
    )

    def __repr__(self):
        return f"<DataSource(name={self.name}, url={self.url})>"


class Region(Base):
    __tablename__ = "region"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=True)
    modified_at = Column(DateTime(timezone=True), nullable=True)

    admin_areas = relationship("AdminArea", back_populates="region")


class AdminArea(Base):
    __tablename__ = "admin_area"

    id = Column(Integer, primary_key=True)
    atco_code = Column(String)
    name = Column(String)
    short_name = Column(String, nullable=True)
    country = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    modified_at = Column(DateTime(timezone=True), nullable=True)
    region_id = Column(String, ForeignKey("region.id"))

    region = relationship("Region", back_populates="admin_areas")
    districts = relationship("District", back_populates="admin_area")
    localities = relationship("Locality", back_populates="admin_area")
    stops = relationship("Stop", back_populates="admin_area")
    stop_areas = relationship("StopArea", back_populates="admin_area")


class District(Base):
    __tablename__ = "district"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=True)
    modified_at = Column(DateTime(timezone=True), nullable=True)
    admin_area_id = Column(Integer, ForeignKey("admin_area.id"))

    admin_area = relationship("AdminArea", back_populates="districts")
    localities = relationship("Locality", back_populates="district")


class Locality(Base):
    __tablename__ = "locality"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    qualifier_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    modified_at = Column(DateTime(timezone=True), nullable=True)
    admin_area_id = Column(Integer, ForeignKey("admin_area.id"), nullable=True)
    district_id = Column(Integer, ForeignKey("district.id"), nullable=True)
    parent_id = Column(String, ForeignKey("locality.id"), nullable=True)
    point = Column(
        Geometry(geometry_type="POINT"), nullable=False
    )  # PostGIS point for (lat, lon)
    lat = Column(Float, Computed("ST_Y(point::geometry)"), nullable=False)
    lon = Column(Float, Computed("ST_X(point::geometry)"), nullable=False)

    parent = relationship("Locality", remote_side=[id], backref="children")
    district = relationship("District", back_populates="localities")
    admin_area = relationship("AdminArea", back_populates="localities")
    stops = relationship("Stop", back_populates="locality")

    search_vector = deferred(
        Column(
            TSVectorType(
                "name",
                "qualifier_name",
            )
        )
    )

    def lines_served(self):
        with SessionLocal() as db:
            lines: list["Line"] | list[None] = (
                db.query(Line)
                .join(LineStopUsage, Line.id == LineStopUsage.line_id)
                .join(Stop, Stop.atco_code == LineStopUsage.stop_id)
                .filter(Stop.locality_id == self.id)
                .distinct()
                .all()
            )

            return lines


class Stop(Base):
    __tablename__ = "stop"

    atco_code = Column(String, primary_key=True, index=True)  # atco_code
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
    stop_area_id = Column(
        String, ForeignKey("stoparea.id", ondelete="CASCADE"), nullable=True
    )
    locality_id = Column(String, ForeignKey("locality.id"), nullable=True, index=True)
    admin_area_id = Column(Integer, ForeignKey("admin_area.id"), nullable=True)

    suburb = Column(String, nullable=True)
    town = Column(String, nullable=True)

    heading = Column(Integer, nullable=True)
    bearing = Column(String, nullable=True)
    stop_type = Column(Enum(StopTypeEnum), nullable=True)
    bus_stop_type = Column(Enum(BusStopTypeEnum), nullable=True)
    timing_status = Column(String, nullable=True)
    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=True)
    modified_at = Column(DateTime(timezone=True), nullable=True)
    revision_number = Column(Integer, nullable=True)

    stop_area = relationship("StopArea", back_populates="stops")
    locality = relationship("Locality", back_populates="stops")
    admin_area = relationship("AdminArea", back_populates="stops")
    stop_times = relationship("StopTime", back_populates="stop")
    lines = relationship("Line", secondary="line_stop_usage", back_populates="stops")

    search_vector = deferred(
        Column(
            TSVectorType(
                "common_name",
                "common_short_name",
                "landmark",
                "street",
                "suburb",
                "town",
                weights={
                    "common_name": "A",
                    "common_short_name": "A",
                    "landmark": "B",
                    "street": "B",
                    "suburb": "C",
                    "town": "C",
                },
            ),
        )
    )

    @property
    def name(self):
        locality_name = self.locality.name if self.locality else ""
        if locality_name.lower() in self.common_name.lower():
            return self.common_name
        return f"{self.locality.name} {self.common_name}"

    @property
    def long_name(self):
        return f"{self.name} ({self.indicator or self.bearing})"

    def lines_served(self, db: Session) -> list["Line"]:
        """
        Returns a list of lines that serve this stop.
        """
        lines: list["Line"] = (
            db.query(Line)
            .join(LineStopUsage, Line.id == LineStopUsage.line_id)
            .filter(LineStopUsage.stop_id == self.atco_code)
            .distinct()
            .all()
        )
        return lines

    def localities_towards(self):
        with SessionLocal() as db:
            line_ids = [line.id for line in self.lines_served(db)]
            if not line_ids:
                return []

            ST_origin = aliased(StopTime)

            localities = (
                db.query(Locality)
                .join(Stop, Stop.locality_id == Locality.id)
                .join(Journey, Journey.destination_stop_id == Stop.atco_code)
                .join(ST_origin, ST_origin.journey_id == Journey.id)
                .filter(
                    Journey.line_id.in_(line_ids),
                    ST_origin.stop_id == self.atco_code,
                    Stop.locality_id.isnot(None),
                )
                .distinct()
            ).all()

            # resolve parents in Python
            result = []
            seen = set()
            for loc in localities:
                parent = loc.parent if loc.parent else loc
                if parent.id != self.locality_id and parent.id not in seen:
                    seen.add(parent.id)
                    result.append(parent)

            return result

    def times_from_stop(
        self, db: Session, date: datetime | None = None, limit: int = 10
    ) -> list["StopTime"]:
        """
        Returns a list of upcoming StopTime objects for this stop, with joined journey, line, and service.
        """

        if date is None:
            now = datetime.now(tz=LONDON)
        else:
            now = date

        today_date = now.date()
        seconds_since_midnight = now.hour * 3600 + now.minute * 60 + now.second
        current_time = timedelta(seconds=seconds_since_midnight)

        stop_times = (
            db.query(StopTime)
            .filter(StopTime.stop_id == self.atco_code)
            .filter(StopTime.pick_up == True)
            .join(Journey)
            .join(Calendar)
            .options(
                joinedload(StopTime.journey).joinedload(Journey.calendar),
                joinedload(StopTime.journey)
                .joinedload(Journey.line)
                .joinedload(Line.service),
            )
            .all()
        )

        active_stop_times = []
        for st in stop_times:
            if not st.journey.is_valid(today_date):
                continue
            active_stop_times.append(st)

        future_stop_times = [
            st
            for st in active_stop_times
            if st.departure_time and st.departure_time >= current_time
        ]

        future_stop_times.sort(key=lambda st: st.departure_time)

        return future_stop_times[:limit]


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
    admin_area_id = Column(Integer, ForeignKey("admin_area.id"))
    active = Column(Boolean, nullable=False)
    revision_number = Column(Integer, nullable=True)

    parent = relationship("StopArea", remote_side=[id], backref="children")
    admin_area = relationship("AdminArea", back_populates="stop_areas")

    stops = relationship(
        "Stop",
        back_populates="stop_area",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Operator(Base):
    __tablename__ = "operator"

    noc = Column(String, nullable=False, primary_key=True)
    ref = Column(String, nullable=True)
    name = Column(String, nullable=False)

    services = relationship(
        "Service",
        back_populates="operator",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    search_vector = deferred(Column(TSVectorType("name", "noc")))


class BankHoliday(Base):
    __tablename__ = "bank_holiday"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)

    dates = relationship(
        "BankHolidayDate",
        back_populates="bank_holiday",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    calendar_links = relationship(
        "CalendarToBankHoliday",
        back_populates="bank_holiday",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    calendars = association_proxy("calendar_links", "calendar")


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

    bank_holiday = relationship(
        "BankHoliday", back_populates="calendar_links", overlaps="calendars"
    )
    calendar = relationship(
        "Calendar", back_populates="calendar_bank_holiday", overlaps="calendars"
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

    calendar_bank_holiday = relationship(
        "CalendarToBankHoliday",
        back_populates="calendar",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    bank_holidays = association_proxy("calendar_bank_holiday", "bank_holiday")
    calendar_exceptions = relationship(
        "CalendarException",
        back_populates="calendar",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    journeys = relationship(
        "Journey",
        back_populates="calendar",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

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

    def is_valid(self, date: date | None = None) -> bool:
        """
        Returns True if the calendar is valid on the given date (or today if no date is given).
        """

        if not date:
            date = datetime.now(tz=LONDON).date()

        if not (
            self.start_date <= date and (self.end_date is None or self.end_date >= date)
        ):  # type: ignore
            return False

        # check day
        weekday = date.strftime("%A").lower()
        if not getattr(self, weekday):
            # log.debug("Not valid on this weekday, active days:", self.days_of_week)
            return False

        # check exceptions
        for exc in self.calendar_exceptions:
            if date < exc.start_date and exc.operating is True:
                return False
            if exc.start_date <= date <= exc.end_date:
                return exc.operating
            if date > exc.end_date and exc.operating is True:
                return False

        # check bank holidays
        for link in self.calendar_bank_holiday:
            bh = link.bank_holiday
            for bh_date in bh.dates:
                if bh_date.date == date:
                    log.debug(f"Bank holiday valid, and operating={link.operating}")
                    return link.operating

        return True


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

    data_source_id = Column(
        Integer, ForeignKey("data_source.id", ondelete="SET NULL"), nullable=True
    )

    data_source = relationship("DataSource", back_populates="services")

    operator = relationship("Operator", back_populates="services")
    lines = relationship(
        "Line",
        back_populates="service",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    journeys = relationship(
        "Journey",
        back_populates="service",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    search_vector = deferred(
        Column(
            TSVectorType(
                "description",
                "origin",
                "destination",
                "vias",
                "line_names",
                weights={
                    "line_names": "A",
                    "description": "B",
                    "origin": "C",
                    "destination": "C",
                    "vias": "C",
                },
            ),
        )
    )


class Line(Base):
    """
    A line is a specific route of a service, e.g. 67, 667, 67X
    """

    __tablename__ = "line"
    id = Column(String, primary_key=True, index=True)
    bt_service_id = Column(Integer, nullable=True)
    line_name = Column(String, nullable=False)
    inbound_description = Column(String)
    outbound_description = Column(String)
    geometry = Column(
        Geometry(geometry_type="MULTILINESTRING", srid=4326), nullable=True
    )  # an overall geometry of the line, merged from all track sections
    service_code = Column(
        String, ForeignKey("service.service_code", ondelete="CASCADE"), nullable=False
    )

    service = relationship("Service", back_populates="lines")
    journeys = relationship("Journey", back_populates="line")
    routes = relationship(
        "Route",
        back_populates="lines",
        secondary="line_to_route",
        cascade="all",
        passive_deletes=True,
    )
    stops = relationship("Stop", secondary="line_stop_usage", back_populates="lines")

    __table_args__ = (
        UniqueConstraint("line_name", "service_code", name="uq_line_per_service"),
    )

    search_vector = deferred(
        Column(
            TSVectorType(
                "line_name",
                "inbound_description",
                "outbound_description",
                weights={
                    "line_name": "A",
                    "inbound_description": "B",
                    "outbound_description": "B",
                },
            ),
        )
    )

    def get_dest_localities(self):
        with SessionLocal() as db:
            localities = (
                db.query(Locality)
                .join(Stop, Stop.locality_id == Locality.id)
                .join(Journey, Journey.destination_stop_id == Stop.atco_code)
                .filter(Journey.line_id == self.id)
                .filter(Stop.locality_id.isnot(None))
                .distinct()
                .all()
            )

            result_localities = []
            for locality in localities:
                if locality.parent_id:
                    parent = db.query(Locality).get(locality.parent_id)
                    if parent not in result_localities:
                        result_localities.append(parent)
                elif locality not in result_localities:
                    result_localities.append(locality)

        return result_localities

    async def get_bt_service_id(self, db: Session) -> int | None:
        """
        Returns the bustimes service ID if available, otherwise finds it.
        """
        bt_service_id = getattr(self, "bt_service_id", None)
        if bt_service_id is not None:
            return bt_service_id
        else:
            noc = self.service.operator_noc or ""
            line_name = self.line_name
            origin = self.service.origin
            destination = self.service.destination

            results = await fetch_json(
                f"{API_BASE}/services/?operator={noc}&search={' '.join([str(line_name), str(origin), str(destination)])}"
            )

            if not results or "results" not in results:
                return None

            bt_service = results["results"]

            if len(bt_service) != 1:
                return None

            service_id = bt_service[0]["id"]

            obj = db.merge(self)
            obj.bt_service_id = service_id
            db.commit()
            db.refresh(obj)

            self.bt_service_id = service_id
            return service_id


class LineStopUsage(Base):
    """
    A collection of all the stops that a line serves across all journeys
    """

    __tablename__ = "line_stop_usage"
    line_id = Column(
        String,
        ForeignKey("line.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    stop_id = Column(
        String,
        ForeignKey("stop.atco_code", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint("line_id", "stop_id", name="uq_line_stop_usage"),
    )


class LineToRoute(Base):
    """
    Many-to-many relationship between Line and Route
    """

    __tablename__ = "line_to_route"
    line_id = Column(
        String,
        ForeignKey("line.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    route_id = Column(
        String,
        ForeignKey("route.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("line_id", "route_id", name="uq_line_to_route"),)


class TrackSection(Base):
    """
    A point in a track, used to build the geometry of a route. known as RouteLink in TXC.
    """

    __tablename__ = "track_section"
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_stop = Column(String, nullable=True)  # if null, it is the first
    to_stop = Column(String, nullable=True)  # if null, it is the last
    distance = Column(Float, nullable=True)  # distance in meters
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=False)
    route_link_ref = Column(String, nullable=True)  # Reference to the route link
    route_section_id = Column(
        String, ForeignKey("route_section.id", ondelete="CASCADE"), nullable=False
    )

    route_section = relationship("RouteSection", back_populates="track")


class RouteSection(Base):
    """
    A section of a route, used to build the geometry of a route.
    """

    __tablename__ = "route_section"
    id = Column(String, primary_key=True)
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=True)

    track = relationship(
        "TrackSection",
        back_populates="route_section",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    route = relationship(
        "Route",
        back_populates="route_section",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Route(Base):
    """
    container for a route section
    """

    __tablename__ = "route"
    id = Column(String, primary_key=True)
    private_code = Column(String, nullable=True)
    description = Column(String, nullable=True)
    route_section_id = Column(
        String, ForeignKey("route_section.id", ondelete="CASCADE"), nullable=True
    )

    lines = relationship("Line", back_populates="routes", secondary="line_to_route")
    route_section = relationship("RouteSection", back_populates="route")


class Journey(Base):
    """
    full scheduled trip, has a one to many relationship with stop times to generate a schedule
    """

    __tablename__ = "journey"
    id = Column(String, primary_key=True)
    bt_trip_id = Column(Integer, nullable=True)
    service_code = Column(
        String, ForeignKey("service.service_code", ondelete="CASCADE"), nullable=False
    )
    vehicle_journey_code = Column(String, nullable=True)
    ticket_machine_code = Column(String, nullable=True)
    line_id = Column(
        String, ForeignKey("line.id", ondelete="CASCADE"), nullable=True, index=True
    )
    block_id = Column(String, nullable=True)
    direction = Column(Enum(DirectionType))
    headsign = Column(String, nullable=True)
    start_time = Column(Interval, nullable=False)
    end_time = Column(Interval)
    origin_stop_id = Column(
        String, ForeignKey("stop.atco_code"), nullable=True, index=True
    )
    destination_stop_id = Column(
        String, ForeignKey("stop.atco_code"), nullable=True, index=True
    )
    calendar_id = Column(
        Integer, ForeignKey("calendar.id", ondelete="CASCADE"), nullable=True
    )

    calendar = relationship("Calendar", back_populates="journeys")

    origin = relationship("Stop", foreign_keys=[origin_stop_id])
    destination = relationship("Stop", foreign_keys=[destination_stop_id])

    service = relationship("Service", back_populates="journeys")
    line = relationship("Line", back_populates="journeys")
    stop_times = relationship(
        "StopTime", back_populates="journey", cascade="all, delete-orphan"
    )

    def is_valid(self, date: date | None = None) -> bool:
        """
        Returns True if the journey is valid on the given date (or today if no date is given).
        """
        if not self.calendar:
            return False

        if not date:
            date = datetime.now(tz=LONDON).date()

        return self.calendar.is_valid(date)

    def get_previous_journey(
        self, db: Session, date: date | None = None
    ) -> "Journey | None":
        """
        Returns the previous journey in the same block, active on the same date, ordered by end_time.
        Adds debug output to show all candidate journeys.
        """

        if self.block_id is None:
            log.debug(f"No block_id for journey {self.id}")
            return None

        if not date:
            date = datetime.now(tz=LONDON).date()

        query = db.query(Journey).filter(
            Journey.block_id == self.block_id,
            Journey.id != self.id,
            Journey.end_time < self.start_time,
        )

        candidate_journeys = (
            query.options(joinedload(Journey.line).joinedload(Line.service))
            .order_by(Journey.end_time.desc())
            .all()
        )

        valid_candidates = [j for j in candidate_journeys if j.is_valid(date)]
        # log.debug(
        #     f"Candidate journeys for {self.ticket_machine_code} block {self.block_id} on {date} starting {self.start_time}:"
        # )
        # for j in valid_candidates:
        #     log.debug(
        #         f"  tmc: {j.ticket_machine_code}, End Time: {j.end_time}, Valid: {j.is_valid(date)}"
        #     )

        prev_journey = valid_candidates[0] if valid_candidates else None
        return prev_journey

    async def get_bt_trip_id(self, db: Session) -> int | None:
        """
        Returns the bustimes trip ID if available, otherwise finds it.
        """
        bt_trip_id = getattr(self, "bt_trip_id", None)
        if bt_trip_id is not None:
            return bt_trip_id
        else:
            vjc = self.vehicle_journey_code
            tmc = self.ticket_machine_code
            block = self.block_id

            results = await fetch_json(
                f"{API_BASE}/trips/?vehicle_journey_code={vjc}&ticket_machine_code={tmc}&block={block or ''}"
            )

            if not results or "results" not in results:
                return None

            bt_trip = results["results"]

            if len(bt_trip) != 1:
                return None

            trip_id = bt_trip[0]["id"]

            obj = db.merge(self)
            obj.bt_trip_id = trip_id
            db.commit()
            db.refresh(obj)

            self.bt_trip_id = trip_id
            return trip_id


class StopTime(Base):
    """
    every time a journey stops at a stop
    """

    __tablename__ = "stop_time"
    id = Column(Integer, primary_key=True, autoincrement=True)
    journey_id = Column(
        String, ForeignKey("journey.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stop_id = Column(
        String,
        ForeignKey("stop.atco_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stop_sequence = Column(Integer, nullable=False)
    arrival_time = Column(Interval, nullable=True)
    departure_time = Column(Interval, nullable=True, index=True)
    dest_display = Column(String, nullable=True)
    timing_status = Column(String, nullable=True)
    pick_up = Column(Boolean, nullable=True)
    drop_off = Column(Boolean, nullable=True)
    wait_time = Column(Interval, nullable=True)  # wait time in seconds
    distance_traveled = Column(Float, nullable=True)  # distance in meters

    journey = relationship("Journey", back_populates="stop_times")
    stop = relationship("Stop", back_populates="stop_times")

    __table_args__ = (Index("ix_stoptime_journey_seq", "journey_id", "stop_sequence"),)

    @property
    def headsign(self):
        # return self.journey.destination.locality.name#

        is_outbound = self.journey.direction == DirectionType.outbound

        main_dest = (
            self.journey.line.service.destination
            if is_outbound
            else self.journey.line.service.origin
        )

        line_dest = (
            self.journey.line.outbound_description
            if is_outbound
            else self.journey.line.inbound_description
        )

        vias = self.journey.line.service.vias or ""

        raw_headsign = self.dest_display or self.journey.headsign
        fallback_headsign = main_dest

        do_makeshift = False

        show_headsign = False
        if raw_headsign:
            short_enough = len(raw_headsign) < 25
            overlaps = any(
                word in raw_headsign.split()
                for word in (main_dest.split() + line_dest.split() + vias.split(", "))
            )
            show_headsign = short_enough and overlaps
        if do_makeshift:
            if show_headsign:
                final = raw_headsign
            else:
                makeshift = (
                    f"{main_dest} {raw_headsign}" if raw_headsign else fallback_headsign
                )
                log.debug("using makeshift headsign", makeshift)
                final = makeshift
        else:
            if show_headsign:
                final = raw_headsign
            else:
                final = fallback_headsign
        if self.journey.destination and self.journey.destination.locality:
            return final or self.journey.destination.locality.name

        return final or fallback_headsign

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
