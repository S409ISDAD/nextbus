import api from "../src/api"

import type { ServiceInfo } from "../models/ServiceInfo";

interface StopResponse {
    name: string;
    long_name: string;
    active: boolean;
    services: ServiceInfo[];
}

const getStopData = async (stop_id: string) => {
    try {
        const response = await api.get<StopResponse>(
            `/stops/?stop_id=${stop_id}`
        );

        const stop_name = response.data.name
        const long_name = response.data.long_name
        const active = response.data.active
        const services = response.data.services

        return { stop_name, long_name, active, services }

    } catch (error) {
        console.error("failed to get stop", error);
        return null;
    }
};

export default getStopData