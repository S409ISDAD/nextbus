import type { ServiceInfo } from "./ServiceInfo";
import type { Times } from "./Times";
import type { ProgressInfo } from "./ProgressInfo";

export interface Bus {
    service: ServiceInfo;
    destination: string;
    reg: string;
    fleet_num: string;
    journey_id: number;
    delay: number;
    lateness: string;
    expected: string;
    scheduled: string;
    times?: Times; // If it's used elsewhere in other cases
    progress?: ProgressInfo;
    coords?: number[];
    timestamp?: string;
}