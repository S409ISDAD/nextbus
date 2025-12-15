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

export interface BaseBus {
    destination: string;
    scheduled: string;
    expected: string;
    started: boolean;
    trip?: number | null;
    db_journey?: number | null;
    status: string;
    source: string;
}

export interface ScheduledBus extends BaseBus {
    type: "scheduled";
    line: string;
    timeTo?: string; // calculated field
}

export interface TrackedBus extends BaseBus {
    type: "tracked";
    id: number;
    timestamp: string;
    service: ServiceInfo;
    vehicle: Vehicle;
    bus_type: string;
    journey_id: number;
    delay: number;
    min_expected?: string;
    max_expected?: string;
    finished: boolean;
    target_seq?: number;
    speed?: number;
    progress: ProgressInfo;
    predictions: Prediction[];
    journey?: LiveJourney;
    confidence: Confidence;
    coords: number[];
    heading: number;
    timeTo?: string; // Calculated on frontend
}

export interface Prediction {
    timestamp: string;
    sequence: number;
    progress: number;
    location: number[];
    heading: number;
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
    livery_id?: number;
}

export interface MapVehicle {
    name: string;
    features: string;
    livery: string;
}

interface MapService {
    line_name: string;
}

export function isTrackedBus(bus: Departure): bus is TrackedBus {
    return bus.type === "tracked";
}

export function getKey(bus: Departure): string {
    const scheduled = new Date(bus.scheduled);
    scheduled.setSeconds(0, 0); // ignore seconds for key
    if (isTrackedBus(bus)) {
        return `${scheduled.toISOString()}-${bus.service.line_name}`;
    } else {
        return `${scheduled.toISOString()}-${bus.line}`;
    }
}

export type Departure = TrackedBus | ScheduledBus;
