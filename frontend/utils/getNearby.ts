import api from "../src/api"

import type { ServiceInfo } from "../models/ServiceInfo";

const getNearby = async (position: number[]) => {
    try {
        const lat = position[0]
        const lng = position[1]

        const response = await api.get<ServiceInfo[]>(
            `/location/nearby?lat=${lat}&lng=${lng}&dist=0.01`
        );

        return response.data.map(service => ({
            id: service.id,
            line_name: service.line_name,
            detail: service.detail

        }));

    } catch (error) {
        console.error("failed to get stop", error);
        return null;
    }
};

export default getNearby