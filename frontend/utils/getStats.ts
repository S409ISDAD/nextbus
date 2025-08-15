
import type { Stats, StatsTimeSeries } from "../models/Stats";
import api from "../src/api"

const getStats = async () => {
    try {
        const response = await api.get<Stats>(
            `/stats/`
        );

        const stats = response.data;

        const timeseriesResponse = await api.get<StatsTimeSeries[]>(
            `/stats/timeseries`
        );
        const timeseries = timeseriesResponse.data;

        return { stats: stats, timeseries: timeseries };

    } catch (error) {
        console.error("failed to get stats", error);
        return null;
    }
};

export default getStats