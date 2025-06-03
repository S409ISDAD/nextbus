import type { ServiceInfo } from "./ServiceInfo";

export interface Stop {
    stop_id: string;
    stop_name: string;
    long_name: string;
    indicator: string;
    bearing: string;
    active: boolean;
    coords: number[];
    services: ServiceInfo[];
}