export interface Search {
    stops: StopResult[];
    lines: LineResult[];
    services: ServiceResult[];
}

interface LineResult {
    bt_service_id: string | null;
    line_name: string;
    outbound_description: string;
    service_code: string;
    id: string;
    inbound_description: string;
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

interface ServiceResult {
    description: string;
    origin: string;
    vias: string;
    line_names: string;
    service_code: string;
    destination: string;
    operator_noc: string;
    data_source_id: string | null;
}