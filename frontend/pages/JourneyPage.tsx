import { useEffect, useRef, useState } from "react";
import type { Journey } from "../models/Journey";
import getBus from "../utils/getBus";
import { useNavigate, useParams } from "react-router";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
    faBus,
    faCalendarXmark,
    faFlagCheckered,
    faLocationDot,
    faMapPin,
} from "@fortawesome/free-solid-svg-icons";
import type { Bus } from "../models/Bus";

const BusProgress = ({ progress }: { progress: number }) => {
    const translateY = progress * 100;

    return (
        <div className="flex justify-center transition-all duration-300 w-9">
            <div className="w-0.5 rounded-full bg-neutral-600 pb-9">
                <div
                    className="transition-transform duration-300 translate-x-[-17px] w-max h-25"
                    style={{ transform: `translateY(${translateY}%)` }}>
                    <div className="flex flex-row items-center gap-3">
                        <div className="flex items-center justify-center p-2 bg-red-400 rounded-full w-9 h-9">
                            <FontAwesomeIcon icon={faBus} />
                        </div>
                        <span className="font-bold ">Heading to next stop</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

const JourneyPage: React.FC = () => {
    const { bus_id } = useParams();

    const navigate = useNavigate();

    const [bus, setBus] = useState<Bus>();
    const [sequence, setSeq] = useState<number>(0);
    const [progress, setProg] = useState<number>(0);
    const [showProg, setShowProg] = useState(true);
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

    useEffect(() => {
        const interval = setInterval(() => {
            const now = new Date();

            if (!bus?.predictions || bus.predictions.length < 2) return;

            const upcoming = bus.predictions.find((pred, idx) => {
                const nextTime = pred.timestamp * 1000;
                return nextTime > now.getTime() && idx > 0;
            });

            if (!upcoming) return;

            const idx = bus.predictions.indexOf(upcoming);
            const prev = bus.predictions[idx - 1];

            const newProgress = upcoming.progress;
            const prevProgress = prev.progress;

            const progressDelta = newProgress - prevProgress;

            const timeDelta = upcoming.timestamp * 1000 - now.getTime();
            const predictionDuration =
                (upcoming.timestamp - prev.timestamp) * 1000;

            const interpolatedProgress =
                prevProgress +
                -Math.abs(progressDelta * -(timeDelta / predictionDuration));

            setProg(interpolatedProgress);
            if (upcoming.sequence > sequence) {
                setProg(0.5);
            }

            if (interpolatedProgress > 0.95 || interpolatedProgress < 0.05) {
                setShowProg(false);
            } else {
                setShowProg(true);
            }

            setSeq(upcoming.sequence);
        }, 100);
        return () => clearInterval(interval);
    }, [progress, sequence]);

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
        const getData = async (bus_id: string) => {
            try {
                const bus = await getBus(bus_id);

                const now = new Date();

                if (bus) {
                    setBus(bus);
                    setJourney(bus.journey);
                    document.title = `${journey?.route_name} to ${journey?.destination}`;
                    setSeq(bus.predictions[0].sequence);
                    setProg(bus.predictions[0].progress);
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
        const init = async (bus_id: string) => {
            try {
                await getData(bus_id);
                interval = setInterval(() => getData(bus_id), 30000);
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get journey data.");
                setLoading(false);
            }
        };

        if (bus_id) {
            init(bus_id);
        }

        return () => clearInterval(interval);
    }, [bus_id]);

    if (loading) {
        return <></>;
    }

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
                        <a
                            className="text-teal-500 underline"
                            href={`https://bustimes.org/vehicles/${bus?.id}#journeys/${bus?.journey_id}`}
                            target="_blank">
                            View on bustimes.org
                        </a>
                        {msg ? (
                            <span className="text-red-400">{msg}</span>
                        ) : (
                            <></>
                        )}
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
                {bus?.finished ? (
                    <div className="flex flex-col gap-3 mt-4 grow h-[60vh] md:max-h-[80vh] items-center justify-center">
                        <FontAwesomeIcon
                            icon={faCalendarXmark}
                            size="5x"
                            className="text-neutral-400"></FontAwesomeIcon>
                        <span className="text-xl font-bold text-neutral-500">
                            This service has ended.
                        </span>
                    </div>
                ) : (
                    <div className="flex flex-col gap-3 mt-4 overflow-y-auto grow max-h-[60vh] md:max-h-[80vh]">
                        {journey?.stops.map((stop, idx) => (
                            <>
                                <div
                                    className={`flex items-center gap-2 ${
                                        idx < sequence ? "opacity-60" : ""
                                    }`}
                                    key={stop.stop_id}>
                                    {sequence == idx && !showProg ? (
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
                                                        journey.stops.length -
                                                            1 || idx == 0
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
                                        <span className="font-bold">
                                            {stop.name}
                                        </span>
                                        <div className="flex flex-row gap-6">
                                            <span>
                                                {stop.aimed_time.toLocaleTimeString()}
                                            </span>
                                            {sequence >= idx ? (
                                                <>
                                                    {stop.actual_time &&
                                                    sequence != 0 ? (
                                                        <></>
                                                    ) : (
                                                        <span className="font-bold">
                                                            No Data
                                                        </span>
                                                    )}
                                                    {stop.actual_time &&
                                                        sequence != 0 && (
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
                                              sequence != 0 &&
                                              Math.abs(
                                                  stop.expt_time.getTime() -
                                                      stop.aimed_time.getTime()
                                              ) > 60000 ? (
                                                <span className="font-bold text-blue-400">
                                                    Expt:{" "}
                                                    {stop.expt_time
                                                        .toLocaleTimeString
                                                        // [],
                                                        // {
                                                        //     hour: "2-digit",
                                                        //     minute: "2-digit",
                                                        // }
                                                        ()}
                                                </span>
                                            ) : (
                                                <span className="font-bold text-green-400 ">
                                                    On Time
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                                {sequence == idx && showProg ? (
                                    <div ref={busRef}>
                                        <BusProgress
                                            progress={progress}></BusProgress>
                                    </div>
                                ) : (
                                    <></>
                                )}
                            </>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default JourneyPage;
