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
    progress?: ProgressInfo;
    coords?: number[];
    timeto: string;
}