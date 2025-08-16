
import type { Stats, StatsTimeSeries } from "../models/Stats";
import api from "../src/api"

export const timespans = [
    { label: "Last hour", value: "1h", ms: 60 * 60 * 1000 },
    { label: "Last 6 hours", value: "6h", ms: 6 * 60 * 60 * 1000 },
    { label: "Last 12 hours", value: "12h", ms: 12 * 60 * 60 * 1000 },
    { label: "Last 24 hours", value: "24h", ms: 24 * 60 * 60 * 1000 },
    { label: "Last 3 days", value: "3d", ms: 3 * 24 * 60 * 60 * 1000 },
    { label: "Last 7 days", value: "7d", ms: 7 * 24 * 60 * 60 * 1000 },
];

const getStats = async (selectedTimespan: typeof timespans[number]) => {
    try {
        const now = new Date();
        const start = new Date(now.getTime() - selectedTimespan.ms);

        const response = await api.get<Stats>(
            `/stats/`
        );

        const stats = response.data;

        const timeseriesResponse = await api.get<StatsTimeSeries[]>(
            `/stats/timeseries?start=${start.toISOString()}&end=${now.toISOString()}`
        );
        const timeseries = timeseriesResponse.data;

        return { stats: stats, timeseries: timeseries };

    } catch (error) {
        console.error("failed to get stats", error);
        return null;
    }
};

export default getStats