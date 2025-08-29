import { useEffect, useRef, useState } from "react";
import { fetchTrain } from "../utils/getTrain";
import { useNavigate, useParams, useSearchParams } from "react-router";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { lateness, toTime } from "../utils/timeUtils";
import { Pulse } from "../components/ui/Pulse";
import {
    faCalendarCheck,
    faCalendarXmark,
    faRightFromBracket,
    faRightToBracket,
    faTrainSubway,
    faWarning,
} from "@fortawesome/free-solid-svg-icons";
import type { Prediction } from "../models/Bus";
import type { TrainService } from "../models/Trains";
import React from "react";

export const TrainProgress: React.FC<{
    sequence: number;
    progress: number;
    trainRef: React.RefObject<HTMLDivElement | null>;
    finished?: boolean;
}> = React.memo(({ sequence, progress, trainRef, finished }) => {
    const sectionLength = 72;
    const translateY = (sequence + progress) * sectionLength;

    return (
        <div className="absolute top-0 left-0 h-full mt-[15px] z-11 w-9">
            <div
                className="absolute transition-all duration-500 ease-in-out translate-x-[-16px]"
                style={{ transform: `translateY(${translateY}px)` }}>
                <div className="relative flex items-center justify-center">
                    {!finished && (
                        <Pulse size={34} color="bg-rose-400" duration={2} />
                    )}
                    <div
                        className={`relative z-10 flex items-center justify-center p-2 rounded-full w-9 h-9 ${
                            finished ? "bg-neutral-700" : "bg-rose-500"
                        }`}
                        ref={trainRef}>
                        <FontAwesomeIcon icon={faTrainSubway} />
                    </div>
                    {/* {sequence} {progress} */}
                </div>
            </div>
        </div>
    );
});

const BoardAlightLabel: React.FC<{
    idx: number;
    startIdx: number;
    endIdx: number;
}> = ({ idx, startIdx, endIdx }) => {
    if (idx === startIdx) {
        return (
            <div className="text-sm font-semibold text-neutral-400 text-nowrap md:hidden">
                <span className="z-10 flex items-center justify-center">
                    board at
                </span>
            </div>
        );
    }
    if (idx === endIdx) {
        return (
            <div className="text-sm font-semibold text-neutral-400 text-nowrap md:hidden">
                <span className="z-10 flex items-center justify-center">
                    alight at
                </span>
            </div>
        );
    }
    return null;
};

const TrainPage: React.FC = () => {
    const { service_id } = useParams();

    const [searchParams] = useSearchParams();
    const fromStationCode = searchParams.get("from");
    const toStationCode = searchParams.get("to");

    const [startIdx, setStartIdx] = useState<number>(0);
    const [endIdx, setEndIdx] = useState<number>(0);
    const [showRoute, setShowRoute] = useState<boolean>(false);

    const navigate = useNavigate();

    const [train, setTrain] = useState<TrainService>();
    const [predictions, setPredictions] = useState<Prediction[]>();
    const [sequence, setSeq] = useState<number>(0);
    const [progress, setProg] = useState<number>(0);
    // const [location, setLoc] = useState<number[]>([0, 0]);
    const [loading, setLoading] = useState(true);
    const [fetching, setFetching] = useState(false);
    const [lastRefreshed, setRefreshed] = useState(new Date());
    const [elapsed, setElapsed] = useState<string>("0s");
    const [msg, setMsg] = useState<string>("");
    const [trainInfoHeight, setTrainInfoHeight] = useState(0);
    const trainInfoRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (trainInfoRef.current) {
            setTrainInfoHeight(trainInfoRef.current.clientHeight);
        }
    }, [trainInfoRef, loading, showRoute]);

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
    }, []);

    useEffect(() => {
        const interval = setInterval(() => {
            const now = new Date();
            if (!predictions || predictions.length < 2) {
                setSeq(
                    typeof train?.sequence === "number"
                        ? Math.max(train.sequence - 1, 0)
                        : 0
                );

                let prog = 0;
                if (train?.sequence === 0) {
                    prog = 0;
                } else if (
                    train?.nextStation?.expectedArrival &&
                    now.getTime() >
                        new Date(train.nextStation.expectedArrival).getTime()
                ) {
                    prog = 1;
                } else if (typeof train?.progress === "number") {
                    prog = train.progress;
                } else {
                    // Fallback to 0.5 (midpoint) if progress cannot be determined
                    prog = 0.5;
                }
                setProg(prog);
                return;
            }

            const upcoming = predictions.find((pred) => {
                const nextTime = new Date(pred.timestamp).getTime();
                return nextTime > now.getTime();
            });

            if (!upcoming) return;

            const upcoming_timestamp = new Date(upcoming.timestamp);

            const idx = predictions.indexOf(upcoming);

            const prev = predictions[idx - 1];
            const prev_timestamp = new Date(prev.timestamp);

            const newProgress = upcoming.progress;
            const prevProgress = prev.progress;

            const progressDelta = newProgress - prevProgress;

            const timeDelta = upcoming_timestamp.getTime() - now.getTime();
            const predictionDuration =
                upcoming_timestamp.getTime() - prev_timestamp.getTime();

            const interpolatedProgress =
                prevProgress +
                -Math.abs(progressDelta * -(timeDelta / predictionDuration));

            setProg(interpolatedProgress);

            setSeq(upcoming.sequence);
        }, 200);
        return () => clearInterval(interval);
    }, [predictions, train?.sequence]);

    const trainRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (trainRef.current) {
            requestAnimationFrame(() => {
                trainRef.current?.scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                });
            });
        }
    }, [sequence]);

    const findStartEndIdx = () => {
        train?.locations.forEach((stop) => {
            if (stop.crs == fromStationCode?.toUpperCase()) {
                setStartIdx(train.locations.indexOf(stop));
            }
            if (stop.crs == toStationCode?.toUpperCase()) {
                setEndIdx(train.locations.indexOf(stop));
            }
        });
    };

    useEffect(() => {
        if (train && fromStationCode && toStationCode) {
            setShowRoute(true);
            findStartEndIdx();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [train, fromStationCode, toStationCode]);

    useEffect(() => {
        let interval: any;
        const getData = async (service_id: string) => {
            if (fetching) {
                return;
            }
            setFetching(true);
            try {
                const train_response: TrainService | null = await fetchTrain(
                    service_id
                );

                if (train_response) {
                    setTrain(train_response);
                    setPredictions(train_response.predictions);
                    document.title = `${train_response.origin[0].description} to ${train_response.destination[0].description} | nextbus`;
                    setMsg("");
                    setRefreshed(new Date());
                    setTimeout(() => {
                        requestAnimationFrame(() => {
                            trainRef.current?.scrollIntoView({
                                behavior: "smooth",
                                block: "center",
                            });
                        });
                    }, 1000);
                } else {
                    setMsg("Failed to fetch train. Try reloading the page");
                }
            } catch (error) {
                console.log("uh oh", error);
            } finally {
                setLoading(false);
                setFetching(false);
            }
        };
        const init = async (service_id: string) => {
            try {
                await getData(service_id);
                interval = setInterval(() => getData(service_id), 30000);
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get train service data.");
                setLoading(false);
                setFetching(false);
            }
        };

        if (service_id) {
            init(service_id);
        }

        return () => clearInterval(interval);
    }, [service_id]);

    if (loading) {
        return <></>;
    }

    return (
        <div className="flex flex-col">
            <div
                className="fixed flex flex-col w-full gap-2 p-3 pb-1 top-0 mt-14 grow bg-[#111111] z-15 rounded-b-2xl"
                ref={trainInfoRef}>
                {train ? (
                    <div className="flex flex-col items-center justify-center gap-2">
                        <div className="flex flex-wrap items-center justify-center w-full gap-2 text-2xl font-bold">
                            {train.origin.map((o, i) => (
                                <span key={o.description}>
                                    {o.description}
                                    {i < train.origin.length - 2 ? ", " : ""}
                                    {i === train.origin.length - 2
                                        ? " and "
                                        : ""}
                                </span>
                            ))}
                            <span>to</span>
                            {train.destination.map((d, i) => (
                                <span key={d.description}>
                                    {d.description}
                                    {i < train.destination.length - 2
                                        ? ", "
                                        : ""}
                                    {i === train.destination.length - 2
                                        ? " and "
                                        : ""}
                                </span>
                            ))}
                        </div>
                        <div className="flex gap-3">
                            <a
                                className="underline text-sky-500"
                                href={`https://www.realtimetrains.co.uk/service/gb-nr:${train.serviceUid}/${train.runDate}`}
                                target="_blank"
                                rel="noopener noreferrer">
                                View on realtimetrains
                            </a>
                            <span className="text-center">
                                {train.locations.length} stops
                            </span>
                        </div>
                        <div className="flex flex-wrap items-center justify-center gap-3 gap-y-1">
                            <div className="flex flex-col items-center gap-1">
                                <span className="font-bold align-middle">
                                    {train.trainIdentity}
                                </span>
                            </div>

                            <div className="flex flex-col items-center gap-1">
                                <span
                                    className="p-2 py-1 font-bold rounded-lg text-nowrap"
                                    style={{
                                        backgroundColor: train.atocColor,
                                    }}>
                                    {train.atocName}
                                </span>
                            </div>

                            <div className="flex justify-center px-2 py-1 rounded-lg bg-neutral-800/50">
                                <span className="font-bold align-middle text-nowrap">
                                    {lateness(train.delay ? train.delay : 0)}
                                </span>
                            </div>
                            {showRoute && (
                                <button
                                    className="flex justify-center text-sm font-bold underline text-nowrap"
                                    onClick={() => {
                                        setShowRoute(false);
                                    }}
                                    type="button">
                                    View full route
                                </button>
                            )}
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
                                Train not active.
                            </span>
                        </div>
                    </div>
                )}
                {msg ? (
                    <span className="text-center text-red-400">{msg}</span>
                ) : (
                    <></>
                )}
                <div className="flex flex-row items-center justify-center gap-2 text-sm font-semibold text-neutral-300/75">
                    <span>
                        <FontAwesomeIcon
                            icon={faRightToBracket}
                            className="text-cyan-400"
                        />{" "}
                        = Arrival
                    </span>
                    <span>
                        <FontAwesomeIcon
                            icon={faRightFromBracket}
                            className="text-purple-500"
                        />{" "}
                        = Departure
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
            <div style={{ marginTop: trainInfoHeight }}>
                {train && (
                    <div className="flex flex-row gap-2 px-3 md:px-0">
                        <div className="relative flex mx-5 md:mx-40">
                            <div className="relative flex flex-col items-center py-8">
                                <TrainProgress
                                    sequence={sequence}
                                    progress={progress}
                                    trainRef={trainRef}
                                    finished={train.finished}></TrainProgress>
                                {train.locations.map((stop, idx) => (
                                    <div
                                        key={stop.crs}
                                        className="relative flex flex-col items-center">
                                        <div
                                            className={`z-10 w-1 h-1 ${
                                                idx >= startIdx &&
                                                idx <= endIdx &&
                                                showRoute
                                                    ? "bg-slate-400"
                                                    : "bg-neutral-700"
                                            } ${
                                                idx == 0
                                                    ? "rounded-tl-full"
                                                    : idx ==
                                                      train.locations.length - 1
                                                    ? "rounded-bl-full"
                                                    : ""
                                            }`}></div>
                                        {idx == startIdx && showRoute && (
                                            <>
                                                <span className="absolute z-10 font-semibold text-neutral-400 text-nowrap translate-y-[-45%] translate-x-[-80%] items-center justify-center hidden md:flex">
                                                    board here
                                                </span>
                                                <div className="absolute z-10 w-6 h-6 translate-y-[-40%] rounded-full bg-slate-400 flex items-center justify-center">
                                                    <FontAwesomeIcon
                                                        icon={faRightToBracket}
                                                        className="text-neutral-900"
                                                    />
                                                </div>
                                            </>
                                        )}

                                        {idx == endIdx && showRoute && (
                                            <>
                                                <span className="absolute z-10 font-semibold text-neutral-400 text-nowrap translate-y-[-45%] translate-x-[-80%] items-center justify-center hidden md:flex">
                                                    alight here
                                                </span>
                                                <div className="absolute z-10 w-6 h-6 translate-y-[-40%] rounded-full bg-slate-400 flex items-center justify-center">
                                                    <FontAwesomeIcon
                                                        icon={
                                                            faRightFromBracket
                                                        }
                                                        className="text-neutral-900"
                                                    />
                                                </div>
                                            </>
                                        )}
                                        {idx < train.locations.length - 1 && (
                                            <div
                                                className={`w-[4px] ${
                                                    idx >= startIdx &&
                                                    idx < endIdx &&
                                                    showRoute
                                                        ? "bg-slate-400"
                                                        : "bg-neutral-700"
                                                } flex-1 min-h-[68px]`}></div>
                                        )}
                                    </div>
                                ))}
                            </div>
                            <div className="flex flex-col gap-1">
                                {train.locations.map((stop, idx) => (
                                    <div
                                        key={stop.crs}
                                        className="flex flex-row items-center">
                                        <div
                                            className={`w-4 ${
                                                idx >= startIdx &&
                                                idx <= endIdx &&
                                                showRoute
                                                    ? "bg-slate-400"
                                                    : "bg-neutral-700"
                                            } rounded-r-full h-[4px]`}></div>
                                        <div
                                            className="p-2 w-fit h-17"
                                            onClick={() =>
                                                navigate(
                                                    `/stations/${stop.crs}`
                                                )
                                            }
                                            style={{
                                                cursor: "pointer",
                                            }}>
                                            <div
                                                className={`flex flex-col items-stretch ${
                                                    stop.departed ||
                                                    ((idx < startIdx ||
                                                        idx > endIdx) &&
                                                        showRoute)
                                                        ? "opacity-50"
                                                        : ""
                                                }`}>
                                                <div className="flex flex-wrap items-center min-w-full gap-2 gap-y-0">
                                                    {showRoute &&
                                                        (idx == startIdx ||
                                                            idx == endIdx) && (
                                                            <BoardAlightLabel
                                                                idx={idx}
                                                                startIdx={
                                                                    startIdx
                                                                }
                                                                endIdx={endIdx}
                                                            />
                                                        )}

                                                    <span className="block overflow-hidden font-bold truncate text-nowrap max-w-55 md:max-w-full">
                                                        {stop.description}
                                                    </span>
                                                    <span className="font-bold text-neutral-400 min-h-fit">
                                                        ·
                                                    </span>

                                                    <span className="text-xs font-bold text-neutral-400 text-nowrap">
                                                        Plat.{" "}
                                                        {stop.platform || "-"}
                                                    </span>

                                                    {stop.serviceLocation && (
                                                        <>
                                                            {stop.serviceLocation ===
                                                                "APPR_STAT" && (
                                                                <span className="px-2 py-1 text-xs font-bold text-yellow-400 rounded-full bg-yellow-500/20">
                                                                    Approaching
                                                                    station
                                                                </span>
                                                            )}
                                                            {stop.serviceLocation ===
                                                                "APPR_PLAT" && (
                                                                <span className="px-2 py-1 text-xs font-bold text-orange-400 rounded-full bg-orange-500/20">
                                                                    Arriving
                                                                </span>
                                                            )}
                                                            {stop.serviceLocation ===
                                                                "AT_PLAT" && (
                                                                <span className="px-2 py-1 text-xs font-bold text-blue-400 rounded-full bg-blue-600/20">
                                                                    At platform
                                                                </span>
                                                            )}
                                                            {stop.serviceLocation ===
                                                                "DEP_PREP" && (
                                                                <span className="px-2 py-1 text-xs font-bold text-purple-400 rounded-full bg-purple-500/20">
                                                                    Preparing to
                                                                    depart
                                                                </span>
                                                            )}
                                                            {stop.serviceLocation ===
                                                                "DEP_READY" && (
                                                                <span className="px-2 py-1 text-xs font-bold text-green-400 rounded-full bg-green-500/20">
                                                                    Ready to
                                                                    depart
                                                                </span>
                                                            )}
                                                        </>
                                                    )}
                                                </div>

                                                {stop.displayAs ===
                                                "CANCELLED_CALL" ? (
                                                    <div className="flex flex-row gap-6 font-semibold text-red-500">
                                                        <div className="flex gap-2">
                                                            <div className="flex items-center gap-2">
                                                                <FontAwesomeIcon
                                                                    icon={
                                                                        faCalendarXmark
                                                                    }
                                                                />
                                                                <div className="flex gap-2">
                                                                    <span className="line-through text-neutral-500">
                                                                        {toTime(
                                                                            stop.scheduledDeparture
                                                                        )}
                                                                    </span>
                                                                    <span className="text-red-500 ">
                                                                        CANCELLED
                                                                    </span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <div className="flex flex-row gap-6 font-semibold text-purple-500">
                                                        {stop.departed && (
                                                            <div className="flex gap-2">
                                                                <div className="flex items-center gap-2">
                                                                    <FontAwesomeIcon
                                                                        icon={
                                                                            faCalendarCheck
                                                                        }
                                                                    />
                                                                    <div className="flex">
                                                                        {stop.expectedDeparture &&
                                                                        stop.scheduledDeparture ? (
                                                                            <div className="flex gap-1">
                                                                                {new Date(
                                                                                    stop.expectedDeparture
                                                                                ).getTime() >
                                                                                    new Date(
                                                                                        stop.scheduledDeparture
                                                                                    ).getTime() && (
                                                                                    <span className="line-through text-neutral-500">
                                                                                        {toTime(
                                                                                            stop.scheduledDeparture
                                                                                        )}
                                                                                    </span>
                                                                                )}
                                                                                <span
                                                                                    className={
                                                                                        new Date(
                                                                                            stop.expectedDeparture
                                                                                        ).getTime() >
                                                                                        new Date(
                                                                                            stop.scheduledDeparture
                                                                                        ).getTime()
                                                                                            ? "text-red-400"
                                                                                            : "text-green-400"
                                                                                    }>
                                                                                    {toTime(
                                                                                        stop.expectedDeparture
                                                                                    )}
                                                                                </span>
                                                                            </div>
                                                                        ) : (
                                                                            "-"
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        )}

                                                        {!stop.departed &&
                                                            idx ===
                                                                train?.locations
                                                                    .length -
                                                                    1 &&
                                                            stop.expectedArrival &&
                                                            (() => {
                                                                const now =
                                                                    new Date();
                                                                const arrival =
                                                                    new Date(
                                                                        stop.expectedArrival
                                                                    );
                                                                if (
                                                                    now >
                                                                    arrival
                                                                ) {
                                                                    return (
                                                                        <div className="flex gap-2">
                                                                            <div className="flex items-center gap-2">
                                                                                <FontAwesomeIcon
                                                                                    icon={
                                                                                        faCalendarCheck
                                                                                    }
                                                                                />
                                                                                <div className="flex">
                                                                                    {stop.expectedArrival &&
                                                                                    stop.scheduledArrival ? (
                                                                                        <div className="flex gap-1">
                                                                                            {new Date(
                                                                                                stop.expectedArrival
                                                                                            ).getTime() >
                                                                                                new Date(
                                                                                                    stop.scheduledArrival
                                                                                                ).getTime() && (
                                                                                                <span className="line-through text-neutral-500">
                                                                                                    {toTime(
                                                                                                        stop.scheduledArrival
                                                                                                    )}
                                                                                                </span>
                                                                                            )}
                                                                                            <span
                                                                                                className={
                                                                                                    new Date(
                                                                                                        stop.expectedArrival
                                                                                                    ).getTime() >
                                                                                                    new Date(
                                                                                                        stop.scheduledArrival
                                                                                                    ).getTime()
                                                                                                        ? "text-red-400"
                                                                                                        : "text-green-400"
                                                                                                }>
                                                                                                {toTime(
                                                                                                    stop.expectedArrival
                                                                                                )}
                                                                                            </span>
                                                                                        </div>
                                                                                    ) : (
                                                                                        "-"
                                                                                    )}
                                                                                </div>
                                                                            </div>
                                                                        </div>
                                                                    );
                                                                }
                                                                return null;
                                                            })()}

                                                        {!stop.departed &&
                                                            !(
                                                                idx ===
                                                                    train
                                                                        ?.locations
                                                                        .length -
                                                                        1 &&
                                                                stop.expectedArrival &&
                                                                new Date() >
                                                                    new Date(
                                                                        stop.expectedArrival
                                                                    )
                                                            ) && (
                                                                <>
                                                                    {idx !==
                                                                        0 && (
                                                                        <div className="flex items-center gap-2 ">
                                                                            <FontAwesomeIcon
                                                                                icon={
                                                                                    faRightToBracket
                                                                                }
                                                                                className="text-cyan-400"
                                                                            />
                                                                            {stop.expectedArrival &&
                                                                            stop.scheduledArrival ? (
                                                                                <div className="flex gap-1">
                                                                                    {new Date(
                                                                                        stop.expectedArrival
                                                                                    ).getTime() >
                                                                                        new Date(
                                                                                            stop.scheduledArrival
                                                                                        ).getTime() && (
                                                                                        <span className="line-through text-neutral-500">
                                                                                            {toTime(
                                                                                                stop.scheduledArrival
                                                                                            )}
                                                                                        </span>
                                                                                    )}
                                                                                    <span
                                                                                        className={
                                                                                            new Date(
                                                                                                stop.expectedArrival
                                                                                            ).getTime() >
                                                                                            new Date(
                                                                                                stop.scheduledArrival
                                                                                            ).getTime()
                                                                                                ? "text-red-400"
                                                                                                : "text-green-400"
                                                                                        }>
                                                                                        {toTime(
                                                                                            stop.expectedArrival
                                                                                        )}
                                                                                    </span>
                                                                                </div>
                                                                            ) : (
                                                                                <span className="text-sm text-neutral-500">
                                                                                    pick
                                                                                    up
                                                                                    only
                                                                                </span>
                                                                            )}
                                                                        </div>
                                                                    )}

                                                                    {idx !==
                                                                        train
                                                                            ?.locations
                                                                            .length -
                                                                            1 && (
                                                                        <div className="flex items-center gap-2">
                                                                            <FontAwesomeIcon
                                                                                icon={
                                                                                    faRightFromBracket
                                                                                }
                                                                            />
                                                                            {stop.expectedDeparture &&
                                                                            stop.scheduledDeparture ? (
                                                                                <div className="flex gap-1">
                                                                                    {new Date(
                                                                                        stop.expectedDeparture
                                                                                    ).getTime() >
                                                                                        new Date(
                                                                                            stop.scheduledDeparture
                                                                                        ).getTime() && (
                                                                                        <span className="line-through text-neutral-500">
                                                                                            {toTime(
                                                                                                stop.scheduledDeparture
                                                                                            )}
                                                                                        </span>
                                                                                    )}
                                                                                    <span
                                                                                        className={
                                                                                            new Date(
                                                                                                stop.expectedDeparture
                                                                                            ).getTime() >
                                                                                            new Date(
                                                                                                stop.scheduledDeparture
                                                                                            ).getTime()
                                                                                                ? "text-red-400"
                                                                                                : "text-green-400"
                                                                                        }>
                                                                                        {toTime(
                                                                                            stop.expectedDeparture
                                                                                        )}
                                                                                    </span>
                                                                                </div>
                                                                            ) : (
                                                                                <span className="text-sm text-neutral-500">
                                                                                    drop
                                                                                    off
                                                                                    only
                                                                                </span>
                                                                            )}
                                                                        </div>
                                                                    )}
                                                                </>
                                                            )}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TrainPage;
