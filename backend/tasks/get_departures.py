from backend.services import bus, stops
from backend.db.db import SessionLocal
from backend.models import Line, Stop
from backend.utils.match_bt import match_journey_trip


async def get_departures(stop_id: str, redis):
    services = await stops.get_services_from_stop(stop_id, redis)

    service_ids = [service.get("id") for service in services]

    line_names = [service.get("line_name") for service in services]

    with SessionLocal() as db:
        stop = db.query(Stop).filter(Stop.atco_code == stop_id).first()
        use_db_method = False

        if stop:
            db_lines = Stop.lines_served(stop, db)
            db_line_names = [line.line_name for line in db_lines]
            if set(line_names).issubset(set(db_line_names)):
                use_db_method = True

        if use_db_method:
            print("Using DB method for departures")
            db_times = stop.times_from_stop(db)
            times = []
            for time in db_times:
                journey = time.journey
                trip_id = await match_journey_trip(db, journey.id, redis)
                if trip_id:
                    times.append({"trip_id": int(trip_id)})
        else:
            print("Not all data in db, using old method")
            times = await stops.get_times(stop_id, redis)

    buses = await bus.fetch_buses(
        service_ids, stop_id, times, redis, use_db=use_db_method
    )

    return buses
