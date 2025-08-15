
import type { Stats } from "../models/Stats";
import api from "../src/api"

const getStats = async () => {
    try {
        const response = await api.get<Stats>(
            `/stats/`
        );

        const stats = response.data;

        return stats;

    } catch (error) {
        console.error("failed to get stats", error);
        return null;
    }
};

export default getStats