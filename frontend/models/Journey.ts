import type { StopTime } from "./StopTime"

export interface Location {
    coords: number[];
    direction: number;
    timestamp: string;
}

export interface BaseJourney {
    route_name: string;
    destination: string;
    service_id: number;
    stops: StopTime[];
}

export interface Journey extends BaseJourney {
    // Simple journey
}

export interface Trip extends BaseJourney {
    vehicle_journey_code: string;
    ticket_machine_code: string;
    block?: string;
}

export interface LiveJourney extends BaseJourney {
    vehicle_id: number;
    trip_id: number;
    start_time: string;
    current: boolean;
    locations: Location[];
}
