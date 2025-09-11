export interface Search {
    stops: StopResult[];
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

interface StopResult {
    atco_code: string;
    bus_stop_type: string;
    common_name: string;
    lat: number;
    lon: number;
    common_short_name: string | null;
    active: boolean;
    landmark: string;
    suburb: string | null;
    street: string;
    town: string | null;
    crossing: string | null;
    heading: string | null;
    indicator: string;
    bearing: string | null;
    naptan_code: string;
    stop_type: string;
}