import { useEffect, useState } from "react";
import type { Bus } from "../models/Bus";
import type { Stop } from "../models/Stop";
import fetchDepartures from "../utils/getDepartures";
import getStopData from "../utils/getStopData";
import { useNavigate, useParams } from "react-router";
import { Skeleton } from "@radix-ui/themes";
import { Card } from "../components/ui/Card";
import timeTo from "../utils/timeTo";
import getClosestStop from "../utils/closestStop";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faUpRightFromSquare } from "@fortawesome/free-solid-svg-icons";

const DeparturePage: React.FC = () => {
    const { stop_id } = useParams();

    const navigate = useNavigate();

    const [buses, setBuses] = useState<Bus[]>([]);
    const [stop, setStop] = useState<Stop>();
    const [closestStop, setClosest] = useState<string>();
    const [loading, setLoading] = useState(true);
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
                const stop = await getStopData(id);

                if (stop) {
                    setStop(stop);
                    const closestStop = await getClosestStop(
                        stop.coords,
                        stop_id
                    );
                    setClosest(closestStop);
                }

                const departures = await fetchDepartures(id);

                if (departures) {
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
                        Updated {elapsed} ago
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
                                    <div
                                        onClick={() =>
                                            navigate(
                                                `/buses/${bus.id}/journeys/${bus.journey_id}`
                                            )
                                        }
                                        className="cursor-pointer">
                                        <Card key={bus.reg}>
                                            <div className="flex flex-row justify-between align-center">
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
                                                        {bus.delay > 15 ||
                                                        bus.delay < -15 ? (
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
                                                    {bus.service.detail && (
                                                        <span className="wrap-anywhere">
                                                            Via:{" "}
                                                            {bus.service.detail}
                                                        </span>
                                                    )}
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
