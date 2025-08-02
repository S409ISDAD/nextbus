
import type { Bus } from "../models/Bus";
import api from "../src/api"

const getBus = async (bus_id: string) => {
    try {
        const response = await api.get<Bus>(
            `/buses/?bus_id=${bus_id}`
        );

        const bus = response.data;

        return {
            ...bus,
            timeTo: ""
        };

    } catch (error) {
        console.error("failed to get bus", error);
        return null;
    }
};

export default getBus