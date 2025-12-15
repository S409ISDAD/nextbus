import type { ServiceWithTimetable } from "./ServiceInfo";

export interface Line {
    id: string;
    bt_service_id: number;
    line_name: string;
    outbound_description: string;
    service_code: string;
    inbound_description: string;
    service?: Service;
}