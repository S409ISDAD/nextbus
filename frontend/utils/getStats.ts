
import type { Stats, DBStats } from "../models/Stats";
import api from "../src/api"

export const getDBStats = async () => {
    try {
        const response = await api.get<DBStats>(
            `/stats/db`
        );

        const dbStats = response.data;

        return { dbStats: dbStats, };

    } catch (error) {
        console.error("failed to get db stats", error);
        return null;
    }
};

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