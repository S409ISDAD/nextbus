import { useEffect, useState } from "react";
import type { Bus } from "../models/Bus";
import fetchDepartures from "../utils/getDepartures";
import { useNavigate } from "react-router";
import timeTo from "../utils/timeTo";
import { Spinner } from "@radix-ui/themes";
import { Card } from "./ui/Card";
import getClosestStop, { getCurrentPosition } from "../utils/closestStop";

interface Props {
    stop_id: string;
    closest?: boolean;
}

function DepartureBoard({ stop_id, closest }: Props) {
    const [buses, setBuses] = useState<Bus[]>([]);
    const [stop, setStop] = useState<String>("");
    const [stopID, setStopID] = useState<String>("");
    const [loading, setLoading] = useState(true);
    const [lastRefreshed, setRefreshed] = useState(new Date());
    const [elapsed, setElapsed] = useState<string>("0s");
    const [msg, setMsg] = useState<string>("");

    const navigate = useNavigate();

    useEffect(() => {
        const interval = setInterval(() => {
            const now = new Date();
            const diffSec = Math.floor(
                (now.getTime() - lastRefreshed.getTime()) / 1000
            );
            const min = Math.floor(diffSec / 60);
            const sec = diffSec % 60;

            setElapsed(min > 0 ? `${min}m ${sec}s` : `${sec}s`);
            const newBuses = buses
                .map((bus) => {
                    return {
                        ...bus,
                        timeto: timeTo(bus),
                    };
                })
                .filter(
                    (bus) => new Date(bus.expected.getTime() + 15 * 1000) > now
                );
            setBuses(newBuses);
        }, 1000);
        return () => clearInterval(interval);
    }, [lastRefreshed]);

    useEffect(() => {
        let interval: any;
        const getData = async (id: string) => {
            try {
                const departures = await fetchDepartures(id);

                if (departures) {
                    setBuses(departures.updatedBuses);
                    setStop(departures.stop_name);
                    setRefreshed(departures.timestamp);
                    setMsg("");
                }
                // else {
                //     setMsg("Failed to fetch departures.");
                // }
            } catch {
                console.log("uh oh");
            } finally {
                setLoading(false);
            }
        };
        const init = async () => {
            try {
                if (closest) {
                    const pos = await getCurrentPosition();
                    const closest_stop_id = await getClosestStop(pos);
                    if (closest_stop_id) {
                        await getData(closest_stop_id);
                        setStopID(closest_stop_id);
                        const interval = setInterval(
                            () => getData(closest_stop_id),
                            30000
                        );
                        return () => clearInterval(interval);
                    } else {
                        setMsg("No stop found nearby");
                        setLoading(false);
                    }
                } else {
                    await getData(stop_id);
                    setStopID(stop_id);
                    interval = setInterval(() => getData(stop_id), 30000);
                }
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get location or stop data.");
                setLoading(false);
            }
        };

        init();

        return () => clearInterval(interval);
    }, [stop_id, closest]);

    if (loading) {
        return (
            <div className="h-[100px] w-[300px]">
                <Card className="h-full">
                    <div className="flex flex-col items-center h-full gap-3">
                        <span>Loading...</span>
                        <Spinner size="3"></Spinner>
                    </div>
                </Card>
            </div>
        );
    }

    return (
        <div>
            <Card>
                <div className="flex flex-col gap-2">
                    <div
                        className="flex justify-center cursor-pointer"
                        onClick={() => navigate(`/departures/${stopID}`)}>
                        <span className="text-xl font-bold text-center wrap-normal">
                            {stop}
                        </span>
                    </div>

                    <div className="px-2">
                        <div className="flex flex-col overflow-y-scroll max-h-[200px] grow">
                            {msg ? (
                                <div className="flex justify-center">
                                    <span className="text-red-400">{msg}</span>
                                </div>
                            ) : (
                                <>
                                    {buses.map((bus) => (
                                        <div
                                            className="cursor-pointer"
                                            key={bus.reg}
                                            onClick={() =>
                                                navigate(
                                                    `/buses/${bus.id}/journeys/${bus.journey_id}`
                                                )
                                            }>
                                            <div className="flex flex-row items-center justify-between">
                                                <div className="flex flex-col">
                                                    <div className="flex flex-row flex-wrap items-center gap-1">
                                                        <span className="text-xl font-bold">
                                                            {
                                                                bus.service
                                                                    .line_name
                                                            }
                                                        </span>
                                                        <span>to</span>
                                                        <span className="font-bold">
                                                            {bus.destination}
                                                        </span>
                                                    </div>
                                                    <div className="flex flex-row gap-3">
                                                        {bus.delay > 0 ? (
                                                            <>
                                                                <span className="text-red-400">
                                                                    <s>
                                                                        {bus.scheduled.toLocaleTimeString(
                                                                            [],
                                                                            {
                                                                                hour: "2-digit",
                                                                                minute: "2-digit",
                                                                            }
                                                                        )}
                                                                    </s>
                                                                </span>
                                                                <span className="text-green-400">
                                                                    {bus.expected.toLocaleTimeString()}
                                                                </span>
                                                            </>
                                                        ) : (
                                                            <span className="text-green-400">
                                                                {bus.scheduled.toLocaleTimeString(
                                                                    [],
                                                                    {
                                                                        hour: "2-digit",
                                                                        minute: "2-digit",
                                                                    }
                                                                )}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="flex flex-row flex-wrap items-center justify-end gap-2">
                                                    <div className="flex justify-center px-2 py-1 rounded-lg bg-amber-400">
                                                        <span className="text-xs font-bold text-neutral-950">
                                                            {bus.reg}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center justify-center gap-1 p-1 rounded-lg w-15 bg-blue-950 h-fit">
                                                        <span className="text-sm font-bold text-blue-300">
                                                            {bus.timeto}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="bg-neutral-700 h-[1px] m-1"></div>
                                        </div>
                                    ))}
                                    {buses.length < 4 ? (
                                        <div className="flex justify-center">
                                            <span className="text-neutral-400">
                                                No more departures!
                                            </span>
                                        </div>
                                    ) : (
                                        <></>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                    <div className="flex justify-center gap-2">
                        <span className="text-xs text-neutral-400">
                            Updated {elapsed} ago
                        </span>
                        <span className="text-xs text-neutral-400">·</span>
                        <span className="text-xs text-neutral-400">
                            Updates every 30s
                        </span>
                    </div>
                </div>
            </Card>
        </div>
    );
}

export default DepartureBoard;
