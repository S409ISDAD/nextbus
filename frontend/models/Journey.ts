import type { StopTime } from "./StopTime"

export interface Journey {
    route_name: string;
    destination: string;
    stops: StopTime[]
}