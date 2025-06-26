import { useEffect, useRef, useState } from "react";
import { isTrackedBus, type Departure } from "../models/Bus";
import fetchDepartures, { parseDepartures } from "../utils/getDepartures";
import { useNavigate } from "react-router";
import timeTo, { lateness } from "../utils/timeTo";
import { Card } from "./ui/Card";
import getClosestStop, { getCurrentPosition } from "../utils/closestStop";
import getStopData from "../utils/getStopData";
import type { Stop } from "../models/Stop";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSatelliteDish, faSlash } from "@fortawesome/free-solid-svg-icons";
import clsx from "clsx";
import { WebSocketManager } from "../websockets/ws_manager";

interface Props {
    stop_id: string;
    closest?: boolean;
}

function DepartureBoard({ stop_id, closest }: Props) {
    const [buses, setBuses] = useState<Departure[]>([]);
    const [stop, setStop] = useState<Stop>();
    const [stopID, setStopID] = useState<string>("");
    const [loading, setLoading] = useState(true);
    const [fetching, setFetching] = useState(false);
    const [lastRefreshed, setRefreshed] = useState(new Date());
    const [elapsed, setElapsed] = useState<string>("0s");
    const [msg, setMsg] = useState<string>("");

    const firstFetch = useRef(true);

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
                    (bus) => new Date(bus.expected.getTime() + 60 * 1000) > now
                );

            setBuses(newBuses);
        }, 1000);
        return () => clearInterval(interval);
    }, [lastRefreshed, buses]);

    useEffect(() => {
        let interval: any;
        const getData = async (id: string) => {
            if (fetching) {
                return;
            }
            setFetching(true);
            try {
                const stopPromise = getStopData(id);
                const schedDeparturesPromise = fetchDepartures(id, "scheduled");

                if (firstFetch.current) {
                    const stopData = await stopPromise;

                    if (stopData) {
                        setStop(stopData);
                    }
                    const departures = await schedDeparturesPromise;

                    if (departures) {
                        setBuses(departures.updatedBuses);
                        setRefreshed(departures.timestamp);
                        setMsg("");
                        setLoading(false);
                    }
                    firstFetch.current = false;
                }
                // else {
                //     setMsg("Failed to fetch departures.");
                // }
            } catch {
                console.log("uh oh");
            } finally {
                setFetching(false);
            }
        };
        const init = async (id: string) => {
            try {
                let stop_id = id;
                if (closest) {
                    const pos = await getCurrentPosition();
                    stop_id = await getClosestStop([
                        pos.coords.latitude,
                        pos.coords.longitude,
                    ]);
                    if (!stop_id) {
                        setMsg("No stop found nearby");
                        setLoading(false);
                        setFetching(false);
                    }
                }
                setStopID(stop_id);

                await getData(stop_id);

                const ws = WebSocketManager.getInstance(`stop/${stop_id}`);
                ws.connect();
                ws.onOpen(() => {
                    console.log("WS connected");
                });

                ws.onMessage(async (msg) => {
                    if (msg.type === "departures") {
                        console.log("Got departures", msg.data);
                        const buses = await parseDepartures(msg.data);

                        if (buses) {
                            setBuses(buses.updatedBuses);
                            setRefreshed(buses.timestamp);
                            setMsg("");
                            setLoading(false);
                        }
                    }
                });

                return () => ws.close();
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get location or stop data.");
                setLoading(false);
                setFetching(false);
            }
        };

        init(stop_id);

        return () => clearInterval(interval);
    }, [stop_id, closest]);

    return (
        <div className="min-w-[350px] w-[100vw] sm:w-[25vw]">
            <Card>
                <div className="flex flex-col gap-2">
                    <div
                        className="flex flex-col justify-center gap-1 cursor-pointer"
                        onClick={() => navigate(`/departures/${stopID}`)}>
                        {closest && (
                            <div className="flex items-center justify-center gap-1 p-1 rounded-lg w-fit bg-blue-950 h-fit">
                                <span className="text-xs font-bold text-blue-300">
                                    Closest Stop
                                </span>
                            </div>
                        )}
                        <span className="text-xl font-bold text-center wrap-normal">
                            {stop?.name}{" "}
                            {stop?.indicator
                                ? `(${stop.indicator})`
                                : stop?.bearing
                                ? `(${stop.bearing})`
                                : ""}
                        </span>
                    </div>
                    {loading ? (
                        <div className="flex items-center justify-center h-10 min-w-[300px] grow">
                            <span className="text-neutral-400">
                                Loading Buses...
                            </span>
                        </div>
                    ) : (
                        <>
                            <div className="px-2">
                                <div className="flex flex-col overflow-y-scroll max-h-[200px] grow">
                                    {msg ? (
                                        <div className="flex justify-center">
                                            <span className="text-red-400">
                                                {msg}
                                            </span>
                                        </div>
                                    ) : (
                                        <>
                                            {buses.map((bus) => (
                                                <>
                                                    {isTrackedBus(bus) ? (
                                                        <div
                                                            className="cursor-pointer"
                                                            key={bus.reg}
                                                            onClick={() =>
                                                                navigate(
                                                                    `/buses/${bus.id}`
                                                                )
                                                            }>
                                                            <div className="flex flex-row items-center justify-between gap-2">
                                                                <div className="flex flex-col">
                                                                    <div className="flex flex-row flex-wrap items-center gap-1">
                                                                        <span className="text-xl font-bold">
                                                                            {
                                                                                bus
                                                                                    .service
                                                                                    .line_name
                                                                            }
                                                                        </span>
                                                                        <span>
                                                                            to
                                                                        </span>
                                                                        <span className="font-bold">
                                                                            {
                                                                                bus.destination
                                                                            }
                                                                        </span>
                                                                    </div>
                                                                    <div className="flex flex-row items-center gap-3 font-semibold text-nowrap">
                                                                        <div className="flex items-center gap-0.5">
                                                                            <span className="text-sm text-teal-400">
                                                                                Expt:
                                                                            </span>
                                                                            <span className="text-teal-400">
                                                                                {bus.expected.toLocaleTimeString(
                                                                                    [],
                                                                                    {
                                                                                        hour: "2-digit",
                                                                                        minute: "2-digit",
                                                                                    }
                                                                                )}
                                                                            </span>
                                                                        </div>
                                                                        <span
                                                                            className={`text-${
                                                                                bus.delay >=
                                                                                60
                                                                                    ? "red"
                                                                                    : "green"
                                                                            }-400`}>
                                                                            {lateness(
                                                                                bus
                                                                                    ? bus.delay
                                                                                    : 0
                                                                            )}
                                                                        </span>
                                                                        <div className="relative w-5 h-5">
                                                                            <FontAwesomeIcon
                                                                                icon={
                                                                                    faSatelliteDish
                                                                                }
                                                                                className={clsx(
                                                                                    "absolute top-0 left-0 w-5 h-5",
                                                                                    {
                                                                                        "text-sky-500":
                                                                                            bus.status ===
                                                                                            "tracking",
                                                                                        "text-emerald-500":
                                                                                            bus.status ===
                                                                                            "user_tracking",
                                                                                    }
                                                                                )}
                                                                            />
                                                                        </div>
                                                                    </div>
                                                                </div>

                                                                <div className="flex items-center justify-center gap-1 p-1 ml-5 rounded-lg w-15 bg-blue-950 h-fit">
                                                                    <span className="text-sm font-bold text-blue-300 text-nowrap">
                                                                        {
                                                                            bus.timeto
                                                                        }
                                                                    </span>
                                                                </div>
                                                            </div>
                                                            <div className="bg-neutral-700 h-[1px] m-1"></div>
                                                        </div>
                                                    ) : (
                                                        <div
                                                            className="cursor-pointer"
                                                            key={bus.trip}
                                                            onClick={() =>
                                                                window.open(
                                                                    `https://bustimes.org/trips/${bus.trip}`,
                                                                    "_blank"
                                                                )
                                                            }>
                                                            <div className="flex flex-row items-center justify-between gap-2">
                                                                <div className="flex flex-col">
                                                                    <div className="flex flex-row flex-wrap items-center gap-1">
                                                                        <span className="text-xl font-bold">
                                                                            {
                                                                                bus.line
                                                                            }
                                                                        </span>
                                                                        <span>
                                                                            to
                                                                        </span>
                                                                        <span className="font-bold">
                                                                            {
                                                                                bus.destination
                                                                            }
                                                                        </span>
                                                                    </div>
                                                                    <div className="flex flex-row items-center gap-3 font-semibold text-nowrap">
                                                                        <div className="flex items-center gap-0.5">
                                                                            <span className="text-teal-400">
                                                                                {bus.expected.toLocaleTimeString(
                                                                                    [],
                                                                                    {
                                                                                        hour: "2-digit",
                                                                                        minute: "2-digit",
                                                                                    }
                                                                                )}
                                                                            </span>
                                                                        </div>
                                                                        {!bus.started && (
                                                                            <span className="font-medium opacity-70">
                                                                                Upcoming
                                                                            </span>
                                                                        )}
                                                                        {bus.started && (
                                                                            <div className="relative w-5 h-5">
                                                                                <FontAwesomeIcon
                                                                                    icon={
                                                                                        faSatelliteDish
                                                                                    }
                                                                                    className={clsx(
                                                                                        "absolute top-0 left-0 w-5 h-5",
                                                                                        {
                                                                                            "text-blue-400 opacity-40":
                                                                                                bus.status ===
                                                                                                "not_tracking",
                                                                                            "text-sky-500":
                                                                                                bus.status ===
                                                                                                "tracking",
                                                                                            "text-emerald-500":
                                                                                                bus.status ===
                                                                                                "user_tracking",
                                                                                        }
                                                                                    )}
                                                                                />
                                                                                {bus.status ===
                                                                                    "not_tracking" && (
                                                                                    <FontAwesomeIcon
                                                                                        icon={
                                                                                            faSlash
                                                                                        }
                                                                                        className="absolute top-0 left-0 w-5 h-5 text-red-500"
                                                                                    />
                                                                                )}
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                </div>

                                                                <div className="flex items-center justify-center gap-1 p-1 ml-5 rounded-lg w-15 bg-blue-950 h-fit">
                                                                    <span className="text-sm font-bold text-blue-300 text-nowrap">
                                                                        {
                                                                            bus.timeto
                                                                        }
                                                                    </span>
                                                                </div>
                                                            </div>
                                                            <div className="bg-neutral-700 h-[1px] m-1"></div>
                                                        </div>
                                                    )}
                                                </>
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
                                    {loading
                                        ? "Loading..."
                                        : `Updated ${elapsed} ago`}
                                </span>
                                <span className="text-xs text-neutral-400">
                                    ·
                                </span>
                                <span className="text-xs text-neutral-400">
                                    Updates every 20s
                                </span>
                            </div>
                        </>
                    )}
                </div>
            </Card>
        </div>
    );
}

export default DepartureBoard;
