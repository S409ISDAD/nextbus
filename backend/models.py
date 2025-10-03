import enum
from datetime import date, datetime, timedelta
import copy
from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
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
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    UniqueConstraint,
    and_,
    func,
    Index,
    inspect,
    or_,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, Session, joinedload, deferred, aliased
from sqlalchemy_searchable import make_searchable
from sqlalchemy_utils.types import TSVectorType
from functools import lru_cache
from backend.autoslug import AutoSlugMixin
from backend.config import API_BASE, get_logger
from backend.db.db import SessionLocal
from backend.deps import LONDON
from backend.utils.fetch_json import fetch_json
from sqlalchemy import select
from backend.utils.bulk_upsert import bulk_upsert
from collections import namedtuple

log = get_logger(__name__)

Base = declarative_base()
make_searchable(Base.metadata)


ServiceLite = namedtuple("ServiceLite", ["id", "line_name"])


def to_dict(obj, exclude: list = []):
    return {
        c.key: getattr(obj, c.key)
        for c in inspect(obj).mapper.column_attrs
        if c.key not in exclude
    }


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


class TimingStatusEnum(str, enum.Enum):
    other = "OTH"
    time_info_point = "TIP"
    principal_timing_point = "PTP"


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
    url = Column(String, nullable=True, doc="URL for non-BODS like stagecoach")
    bods_id = Column(Integer, nullable=True, doc="BODS dataset ID")
    search = Column(String, nullable=True, doc="Search term for BODS")
    last_modified = Column(DateTime(timezone=True), nullable=True)

    services = relationship(
        "Service",
        back_populates="data_source",
    )
    timetables = relationship(
        "Timetable",
        back_populates="data_source",
    )


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


class Locality(Base, AutoSlugMixin):
    __tablename__ = "locality"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    qualifier_name = Column(String, nullable=True)
    # slug = AutoSlug(source="get_full_name", max_length=100, unique=True, nullable=False)
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

    @property
    def get_full_name(self):
        if self.qualifier_name:
            return f"{self.name}, {self.qualifier_name}"
        return self.name

    @property
    def has_stops(self):
        return len(self.stops) > 0

    def services_served(self):
        with SessionLocal() as db:
            services: list["Service"] | list[None] = (
                db.query(Service)
                .join(ServiceStopUsage, Service.id == ServiceStopUsage.service_id)
                .join(Stop, Stop.atco_code == ServiceStopUsage.stop_id)
                .options(joinedload(Service.operator))
                .filter(Stop.locality_id == self.id)
                .distinct()
                .all()
            )

            return services if services else []


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
        String, ForeignKey("stop_area.id", ondelete="CASCADE"), nullable=True
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
    services = relationship(
        "Service", secondary="service_stop_usage", back_populates="stops"
    )

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

    @property
    def does_serve_buses(self) -> bool:
        return any(s for s in self.services if s.public_use)

    def lines_served(self, db: Session) -> list["ServiceLite"]:
        """
        Returns a list of services that serve this stop.
        """

        lines = [
            ServiceLite(id=row[0], line_name=row[1])
            for row in (
                db.query(Service.id, Service.line_name)
                .filter(
                    db.query(ServiceStopUsage)
                    .filter(
                        ServiceStopUsage.service_id == Service.id,
                        ServiceStopUsage.stop_id == self.atco_code,
                    )
                    .exists()
                )
                .all()
            )
        ]
        return lines

    def headsigns(self):
        with SessionLocal() as db:
            service_ids = [service.id for service in self.lines_served(db)]
            if not service_ids:
                return []

            headsigns = (
                db.query(StopTime.headsign)
                .join(StopTime, StopTime.journey_id == Journey.id)
                .filter(
                    Journey.service_id.in_(service_ids),
                    StopTime.stop_id == self.atco_code,
                )
                .distinct()
            ).all()

            return headsigns

    def localities_towards(self):
        with SessionLocal() as db:
            service_ids = [service.id for service in self.lines_served(db)]
            if not service_ids:
                return []

            ST_origin = aliased(StopTime)

            localities = (
                db.query(Locality)
                .join(Stop, Stop.locality_id == Locality.id)
                .join(Journey, Journey.destination_stop_id == Stop.atco_code)
                .join(ST_origin, ST_origin.journey_id == Journey.id)
                .filter(
                    Journey.service_id.in_(service_ids),
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
        self,
        db: Session,
        date_time: datetime | None = None,
        limit: int = 10,
        line_names: list[str] | None = None,
    ) -> list["StopTime"]:
        """
        Returns a list of upcoming StopTime objects for this stop, with joined journey and service.
        """

        now = date_time or datetime.now(tz=LONDON)

        results = []
        stop_times_q = (
            db.query(StopTime)
            .join(StopTime.journey)
            .join(Journey.calendar)
            .filter(StopTime.stop_id == self.atco_code)
            .filter(StopTime.pick_up)
            .options(
                joinedload(StopTime.journey).joinedload(Journey.calendar),
                joinedload(StopTime.journey).joinedload(Journey.timetable),
            )
        )

        if line_names:
            stop_times_q = (
                stop_times_q.join(StopTime.journey)
                .join(Journey.service)
                .filter(Service.line_name.in_(line_names))
            )

        stop_times = stop_times_q.all()

        day_offsets = [0]

        if now.hour < 3:
            # consider yesterdays night trips
            day_offsets.insert(0, -1)

        if now.hour >= 21:
            # consider tomorrows morning trips
            day_offsets.append(1)

        for day_offset in day_offsets:
            service_day = (now + timedelta(days=day_offset)).date()

            stop_times_today = [
                st for st in stop_times if st.journey.is_valid(service_day)
            ]
            for st in stop_times_today:
                depdt = st.departure_datetime(service_day)

                if not depdt:
                    log.warning(
                        f"StopTime {st.id} has no departure datetime for service day {service_day}"
                    )  # should not happen
                    continue
                if depdt >= now:
                    # make a new copy to avoid overwriting _dep_dt, as a stoptime object can be reused for multiple service days
                    st_copy = copy.copy(st)
                    st_copy._dep_dt = depdt
                    results.append(st_copy)

        results.sort(key=lambda x: x._dep_dt)
        return results[:limit]


class StopArea(Base):
    __tablename__ = "stop_area"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    point = Column(
        Geometry(geometry_type="POINT"),
        nullable=True,
    )
    lat = Column(Float, Computed("ST_Y(point::geometry)"), nullable=True)
    lon = Column(Float, Computed("ST_X(point::geometry)"), nullable=True)
    type = Column(Enum(StopAreaTypeEnum), nullable=True)
    parent_id = Column(String, ForeignKey("stop_area.id"), nullable=True)
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

    id = Column(Integer, primary_key=True, autoincrement=True)

    noc = Column(String, nullable=False)
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
    name = Column(String, unique=True)

    dates = relationship(
        "BankHolidayDate",
        back_populates="bank_holiday",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __str__(self):
        return str(self.name)


class BankHolidayDate(Base):
    __tablename__ = "bank_holiday_date"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bank_holiday_name = Column(
        String, ForeignKey("bank_holiday.name"), nullable=False, index=True
    )
    date = Column(Date, nullable=False)

    bank_holiday = relationship("BankHoliday", back_populates="dates")

    __table_args__ = (
        UniqueConstraint(
            "bank_holiday_name",
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
    bank_holiday = Column(
        String,
        ForeignKey("bank_holiday.name"),
        nullable=False,
    )
    calendar_id = Column(
        Integer, ForeignKey("calendar.id", ondelete="CASCADE"), nullable=False
    )
    calendar = relationship("Calendar", back_populates="calendar_bank_holiday")
    bh = relationship("BankHoliday")
    __table_args__ = (
        PrimaryKeyConstraint(
            "bank_holiday", "calendar_id", name="pk_calendar_bank_holiday"
        ),
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

    def is_valid(self, service_day: date | None = None) -> bool:
        """
        Returns True if the calendar is valid on the given date (or today if no date is given).
        """

        date = service_day or datetime.now(tz=LONDON).date()

        if not (
            self.start_date <= date and (self.end_date is None or self.end_date >= date)
        ):  # type: ignore
            # log.debug("Date not in range of calendar")
            return False

        # check day
        weekday = date.strftime("%A").lower()
        if not getattr(self, weekday):
            # log.debug(f"Not valid on this weekday, active days: {self.days_of_week}")
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
            bh = link.bh
            for bh_date in bh.dates:
                if bh_date.date == date:
                    log.debug(f"Bank holiday valid, and operating={link.operating}")
                    return link.operating

        return True

    def is_valid_exp(self, service_day: date | None = None) -> bool:
        """
        Checks only exceptions (and bank holidays for now)
        """

        date = service_day or datetime.now(tz=LONDON).date()

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
            bh = link.bh
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
    calendar_id = Column(
        Integer, ForeignKey("calendar.id", ondelete="CASCADE"), nullable=False
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    operating = Column(Boolean, nullable=False, default=True)
    description = Column(String, nullable=True)

    calendar = relationship("Calendar", back_populates="calendar_exceptions")

    __table_args__ = (
        UniqueConstraint(
            "calendar_id",
            "start_date",
            "end_date",
            "operating",
            name="uq_calendar_exception",
        ),
    )


class Service(Base, AutoSlugMixin):
    """
    The top level representation of a bus service, containing all the generic information. can have multiple route objects, being timetable revisions
    """

    __tablename__ = "service"
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_code = Column(String, nullable=False, index=True)
    operator_id = Column(Integer, ForeignKey("operator.id"), nullable=True)
    bt_service_id = Column(Integer, nullable=True, index=True)
    data_source_id = Column(
        Integer, ForeignKey("data_source.id", ondelete="SET NULL"), nullable=True
    )

    line_name = Column(String, nullable=False)
    line_brand = Column(String, nullable=True)
    description = Column(String)
    vias = Column(String, nullable=True)
    # slug = AutoSlug(source="get_full_name", max_length=100, unique=True, nullable=False)

    public_use = Column(Boolean)
    current = Column(Boolean, nullable=False, default=True, index=True)
    geometry = Column(
        Geometry(geometry_type="MULTILINESTRING", srid=4326), nullable=True
    )
    data_wrong = Column(
        Boolean, nullable=False, default=False
    )  # flag to indicate that the timetable is incorrect
    last_modified = Column(DateTime(timezone=True), server_default=func.now())

    operator = relationship(
        "Operator",
        back_populates="services",
    )
    data_source = relationship("DataSource", back_populates="services")
    timetables = relationship(
        "Timetable",
        back_populates="service",
    )
    stops = relationship(
        "Stop", secondary="service_stop_usage", back_populates="services"
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
                "line_name",
                "line_brand",
                "description",
                "vias",
                weights={
                    "line_name": "A",
                    "description": "A",
                    "line_brand": "B",
                    "vias": "B",
                },
            )
        )
    )

    @property
    def get_full_name(self):
        return f"{self.line_name} {self.description}".strip()

    def with_timetable(self):
        timetable = next((tt for tt in self.timetables if tt.is_valid()), None)
        if timetable:
            return {
                "service_id": self.id,
                "line_name": timetable.line_name,
                "inbound_description": timetable.inbound_description,
                "outbound_description": timetable.outbound_description,
                "geometry": None,
                "bt_service_id": self.bt_service_id,
                "service_code": self.service_code,
                "description": self.description,
                "origin": timetable.origin,
                "destination": timetable.destination,
                "vias": timetable.vias,
                "operator_noc": self.operator.noc,
                "operator": self.operator.name,
            }

    def get_dest_localities(self):
        with SessionLocal() as db:
            localities = (
                db.query(Locality)
                .join(Stop, Stop.locality_id == Locality.id)
                .join(Journey, Journey.destination_stop_id == Stop.atco_code)
                .filter(Journey.service_id == self.id)
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
        if self.bt_service_id is not None:
            return self.bt_service_id

        noc = self.operator.noc or ""

        results = await fetch_json(
            f"{API_BASE}/services/?operator={noc}&search={self.description.replace('-', ' ')}"
        )

        if not results or "results" not in results or len(results["results"]) != 1:
            return None

        service_id = results["results"][0]["id"]

        obj = db.merge(self)
        obj.bt_service_id = service_id
        db.commit()
        db.refresh(obj)

        self.bt_service_id = service_id
        return service_id

    def do_stopusages(self, db: Session):
        """
        builds the service_stop_usage table for this service
        """

        existing = (
            db.query(ServiceStopUsage)
            .filter(ServiceStopUsage.service_id == self.id)
            .order_by(ServiceStopUsage.inbound, ServiceStopUsage.order)
            .all()
        )

        stop_times_subq = (
            select(
                Journey.inbound,
                Timetable.line_name,
                StopTime.stop_sequence.label("sequence"),
                StopTime.id.label("st_id"),
                StopTime.stop_id,
                StopTime.timing_status,
            )
            .join(Journey, StopTime.journey_id == Journey.id)
            .join(Timetable, Journey.timetable_id == Timetable.id)
            .where(Journey.service_id == self.id, StopTime.stop_id is not None)
            .distinct(Journey.inbound, Timetable.line_name, StopTime.stop_id)
            .subquery()
        )

        rows = db.execute(select(stop_times_subq)).all()

        stop_usages = [
            (
                row.line_name,
                row.inbound,
                row.sequence or 0,
                row.st_id,
                row.stop_id,
                row.timing_status,
            )
            for row in rows
        ]

        stop_usages.sort()

        new = [
            ServiceStopUsage(
                service_id=self.id,
                stop_id=stop_id,
                timing_point=(timing_status == "PTP"),
                inbound=inbound,
                order=i,
                line_name=line_name,
            )
            for i, (line_name, inbound, _, _, stop_id, timing_status) in enumerate(
                stop_usages
            )
        ]

        existing_hash = [
            (su.stop_id, su.timing_point, su.inbound, su.order, su.line_name)
            for su in existing
        ]
        new_hash = [
            (su.stop_id, su.timing_point, su.inbound, su.order, su.line_name)
            for su in new
        ]

        if existing_hash != new_hash:
            log.info(
                f"ServiceStopUsage for service {self.id} is out of date, updating..."
            )
            if len(existing_hash) >= len(new_hash):
                for new_su, exist_su in zip(new, existing):
                    new_su.id = exist_su.id

                upsert_data = [to_dict(n) for n in new if n.id is not None]
                bulk_upsert(
                    db,
                    ServiceStopUsage,
                    upsert_data,
                    ["id"],
                    [
                        "service_id",
                        "stop_id",
                        "timing_point",
                        "inbound",
                        "order",
                        "line_name",
                    ],
                )
                if len(existing_hash) > len(new_hash):
                    existing_ids = [su.id for su in existing[len(new) :]]
                    db.query(ServiceStopUsage).filter(
                        ServiceStopUsage.id.in_(existing_ids)
                    ).delete(synchronize_session=False)
            else:
                if existing_hash:
                    existing_ids = [su.id for su in existing]
                    db.query(ServiceStopUsage).filter(
                        ServiceStopUsage.id.in_(existing_ids)
                    ).delete(synchronize_session=False)

                db.add_all(new)

            db.commit()

    def do_geometry(self, db: Session):
        """
        builds the geometry for this service from its stops
        """

        simplify_tolerance = 0.0002  # 20 meters

        route_link_count = (
            db.query(RouteLink)
            .join(Journey, Journey.timetable_id == RouteLink.timetable_id)
            .filter(Journey.service_id == self.id)
            .count()
        )

        if route_link_count == 0:
            log.warning(
                f"Service {self.id} has no route links, building geometry from stops"
            )
            subq = (
                db.query(
                    ServiceStopUsage.line_name,
                    ServiceStopUsage.inbound,
                    func.ST_Transform(Stop.point, 4326).label("pt"),
                )
                .join(Stop, Stop.atco_code == ServiceStopUsage.stop_id)
                .filter(ServiceStopUsage.service_id == self.id)
                .order_by(
                    ServiceStopUsage.inbound,
                    ServiceStopUsage.line_name,
                    ServiceStopUsage.order,
                )
                .subquery()
            )

            lines = (
                db.query(func.ST_MakeLine(subq.c.pt))
                .group_by(subq.c.line_name, subq.c.inbound)
                .all()
            )

            if lines:
                multiline = db.query(
                    func.ST_Collect(*[line[0] for line in lines])
                ).scalar()
                self.geometry = multiline
                db.add(self)
                db.commit()
            return

        subq = (
            db.query(RouteLink.geometry.label("geom"))
            .join(Journey, Journey.timetable_id == RouteLink.timetable_id)
            .filter(Journey.service_id == self.id)
            .subquery()
        )
        collected = db.query(func.ST_Collect(subq.c.geom).label("geom")).scalar()

        if collected:
            merged = db.query(func.ST_LineMerge(collected)).scalar()
            simplified = db.query(func.ST_Simplify(merged, simplify_tolerance)).scalar()
            multiline = db.query(func.ST_Multi(simplified)).scalar()

            self.geometry = multiline
            db.add(self)
            db.commit()


class ServiceStopUsage(Base):
    """
    A collection of all the stops that a service serves across all journeys
    """

    __tablename__ = "service_stop_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(
        Integer,
        ForeignKey("service.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stop_id = Column(
        String,
        ForeignKey("stop.atco_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order = Column(SmallInteger)
    inbound = Column(Boolean, default=False)
    line_name = Column(String, nullable=True)
    timing_point = Column(Boolean, default=True)

    __table_args__ = (Index("ix_stopusage_inbound_order", "inbound", "order"),)


class TimetableDataSource(Base):
    __tablename__ = "timetable_data_source"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String)
    file_hash = Column(String, nullable=False, unique=True, index=True)
    size_bytes = Column(Integer, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    data_source_id = Column(Integer, ForeignKey("data_source.id"), nullable=True)

    data_source = relationship("DataSource")
    timetables = relationship(
        "Timetable",
        back_populates="timetable_data_sources",
        secondary="timetable_tt_data_source_link",
        passive_deletes=True,
    )


class TimetableToTTDataSource(Base):
    """
    Many-to-many relationship between Timetable and TimetableDataSource
    """

    __tablename__ = "timetable_tt_data_source_link"
    timetable_id = Column(
        Integer,
        ForeignKey("timetable.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tt_data_source_id = Column(
        Integer,
        ForeignKey("timetable_data_source.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "timetable_id", "tt_data_source_id", name="pk_timetable_data_source_link"
        ),
    )


class Timetable(Base):
    """
    The timetable level of a bus route, associated with one service. contains information about the bus timetable itself, being stuff that can change.
    """

    __tablename__ = "timetable"
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey("service.id"), nullable=False, index=True)
    line_id = Column(String, nullable=True)
    operator_id = Column(Integer, ForeignKey("operator.id"), nullable=True)
    data_source_id = Column(
        Integer,
        ForeignKey("data_source.id", ondelete="SET NULL"),
        nullable=True,
    )
    bt_service_id = Column(Integer, nullable=True, index=True)

    service_code = Column(String, nullable=False)
    line_name = Column(String, nullable=False)
    line_brand = Column(String, nullable=True)
    description = Column(String)
    origin = Column(String, nullable=True)
    destination = Column(String, nullable=True)
    vias = Column(String, nullable=True)
    inbound_description = Column(String, nullable=True)
    outbound_description = Column(String, nullable=True)

    revision_number = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    modified_at = Column(DateTime(timezone=True), nullable=True)
    start_date = Column(Date)
    end_date = Column(
        Date, default=date(9999, 12, 31)
    )  # no end date means it is valid indefinitely
    geometry = Column(
        Geometry(geometry_type="MULTILINESTRING", srid=4326), nullable=True
    )

    public_use = Column(Boolean)

    service = relationship("Service", back_populates="timetables")
    operator = relationship("Operator")
    data_source = relationship("DataSource", back_populates="timetables")
    timetable_data_sources = relationship(
        "TimetableDataSource",
        back_populates="timetables",
        secondary="timetable_tt_data_source_link",
        passive_deletes=True,
    )
    journeys = relationship(
        "Journey",
        back_populates="timetable",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    route_links = relationship(
        "RouteLink",
        back_populates="timetable",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def actual_end_date(self):
        if self.end_date == date(9999, 12, 31):
            return None
        return self.end_date

    def is_valid(self, date: date | None = None) -> bool:
        """
        checks if the timetable is valid on the given date / today.
        """

        if not date:
            date = datetime.now(tz=LONDON).date()

        if not (
            self.start_date <= date
            and (self.actual_end_date is None or self.actual_end_date >= date)
        ):  # type: ignore
            return False

        return True

    __table_args__ = (
        Index(
            "uq_service_revision_with_nulls",
            "service_id",
            "revision_number",
            "start_date",
            "end_date",
            "data_source_id",
            unique=True,
        ),
        Index("ix_timetable_service_line_name", "service_id", "line_name"),
    )


class RouteLink(Base):
    """
    A connection between 2 stops, used to build the geometry of a route
    """

    __tablename__ = "route_link"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timetable_id = Column(
        Integer, ForeignKey("timetable.id", ondelete="CASCADE"), nullable=False
    )
    from_stop = Column(
        String, ForeignKey("stop.atco_code"), nullable=True
    )  # if null, it is the first
    to_stop = Column(
        String, ForeignKey("stop.atco_code"), nullable=True
    )  # if null, it is the last
    distance = Column(Float, nullable=True)  # distance in meters
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=False)

    timetable = relationship("Timetable", back_populates="route_links")
    link_from = relationship("Stop", foreign_keys=[from_stop])
    link_to = relationship("Stop", foreign_keys=[to_stop])

    __table_args__ = (
        UniqueConstraint(
            "timetable_id", "from_stop", "to_stop", name="uq_timetable_routelink"
        ),
    )


class Journey(Base):
    """
    full scheduled trip, has a one to many relationship with stop times to generate a schedule
    """

    __tablename__ = "journey"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bt_trip_id = Column(Integer, nullable=True)
    service_id = Column(
        Integer,
        ForeignKey("service.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timetable_id = Column(
        Integer,
        ForeignKey("timetable.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vehicle_journey_code = Column(String, nullable=True)
    ticket_machine_code = Column(String, nullable=True)
    sequence = Column(SmallInteger, nullable=True)
    block_id = Column(String, nullable=True)
    inbound = Column(Boolean)
    headsign = Column(String, nullable=True)
    start_time = Column(Interval, nullable=True)
    end_time = Column(Interval, nullable=True)
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
    timetable = relationship("Timetable", back_populates="journeys")
    stop_times = relationship(
        "StopTime", back_populates="journey", cascade="all, delete-orphan"
    )

    # def is_valid(self, date_time: datetime | None = None) -> bool:
    #     """
    #     Returns True if the journey is valid on the given date (or today if no date is given).
    #     """
    #     if not self.calendar:
    #         log.warning(f"No calendar for journey {self.id}")
    #         return True

    #     date_time = date_time or datetime.now(tz=LONDON)

    #     if self.start_time is not None:
    #         journey_start_today = datetime.combine(
    #             date_time.date(),
    #             (datetime.min + self.start_time).time(),
    #         ).astimezone(LONDON)

    #         time_diff = date_time - journey_start_today

    #         if time_diff > timedelta(hours=12):
    #             date_time -= timedelta(days=1)

    #     return self.calendar.is_valid(date_time)

    def is_valid(self, service_day: date | None = None) -> bool:
        """
        Returns True if the journey is valid on the given date (or today if no date is given).
        """
        if not self.calendar:
            log.warning(f"No calendar for journey {self.id}")
            return True

        date = service_day or datetime.now(tz=LONDON).date()

        return self.calendar.is_valid(date)

    def is_valid_exp(self, service_day: date | None = None) -> bool:
        """
        Checks only exceptions
        """
        if not self.calendar:
            log.warning(f"No calendar for journey {self.id}")
            return True

        date = service_day or datetime.now(tz=LONDON).date()

        return self.calendar.is_valid_exp(date)

    @lru_cache(maxsize=128)
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

        date = date or datetime.now(tz=LONDON).date()

        query = (
            db.query(Journey)
            .join(Journey.calendar)
            .filter(
                Journey.block_id == self.block_id,
                Journey.sequence < self.sequence,
                Journey.end_time < self.start_time,
                journey_is_valid_filter(date),
            )
            .options(joinedload(Journey.service).joinedload(Service.operator))
        )

        candidate_journeys = (
            query.options(joinedload(Journey.service))
            .order_by(Journey.sequence.desc())
            .all()
        )

        prev_journey = candidate_journeys[0] if candidate_journeys else None
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

            bt_trips = results["results"]

            if len(bt_trips) == 1:
                trip_id = bt_trips[0]["id"]

            elif len(bt_trips) > 1:
                trip_id = next(
                    (
                        trip["id"]
                        for trip in bt_trips
                        if trip.get("service") and trip["service"].get("id")
                    ),
                    None,
                )
            else:
                trip_id = None

            obj = db.merge(self)
            obj.bt_trip_id = trip_id
            db.commit()
            db.refresh(obj)

            self.bt_trip_id = trip_id
            return trip_id


def journey_is_valid_filter(date: date | None = None):
    date = date or datetime.now(tz=LONDON).date()
    weekday = date.strftime("%A").lower()

    base_filter = and_(
        Calendar.start_date <= date,
        or_(Calendar.end_date == None, Calendar.end_date >= date),
        getattr(Calendar, weekday),
    )

    # bh_filter = or_(
    #     ~Calendar.calendar_bank_holiday.any(),  # no bank holiday links
    #     Calendar.calendar_bank_holiday.any(
    #         and_(
    #             CalendarToBankHoliday.operating == True,
    #             CalendarToBankHoliday.bh.has(
    #                 BankHoliday.dates.any(BankHolidayDate.date == date)
    #             ),
    #         )
    #     ),
    # )

    # return and_(base_filter, bh_filter)
    return base_filter


class StopTime(Base):
    """
    every time a journey stops at a stop
    """

    __tablename__ = "stop_time"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    journey_id = Column(
        BigInteger,
        ForeignKey("journey.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stop_id = Column(
        String,
        ForeignKey("stop.atco_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stop_sequence = Column(SmallInteger, nullable=False)
    arrival_time = Column(Interval, nullable=True)
    departure_time = Column(Interval, nullable=True, index=True)
    dest_display = Column(String, nullable=True)
    timing_status = Column(Enum(TimingStatusEnum), nullable=True)
    pick_up = Column(Boolean, nullable=True)
    drop_off = Column(Boolean, nullable=True)

    journey = relationship("Journey", back_populates="stop_times")
    stop = relationship("Stop", back_populates="stop_times")

    __table_args__ = (Index("ix_stoptime_journey_seq", "journey_id", "stop_sequence"),)

    def __repr__(self):
        return f"id={self.id}, journey_id={self.journey_id}, stop_id={self.stop_id}, stop_sequence={self.stop_sequence}, arrival_time={self.arrival_time}, departure_time={self.departure_time}"

    @property
    def headsign(self):
        try:
            # return self.journey.destination.locality.name#

            is_outbound = self.journey.inbound is False

            main_dest = (
                self.journey.timetable.destination
                if is_outbound
                else self.journey.timetable.origin
            )

            line_dest = (
                self.journey.timetable.outbound_description
                if is_outbound
                else self.journey.timetable.inbound_description
            )

            vias = self.journey.timetable.vias or ""

            raw_headsign = self.dest_display or self.journey.headsign
            fallback_headsign = main_dest

            do_makeshift = False

            show_headsign = False
            if raw_headsign:
                short_enough = len(raw_headsign) < 25
                overlaps = any(
                    word in raw_headsign.split()
                    for word in (
                        main_dest.split()
                        + line_dest.split()
                        + vias.split(", ")
                        + self.journey.service.description.split()
                    )
                )
                bad_chars = any(c in raw_headsign for c in ("/",))
                show_headsign = short_enough and overlaps and not bad_chars

            if do_makeshift:
                if show_headsign:
                    final = raw_headsign
                else:
                    makeshift = (
                        f"{main_dest} {raw_headsign}"
                        if raw_headsign
                        else fallback_headsign
                    )
                    log.debug("using makeshift headsign", makeshift)
                    final = makeshift
            else:
                if show_headsign:
                    final = raw_headsign
                else:
                    final = fallback_headsign

            bad_chars = any(c in final for c in ("/",))
            if (
                bad_chars
                and self.journey.destination
                and self.journey.destination.locality
            ):
                return self.journey.destination.locality.name

            if self.journey.destination and self.journey.destination.locality:
                return final or self.journey.destination.locality.name

            return final or fallback_headsign
        except Exception as e:
            log.error(f"Error getting headsign for stoptime {self.id}: {e}")
            return None

    def departure_datetime(self, service_day: date) -> datetime | None:
        dep = self.departure_time or self.arrival_time
        if dep is None:
            return None

        return datetime.combine(service_day, (datetime.min + dep).time(), tzinfo=LONDON)

    @property
    def dep_or_arr(self):
        return self.departure_time or self.arrival_time

    @property
    def dep_or_arr_str(self):
        return self.departure_time_str or self.arrival_time_str

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
