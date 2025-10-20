import type { Operator } from "./Operator";

export interface ServiceInfo {
    id: number;
    line_name: string;
    detail?: string;
}


export interface Service {
    id: number;
    service_code?: string;
    description?: string;
    vias?: string;
    line_name: string;
    line_brand?: string;
    last_modified?: string;
    operators?: Operator[];
    _user_distance?: number; // in meters, optional
}