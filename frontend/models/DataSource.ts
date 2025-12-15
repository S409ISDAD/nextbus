import { type ServiceWithTimetable } from "./ServiceInfo";
import { type DBTimetable } from "./Timetable";

export interface DataSourceVersion {
    id: number;
    name: string;
    start_date?: string;
    end_date?: string;
    url?: string;
    bods_id?: number;
    last_modified?: string;
    timetable_count: number;
}

export interface DataSource {
    id: number;
    name: string;
    description?: string;
    url?: string;
    service_count: number;
    timetable_count: number;
    versions?: DataSourceVersion[];
}

export interface DetailedDataSource extends DataSource {
    services: {
        [service_code: string]: {
            [line_name: string]: {
                service: ServiceWithTimetable;
                timetables: DBTimetable[];
            };
        };
    };
}