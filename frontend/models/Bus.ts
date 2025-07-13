import type { ServiceInfo } from "./ServiceInfo";
import type { ProgressInfo } from "./ProgressInfo";
import type { Journey } from "./Journey";
import type { Livery } from "./Livery";

export interface ScheduledBus {
    type: string;
    line: string;
    destination: string;
    expected: Date;
    scheduled: Date;
    timeto: string;
    started: boolean;
    trip: number;
    status: string;
}

export interface Bus {
    type: string;
    id: number;
    trip: number;
    timestamp: Date;
    service: ServiceInfo;
    destination: string;
    reg: string;
    bus_type: string;
    fleet_num: string;
    journey_id: number;
    delay: number;
    expected: Date;
    scheduled: Date;
    started: boolean;
    finished: boolean;
    progress?: ProgressInfo;
    coords?: number[];
    predictions: Prediction[];
    livery?: Livery
    journey: Journey
    timeto: string;
    status: string;
}

export interface Prediction {
    timestamp: number;
    sequence: number;
    progress: number;
    location: number[];
}

export function isTrackedBus(bus: Departure): bus is Bus {
    return bus.type === "tracked";
}

export type Departure = Bus | ScheduledBus;
