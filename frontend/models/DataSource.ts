import type { Service } from "./ServiceInfo";
import type { DBTimetable } from "./Timetable";

export interface DataSource {
    id: number;
    name: string;
    description: string | null;
}

export interface DataSourceVersion {
    id: number;
    name: string;
    data_source_id: number;
    start_date: string;
    end_date: string | null;
    url: string | null;
    bods_id: string | null;
    imported_at: string;
    last_modified: string | null;
}

export interface SimpleDataSource extends DataSource {
    service_count: number;
    timetable_count: number;
    versions: DataSourceVersion[];
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