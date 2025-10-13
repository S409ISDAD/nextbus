import type { ServiceInfo } from "./ServiceInfo";

export interface BTStop {
    stop_id: string;
    name: string;
    long_name: string;
    indicator: string;
    bearing: string;
    active: boolean;
    coords: number[];
    services: ServiceInfo[];
}

export interface Stop {
    atco_code: string;
    common_name: string;
    common_short_name: string;
    indicator: string;
    bearing: string;
    active: boolean;
}