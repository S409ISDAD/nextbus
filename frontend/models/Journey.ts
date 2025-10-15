import type { StopTime } from "./StopTime"

export interface LiveJourney {
    route_name: string;
    destination: string;
    stops: StopTime[]
}

export interface Trip extends LiveJourney {
    vehicle_journey_code: string;
    ticket_machine_code: string;
    block: string;
}
