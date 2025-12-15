export interface TimetableService {
    id: number;
    line_name: string;
    inbound: boolean;
}

export interface TimetableStop {
    id: string;
    name: string;
    timing_status: string;
}

export interface TimetableJourney {
    id: number;
    start_time: string;
    times: (string | null)[];
}

export interface TimetableResponse {
    service: TimetableService;
    stops: TimetableStop[];
    journeys: TimetableJourney[];
}

export interface DBTimetable {
    id: number;
    service_code: string;
    line_id: string;
    line_name: string;
    line_brand: string | null;
    service_id: number;
    bt_service_id: number | null;
    revision_number: number;
    description: string;
    outbound_description: string;
    inbound_description: string;
    origin: string;
    destination: string;
    vias: string | null;
    public_use: boolean;
    data_source_id: number;
    created_at: string;
    modified_at: string;
    start_date: string;
    end_date: string;
    journey_count?: number;
}