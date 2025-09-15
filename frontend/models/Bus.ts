import type { ServiceInfo } from "./ServiceInfo";
import type { ProgressInfo } from "./ProgressInfo";
import type { Journey } from "./Journey";
import type { Livery } from "./Livery";

export interface ScheduledBus {
    type: string;
    line: string;
    destination: string;
    expected: string;
    scheduled: string;
    timeTo: string;
    started: boolean;
    trip: number;
    status: string;
}

export interface Bus {
    type: string;
    id: number;
    trip: number;
    timestamp: string;
    service: ServiceInfo;
    destination: string;
    reg: string;
    bus_type: string;
    fleet_num: string;
    journey_id: number;
    delay: number;
    expected: string;
    min_expected?: string;
    max_expected?: string;
    scheduled: string;
    started: boolean;
    finished: boolean;
    target_seq?: number;
    progress?: ProgressInfo;
    coords?: number[];
    predictions: Prediction[];
    livery?: Livery
    journey: Journey
    timeTo: string;
    status: string;
}

export interface Prediction {
    timestamp: string;
    sequence: number;
    progress: number;
    location: number[];
}

export interface MapBus {
    id: number;
    coords: number[];
    heading: number;
    updated: Date;
    destination: string;
    trip_id: number;
    service_id: string;
    service: MapService;
    vehicle: Vehicle;
    livery?: Livery;
}

interface Vehicle {
    name: string;
    features: string;
    livery: string;
}

interface MapService {
    line_name: string;
}

export function isTrackedBus(bus: Departure): bus is Bus {
    return bus.type === "tracked";
}

export type Departure = Bus | ScheduledBus;
