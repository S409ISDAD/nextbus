import React, { useEffect, useState } from "react";
import { Card } from "../../components/ui/Card";
import { useNavigate } from "react-router";
import UsageManager from "../../usage/UsageManager";
import type {
    DayBucket,
    Interaction,
    TimeBucket,
    Usage,
} from "../../usage/usageModels";
import { useLocalSetting } from "../../src/settings";
import { Switch } from "@headlessui/react";

const DAYMAP = {
    weekday: "weekday",
    weekend: "weekend",
};

const PredictionsPage: React.FC = () => {
    useEffect(() => {
        document.title = "your predictions | nextbus";
    }, []);

    const usageManager = UsageManager.getInstance();
    const [usageData, setUsageData] = useState<Usage>();
    const [tab, setTab] = useState<"stop" | "route">("route");
    const [usageToggle, setUsageToggle] = useLocalSetting("usageToggle", true);

    const navigate = useNavigate();
    // const isGranted = useIsLocationGranted();

    useEffect(() => {
        const getUsageData = async () => {
            (await usageManager).getAllUsage().then((data) => {
                setUsageData(data);
            });
        };
        getUsageData();
    }, []);

    function highestDay(interactions: Interaction[]): string | null {
        if (!interactions || interactions.length === 0) return null;

        const dayCounts: Record<DayBucket, number> = { weekday: 0, weekend: 0 };
        for (const i of interactions) {
            dayCounts[i.dayType]++;
        }

        const highestDay = Object.entries(dayCounts).sort(
            (a, b) => b[1] - a[1]
        )[0][0] as DayBucket;
        return DAYMAP[highestDay] || null;
    }

    function highestTime(interactions: Interaction[]): string {
        if (!interactions || interactions.length === 0)
            return "at various times";

        const timeCounts: Record<TimeBucket, number> = {
            morning: 0,
            midday: 0,
            afternoon: 0,
            evening: 0,
            night: 0,
        };

        for (const i of interactions) {
            timeCounts[i.timeBucket]++;
        }

        const highestTime = Object.entries(timeCounts).sort(
            (a, b) => b[1] - a[1]
        )[0][0];
        return `in the ${highestTime}`;
    }

    return (
        <div className="flex flex-col items-center justify-center gap-3 p-4">
            <span className="mb-4 text-3xl font-bold">
                Your Usage Predictions
            </span>

            <div className="flex flex-col items-center justify-center gap-2">
                <span className="text-center text-neutral-300 max-w-150">
                    based on your previous activity, time of day, weekday, and
                    location.
                </span>
                <ul className="list-disc list-inside font bold max-w-150 text-neutral-200">
                    <li>
                        this data is stored only on your device and never sent
                        to our servers.
                    </li>
                    <li>
                        you can clear the data or turn off usage tracking
                        completly right here:
                    </li>
                </ul>
                <div className="flex flex-col items-center justify-center gap-2 p-8">
                    <div className="flex flex-row items-center justify-center gap-2">
                        <span className="text-center text-neutral-400">
                            usage tracking:
                        </span>

                        <Switch
                            checked={usageToggle}
                            onChange={setUsageToggle}
                            className="relative flex p-1 ease-in-out rounded-full cursor-pointer group h-7 w-14 bg-white/10 focus:not-data-focus:outline-none data-checked:bg-primary data-focus:outline data-focus:outline-white">
                            <span
                                aria-hidden="true"
                                className="inline-block transition duration-200 ease-in-out translate-x-0 bg-white rounded-full shadow-lg pointer-events-none size-5 ring-0 group-data-checked:translate-x-7"
                            />
                        </Switch>
                    </div>
                    <button
                        className="button max-w-fit"
                        onClick={async () => {
                            setUsageData(undefined);
                            (await usageManager).clearAllUsage();
                        }}>
                        Clear Usage Data
                    </button>
                </div>

                <div className="flex flex-row justify-center gap-4 mb-4">
                    <button
                        className={`px-4 py-2 text-lg font-semibold rounded-xl transition-all duration-150 cursor-pointer ${
                            tab === "route"
                                ? " bg-neutral-800 text-primary-400 scale-105"
                                : " bg-neutral-900 text-neutral-400 hover:text-primary-300"
                        }`}
                        onClick={() => setTab("route")}
                        aria-selected={tab === "route"}>
                        Routes
                    </button>
                    <button
                        className={`px-4 py-2 text-lg font-semibold rounded-xl transition-all duration-150 cursor-pointer ${
                            tab === "stop"
                                ? " bg-neutral-800 text-primary-400 scale-105"
                                : " bg-neutral-900 text-neutral-400 hover:text-primary-300"
                        }`}
                        onClick={() => setTab("stop")}
                        aria-selected={tab === "stop"}>
                        Stops
                    </button>
                </div>
                <div
                    style={{ display: tab === "route" ? "flex" : "none" }}
                    className="flex flex-col w-full">
                    {usageData &&
                        Object.entries(usageData.routes).map(([id, route]) => (
                            <Card key={id} className="flex flex-col gap-1 mb-2">
                                <div className="flex flex-row items-stretch cursor-pointer">
                                    {" "}
                                    <div className="flex items-center px-3 py-1 bg-primary-700 rounded-l-2xl">
                                        <span className="flex items-center justify-center text-lg font-bold text-center">
                                            {route.lineName}
                                        </span>
                                    </div>
                                    <div className="flex flex-col justify-center px-3 bg-neutral-800/50 rounded-r-2xl">
                                        <span className="font-semibold text">
                                            {route.description}
                                        </span>
                                    </div>
                                </div>
                                <span className="text-sm text-neutral-400">
                                    You use this route the most on{" "}
                                    {highestDay(route.interactions!) ||
                                        "various days"}
                                    s, {highestTime(route.interactions!)}.
                                </span>
                            </Card>
                        ))}
                </div>
                <div
                    style={{ display: tab === "stop" ? "flex" : "none" }}
                    className="flex flex-col w-full">
                    {usageData &&
                        Object.entries(usageData.stops).map(([id, stop]) => (
                            <Card
                                key={id}
                                className="flex flex-col gap-1 mb-2 cursor-pointer"
                                onClick={() => {
                                    navigate(`/buses/stops/${stop.id}`);
                                }}>
                                <span className="flex text-lg font-bold text-center">
                                    {stop.name}
                                </span>
                                <span className="text-sm text-neutral-400">
                                    You use this stop the most on{" "}
                                    {highestDay(stop.interactions!) ||
                                        "various day"}
                                    s, {highestTime(stop.interactions!)}.
                                </span>
                                <div>
                                    {Object.entries(stop.routes).map(
                                        ([lineName, route]) => (
                                            <div
                                                key={lineName}
                                                className="flex flex-col gap-1 mt-2">
                                                <span className="font-semibold">
                                                    Route: {lineName}
                                                </span>
                                                {Object.entries(
                                                    route.destinations
                                                ).map(
                                                    ([
                                                        destinationName,
                                                        destination,
                                                    ]) => (
                                                        <div
                                                            key={
                                                                destinationName
                                                            }
                                                            className="flex flex-col ml-4">
                                                            <span className=" text-neutral-400">
                                                                You go towards{" "}
                                                                {
                                                                    destinationName
                                                                }{" "}
                                                                the most on{" "}
                                                                {highestDay(
                                                                    destination.interactions!
                                                                ) ||
                                                                    "various days"}
                                                                s,{" "}
                                                                {highestTime(
                                                                    destination.interactions!
                                                                )}
                                                                .
                                                            </span>
                                                        </div>
                                                    )
                                                )}
                                            </div>
                                        )
                                    )}
                                </div>
                            </Card>
                        ))}
                </div>
            </div>
        </div>
    );
};

export default PredictionsPage;
