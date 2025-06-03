import api from "../src/api"

import type { ServiceInfo } from "../models/ServiceInfo";


interface StopResponse {
    stop_id: string;
    name: string;
    long_name: string;
    indicator: string;
    bearing: string;
    active: boolean;
    coords: number[];
    services: ServiceInfo[];
}

const getStopData = async (stop_id: string) => {
    try {
        const response = await api.get<StopResponse>(
            `/stops/?stop_id=${stop_id}`
        );

        const stop_name = response.data.name
        const long_name = response.data.long_name
        const indicator = response.data.indicator
        const bearing = response.data.bearing
        const active = response.data.active
        const coords = response.data.coords
        const services = response.data.services

        return { stop_id, stop_name, long_name, indicator, bearing, active, coords, services }

    } catch (error) {
        console.error("failed to get stop", error);
        return null;
    }
};

export default getStopData