import type { Operator } from "./Operator";

export interface ServiceInfo {
    id: number;
    line_name: string;
    detail?: string;
}


export interface Service {
    description: string;
    origin: string;
    vias: string;
    line_names: string;
    service_code: string;
    destination: string;
    operator_noc: string;
    operator?: Operator;
}