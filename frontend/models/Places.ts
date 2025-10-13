import type { Service } from "./ServiceInfo";
import type { Stop } from "./Stop";

export interface Locality {
    id: string;
    name: string;
    qualifier?: string;
    slug?: string;
    services: Service[];
    stops: Stop[];
}

export interface AdminArea {
    id: string;
    name: string;
    districts?: District[];
}

export interface Region {
    id: string;
    name: string;
    admin_areas?: AdminArea[];
}

export interface District {
    id: string;
    name: string;
    localities?: Locality[];
}