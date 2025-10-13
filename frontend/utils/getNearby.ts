import api from "../src/api"

import type { Service } from "../models/ServiceInfo";

const getNearby = async (position: number[]) => {
    try {
        const lat = position[0]
        const lon = position[1]

        const response = await api.post<Service[]>(
            `/location/nearby?dist=200`, // 200 meters
            {
                lat: lat,
                lon: lon,
            }
        );

        return response.data;

    } catch (error) {
        console.error("failed to get nearby services", error);
        return null;
    }
};

export default getNearby