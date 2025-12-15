import type { Operator } from "./Operator";

export interface ServiceInfo {
    id: number;
    line_name: string;
    description: string;
    detail?: string;
}

export interface ServiceWithTimetable {
    id: number;
    line_name: string;
    inbound_description?: string;
    outbound_description?: string;
    geometry?: string;
    bt_service_id?: number;
    service_code: string;
    description: string;
    origin?: string;
    destination?: string;
    vias?: string;
    operators: Operator[];
    last_modified?: string;
    rank?: number;
}