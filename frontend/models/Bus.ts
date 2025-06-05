import type { ServiceInfo } from "./ServiceInfo";
import type { ProgressInfo } from "./ProgressInfo";

export interface Bus {
    id: number;
    service: ServiceInfo;
    destination: string;
    reg: string;
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
    timeto: string;
}

export interface Prediction {
    timestamp: number;
    sequence: number;
    progress: number;
    location: number[];
}
