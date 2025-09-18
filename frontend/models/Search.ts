export interface Search {
    localities: LocalityResult[];
    lines: LineResult[];
}

export interface LineResult {
    line_id: string;
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
    line_names: string;
}

interface LocalityResult {
    id: string;
    name: string;
    qualifier_name: string;
    admin_area_id: number;
    district_id: number;
    parent_id: string | null;
    lat: number;
    lon: number;
    created_at: string;
    modified_at: string;
}