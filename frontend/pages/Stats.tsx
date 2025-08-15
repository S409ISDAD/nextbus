import React, { useEffect, useState } from "react";
import getStats from "../utils/getStats";
import type { Stats } from "../models/Stats";

const StatsPage: React.FC = () => {
    // const navigate = useNavigate();

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
            console.log("fetching stats");
            try {
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

        interval = setInterval(fetchStats, 30000);

        return () => {
            clearInterval(interval);
        };
    }, []);

    return (
        <div>
            <div className="flex flex-col items-center justify-center gap-6">
                <div className="flex flex-col items-center justify-center gap-2 pt-0 p-7">
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
                            Updates every 30s
                        </span>
                    </div>

                    <div className="text-lg font-semibold">
                        Total Active Connections:{" "}
                        {loading ? "-" : stats?.total_active}
                    </div>
                    <div className="text-lg font-semibold">
                        Active Users: {loading ? "-" : stats?.unique_active}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default StatsPage;
