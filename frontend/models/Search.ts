export interface Search {
    operators: OperatorResult[];
    localities: LocalityResult[];
    services: ServiceResult[];
}

export interface OperatorResult {
    noc: string;
    name: string;
}

export interface ServiceResult {
    service_id: number;
    line_name: string;
    inbound_description: string;
    outbound_description: string;
    geometry: any | null;
    bt_service_id: string;
    service_code: string;
    description: string | null;
    origin: string | null;
    destination: string | null;
    vias: string | null;
    operator_noc: string | null;
    operator: string | null;
    line_names: string;
    last_modified?: string;
}

interface LocalityResult {
    id: string;
    name: string;
    full_name: string;
    qualifier_name: string;
    admin_area_id: number;
    district_id: number;
    parent_id: string | null;
    lat: number;
    lon: number;
    created_at: string;
    modified_at: string;
}