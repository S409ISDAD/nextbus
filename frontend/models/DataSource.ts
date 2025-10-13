import type { Service } from "./ServiceInfo";
import type { DBTimetable } from "./Timetable";

export interface DataSource {
    id: number;
    name: string;
    description: string | null;
    url: string | null;
    bods_id: string | null;
    modified_at: string | null;
}

export interface SimpleDataSource extends DataSource {
    service_count: number;
    timetable_count: number;
}

export interface DetailedDataSource extends DataSource {
    services: {
        [service_code: string]: {
            [line_name: string]: {
                service: Service;
                timetables: DBTimetable[];
            };
        };
    };
}