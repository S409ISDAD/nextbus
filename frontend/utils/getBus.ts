
import type { TrackedBus } from "../models/Bus";
import api from "../src/api"

const getBus = async (bus_id: string) => {
    try {
        const response = await api.get<TrackedBus>(
            `/buses/?bus_id=${bus_id}`
        );

        const bus = response.data;

        return bus;

    } catch (error) {
        console.error("failed to get bus", error);
        return null;
    }
};

export default getBus