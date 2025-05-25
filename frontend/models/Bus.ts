import type { ServiceInfo } from "./ServiceInfo";
import type { ProgressInfo } from "./ProgressInfo";

export interface Bus {
    service: ServiceInfo;
    destination: string;
    reg: string;
    fleet_num: string;
    journey_id: number;
    delay: number;
    lateness: string;
    expected: Date;
    scheduled: Date;
    started: boolean;
    progress?: ProgressInfo;
    coords?: number[];
    timestamp?: string;
    timeto: string;
}