import asyncio
from datetime import datetime as dt, timedelta

from sqlalchemy import and_
from sqlalchemy.orm import joinedload, aliased

from backend.db.db import SessionLocal
from backend.deps import LONDON
from backend.models import Line, LineStopUsage, Journey, Stop, Locality, StopTime
from backend.schemas.stop import Stop as StopSchema
from backend.services.bus import fetch_bus_trip, build_bus
from backend.services.stops import get_nearby_stops


async def get_possible_journeys(lat: float, lon: float, locality: str, r, now: dt = None):
    if not now:
        now = dt.now(LONDON)

    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    seconds_since_midnight = now.hour * 3600 + now.minute * 60 + now.second
    current_timedelta = timedelta(seconds=seconds_since_midnight)

    lines = set()

    stops: list[StopSchema] = await get_nearby_stops(lat, lon, dist=0.01)
    stops_by_id = {s.stop_id: s for s in stops}
    closest_stop_for_line = {}
    nearby_stop_ids = [s.stop_id for s in stops]
    if not nearby_stop_ids:
        return []

    candidates = []

    with SessionLocal() as db:
        for stop in stops:
            lines_at_stop = {l[0] for l in
                             db.query(LineStopUsage.line_id).filter(LineStopUsage.stop_id == stop.stop_id).all()}
            lines.update(lines_at_stop)

        for line in lines:
            ST_curr = aliased(StopTime)
            ST_dest = aliased(StopTime)
            S_curr = aliased(Stop)
            S_dest = aliased(Stop)

            stops_query = (
                db.query(
                    Journey,
                    S_curr.atco_code,
                ).select_from(ST_curr)
                .distinct(ST_curr.journey_id)
                .join(S_curr, S_curr.atco_code == ST_curr.stop_id)
                .join(Journey, Journey.id == ST_curr.journey_id)
                .join(ST_dest, and_(
                    ST_dest.journey_id == ST_curr.journey_id,
                    ST_dest.stop_sequence > ST_curr.stop_sequence
                ))
                .join(S_dest, S_dest.atco_code == ST_dest.stop_id)
                .filter(
                    Journey.line_id == line,
                    ST_curr.stop_id.in_(nearby_stop_ids),
                    ST_curr.departure_time >= current_timedelta,
                    S_dest.locality_id == locality,
                )
            ).all()

            valid_stops = [
                s for s in stops_query if s.Journey.is_valid(date=now.date())
            ]

            for journey, atco_code in valid_stops:
                if not closest_stop_for_line.get(line):
                    closest_stop_for_line[line] = atco_code
                else:
                    old_closest = stops_by_id[closest_stop_for_line[line]]
                    closest_stop_for_line[
                        line] = atco_code if stops_by_id[atco_code].dist < old_closest.dist else old_closest.stop_id

        for line, closest_stop in closest_stop_for_line.items():
            ST_curr = aliased(StopTime)
            ST_dest = aliased(StopTime)
            S_curr = aliased(Stop)
            S_dest = aliased(Stop)

            journeys = (db.query(
                Journey,
                ST_curr,
                ST_dest,
                S_curr,
                S_dest
            ).select_from(ST_curr).join(Journey, Journey.id == ST_curr.journey_id)
            .distinct(ST_curr.journey_id)
            .join(Line, Journey.line_id == Line.id)
            .join(S_curr, S_curr.atco_code == ST_curr.stop_id)
            .join(ST_dest, and_(
                ST_dest.journey_id == ST_curr.journey_id,
                ST_dest.stop_sequence > ST_curr.stop_sequence,
            ))
            .join(S_dest, S_dest.atco_code == ST_dest.stop_id)
            .filter(
                Journey.line_id == line,
                ST_curr.stop_id == closest_stop,
                ST_curr.departure_time >= current_timedelta,
                S_dest.locality_id == locality,
            )
            .options(
                joinedload(Journey.line)
                .joinedload(Line.service),
                joinedload(Journey.destination)
                .joinedload(Stop.locality),
                joinedload(ST_curr.journey)

            )).all()

            valid_journeys = [
                j for j in journeys if j.Journey.is_valid(date=now.date())
            ]

            if valid_journeys:
                print(f"Found {len(valid_journeys)} valid journeys for line {line}")

                for journey, st_curr, st_dest, s_curr, s_dest in valid_journeys:
                    wait = (st_curr.departure_time - current_timedelta).total_seconds()
                    in_vehicle = (st_dest.arrival_time - st_curr.departure_time).total_seconds()
                    if wait < 0 or in_vehicle <= 0:
                        continue

                    trip_id = await journey.get_bt_trip_id(db)
                    service_id = await journey.line.get_bt_service_id(db)
                    trip_bus = await fetch_bus_trip(service_id, trip_id, r)
                    live_bus = None

                    if trip_bus:
                        live_bus = await build_bus(trip_bus["id"], r, s_curr.atco_code, journey.id)

                    if live_bus:
                        print(live_bus.reg)
                        wait += live_bus.delay
                    headsign = st_curr.headsign

                    departure = midnight + st_curr.departure_time
                    arrival = midnight + st_dest.arrival_time

                    stop_dist = stops_by_id[s_curr.atco_code].dist

                    walk_time = stop_dist * 1.1  # 1.1m/s

                    wait_time = wait - walk_time

                    total = walk_time + wait_time + in_vehicle

                    if wait_time < 0:
                        print("cant walk there in time")
                        continue

                    candidates.append({
                        "journey_id": journey.id,
                        "trip_id": trip_id,
                        "line_id": line,
                        "line_name": journey.line.line_name,
                        "origin_stop_id": s_curr.atco_code,
                        "origin_stop_name": s_curr.common_name,
                        "dest_stop_id": s_dest.atco_code,
                        "dest_stop_name": s_dest.common_name,
                        "headsign": headsign,
                        "departure": departure,
                        "arrival": arrival,
                        "walk_seconds": int(walk_time),
                        "wait_seconds": int(wait_time),
                        "in_vehicle_seconds": int(in_vehicle),
                        "total_seconds": int(total),
                        "live_bus": live_bus,
                    })

        results = sorted(candidates, key=lambda x: (x["walk_seconds"], x["total_seconds"]))[:3]

        return results


async def possible_destinations(lat: float, lon: float, time: dt = None):
    if not time:
        time = dt.now(LONDON)

    seconds_since_midnight = time.hour * 3600 + time.minute * 60 + time.second
    current_timedelta = timedelta(seconds=seconds_since_midnight)

    stops: list[StopSchema] = await get_nearby_stops(lat, lon, dist=0.01)

    lines = set()
    localities = set()

    with SessionLocal() as db:
        for stop in stops:
            lines_at_stop = {l[0] for l in
                             db.query(LineStopUsage.line_id).filter(LineStopUsage.stop_id == stop.stop_id).all()}
            lines.update(lines_at_stop)

        for line in lines:
            line_obj: Line = db.query(Line).filter(Line.id == line).options(
                joinedload(Line.journeys)
                .joinedload(Journey.destination)
                .joinedload(Stop.locality)
            ).first()

            journeys = [journey for journey in line_obj.journeys if
                        journey.is_valid(time.date()) and journey.end_time > current_timedelta]

            for journey in journeys:
                localities.add(journey.destination.locality.id)

        data = []

        for locality in localities:
            db_locality = db.query(Locality).filter(Locality.id == locality).first()

            data.append({"id": locality, "name": db_locality.name})

        return data


if __name__ == "__main__":
    asyncio.run(get_possible_journeys(51.08997, -1.16541, "E0055970", dt.fromisoformat("2025-09-19T10:17:00+01:00")))
