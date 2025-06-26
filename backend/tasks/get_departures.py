from backend.services import bus, stops


async def get_departures(stop_id: str, redis):
    services = await stops.get_services_from_stop(stop_id, redis)

    service_ids = [service.get("id") for service in services]

    times = await stops.get_times(stop_id, redis)

    buses = await bus.fetch_buses(service_ids, stop_id, times, redis)

    return buses
