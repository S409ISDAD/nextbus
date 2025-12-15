import { type Locality } from "./Places";
import { type ServiceWithTimetable } from "./ServiceInfo";
import { type Stop } from "./Stop";

export interface SearchOperator {
    id: number;
    noc: string;
    name: string;
}

export interface SearchResponse {
    operators: SearchOperator[];
    localities: Locality[];
    services: ServiceWithTimetable[];
    stops: Stop[];
}