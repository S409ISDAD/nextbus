import { useEffect, useState } from "react";
import { isTrackedBus, type Bus, type Departure } from "../models/Bus";
import type { Stop } from "../models/Stop";
import fetchDepartures from "../utils/getDepartures";
import getStopData from "../utils/getStopData";
import { redirect, useNavigate, useParams } from "react-router";
import { Skeleton } from "@radix-ui/themes";
import { Card } from "../components/ui/Card";
import timeTo, { lateness } from "../utils/timeTo";
import getClosestStop from "../utils/closestStop";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
    faSatelliteDish,
    faSlash,
    faUpRightFromSquare,
} from "@fortawesome/free-solid-svg-icons";
import clsx from "clsx";

const DeparturePage: React.FC = () => {
    const { stop_id } = useParams();

    const navigate = useNavigate();

    const [buses, setBuses] = useState<Departure[]>([]);
    const [stop, setStop] = useState<Stop>();
    const [closestStop, setClosest] = useState<string>();
    const [loading, setLoading] = useState(true);
    const [fetching, setFetching] = useState(false);
    const [lastRefreshed, setRefreshed] = useState(new Date());
    const [elapsed, setElapsed] = useState<string>("0s");
    const [msg, setMsg] = useState<string>("");
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
                const departuresPromise = fetchDepartures(id);

                const stopData = await stopPromise;
                if (stopData) {
                    setStop(stopData);
                    document.title = stopData.name;
                    const closestStop = await getClosestStop(
                        stopData.coords,
                        stop_id
                    );
                    setClosest(closestStop);
                }

                const departures = await departuresPromise;
                if (departures) {
                    console.log(departures.updatedBuses);
                    setBuses(departures.updatedBuses);
                    setRefreshed(departures.timestamp);
                    setMsg("");
                } else {
                    setMsg("Lost connection to server. Please Wait...");
                }
            } catch {
                console.log("uh oh");
            } finally {
                setLoading(false);
                setFetching(false);
            }
        };
        const init = async (stop_id: string) => {
            try {
                await getData(stop_id);
                interval = setInterval(() => getData(stop_id), 30000);
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get stop data.");
                setLoading(false);
                setFetching(false);
            }
        };

        if (stop_id) {
            init(stop_id);
        }

        return () => clearInterval(interval);
    }, [stop_id]);

    return (
        <div className="p-5 md:mx-20">
            <div className="flex flex-col gap-4">
                <div className="flex flex-col items-center justify-center gap-3">
                    <span className="text-4xl font-bold text-center">
                        {stop?.name}{" "}
                        {stop?.indicator
                            ? `(${stop.indicator})`
                            : stop?.bearing
                            ? `(${stop.bearing})`
                            : ""}
                    </span>
                    <div className="flex flex-wrap items-center justify-center gap-4 gap-y-1">
                        <span className="text-center">{stop?.stop_id}</span>
                        {closestStop ? (
                            <div
                                className="flex items-center gap-2 p-2 cursor-pointer bg-neutral-900 w-fit rounded-2xl border-1 border-neutral-800"
                                onClick={() => {
                                    setBuses([]);
                                    setLoading(true);
                                    navigate(`/departures/${closestStop}`);
                                }}>
                                Nearest Stop{" "}
                                <FontAwesomeIcon
                                    icon={faUpRightFromSquare}
                                    width="20px"></FontAwesomeIcon>
                            </div>
                        ) : (
                            <></>
                        )}
                        <a
                            className="text-teal-500 underline"
                            href={`https://bustimes.org/stops/${stop?.stop_id}`}
                            target="_blank">
                            View on bustimes.org
                        </a>
                    </div>
                </div>
                <div className="flex flex-row flex-wrap justify-center gap-1">
                    {stop?.services
                        .sort((a, b) =>
                            new Intl.Collator(undefined, {
                                numeric: true,
                                sensitivity: "base",
                            }).compare(a.line_name, b.line_name)
                        )
                        .map((service) => (
                            <div
                                className="p-2 bg-neutral-900 rounded-xl border-1 border-neutral-800"
                                key={service.id}>
                                <span className="font-semibold ">
                                    {service.line_name}
                                </span>
                            </div>
                        ))}
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

                <div className="pt-2 grow">
                    <div className="flex flex-col gap-3">
                        {msg ? (
                            <div className="flex justify-center p-3">
                                <span className="text-red-400">{msg}</span>
                            </div>
                        ) : (
                            <></>
                        )}
                        {loading ? (
                            <>
                                {[1, 2, 3, 4, 5].map((i) => (
                                    <Card key={i}>
                                        <div className="flex flex-row justify-between align-center">
                                            <div className="flex flex-col gap-1">
                                                <Skeleton>
                                                    <span className="text-xl">
                                                        123 to Location
                                                    </span>
                                                </Skeleton>
                                                <Skeleton>
                                                    <span>10:10:10</span>
                                                </Skeleton>
                                            </div>
                                            <div className="flex flex-row gap-3">
                                                <Skeleton>
                                                    <div className="p-3">
                                                        <span>AB12ACB</span>
                                                    </div>
                                                </Skeleton>
                                                <Skeleton>
                                                    <div className="p-3">
                                                        <span>5 min</span>
                                                    </div>
                                                </Skeleton>
                                            </div>
                                        </div>
                                    </Card>
                                ))}
                            </>
                        ) : (
                            <>
                                {buses.map((bus) => (
                                    <>
                                        {isTrackedBus(bus) ? (
                                            <div
                                                onClick={() =>
                                                    navigate(`/buses/${bus.id}`)
                                                }
                                                className="cursor-pointer">
                                                <Card key={bus.reg}>
                                                    <div className="flex flex-row justify-between align-center">
                                                        <div className="flex flex-col justify-around">
                                                            {bus.service
                                                                .detail ? (
                                                                <>
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
                                                                    <span className="text-sm wrap-anywhere text-neutral-400">
                                                                        Via:{" "}
                                                                        {
                                                                            bus
                                                                                .service
                                                                                .detail
                                                                        }
                                                                    </span>
                                                                </>
                                                            ) : (
                                                                <div className="flex flex-row flex-wrap items-center gap-1">
                                                                    <span className="text-2xl font-bold">
                                                                        {
                                                                            bus
                                                                                .service
                                                                                .line_name
                                                                        }
                                                                    </span>
                                                                    <span className="text-lg">
                                                                        to
                                                                    </span>
                                                                    <span className="text-xl font-bold">
                                                                        {
                                                                            bus.destination
                                                                        }
                                                                    </span>
                                                                </div>
                                                            )}
                                                            <div className="flex flex-row items-center text-lg font-semibold gap-x-3 text-nowrap">
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
                                                            </div>
                                                        </div>
                                                        <div className="flex flex-row flex-wrap items-center justify-end gap-2 md:gap-4">
                                                            <div className="flex justify-center px-2 py-1 rounded-lg bg-amber-400">
                                                                <span className="text-xs font-bold align-middle text-neutral-950">
                                                                    {bus.reg}
                                                                </span>
                                                            </div>
                                                            <div className="flex items-center justify-center w-20 gap-1 p-2 rounded-xl bg-blue-950 h-fit">
                                                                <span className="text-xl font-bold text-blue-300">
                                                                    {
                                                                        bus.timeto.split(
                                                                            " "
                                                                        )[0]
                                                                    }
                                                                </span>
                                                                <span className="font-bold text-blue-300">
                                                                    {
                                                                        bus.timeto.split(
                                                                            " "
                                                                        )[1]
                                                                    }
                                                                </span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </Card>
                                            </div>
                                        ) : (
                                            <div
                                                className="cursor-pointer"
                                                onClick={() =>
                                                    window.open(
                                                        `https://bustimes.org/trips/${bus.trip}`,
                                                        "_blank"
                                                    )
                                                }>
                                                <Card key={bus.trip}>
                                                    <div className="flex flex-row justify-between align-center">
                                                        <div className="flex flex-col justify-around">
                                                            <div className="flex flex-row flex-wrap items-center gap-1">
                                                                <span className="text-2xl font-bold">
                                                                    {bus.line}
                                                                </span>
                                                                <span>to</span>
                                                                <span className="font-bold">
                                                                    {
                                                                        bus.destination
                                                                    }
                                                                </span>
                                                            </div>

                                                            <div className="flex flex-row items-center text-lg font-semibold gap-x-3 text-nowrap">
                                                                <div className="flex items-center gap-0.5">
                                                                    <span className="text-sm text-teal-400">
                                                                        Schd:
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
                                                                {bus.started ? (
                                                                    <span className="opacity-70">
                                                                        Not
                                                                        Tracking
                                                                    </span>
                                                                ) : (
                                                                    <span>
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
                                                        <div className="flex flex-row flex-wrap items-center justify-end gap-2 md:gap-4">
                                                            <div className="flex items-center justify-center w-20 gap-1 p-2 rounded-xl bg-blue-950 h-fit">
                                                                <span className="text-xl font-bold text-blue-300">
                                                                    {
                                                                        bus.timeto.split(
                                                                            " "
                                                                        )[0]
                                                                    }
                                                                </span>
                                                                <span className="font-bold text-blue-300">
                                                                    {
                                                                        bus.timeto.split(
                                                                            " "
                                                                        )[1]
                                                                    }
                                                                </span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </Card>
                                            </div>
                                        )}
                                    </>
                                ))}
                                {buses.length < 4 && (
                                    <div className="flex justify-center">
                                        <span className="text-neutral-400">
                                            No more departures!
                                        </span>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DeparturePage;
