import { useEffect, useRef, useState } from "react";
import type { Journey } from "../models/Journey";
import { fetchTrain } from "../utils/getTrain";
import { useNavigate, useParams } from "react-router";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { lateness } from "../utils/timeTo";
import { Pulse } from "../components/ui/Pulse";
import generateWholeTrack from "../utils/locations";
import {
    faCalendarXmark,
    faTrainSubway,
    faWarning,
} from "@fortawesome/free-solid-svg-icons";
import type { Bus, Prediction } from "../models/Bus";
import {
    MapContainer,
    Marker,
    Polyline,
    Popup,
    TileLayer,
    useMap,
} from "react-leaflet";
import { LocateControl } from "leaflet.locatecontrol";
import "leaflet.locatecontrol/dist/L.Control.Locate.min.css";
import type { TrainService } from "../models/Trains";

const TrainPage: React.FC = () => {
    const { service_id } = useParams();

    const navigate = useNavigate();

    const [train, setTrain] = useState<TrainService>();
    const [predictions, setPredictions] = useState<Prediction[]>();
    const [sequence, setSeq] = useState<number>(0);
    const [progress, setProg] = useState<number>(0);
    const [location, setLoc] = useState<number[]>([0, 0]);
    const [accuracy, setAccuracy] = useState<string>("unknown");
    const [journey, setJourney] = useState<Journey>();
    const [loading, setLoading] = useState(true);
    const [fetching, setFetching] = useState(false);
    const [lastRefreshed, setRefreshed] = useState(new Date());
    const [elapsed, setElapsed] = useState<string>("0s");
    const [msg, setMsg] = useState<string>("");

    const TrainProgress = () => {
        const sectionLength = 72;
        const translateY = (sequence + progress) * sectionLength;

        return (
            <div className="absolute top-0 left-0 h-full mt-[15px] z-11 w-9">
                <div
                    className="absolute transition-all duration-300 ease-in-out translate-x-[-15px]"
                    style={{ transform: `translateY(${translateY}px)` }}>
                    <div className="relative flex items-center justify-center">
                        <Pulse size={36} color="bg-rose-400" duration={2} />
                        <div
                            className="relative z-10 flex items-center justify-center p-2 rounded-full bg-rose-500 w-9 h-9"
                            ref={busRef}>
                            <FontAwesomeIcon icon={faTrainSubway} />
                        </div>
                    </div>
                </div>
            </div>
        );
    };

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
                // setProg(train?.progress ? train.progress.progress : 0);

                // const lat = train?.coords?.[1] ?? 0;
                // const lng = train?.coords?.[0] ?? 0;
                // setLoc([lat, lng]);
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

            const newCoords = upcoming.location;
            const prevCoords = prev.location;

            const progressDelta = newProgress - prevProgress;

            const timeDelta = upcoming.timestamp * 1000 - now.getTime();
            const predictionDuration =
                (upcoming.timestamp - prev.timestamp) * 1000;

            const interpolatedProgress =
                prevProgress +
                -Math.abs(progressDelta * -(timeDelta / predictionDuration));

            setProg(interpolatedProgress);

            setSeq(upcoming.sequence);

            const latDelta = newCoords[0] - prevCoords[0];
            const lngDelta = newCoords[1] - prevCoords[1];

            const lat =
                prevCoords[0] + latDelta * (-timeDelta / predictionDuration);

            const lng =
                prevCoords[1] + lngDelta * (-timeDelta / predictionDuration);

            setLoc([lat, lng]);
        }, 200);
        return () => clearInterval(interval);
    }, [predictions, train?.sequence]);

    const busRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (busRef.current) {
            requestAnimationFrame(() => {
                busRef.current?.scrollIntoView({
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
                const train_response: TrainService = await fetchTrain(
                    service_id
                );

                const now = new Date();

                if (train_response) {
                    setTrain(train_response);
                    setSeq(train.sequence);
                    setProg(0.5);
                    // setPredictions(bus_response.predictions);
                    document.title = `${train_response.origin[0].description} to ${train_response.destination[0].description} | nextbus`;
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
        const init = async (service_id: string) => {
            try {
                await getData(service_id);
                interval = setInterval(() => getData(service_id), 30000);
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get journey data.");
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
        <div className="px-3 md:px-0">
            <div className="flex flex-col">
                <div className="fixed flex flex-col w-full gap-2 p-3 top-0 mt-12 grow bg-[#111111] z-15 rounded-b-2xl">
                    {train ? (
                        <div className="flex flex-col items-center justify-center gap-2">
                            <div className="flex flex-row items-stretch p-2">
                                <div className="flex items-center gap-2 text-2xl font-bold">
                                    <span>{train.origin[0].description}</span>
                                    <span>to</span>
                                    <span>
                                        {train.destination[0].description}
                                    </span>
                                </div>
                            </div>
                            <div className="flex gap-3">
                                <a
                                    className="underline text-sky-500"
                                    href={`https://realtimetrains.co.uk/train/${train.service_id}`}
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
                                        {lateness(train ? train.delay : 0)}
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
                    <div className="flex flex-row gap-2">
                        <div className="relative flex mx-5 mt-44 md:mx-40">
                            <div className="relative flex flex-col items-center py-8">
                                <TrainProgress></TrainProgress>
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
                                                            ? stop.scheduledArrival?.toLocaleTimeString(
                                                                  [],
                                                                  {
                                                                      hour: "2-digit",
                                                                      minute: "2-digit",
                                                                  }
                                                              )
                                                            : stop.scheduledDeparture?.toLocaleTimeString(
                                                                  [],
                                                                  {
                                                                      hour: "2-digit",
                                                                      minute: "2-digit",
                                                                  }
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
                                                                        stop.expectedArrival.getTime() -
                                                                            stop.scheduledArrival.getTime()
                                                                    ) >
                                                                        60000 ? (
                                                                        <span className="font-bold text-blue-400">
                                                                            {stop.expectedArrival.toLocaleTimeString(
                                                                                [],
                                                                                {
                                                                                    hour: "2-digit",
                                                                                    minute: "2-digit",
                                                                                }
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
                                                                      stop.expectedDeparture.getTime() -
                                                                          stop.scheduledDeparture.getTime()
                                                                  ) > 60000 ? (
                                                                    <span className="font-bold text-red-400">
                                                                        {stop.expectedDeparture.toLocaleTimeString(
                                                                            [],
                                                                            {
                                                                                hour: "2-digit",
                                                                                minute: "2-digit",
                                                                            }
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
                                                                        stop.expectedArrival.getTime() -
                                                                            stop.scheduledArrival.getTime()
                                                                    ) >
                                                                        60000 ? (
                                                                        <>
                                                                            <span className="font-bold text-blue-400">
                                                                                Exptected{" "}
                                                                                {stop.expectedArrival.toLocaleTimeString(
                                                                                    [],
                                                                                    {
                                                                                        hour: "2-digit",
                                                                                        minute: "2-digit",
                                                                                    }
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
                                                                      stop.expectedDeparture.getTime() -
                                                                          stop.scheduledDeparture.getTime()
                                                                  ) > 60000 ? (
                                                                    <>
                                                                        <span className="font-bold text-blue-400">
                                                                            Expected{" "}
                                                                            {stop.expectedDeparture.toLocaleTimeString(
                                                                                [],
                                                                                {
                                                                                    hour: "2-digit",
                                                                                    minute: "2-digit",
                                                                                }
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
