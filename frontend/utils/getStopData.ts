import api from "../src/api"

import type { Stop } from "../models/Stop";


const getStopData = async (stop_id: string) => {
    try {
        const response = await api.get<Stop>(
            `/stops/?stop_id=${stop_id}`
        );

        return response.data

    } catch (error) {
        console.error("failed to get stop", error);
        return null;
    }
};

export default getStopData