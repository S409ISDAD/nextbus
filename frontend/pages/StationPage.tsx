import { useEffect, useRef, useState } from "react";
import {
    fetchDepartures,
    fetchArrivals,
    parseTrains,
    filterDepartures,
    filterArrivals,
} from "../utils/getStationDepartures";
import { useNavigate, useParams } from "react-router";
import { Skeleton } from "@radix-ui/themes";
import { Card } from "../components/ui/Card";
import { WebSocketManager } from "../websockets/ws_manager";
import type { Location, Train } from "../models/Trains";
import timeTo, { generateTimeTo, lateness } from "../utils/timeTo";

function TrainCard({
    train,
    type,
    onClick,
}: {
    train: Train;
    type: "departures" | "arrivals";
    onClick: () => void;
}) {
    return (
        <div
            key={train.serviceUid}
            onClick={onClick}
            className="cursor-pointer">
            <div className="flex flex-row items-center justify-between">
                <div className="flex flex-col justify-around gap-1 mr-5">
                    <div className="flex flex-row items-stretch mb-1">
                        <div
                            className="flex items-center px-3 py-1 rounded-l-2xl"
                            style={{ backgroundColor: train.atocColor }}>
                            <span className="flex items-center justify-center font-bold text-center">
                                {
                                    train.locationDetail.destination[0]
                                        .description
                                }
                            </span>
                        </div>
                        <div className="flex flex-col justify-center px-3 bg-neutral-800/50 rounded-r-2xl">
                            <span className="font-semibold text">
                                {train.atocName}
                            </span>
                        </div>
                    </div>

                    <div className="flex flex-row items-center pl-2 font-semibold text gap-x-3 text-nowrap">
                        <div className="flex gap-0.5 items-center ">
                            <span>
                                {(type === "departures"
                                    ? train.scheduledDeparture
                                    : train.scheduledArrival
                                )?.toLocaleTimeString([], {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                })}
                            </span>
                        </div>
                        <div className="flex gap-0.5 items-center text-sky-400">
                            <span className="text-xs">Expt:</span>
                            <span>
                                {(type === "departures"
                                    ? train.expectedDeparture
                                    : train.expectedArrival
                                )?.toLocaleTimeString([], {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                })}
                            </span>
                        </div>

                        <span
                            className={`text-${
                                train.delay >= 60 ? "red" : "green"
                            }-400`}>
                            {lateness(train ? train.delay : 0)}
                        </span>
                    </div>
                </div>

                <div className="flex flex-row flex-wrap items-center justify-end gap-2 md:gap-4 w-min md:w-auto">
                    <div className="flex justify-center px-2 py-1 bg-blue-500 rounded-lg">
                        <span className="text-xs font-bold align-middle text-neutral-950 text-nowrap">
                            Platform{" "}
                            {train.locationDetail.platform
                                ? train.locationDetail.platform
                                : "-"}
                        </span>
                    </div>

                    <div className="flex items-center justify-center gap-1 p-[0.3rem] w-18 rounded-xl bg-neutral-800/50  h-fit">
                        <span className="text-lg font-bold ">
                            {train.timeto.split(" ")[0]}
                        </span>
                        <span className="self-end h-full mb-[0.15rem] text-sm font-bold ">
                            {train.timeto.split(" ")[1]}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}

const StationPage: React.FC = () => {
    const { station_id } = useParams();

    const navigate = useNavigate();

    const firstFetch = useRef(true);

    const [trains, setTrains] = useState<Train[]>([]);
    const [station, setStation] = useState<Location>();
    const [loading, setLoading] = useState(true);
    const [fetching, setFetching] = useState(false);
    const [lastRefreshed, setRefreshed] = useState(new Date());
    const [elapsed, setElapsed] = useState<string>("0s");
    const [msg, setMsg] = useState<string>("");
    const [type, setType] = useState<"departures" | "arrivals">("departures");

    useEffect(() => {
        const interval = setInterval(() => {
            const now = new Date();
            const diffSec = Math.floor(
                (now.getTime() - lastRefreshed.getTime()) / 1000
            );
            const min = Math.floor(diffSec / 60);
            const sec = diffSec % 60;

            setElapsed(min > 0 ? `${min}m ${sec}s` : `${sec}s`);

            const newTrains = trains
                .map((train) => {
                    return {
                        ...train,
                        timeto: generateTimeTo(
                            ((
                                type === "departures"
                                    ? train.expectedDeparture
                                    : train.expectedArrival
                            )
                                ? (
                                      (type === "departures"
                                          ? train.expectedDeparture
                                          : train.expectedArrival) as Date
                                  ).getTime() - now.getTime()
                                : 0) / 1000
                        ),
                    };
                })
                .filter((train) => {
                    const expectedTime =
                        type === "departures"
                            ? train.expectedDeparture
                            : train.expectedArrival;
                    if (!expectedTime) return false;
                    return new Date(expectedTime.getTime() + 60 * 1000) > now;
                });

            setTrains(newTrains);
        }, 1000);
        return () => clearInterval(interval);
    }, [lastRefreshed, trains]);

    useEffect(() => {
        let interval: any;

        const getData = async (id: string) => {
            if (fetching) {
                return;
            }
            setFetching(true);
            try {
                let trainData;
                if (type === "departures") {
                    trainData = await fetchDepartures(id);
                } else {
                    trainData = await fetchArrivals(id);
                }
                console.log("trainData", trainData);
                if (trainData) {
                    setTrains(trainData.services);
                    setStation(trainData.location);
                    document.title = `${trainData.location.name} Station | nextbus`;
                    setRefreshed(new Date());
                    setMsg("");
                    setLoading(false);
                }

                // else {
                //     setMsg("Failed to fetch departures.");
                // }
            } catch {
                console.log("uh oh");
            } finally {
                setLoading(false);
                setFetching(false);
            }
        };
        const init = async (station_id: string) => {
            try {
                await getData(station_id);
                interval = setInterval(() => getData(station_id), 30000);
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get station data.");
                setLoading(false);
                setFetching(false);
            }
        };

        if (station_id) {
            init(station_id);
        }

        return () => {
            clearInterval(interval);
        };
    }, [station_id, type]);

    return (
        <div className="p-5 md:mx-20">
            <div className="flex flex-col gap-4">
                <div className="flex flex-col items-center justify-center gap-3">
                    <span className="text-3xl font-bold md:text-4xl text-start">
                        {station?.name} Train Station
                    </span>
                    {/* <div className="flex flex-wrap items-center justify-center gap-4 gap-y-1">

                        <a
                            className="underline text-sky-500"
                            href={`https://bustimes.org/stops/${stop?.stop_id}`}
                            target="_blank">
                            View on bustimes.org
                        </a>

                    </div> */}
                </div>
                {/* <div className="flex flex-row justify-center gap-1 overflow-x-auto">
                    {stop?.services
                        .sort((a, b) =>
                            new Intl.Collator(undefined, {
                                numeric: true,
                                sensitivity: "base",
                            }).compare(a.line_name, b.line_name)
                        )
                        .map((service) => (
                            <span
                                key={service.id}
                                className="flex items-center justify-center px-3 py-1 text-lg font-bold text-center rounded-xl bg-neutral-800/50">
                                {service.line_name}
                            </span>
                        ))}
                </div> */}

                <div className="flex justify-center gap-2">
                    <span className="text-xs text-neutral-400">
                        {loading ? "Loading..." : `Updated ${elapsed} ago`}
                    </span>
                    <span className="text-xs text-neutral-400">·</span>
                    <span className="text-xs text-neutral-400">
                        Updates every 30s
                    </span>
                </div>

                <div className="flex justify-center gap-4 mb-2">
                    <button
                        className={`px-4 py-1 rounded-lg font-semibold cursor-pointer ${
                            type === "departures"
                                ? "bg-blue-600 text-white"
                                : "bg-neutral-800/50 text-neutral-200"
                        }`}
                        onClick={() => {
                            setType("departures");
                            setTrains([]);
                        }}
                        disabled={type === "departures"}>
                        Departures
                    </button>
                    <button
                        className={`px-4 py-1 rounded-lg font-semibold cursor-pointer ${
                            type === "arrivals"
                                ? "bg-blue-600 text-white"
                                : "bg-neutral-800/50 text-neutral-200"
                        }`}
                        onClick={() => {
                            setType("arrivals");
                            setTrains([]);
                        }}
                        disabled={type === "arrivals"}>
                        Arrivals
                    </button>
                </div>

                <div className="flex flex-col gap-1">
                    {msg ? (
                        <div className="flex justify-center gap-1 p-3">
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
                            {trains.map((train, idx) => (
                                <>
                                    <div className="flex items-center gap-2 mb-0.5">
                                        <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                        <span className="text-[10px] text-neutral-600">
                                            nextbus
                                        </span>
                                        <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                    </div>

                                    <TrainCard
                                        train={train}
                                        type={type}
                                        onClick={() =>
                                            navigate(
                                                `/trains/${train.serviceUid}`
                                            )
                                        }
                                    />
                                    {idx === trains.length - 1 && (
                                        <div className="flex items-center gap-2 mb-0.5">
                                            <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                            <span className="text-[10px] text-neutral-600">
                                                nextbus
                                            </span>
                                            <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                        </div>
                                    )}
                                </>
                            ))}
                            {trains.length === 0 && (
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
    );
};

export default StationPage;
