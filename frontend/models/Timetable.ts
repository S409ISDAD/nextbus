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