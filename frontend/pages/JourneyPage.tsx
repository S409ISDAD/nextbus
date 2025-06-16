import { useEffect, useRef, useState } from "react";
import type { Journey } from "../models/Journey";
import getBus from "../utils/getBus";
import { useNavigate, useParams } from "react-router";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { lateness } from "../utils/timeTo";
import {
    faBus,
    faCalendarXmark,
    faWarning,
} from "@fortawesome/free-solid-svg-icons";
import type { Bus, Prediction } from "../models/Bus";

const JourneyPage: React.FC = () => {
    const { bus_id } = useParams();

    const navigate = useNavigate();

    const [bus, setBus] = useState<Bus>();
    const [predictions, setPredictions] = useState<Prediction[]>();
    const [sequence, setSeq] = useState<number>(0);
    const [progress, setProg] = useState<number>(0);
    const [journey, setJourney] = useState<Journey>();
    const [loading, setLoading] = useState(true);
    const [fetching, setFetching] = useState(false);
    const [lastRefreshed, setRefreshed] = useState(new Date());
    const [elapsed, setElapsed] = useState<string>("0s");
    const [msg, setMsg] = useState<string>("");

    const BusProgress = () => {
        const sectionLength = 72;

        const translateY = (sequence + progress) * sectionLength;

        return (
            <div className="absolute top-0 left-0 h-full mt-[15px] z-11 w-9 ">
                <div
                    className="absolute transition-all duration-300 ease-in-out  translate-x-[-10px]"
                    style={{ transform: `translateY(${translateY}px)` }}>
                    <div
                        className="flex items-center justify-center p-2 bg-red-400 rounded-full w-9 h-9"
                        ref={busRef}>
                        <FontAwesomeIcon icon={faBus} />
                    </div>
                </div>
            </div>
        );
    };

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

            if (!predictions || predictions.length < 2) {
                setSeq(bus?.progress ? bus.progress.sequence : 0);
                setProg(bus?.progress ? bus.progress.progress : 0);
                return;
            }

            const upcoming = predictions.find((pred) => {
                const nextTime = pred.timestamp * 1000;
                return nextTime > now.getTime();
            });

            if (!upcoming) return;

            const idx = predictions.indexOf(upcoming);
            const prev = predictions[idx - 1];

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

            setSeq(upcoming.sequence);
        }, 200);
        return () => clearInterval(interval);
    }, [predictions, bus?.progress]);

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
    }, [sequence, journey]);

    useEffect(() => {
        let interval: any;
        const getData = async (bus_id: string) => {
            if (fetching) {
                return;
            }
            setFetching(true);
            try {
                const bus_response = await getBus(bus_id);

                const now = new Date();

                if (bus_response) {
                    setBus(bus_response);
                    setPredictions(bus_response.predictions);
                    setJourney(bus_response.journey);
                    document.title = `${bus_response.journey.route_name} to ${bus_response.journey.destination} - ${bus_response.reg}`;
                    setMsg("");
                    setRefreshed(now);
                } else {
                    setMsg("Failed to fetch bus. Try reloading the page");
                }
            } catch (error) {
                console.log("uh oh", error);
            } finally {
                setLoading(false);
                setFetching(false);
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
                setFetching(false);
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
        <div className="">
            <div className="flex flex-col mt-38">
                <div className="flex flex-col gap-2 top-0 grow p-5 pb-1 pt-17 z-12  bg-[#111111] rounded-b-3xl fixed w-full">
                    {bus ? (
                        <div className="flex flex-col items-center gap-2">
                            <span className="text-4xl font-bold wrap-normal">
                                {journey?.route_name} to {journey?.destination}
                            </span>
                            <div className="flex gap-3">
                                <a
                                    className="text-teal-500 underline"
                                    href={`https://bustimes.org/vehicles/${bus?.id}#journeys/${bus?.journey_id}`}
                                    target="_blank">
                                    View on bustimes.org
                                </a>
                                <span className="text-center">
                                    {journey?.stops.length} stops
                                </span>
                            </div>
                            <div className="flex items-center gap-3">
                                <div className="flex flex-col items-center gap-1">
                                    <span className="font-bold align-middle">
                                        {bus?.fleet_num}
                                    </span>
                                    <div className="flex justify-center px-2 py-1 rounded-lg bg-amber-400">
                                        <span className="text-xs font-bold align-middle text-neutral-950">
                                            {bus?.reg}
                                        </span>
                                    </div>
                                </div>

                                <div className="flex flex-col items-center gap-1">
                                    <span className="text-xs font-bold">
                                        {bus.livery
                                            ? bus?.livery.name
                                            : "No livery"}
                                    </span>
                                    <div
                                        className="rounded shadow-2xl w-15 aspect-3/2"
                                        style={{
                                            backgroundImage: bus.livery
                                                ? bus?.livery.css
                                                : "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 200' fill='none' xmlns:xlink='http://www.w3.org/1999/xlink'><rect width='300' height='200' fill='%23222222'/><text x='150' y='110' text-anchor='middle' fill='%23999999' font-size='80' font-family='sans-serif' dy='.35em'>?</text></svg>\")",
                                        }}></div>
                                </div>
                                <div className="flex justify-center px-2 py-1 rounded-lg bg-blue-950">
                                    <span className="font-bold text-blue-300 align-middle text">
                                        {lateness(bus ? bus.delay : 0)}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-row items-center justify-center h-30">
                            <div className="flex flex-row gap-3 p-3 border-2 border-red-400 bg-red-950 rounded-2xl">
                                <FontAwesomeIcon
                                    icon={faWarning}
                                    size="2x"
                                    className="text-neutral-300"></FontAwesomeIcon>
                                <span className="text-2xl font-black text-neutral-300 wrap-normal">
                                    Bus not active.
                                </span>
                            </div>
                        </div>
                    )}
                    {msg ? (
                        <span className="text-center text-red-400">{msg}</span>
                    ) : (
                        <></>
                    )}

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
                {bus?.finished || !bus ? (
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
                    <div className="relative flex mx-5 mt-4 md:mx-40">
                        <div className="relative flex flex-col items-center py-6.5">
                            <BusProgress></BusProgress>
                            {journey?.stops.map((stop, idx) => (
                                <div
                                    key={stop.stop_id}
                                    className="relative flex flex-col items-center">
                                    <div className="z-10 w-4 h-4 rounded-full bg-neutral-700"></div>

                                    {idx < journey.stops.length - 1 && (
                                        <div className="w-[4px] bg-neutral-700 flex-1 min-h-[56px]"></div>
                                    )}
                                </div>
                            ))}
                        </div>
                        <div className="flex flex-col gap-1">
                            {journey?.stops.map((stop, idx) => (
                                <div
                                    key={stop.stop_id}
                                    className="flex flex-row items-center">
                                    <div className="w-5 bg-neutral-700 rounded-r-full h-[4px]"></div>
                                    <div
                                        className="p-2 w-fit h-17 "
                                        onClick={() =>
                                            navigate(
                                                `/departures/${stop.stop_id}`
                                            )
                                        }
                                        style={{
                                            cursor: "pointer",
                                        }}>
                                        <div
                                            className={` ${
                                                idx < sequence
                                                    ? "opacity-40"
                                                    : ""
                                            }`}>
                                            <span className="font-bold">
                                                {stop.name}
                                            </span>
                                            <div className="flex flex-row gap-6">
                                                <span>
                                                    {stop.aimed_time.toLocaleTimeString(
                                                        [],
                                                        {
                                                            hour: "2-digit",
                                                            minute: "2-digit",
                                                        }
                                                    )}
                                                </span>
                                                {sequence >= idx ? (
                                                    <span className="font-bold">
                                                        {sequence == 0 &&
                                                        !bus?.started
                                                            ? "Waiting to Start"
                                                            : "Departed"}
                                                    </span>
                                                ) : stop.expt_time &&
                                                  bus?.started &&
                                                  Math.abs(
                                                      stop.expt_time.getTime() -
                                                          stop.aimed_time.getTime()
                                                  ) > 60000 ? (
                                                    <span className="font-bold text-blue-400">
                                                        Expt:{" "}
                                                        {stop.expt_time.toLocaleTimeString(
                                                            [],
                                                            {
                                                                hour: "2-digit",
                                                                minute: "2-digit",
                                                            }
                                                        )}
                                                    </span>
                                                ) : (
                                                    <span className="font-bold text-green-400 ">
                                                        On Time
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default JourneyPage;
