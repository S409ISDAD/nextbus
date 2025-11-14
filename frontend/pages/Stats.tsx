import React, { useEffect, useState } from "react";
import getStats, { getDBStats } from "../utils/getStats";
import type { DBStats, Stats } from "../models/Stats";

const StatsPage: React.FC = () => {
    const [dbstats, setDBStats] = useState<DBStats>();
    const [stats, setStats] = useState<Stats>();
    const [loading, setLoading] = useState(true);
    const [lastRefreshed, setRefreshed] = useState(new Date());
    const [elapsed, setElapsed] = useState<string>("0s");

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
                const dbstats = await getDBStats();
                if (dbstats) {
                    setDBStats(dbstats.dbStats);
                    setRefreshed(new Date());
                }
                const stats = await getStats();
                if (stats) {
                    setStats(stats);
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

    return (
        <div className="flex items-center justify-center w-full h-full">
            <div className="flex flex-col  items-center justify-center w-full md:w-[80vw] gap-4 pt-0 p-3 h-fit">
                <div className="flex flex-row items-center gap-1 spooky-font">
                    <span className="text-5xl font-black text-center pt-7">
                        nextbus
                    </span>
                    <span className="text-xl font-bold h-fit text-link">
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

                <div className="flex flex-wrap items-center justify-center w-full gap-4 flssssssex-wrap">
                    <div className="flex flex-col items-center p-2 px-6 shadow bg-neutral-800/50 rounded-xl">
                        <span className="text-xl font-bold text-yellow-400">
                            {dbstats?.lines?.toLocaleString() ?? "--"}
                        </span>
                        <span className="mt-1 text-sm text-neutral-400">
                            Services
                        </span>
                    </div>
                    <div className="flex flex-col items-center p-2 px-6 shadow bg-neutral-800/50 rounded-xl">
                        <span className="text-xl font-bold text-pink-400">
                            {dbstats?.stops?.toLocaleString() ?? "--"}
                        </span>
                        <span className="mt-1 text-sm text-neutral-400">
                            Stops
                        </span>
                    </div>
                    <div className="flex flex-col items-center p-2 px-6 shadow bg-neutral-800/50 rounded-xl">
                        <span className="text-xl font-bold text-emerald-400">
                            {dbstats?.operators?.toLocaleString() ?? "--"}
                        </span>
                        <span className="mt-1 text-sm text-neutral-400">
                            Operators
                        </span>
                    </div>
                    <div className="flex flex-col items-center p-2 px-6 shadow bg-neutral-800/50 rounded-xl">
                        <span className="text-xl font-bold text-link-400">
                            {stats?.total_buses?.toLocaleString() ?? "--"}
                        </span>
                        <span className="mt-1 text-sm text-neutral-400">
                            Buses Tracked
                        </span>
                    </div>
                    <div className="flex flex-col items-center p-2 px-6 shadow bg-neutral-800/50 rounded-xl">
                        <span className="text-xl font-bold text-purple-400">
                            {stats?.total_stops?.toLocaleString() ?? "--"}
                        </span>
                        <span className="mt-1 text-sm text-neutral-400">
                            Stops Viewed
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default StatsPage;
