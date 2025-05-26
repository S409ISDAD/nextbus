import type { ServiceInfo } from "./ServiceInfo";

export interface Stop {
    stop_name: string;
    long_name: string;
    active: boolean;
    services: ServiceInfo[];
}