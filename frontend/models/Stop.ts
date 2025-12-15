import type { ServiceInfo } from "./ServiceInfo";

export interface Stop {
    stop_id?: string;
    atco_code?: string;
    name: string;
    long_name: string;
    indicator?: string;
    bearing?: number | string;
    active: boolean;
    coords: number[];
    services?: ServiceInfo[];
    dist?: number;
}