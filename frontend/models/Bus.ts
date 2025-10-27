import type { ServiceInfo } from "./ServiceInfo";
import type { ProgressInfo } from "./ProgressInfo";
import type { LiveJourney } from "./Journey";
import type { Livery } from "./Livery";


export interface VehicleType {
    id: number;
    name: string;
    style?: string;
    fuel: string;
    double_decker: boolean;
    coach: boolean;
    electric: boolean;
}

export interface Vehicle {
    id: number;
    reg: string;
    fleet_num: string;
    vehicle_type?: VehicleType;
    livery?: Livery;
    name?: string;
    special_features?: string[];
}

export interface ScheduledBus {
    type: string;
    line: string;
    destination: string;
    expected: string;
    scheduled: string;
    timeTo: string;
    started: boolean;
    trip: number | null;
    db_journey: number | null;
    status: string;
}

export interface Bus {
    type: string;
    id: number;
    trip: number | null;
    db_journey: number | null;
    timestamp: string;
    service: ServiceInfo;
    destination: string;
    bus_type: string;
    vehicle: Vehicle;
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
    journey: LiveJourney
    confidence: Confidence;
    timeTo: string;
    status: string;
}

export interface Prediction {
    timestamp: string;
    sequence: number;
    progress: number;
    location: number[];
}

export interface Confidence {
    final_confidence: number;
    broken_down_confidence: number;
    log_off_confidence: number;
    diversion_confidence: number;
    broken_tracking_confidence: number;
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
    vehicle: MapVehicle;
    livery?: Livery;
}

interface MapVehicle {
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
