import React, { useEffect, useState } from "react";
import getStats from "../utils/getStats";
import type { Stats, StatsTimeSeries } from "../models/Stats";
import { Line } from "react-chartjs-2";
import {
    Chart as ChartJS,
    LineElement,
    PointElement,
    LinearScale,
    CategoryScale,
    Tooltip as ChartTooltip,
    Legend,
    Title,
} from "chart.js";

ChartJS.register(
    LineElement,
    PointElement,
    LinearScale,
    CategoryScale,
    ChartTooltip,
    Legend,
    Title
);

const StatsPage: React.FC = () => {
    const [stats, setStats] = useState<Stats>();
    const [loading, setLoading] = useState(true);
    const [lastRefreshed, setRefreshed] = useState(new Date());
    const [elapsed, setElapsed] = useState<string>("0s");
    const [statsTimeseries, setStatsTimeseries] = useState<StatsTimeSeries[]>(
        []
    );

    useEffect(() => {
        const interval = setInterval(() => {
            const now = new Date();
            const diffSec = Math.floor(
                (now.getTime() - lastRefreshed.getTime()) / 1000
            );
            const min = Math.floor(diffSec / 60);
            const sec = diffSec % 60;
            setElapsed(min > 0 ? `${min}m ${sec}s` : `${sec}s`);
        }, 1000);
        return () => clearInterval(interval);
    }, [lastRefreshed]);

    useEffect(() => {
        document.title = "stats | nextbus";
    }, []);

    useEffect(() => {
        let interval: any;
        const fetchStats = async () => {
            setLoading(true);
            try {
                const stats = await getStats();
                if (stats) {
                    setStats(stats.stats);
                    setStatsTimeseries(stats.timeseries);
                    setRefreshed(new Date());
                }
            } catch {
                console.log("uh oh");
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
        interval = setInterval(fetchStats, 10000);
        return () => {
            clearInterval(interval);
        };
    }, []);

    const chartData = React.useMemo(
        () => ({
            labels: statsTimeseries.map((d) =>
                new Date(d.timestamp).toLocaleTimeString()
            ),
            datasets: [
                {
                    label: "Total Connections",
                    data: statsTimeseries.map((d) => d.total),
                    borderColor: "#8884d8",
                    backgroundColor: "rgba(136,132,216,0.1)",
                    fill: false,
                    tension: 0.4,
                },
                {
                    label: "Unique Users",
                    data: statsTimeseries.map((d) => d.unique),
                    borderColor: "#82ca9d",
                    backgroundColor: "rgba(130,202,157,0.1)",
                    fill: false,
                    tension: 0.4,
                },
            ],
        }),
        [statsTimeseries]
    );

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: { display: true },
            tooltip: { enabled: true },
            title: { display: false },
        },
        maintainAspectRatio: false,
        scales: {
            x: { title: { display: true, text: "Time" } },
            y: { title: { display: true, text: "Count" }, beginAtZero: true },
        },
        elements: {
            point: { radius: 0 },
        },
    };

    return (
        <div className="flex items-center justify-center w-full h-full">
            <div className="flex flex-col items-center justify-center w-full md:w-[80vw] gap-2 pt-0 p-3 h-fit">
                <div className="flex flex-row items-center gap-1 mb-10">
                    <span className="text-5xl font-black text-center pt-7">
                        nextbus
                    </span>
                    <span className="text-xl font-bold h-fit text-sky-500">
                        stats
                    </span>
                </div>
                <div className="flex justify-center gap-2">
                    <span className="text-xs text-neutral-400">
                        {loading ? "Loading..." : `Updated ${elapsed} ago`}
                    </span>
                    <span className="text-xs text-neutral-400">·</span>
                    <span className="text-xs text-neutral-400">
                        Updates every 10s
                    </span>
                </div>
                <div className="text-lg font-semibold">
                    Total Active Connections:{" "}
                    {loading ? "-" : stats?.total_active}
                </div>
                <div className="text-lg font-semibold">
                    Active Users: {loading ? "-" : stats?.unique_active}
                </div>
                <div className="flex items-center w-full min-h-[300px]">
                    <Line data={chartData} options={chartOptions} />
                </div>
            </div>
        </div>
    );
};

export default StatsPage;
