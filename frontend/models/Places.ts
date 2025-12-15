import type { ServiceWithTimetable } from "./ServiceInfo";
import type { Stop } from "./Stop";

export interface Locality {
    id: string;
    name: string;
    qualifier?: string;
    full_name?: string;
}

export interface LocalityDetails extends Locality {
    services: ServiceWithTimetable[];
    stops: Stop[];
}

export interface District {
    id: string;
    name: string;
}

export interface DistrictDetails extends District {
    localities: Locality[];
}

export interface AdminArea {
    id: string;
    name: string;
}

export interface AdminAreaDetails extends AdminArea {
    districts: District[];
}

export interface Region {
    id: string;
    name: string;
}

export interface RegionDetails extends Region {
    admin_areas: AdminAreaDetails[];
}