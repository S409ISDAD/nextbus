export interface Timetable {
    stops: TimetableStop[];
    journeys: TimetableJourney[];
}

interface TimetableStop {
    id: number;
    name: string;
    timing_status: "PTP" | "TIP" | "OTH";
}
interface TimetableJourney {
    id: number;
    start_time: string;
    times: string | null[];
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
    operator_id: number;
    data_source_id: number;
    created_at: string;
    modified_at: string;
    start_date: string;
    end_date: string;
    journey_count?: number;
}