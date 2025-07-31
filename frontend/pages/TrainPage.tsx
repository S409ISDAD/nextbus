import { useEffect, useRef, useState } from "react";
import { fetchTrain } from "../utils/getTrain";
import { useNavigate, useParams } from "react-router";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { lateness, toTime } from "../utils/timeUtils";
import { Pulse } from "../components/ui/Pulse";
import {
    faCalendarXmark,
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
}> = React.memo(({ sequence, progress, trainRef }) => {
    const sectionLength = 72;
    const translateY = (sequence + progress) * sectionLength;

    return (
        <div className="absolute top-0 left-0 h-full mt-[15px] z-11 w-9">
            <div
                className="absolute transition-all duration-500 ease-in-out translate-x-[-16px]"
                style={{ transform: `translateY(${translateY}px)` }}>
                <div className="relative flex items-center justify-center">
                    <Pulse size={36} color="bg-rose-400" duration={2} />
                    <div
                        className="relative z-10 flex items-center justify-center p-2 rounded-full bg-rose-500 w-9 h-9"
                        ref={trainRef}>
                        <FontAwesomeIcon icon={faTrainSubway} />
                    </div>
                </div>
            </div>
        </div>
    );
});

const TrainPage: React.FC = () => {
    const { service_id } = useParams();

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
                setSeq(train?.sequence ? train.sequence - 1 : 0);
                if (train?.sequence === 0) {
                    setProg(0);
                } else {
                    setProg(0.5);
                }

                if (
                    train?.nextStation?.expectedArrival &&
                    now.getTime() >
                        new Date(train?.nextStation?.expectedArrival).getTime()
                ) {
                    setProg(1);
                }
                setProg(train?.progress ? train.progress : 0);
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

                const now = new Date();

                if (train_response) {
                    setTrain(train_response);
                    setPredictions(train_response.predictions);
                    document.title = `${train_response.origin[0].description} to ${train_response.destination[0].description} | nextbus`;
                    setMsg("");
                    setRefreshed(now);
                    setTimeout(() => {
                        requestAnimationFrame(() => {
                            trainRef.current?.scrollIntoView({
                                behavior: "smooth",
                                block: "center",
                            });
                        });
                    }, 1000);
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
        <div className="">
            <div className="flex flex-col">
                <div className="fixed flex flex-col w-full gap-2 p-3 top-0 mt-13 grow bg-[#111111] z-15 rounded-b-2xl">
                    {train ? (
                        <div className="flex flex-col items-center justify-center gap-2">
                            <div className="flex flex-wrap items-center justify-center w-full gap-2 text-2xl font-bold">
                                <span>{train.origin[0].description}</span>
                                <span>to</span>
                                <span>{train.destination[0].description}</span>
                            </div>

                            <div className="flex gap-3">
                                <a
                                    className="underline text-sky-500"
                                    href={`https://realtimetrains.co.uk/train/${train.serviceUid}`}
                                    target="_blank">
                                    View on realtimetrains
                                </a>
                                <span className="text-center">
                                    {train.locations.length} stops
                                </span>
                            </div>
                            <div className="flex items-center gap-3">
                                <div className="flex flex-col items-center gap-1">
                                    <span className="font-bold align-middle">
                                        {train.trainIdentity}
                                    </span>
                                </div>

                                <div className="flex flex-col items-center gap-1">
                                    <span
                                        className="p-2 py-1 font-bold rounded-lg"
                                        style={{
                                            backgroundColor: train.atocColor,
                                        }}>
                                        {train.atocName}
                                    </span>
                                </div>
                                <div className="flex justify-center px-2 py-1 rounded-lg bg-neutral-800/50">
                                    <span className="font-bold align-middle text">
                                        {lateness(
                                            train.delay ? train.delay : 0
                                        )}
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
                {train?.finished || !train ? (
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
                    <div className="flex flex-row gap-2 px-3 md:px-0">
                        <div className="relative flex mx-5 mt-44 md:mx-40">
                            <div className="relative flex flex-col items-center py-8">
                                <TrainProgress
                                    sequence={sequence}
                                    progress={progress}
                                    trainRef={trainRef}></TrainProgress>
                                {train.locations.map((stop, idx) => (
                                    <div
                                        key={stop.crs}
                                        className="relative flex flex-col items-center">
                                        <div
                                            className={`z-10 w-1 h-1 bg-neutral-700 ${
                                                idx == 0
                                                    ? "rounded-tl-full"
                                                    : idx ==
                                                      train.locations.length - 1
                                                    ? "rounded-bl-full"
                                                    : ""
                                            }`}></div>

                                        {idx < train.locations.length - 1 && (
                                            <div className="w-[4px] bg-neutral-700 flex-1 min-h-[68px]"></div>
                                        )}
                                    </div>
                                ))}
                            </div>
                            <div className="flex flex-col gap-1">
                                {train.locations.map((stop, idx) => (
                                    <div
                                        key={stop.crs}
                                        className="flex flex-row items-center">
                                        <div className="w-4 bg-neutral-700 rounded-r-full h-[4px]"></div>
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
                                                className={`flex items-stretch flex-col ${
                                                    stop.departed
                                                        ? "opacity-50"
                                                        : ""
                                                }`}>
                                                {/* <span className="px-2 py-1 font-bold bg-indigo-800 rounded-t-2xl">
                                                    {stop.name}
                                                </span> */}
                                                <div className="flex items-center gap-4">
                                                    <span className="font-bold">
                                                        {stop.description}
                                                    </span>

                                                    <span className="text-xs font-bold text-neutral-400 text-nowrap">
                                                        Plat.{" "}
                                                        {stop.platform
                                                            ? stop.platform
                                                            : "-"}
                                                    </span>

                                                    {/* Show "At station" if current time is after arrival but before departure */}
                                                    {(() => {
                                                        const now = new Date();
                                                        const arrival =
                                                            stop.expectedArrival
                                                                ? new Date(
                                                                      stop.expectedArrival
                                                                  )
                                                                : null;
                                                        const departure =
                                                            stop.expectedDeparture
                                                                ? new Date(
                                                                      stop.expectedDeparture
                                                                  )
                                                                : null;
                                                        if (
                                                            arrival &&
                                                            departure &&
                                                            now >= arrival &&
                                                            now <= departure &&
                                                            !stop.departed
                                                        ) {
                                                            return (
                                                                <span className="px-2 py-1 ml-2 text-xs font-bold text-blue-400 rounded-full bg-blue-500/20">
                                                                    At station
                                                                </span>
                                                            );
                                                        }
                                                        return null;
                                                    })()}
                                                </div>

                                                {/* <div className="flex flex-row gap-6 px-2 py-1 font-bold bg-neutral-800/50 rounded-b-2xl">
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
                                                </div> */}
                                                <div className="flex flex-row gap-6 font-bold ">
                                                    <span>
                                                        {idx ===
                                                        train.locations.length -
                                                            1
                                                            ? stop.scheduledArrival
                                                                ? toTime(
                                                                      stop.scheduledArrival
                                                                  )
                                                                : "-"
                                                            : toTime(
                                                                  stop.scheduledDeparture
                                                              )}
                                                    </span>

                                                    <span className="flex gap-2">
                                                        {stop.departed ? (
                                                            <>
                                                                <span className="font-bold">
                                                                    Departed
                                                                </span>
                                                                {idx ===
                                                                train.locations
                                                                    .length -
                                                                    1 ? (
                                                                    // Last stop: arrival
                                                                    stop.expectedArrival &&
                                                                    stop.scheduledArrival &&
                                                                    Math.abs(
                                                                        new Date(
                                                                            stop.expectedArrival
                                                                        ).getTime() -
                                                                            new Date(
                                                                                stop.scheduledArrival
                                                                            ).getTime()
                                                                    ) >
                                                                        60000 ? (
                                                                        <span className="font-bold text-blue-400">
                                                                            {toTime(
                                                                                stop.expectedArrival
                                                                            )}
                                                                        </span>
                                                                    ) : (
                                                                        <span className="font-bold text-green-400">
                                                                            On
                                                                            Time
                                                                        </span>
                                                                    )
                                                                ) : stop.expectedDeparture &&
                                                                  stop.scheduledDeparture &&
                                                                  Math.abs(
                                                                      new Date(
                                                                          stop.expectedDeparture
                                                                      ).getTime() -
                                                                          new Date(
                                                                              stop.scheduledDeparture
                                                                          ).getTime()
                                                                  ) > 60000 ? (
                                                                    <span className="font-bold text-red-400">
                                                                        {toTime(
                                                                            stop.expectedDeparture
                                                                        )}
                                                                    </span>
                                                                ) : (
                                                                    <span className="font-bold text-green-400">
                                                                        On Time
                                                                    </span>
                                                                )}
                                                            </>
                                                        ) : (
                                                            <>
                                                                {idx ===
                                                                train.locations
                                                                    .length -
                                                                    1 ? (
                                                                    stop.expectedArrival &&
                                                                    stop.scheduledArrival &&
                                                                    Math.abs(
                                                                        new Date(
                                                                            stop.expectedArrival
                                                                        ).getTime() -
                                                                            new Date(
                                                                                stop.scheduledArrival
                                                                            ).getTime()
                                                                    ) >
                                                                        60000 ? (
                                                                        <>
                                                                            <span className="font-bold text-blue-400">
                                                                                Exptected{" "}
                                                                                {toTime(
                                                                                    stop.expectedArrival
                                                                                )}
                                                                            </span>
                                                                        </>
                                                                    ) : (
                                                                        <span className="font-bold text-green-400">
                                                                            On
                                                                            Time
                                                                        </span>
                                                                    )
                                                                ) : stop.expectedDeparture &&
                                                                  stop.scheduledDeparture &&
                                                                  Math.abs(
                                                                      new Date(
                                                                          stop.expectedDeparture
                                                                      ).getTime() -
                                                                          new Date(
                                                                              stop.scheduledDeparture
                                                                          ).getTime()
                                                                  ) > 60000 ? (
                                                                    <>
                                                                        <span className="font-bold text-blue-400">
                                                                            Expected{" "}
                                                                            {toTime(
                                                                                stop.expectedDeparture
                                                                            )}
                                                                        </span>
                                                                    </>
                                                                ) : (
                                                                    <span className="font-bold text-green-400">
                                                                        On Time
                                                                    </span>
                                                                )}
                                                            </>
                                                        )}
                                                    </span>
                                                </div>
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
