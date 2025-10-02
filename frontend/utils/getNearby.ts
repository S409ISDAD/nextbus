import api from "../src/api"

import type { Service } from "../models/ServiceInfo";

const getNearby = async (position: number[]) => {
    try {
        const lat = position[0]
        const lng = position[1]

        const response = await api.get<Service[]>(
            `/location/nearby?lat=${lat}&lng=${lng}&dist=200` // 200 meters
        );

        return response.data;

    } catch (error) {
        console.error("failed to get nearby services", error);
        return null;
    }
};

export default getNearby