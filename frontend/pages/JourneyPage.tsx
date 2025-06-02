import { useEffect, useRef, useState } from "react";
import type { Journey } from "../models/Journey";
import fetchJourney from "../utils/getJourney";
import getBus, { type BusResponse } from "../utils/getBus";
import { useNavigate, useParams } from "react-router";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
    faBus,
    faFlagCheckered,
    faLocationDot,
    faMapPin,
} from "@fortawesome/free-solid-svg-icons";

const JourneyPage: React.FC = () => {
    const { bus_id, journey_id } = useParams();

    const navigate = useNavigate();

    const [bus, setBus] = useState<BusResponse>();
    const [journey, setJourney] = useState<Journey>();
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
        }, 1000);
        return () => clearInterval(interval);
    }, [lastRefreshed]);

    const busRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (journey && busRef.current) {
            requestAnimationFrame(() => {
                busRef.current?.scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                });
            });
        }
    }, [journey]);

    useEffect(() => {
        let interval: any;
        const getData = async (bus_id: string, journey_id: string) => {
            try {
                const journey = await fetchJourney(bus_id, journey_id);
                const bus = await getBus(bus_id);

                const now = new Date();

                if (journey) {
                    setJourney(journey);
                } else {
                    setMsg("Failed to fetch journey. Try reloading the page");
                }

                if (bus) {
                    setBus(bus);
                } else {
                    setMsg("Failed to fetch bus. Try reloading the page");
                }
                setRefreshed(now);
            } catch {
                console.log("uh oh");
            } finally {
                setLoading(false);
            }
        };
        const init = async (bus_id: string, journey_id: string) => {
            try {
                await getData(bus_id, journey_id);
                interval = setInterval(
                    () => getData(bus_id, journey_id),
                    30000
                );
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get journey data.");
                setLoading(false);
            }
        };

        if (bus_id && journey_id) {
            init(bus_id, journey_id);
        }

        return () => clearInterval(interval);
    }, [bus_id, journey_id]);

    return (
        <div className="lg:mx-40">
            <div className="flex flex-col p-5 pb-0">
                <div className="flex flex-col gap-2">
                    <div className="flex flex-col items-center justify-center gap-1">
                        <span className="text-4xl font-bold text-center wrap-normal">
                            {journey?.route_name} to {journey?.destination}
                        </span>
                        <span className="text-center">
                            {journey?.stops.length} stops
                        </span>
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
                <div className="flex flex-col gap-3 mt-4 overflow-y-auto grow max-h-[60vh] md:max-h-[80vh]">
                    {journey?.stops.map((stop, idx) => (
                        <>
                            <div
                                className={`flex items-center gap-2 ${
                                    bus?.progress &&
                                    idx <= bus?.progress.sequence &&
                                    bus.progress.progress > 0.1
                                        ? "opacity-60"
                                        : ""
                                } ${
                                    bus?.progress &&
                                    idx < bus?.progress.sequence &&
                                    bus.progress.progress < 0.1
                                        ? "opacity-60"
                                        : ""
                                }`}
                                key={stop.stop_id}>
                                {bus?.progress.sequence == idx &&
                                bus.progress.progress < 0.1 ? (
                                    <div ref={busRef}>
                                        <div className="flex items-center justify-center p-2 bg-red-400 rounded-lg cursor-pointer w-9 h-9">
                                            <FontAwesomeIcon icon={faBus} />
                                        </div>
                                    </div>
                                ) : (
                                    <div
                                        className={`flex items-center justify-center p-2 bg-blue-400 rounded-lg cursor-pointer w-9 h-9`}
                                        onClick={() =>
                                            navigate(
                                                `/departures/${stop.stop_id}`
                                            )
                                        }
                                        style={{
                                            cursor: "pointer",
                                        }}>
                                        <FontAwesomeIcon
                                            icon={
                                                idx ==
                                                    journey.stops.length - 1 ||
                                                idx == 0
                                                    ? faFlagCheckered
                                                    : stop.minor
                                                    ? faLocationDot
                                                    : faMapPin
                                            }
                                        />
                                    </div>
                                )}
                                <div className="bg-neutral-700 h-[1px] m-1 w-5"></div>
                                <div className="flex flex-col">
                                    <span>{stop.name}</span>
                                    <div className="flex flex-row gap-6">
                                        {bus?.progress &&
                                        bus?.progress.sequence >= idx ? (
                                            <>
                                                {stop.actual_time ? (
                                                    <span className="text-red-400">
                                                        <s>
                                                            {stop.aimed_time.toLocaleTimeString(
                                                                [],
                                                                {
                                                                    hour: "2-digit",
                                                                    minute: "2-digit",
                                                                }
                                                            )}
                                                        </s>
                                                    </span>
                                                ) : (
                                                    <>
                                                        <span>
                                                            {stop.aimed_time.toLocaleTimeString(
                                                                [],
                                                                {
                                                                    hour: "2-digit",
                                                                    minute: "2-digit",
                                                                }
                                                            )}
                                                        </span>
                                                        <span className="font-bold">
                                                            Did not stop
                                                        </span>
                                                    </>
                                                )}
                                                {stop.actual_time && (
                                                    <span className="font-bold text-orange-400">
                                                        Departed:{" "}
                                                        {stop.actual_time.toLocaleTimeString(
                                                            [],
                                                            {
                                                                hour: "2-digit",
                                                                minute: "2-digit",
                                                            }
                                                        )}
                                                    </span>
                                                )}
                                            </>
                                        ) : stop.expt_time &&
                                          stop.expt_time.getTime() -
                                              stop.aimed_time.getTime() >
                                              60000 ? (
                                            <>
                                                <span className="text-red-400">
                                                    <s>
                                                        {stop.aimed_time.toLocaleTimeString(
                                                            [],
                                                            {
                                                                hour: "2-digit",
                                                                minute: "2-digit",
                                                            }
                                                        )}
                                                    </s>
                                                </span>
                                                <span className="font-bold text-orange-400">
                                                    Expt:{" "}
                                                    {stop.expt_time.toLocaleTimeString(
                                                        [],
                                                        {
                                                            hour: "2-digit",
                                                            minute: "2-digit",
                                                        }
                                                    )}
                                                </span>
                                            </>
                                        ) : (
                                            <>
                                                <span className="text-green-400">
                                                    {stop.aimed_time.toLocaleTimeString(
                                                        [],
                                                        {
                                                            hour: "2-digit",
                                                            minute: "2-digit",
                                                        }
                                                    )}
                                                </span>

                                                <span className="font-bold text-green-400 ">
                                                    On Time
                                                </span>
                                            </>
                                        )}
                                    </div>
                                </div>
                            </div>
                            {bus?.progress.sequence == idx &&
                            bus.progress.progress > 0.1 ? (
                                <div
                                    ref={busRef}
                                    className="flex flex-row items-center gap-3">
                                    <div className="flex items-center justify-center p-2 bg-red-400 rounded-lg cursor-pointer w-9 h-9">
                                        <FontAwesomeIcon icon={faBus} />
                                    </div>
                                    <span className="font-bold">
                                        Heading to next stop
                                    </span>
                                </div>
                            ) : (
                                <></>
                            )}
                        </>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default JourneyPage;
