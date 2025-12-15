import type { TrackedBus } from "./Bus.ts";

export interface PossibleJourney {
    journey_id: string;
    trip_id: number;
    line_id: string;
    line_name: string;
    origin_stop_id: string;
    origin_stop_name: string;
    dest_stop_id: string;
    dest_stop_name: string;
    headsign: string;
    departure: string;
    arrival: string;
    walk_seconds: number;
    wait_seconds: number;
    in_vehicle_seconds: number;
    total_seconds: number;
    live_bus: TrackedBus | null;
}