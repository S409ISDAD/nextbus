import calendar
import datetime as dt
from datetime import datetime, timezone, timedelta
from functools import cache
import logging
from shapely import LineString, Point
from isodate import parse_duration
import xml.etree.cElementTree as ET

uk_timezone = timezone(timedelta(hours=1))

WEEKDAYS = {day: i for i, day in enumerate(calendar.day_name)}


def to_datetime(date_str):
    """Convert a date string to a datetime object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").astimezone(uk_timezone).date()
    except ValueError:
        return None


def parse_time(string: str) -> timedelta:
    hours, minutes, seconds = string.split(":")
    return timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds))


def strip_ns_recursive(elem):
    if elem.tag.startswith("{"):
        elem.tag = elem.tag.split("}", 1)[1]
    for child in elem:
        strip_ns_recursive(child)


class DateRange:
    def __init__(self, element):
        self.start_date = to_datetime(element.findtext("StartDate"))
        self.end_date = to_datetime(element.findtext("EndDate"))
        self.description = element.findtext("Description")

    def is_valid(self, date):
        return (self.start_date is None or date >= self.start_date) and (
            self.end_date is None or date <= self.end_date
        )


class ServicedOrganisation:
    def __init__(self, element):
        self.code = element.findtext("OrganisationCode")
        self.name = element.findtext("Name")

        working_days = element.findall("WorkingDays/DateRange")
        self.working_days = [DateRange(e) for e in working_days if len(e)]

        holidays = element.findall("Holidays/DateRange")
        self.holidays = [DateRange(e) for e in holidays if len(e)]

        self.hash = ET.tostring(element)

    def __str__(self):
        return self.name or self.code


class StopPoint:
    def __init__(self, element):
        atco_code = element.findtext("StopPointRef")
        if not atco_code:
            atco_code = element.findtext("AtcoCode", "")
        self.atco_code = atco_code.upper()
        self.common_name = element.findtext("CommonName")
        if not self.common_name:
            self.common_name = element.findtext("Descriptor/CommonName")


class Location:
    def __init__(self, element):
        self.location_id = element.get("id")
        longitude = element.findtext("Longitude")
        latitude = element.findtext("Latitude")
        point = (
            Point(float(longitude), float(latitude)) if longitude and latitude else None
        )
        self.point = point


class RouteLink:
    def __init__(self, element):
        self.route_link_id = element.get("id")
        self.from_stop = element.findtext("From/StopPointRef")
        self.to_stop = element.findtext("To/StopPointRef")
        self.distance = (
            float(element.findtext("Distance"))
            if element.findtext("Distance") is not None
            else None
        )
        locations: list[Location] = []
        mapping = element.find("Track/Mapping")
        if mapping is not None:
            for loc_elem in mapping.findall("Location"):
                locations.append(Location(loc_elem))

        self.locations = locations


class RouteSection:
    def __init__(self, element):
        self.section_id = element.get("id")
        route_links: list[RouteLink] = []
        for rl_elem in element.findall("RouteLink"):
            route_links.append(RouteLink(rl_elem))
        self.route_links = route_links


class Route:
    def __init__(self, element):
        self.route_id = element.get("id")
        self.creation_datetime = element.get("CreationDateTime")
        self.modification_datetime = element.get("ModificationDateTime")
        self.modification = element.get("Modification")
        self.revision_number = element.get("RevisionNumber")
        self.private_code = element.findtext("PrivateCode")
        self.description = element.findtext("Description")
        self.route_section_ref = element.findtext("RouteSectionRef")


class JourneyPatternTimingLinkFromTo:
    def __init__(self, element):
        self.id = element.get("id")
        self.fromto = (
            ("from" if element.tag == "From" else "to")
            if element.tag in ["From", "To"]
            else None
        )
        self.sequence_number = element.get("SequenceNumber")
        self.activity = element.findtext("Activity")
        self.dynamic_destination_display = element.findtext("DynamicDestinationDisplay")
        self.stop_point_ref = element.findtext("StopPointRef")
        self.timing_status = element.findtext("TimingStatus")
        self.fare_stage_number = element.findtext("FareStageNumber")


class JourneyPatternTimingLink:
    def __init__(self, element):
        self.link_id = element.get("id")
        from_elem = element.find("From")
        to_elem = element.find("To")
        self.from_stop = (
            JourneyPatternTimingLinkFromTo(from_elem) if from_elem is not None else None
        )
        self.to_stop = (
            JourneyPatternTimingLinkFromTo(to_elem) if to_elem is not None else None
        )
        self.route_link_ref = element.findtext("RouteLinkRef")
        self.run_time = element.findtext("RunTime")


class JourneyPatternSection:
    def __init__(self, element):
        self.section_id = element.get("id")
        timing_links: dict[str, JourneyPatternTimingLink] = {}
        for link_elem in element.findall("JourneyPatternTimingLink"):
            jptl = JourneyPatternTimingLink(link_elem)
            timing_links[jptl.link_id] = JourneyPatternTimingLink(link_elem)
        self.timing_links = timing_links


class Garage:
    def __init__(self, element):
        self.garage_code = element.findtext("GarageCode")
        self.garage_name = element.findtext("GarageName")
        location_elem = element.find("Location")
        self.location = Location(location_elem) if location_elem is not None else None


class Operator:
    def __init__(self, element):
        self.operator_id = element.get("id")
        self.national_operator_code = element.findtext("NationalOperatorCode")
        self.operator_code = element.findtext("OperatorCode")
        self.operator_short_name = element.findtext("OperatorShortName")
        self.operator_name_on_licence = element.findtext("OperatorNameOnLicence")
        self.trading_name = element.findtext("TradingName")
        self.licence_number = element.findtext("LicenceNumber")
        garages = []
        garages_elem = element.find("Garages")
        if garages_elem is not None:
            for garage_elem in garages_elem.findall("Garage"):
                garages.append(Garage(garage_elem))
        self.garages = garages


class Service:
    def __init__(self, element):
        self.creation_datetime = element.get("CreationDateTime")
        self.modification_datetime = element.get("ModificationDateTime")
        self.modification = element.get("Modification")
        self.revision_number = element.get("RevisionNumber")
        self.service_code = element.findtext("ServiceCode")
        lines: list[Line] = []
        lines_elem = element.find("Lines")
        if lines_elem is not None:
            for line_elem in lines_elem.findall("Line"):
                lines.append(Line(line_elem))
        self.lines = lines
        operating_period_elem = element.find("OperatingPeriod")
        self.operating_period = (
            OperatingPeriod(operating_period_elem)
            if operating_period_elem is not None
            else None
        )
        self.description = element.findtext("Description")
        if self.description:
            self.description = self.description.strip()
        self.ticket_machine_service_code = element.findtext("TicketMachineServiceCode")
        self.registered_operator_ref = element.findtext("RegisteredOperatorRef")
        self.public_use = element.findtext("PublicUse") == "true"

        self.origin = element.findtext("StandardService/Origin")
        if self.origin:
            self.origin = self.origin.replace("`", "'").strip()

        self.destination = element.findtext("StandardService/Destination")
        if self.destination:
            self.destination = self.destination.replace("`", "'").strip()

        vias_elem = element.find("StandardService/Vias")
        if vias_elem is not None:
            self.vias = ", ".join(via.text for via in vias_elem if via.text)
        else:
            self.vias = ""

        journey_patterns: dict[str, JourneyPattern] = {}
        for jp_elem in element.findall("StandardService/JourneyPattern"):
            jp = JourneyPattern(jp_elem)

            journey_patterns[jp.journey_pattern_id] = JourneyPattern(jp_elem)
        self.journey_patterns = journey_patterns


class Line:
    def __init__(self, element):
        self.line_id = element.get("id")
        self.line_name = element.findtext("LineName")
        outbound_elem = element.find("OutboundDescription")
        self.outbound_description = (
            DirectionDescription(outbound_elem) if outbound_elem is not None else None
        )
        inbound_elem = element.find("InboundDescription")
        self.inbound_description = (
            DirectionDescription(inbound_elem) if inbound_elem is not None else None
        )


class DirectionDescription:
    def __init__(self, element):
        self.origin = element.findtext("Origin")
        self.destination = element.findtext("Destination")
        vias = []
        vias_elem = element.find("Vias")
        if vias_elem is not None:
            for via_elem in vias_elem.findall("Via"):
                vias.append(via_elem.text)
        self.vias = vias
        self.description = element.findtext("Description")


class OperatingPeriod:
    def __init__(self, element):
        self.start_date = to_datetime(element.findtext("StartDate"))
        self.end_date = to_datetime(element.findtext("EndDate"))


class JourneyPattern:
    def __init__(self, element):
        self.journey_pattern_id = element.get("id")
        self.creation_datetime = element.get("CreationDateTime")
        self.modification_datetime = element.get("ModificationDateTime")
        self.modification = element.get("Modification")
        self.revision_number = element.get("RevisionNumber")
        self.destination_display = element.findtext("DestinationDisplay")
        self.operator_ref = element.findtext("OperatorRef")
        self.direction = element.findtext("Direction")
        self.route_ref = element.findtext("RouteRef")
        jps_refs_text = element.findtext("JourneyPatternSectionRefs")
        self.journey_pattern_section_refs: list[str] = (
            jps_refs_text.split() if jps_refs_text else []
        )


class VehicleJourney:
    def __init__(self, element):
        self.sequence_number = element.get("SequenceNumber")
        self.creation_datetime = to_datetime(element.get("CreationDateTime"))
        self.modification_datetime = to_datetime(element.get("ModificationDateTime"))
        self.modification = element.get("Modification")
        self.revision_number = element.get("RevisionNumber")
        self.private_code = element.findtext("PrivateCode")
        self.operator_ref = element.findtext("OperatorRef")
        self.journey_code = element.findtext("VehicleJourneyCode")

        ticket_machine_code = None
        block = None
        operational_elem = element.find("Operational")
        if operational_elem is not None:
            block_elem = operational_elem.find("Block")
            if block_elem is not None:
                block = block_elem.findtext("BlockNumber")
            ticket_machine_elem = operational_elem.find("TicketMachine")
            if ticket_machine_elem is not None:
                ticket_machine_code = ticket_machine_elem.findtext("JourneyCode")
        self.ticket_machine_code = ticket_machine_code
        self.block = block
        operating_profile_elem = element.find("OperatingProfile")
        self.operating_profile = (
            OperatingProfile(operating_profile_elem)
            if operating_profile_elem is not None
            else None
        )
        self.garage_ref = element.findtext("GarageRef")
        self.vehicle_journey_code = element.findtext("VehicleJourneyCode")
        self.service_ref = element.findtext("ServiceRef")
        self.line_ref = element.findtext("LineRef")
        self.journey_pattern_ref = element.findtext("JourneyPatternRef")
        self.departure_time = parse_time(element.findtext("DepartureTime"))
        timing_links: list[VehicleJourneyTimingLink] = []
        for vjtl_elem in element.findall("VehicleJourneyTimingLink"):
            timing_links.append(VehicleJourneyTimingLink(vjtl_elem))
        self.timing_links = timing_links


class VehicleJourneyTimingLink:
    def __init__(self, element):
        self.link_id = element.get("id")
        self.journey_pattern_timing_link_ref = element.findtext(
            "JourneyPatternTimingLinkRef"
        )
        self.run_time = element.findtext("RunTime")


class OperatingProfile:
    def __init__(self, element):
        regular_day_type_elem = element.find("RegularDayType")
        self.regular_day_type = (
            RegularDayType(regular_day_type_elem)
            if regular_day_type_elem is not None
            else None
        )
        bank_holiday_operation_elem = element.find("BankHolidayOperation")
        self.bank_holiday_operation = (
            BankHolidayOperation(bank_holiday_operation_elem)
            if bank_holiday_operation_elem is not None
            else None
        )
        nonoperation_days = element.findall(
            "SpecialDaysOperation/DaysOfNonOperation/DateRange"
        )
        self.non_operation_days = [DateRange(e) for e in nonoperation_days if len(e)]

        operation_days = element.findall(
            "SpecialDaysOperation/DaysOfOperation/DateRange"
        )
        self.operation_days = [DateRange(e) for e in operation_days if len(e)]
        self.hash = ET.tostring(element)


class RegularDayType:
    def __init__(self, element):
        days_of_week_elem = element.find("DaysOfWeek")
        days_of_week = []
        if days_of_week_elem is not None:
            for day_elem in days_of_week_elem:
                days_of_week.append(day_elem.tag.lower())
        self.days_of_week = days_of_week


class BankHolidayOperation:
    def __init__(self, element):
        days_of_operation_elem = element.find("DaysOfOperation")
        days_of_operation = []
        if days_of_operation_elem is not None:
            for day_elem in days_of_operation_elem:
                days_of_operation.append(day_elem.tag)
        days_of_non_operation_elem = element.find("DaysOfNonOperation")
        days_of_non_operation = []
        if days_of_non_operation_elem is not None:
            for day_elem in days_of_non_operation_elem:
                days_of_non_operation.append(day_elem.tag)
        self.days_of_operation = days_of_operation
        self.days_of_non_operation = days_of_non_operation


class TransXChange:
    def get_journeys(self, line_id, service_code=None):
        return [
            journey
            for journey in self.vehicle_journeys
            if journey.service_ref == service_code and journey.line_ref == line_id
        ]

    def __init__(
        self,
        xml_file,
    ):
        self.serviced_organisations: list[ServicedOrganisation] = []
        self.stop_points: list[StopPoint] = []
        self.route_sections: dict[str, RouteSection] = {}
        self.routes: list[Route] = []
        self.journey_pattern_sections: dict[str, JourneyPatternSection] = {}
        self.operators: list[Operator] = []
        self.services: list[Service] = []
        self.vehicle_journeys: list[VehicleJourney] = []

        iterator = ET.iterparse(xml_file)

        for _, element in iterator:
            if element.tag[:33] == "{http://www.transxchange.org.uk/}":
                element.tag = element.tag[33:]

            if element.tag == "ServicedOrganisations":
                for org_elem in element:
                    self.serviced_organisations.append(ServicedOrganisation(org_elem))
                element.clear()

            elif element.tag == "StopPoints":
                for stop_elem in element:
                    self.stop_points.append(StopPoint(stop_elem))
                element.clear()

            elif element.tag == "RouteSections":
                for section_elem in element:
                    route_section = RouteSection(section_elem)
                    self.route_sections[route_section.section_id] = route_section
                element.clear()

            elif element.tag == "Routes":
                for route_elem in element:
                    self.routes.append(Route(route_elem))
                element.clear()

            elif element.tag == "JourneyPatternSections":
                for section_elem in element:
                    jps = JourneyPatternSection(section_elem)
                    self.journey_pattern_sections[jps.section_id] = jps
                element.clear()
            elif element.tag == "Operators":
                for operator_elem in element:
                    self.operators.append(Operator(operator_elem))
                element.clear()

            elif element.tag == "Services":
                for service_elem in element:
                    self.services.append(Service(service_elem))
                element.clear()

            elif element.tag == "VehicleJourneys":
                for vj_elem in element:
                    self.vehicle_journeys.append(VehicleJourney(vj_elem))
                element.clear()


def parse_transxchange(xml_file):
    transxchange = TransXChange(xml_file)
    return transxchange


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: <path_to_transxchange_xml>")
        sys.exit(1)
    xml_file = sys.argv[1]
    # try:
    #     transxchange = parse_transxchange(xml_file)
    #     print(transxchange.operators)
    #     print(f"Parsed TransXChange data from {xml_file}")
    # except ET.ParseError as e:
    #     print(f"Failed to parse XML: {e}")
    # except Exception as e:
    #     print(f"An error occurred: {e}")

    transxchange = parse_transxchange(xml_file)
    print(len(transxchange.serviced_organisations), "serviced organisations found")
    print(len(transxchange.services), "services found")
    print(len(transxchange.routes), "routes found")
    print(len(transxchange.operators), "operators found")
    print(len(transxchange.stop_points), "stop points found")
    print(len(transxchange.vehicle_journeys), "vehicle journeys found")
    print(f"Parsed TransXChange data from {xml_file}")
