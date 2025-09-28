import type { Operator } from "./Operator";

export interface ServiceInfo {
    id: number;
    line_name: string;
    detail?: string;
}


export interface Service {
    id: number;
    description: string;
    vias?: string;
    line_name: string;
    line_brand?: string;
    operator?: Operator;
}