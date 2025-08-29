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
import {
    Listbox,
    ListboxButton,
    ListboxOption,
    ListboxOptions,
} from "@headlessui/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCaretDown } from "@fortawesome/free-solid-svg-icons";
import { timespans } from "../utils/getStats";

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
    const [selectedTimespan, setSelectedTimespan] = useState<{
        label: string;
        value: string;
        ms: number;
    }>({
        label: "Last hour",
        value: "1h",
        ms: 60 * 60 * 1000,
    });

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
                const stats = await getStats(selectedTimespan);
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
    }, [selectedTimespan]);

    const chartData = React.useMemo(() => {
        const isSameDay =
            statsTimeseries.length > 0 &&
            new Date(statsTimeseries[0].timestamp).toDateString() ===
                new Date(
                    statsTimeseries[statsTimeseries.length - 1].timestamp
                ).toDateString();

        const labels = statsTimeseries.map((d) => {
            const date = new Date(d.timestamp);
            if (isSameDay) {
                // Show only time if all data is from the same day
                return date.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                });
            } else if (
                selectedTimespan.value === "7d" ||
                selectedTimespan.ms >= 24 * 60 * 60 * 1000
            ) {
                // Show date (and maybe time) for longer ranges
                return (
                    date.toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                    }) +
                    " " +
                    date.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                    })
                );
            } else {
                // Fallback: show both date and time
                return date.toLocaleString([], {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                });
            }
        });

        return {
            labels,
            datasets: [
                {
                    label: "Unique Users",
                    data: statsTimeseries.map((d) => d.unique),
                    borderColor: "#82ca9d",
                    backgroundColor: "rgba(130,202,157,0.1)",
                    fill: false,
                    tension: 0.4,
                },
            ],
        };
    }, [statsTimeseries, selectedTimespan]);

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
            <div className="flex flex-col items-center justify-center w-full md:w-[80vw] gap-4 pt-0 p-3 h-fit">
                <div className="flex flex-row items-center gap-1">
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
                <div className="flex flex-wrap items-center justify-center w-full gap-4 mb-4">
                    <div className="flex flex-col items-center p-4 shadow w-50 bg-neutral-800/50 rounded-xl">
                        <span className="text-3xl font-bold text-sky-400">
                            {stats?.unique_active ?? "--"}
                        </span>
                        <span className="mt-1 text-sm text-neutral-400">
                            Active Users
                        </span>
                    </div>
                    <div className="flex flex-col items-center p-4 shadow w-50 bg-neutral-800/50 rounded-xl">
                        <span className="text-3xl font-bold text-purple-400">
                            {stats?.total_users ?? "--"}
                        </span>
                        <span className="mt-1 text-sm text-neutral-400">
                            Users Today
                        </span>
                    </div>
                    <div className="flex flex-col items-center p-4 shadow w-50 bg-neutral-800/50 rounded-xl">
                        <span className="text-3xl font-bold text-emerald-400">
                            {stats?.total_buses ?? "--"}
                        </span>
                        <span className="mt-1 text-sm text-neutral-400">
                            Buses Tracked Today
                        </span>
                    </div>
                    <div className="flex flex-col items-center p-4 shadow w-50 bg-neutral-800/50 rounded-xl">
                        <span className="text-3xl font-bold text-amber-400">
                            {stats?.total_stops ?? "--"}
                        </span>
                        <span className="mt-1 text-sm text-neutral-400">
                            Stops Viewed Today
                        </span>
                    </div>
                </div>
                <div className="flex items-center gap-2 mb-4">
                    <label htmlFor="timespan" className="text-sm font-medium">
                        Show data for:
                    </label>
                    <Listbox
                        value={selectedTimespan}
                        onChange={setSelectedTimespan}>
                        <div className="relative">
                            <ListboxButton className="flex items-center w-full gap-1 p-2 text-sm font-semibold border border-neutral-700 rounded-xl bg-neutral-800/50">
                                {selectedTimespan.label}
                                <FontAwesomeIcon icon={faCaretDown} />
                            </ListboxButton>
                            <ListboxOptions className="absolute z-[9999999] w-full overflow-auto border shadow-lg max-h-60 rounded-xl border-neutral-700 bg-neutral-900">
                                {timespans.map((span) => (
                                    <ListboxOption
                                        key={span.value}
                                        value={span}
                                        className={({ active }) =>
                                            `px-2 py-1 text-sm cursor-pointer ${
                                                active ? "bg-neutral-800" : ""
                                            }`
                                        }>
                                        {span.label}
                                    </ListboxOption>
                                ))}
                            </ListboxOptions>
                        </div>
                    </Listbox>
                </div>
                <div className="flex items-center w-full min-h-[300px]">
                    <Line data={chartData} options={chartOptions} />
                </div>
            </div>
        </div>
    );
};

export default StatsPage;
