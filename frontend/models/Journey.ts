import type { StopTime } from "./StopTime"

export interface LiveJourney {
    route_name: string;
    destination: string;
    stops: StopTime[]
}