import { useEffect, useRef, useState } from "react";
import { isTrackedBus, type Departure } from "../models/Bus";
import fetchDepartures, { parseDepartures } from "../utils/getDepartures";
import { useNavigate } from "react-router";
import timeTo, { lateness, toTime } from "../utils/timeUtils";
import { Card } from "./ui/Card";
import { getClosestStops } from "../utils/closestStop";
import { getCurrentPosition } from "../utils/locations";
import getStopData from "../utils/getStopData";
import type { BTStop } from "../models/Stop";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { motion, AnimatePresence } from "framer-motion";
import {
    faSatelliteDish,
    faSlash,
    faWarning,
} from "@fortawesome/free-solid-svg-icons";
import clsx from "clsx";
import { WebSocketManager } from "../websockets/ws_manager";
// import {
//     Transition,
//     TransitionChild,
//     Dialog,
//     DialogPanel,
//     DialogTitle,
//     Description,
// } from "@headlessui/react";

interface Props {
    stop_id: string;
    closest?: boolean;
    filter?: string;
}

function BusCard({
    bus,
    gettingLiveData,
}: {
    bus: Departure;
    gettingLiveData: boolean;
}) {
    const [trackingBroken, setTrackingBroken] = useState(false);
    const [notLoggedOff, setNotLoggedOff] = useState(false);
    const [brokenDown, setBrokenDown] = useState(false);
    const [isOnDiversion, setIsOnDiversion] = useState(false);
    // const [showExternalDialog, setShowExternalDialog] = useState(false);
    // const [externalUrl, setExternalUrl] = useState<string | null>(null);

    const navigate = useNavigate();

    useEffect(() => {
        setTrackingBroken(false);
        setBrokenDown(false);
        setNotLoggedOff(false);
        setIsOnDiversion(false);
        if (
            isTrackedBus(bus) &&
            bus.confidence.broken_tracking_confidence >= 0.65
        ) {
            setTrackingBroken(true);
        }
        if (
            isTrackedBus(bus) &&
            bus.confidence.broken_down_confidence >= 0.65
        ) {
            setBrokenDown(true);
        }
        if (isTrackedBus(bus) && bus.confidence.log_off_confidence >= 0.65) {
            setNotLoggedOff(true);
        }
        if (isTrackedBus(bus) && bus.confidence.diversion_confidence >= 0.65) {
            setIsOnDiversion(true);
        }
    }, [bus]);

    const handleClick = () => {
        if (isTrackedBus(bus) && bus.status !== "on_prev_trip") {
            navigate(`/buses/${bus.id}`);
        } else if (bus.db_journey) {
            navigate(`/buses/dbjourneys/${bus.db_journey}`);
        } else {
            navigate(`/buses/trips/${bus.trip}`);
        }
    };

    return (
        <>
            <div
                className={clsx(
                    "cursor-pointer",
                    isTrackedBus(bus) &&
                        (bus.delay >= 2700 ||
                            trackingBroken ||
                            brokenDown ||
                            notLoggedOff ||
                            bus.status == "cancelled") &&
                        "opacity-75"
                )}
                key={bus.trip}
                onClick={handleClick}>
                <div className="flex flex-row items-center justify-between gap-2">
                    <div className="flex flex-col justify-around">
                        <div className="flex flex-row items-stretch mb-1">
                            <div className="flex items-center px-2 bg-primary-700 rounded-l-2xl">
                                <span className="flex items-center justify-center text-lg font-bold text-center">
                                    {isTrackedBus(bus)
                                        ? bus.service.line_name
                                        : bus.line}
                                </span>
                            </div>
                            <div className="flex flex-col justify-center px-2 bg-neutral-800/50 rounded-r-2xl">
                                <span className="font-semibold text">
                                    {bus.destination}
                                </span>
                            </div>
                        </div>
                        {isTrackedBus(bus) && bus.delay >= 2700 && (
                            <div className="flex items-center gap-1 text-xs ">
                                <FontAwesomeIcon
                                    icon={faWarning}
                                    className="text-red-400"
                                />
                                This bus is quite late, it may not arrive
                            </div>
                        )}
                        {trackingBroken && (
                            <div className="flex items-center gap-1 text-xs ">
                                <FontAwesomeIcon
                                    icon={faWarning}
                                    className="text-red-400"
                                />
                                This bus may not be tracking properly.
                            </div>
                        )}

                        {brokenDown && (
                            <div className="flex items-center gap-1 text-xs ">
                                <FontAwesomeIcon
                                    icon={faWarning}
                                    className="text-red-400"
                                />
                                This bus may have broken down or is not moving.
                            </div>
                        )}
                        {notLoggedOff && (
                            <div className="flex items-center gap-1 text-xs ">
                                <FontAwesomeIcon
                                    icon={faWarning}
                                    className="text-red-400"
                                />
                                This bus may have finished its route.
                            </div>
                        )}
                        {isOnDiversion && (
                            <div className="flex items-center gap-1 text-xs ">
                                <FontAwesomeIcon
                                    icon={faWarning}
                                    className="text-red-400"
                                />
                                This bus may be on diversion.
                            </div>
                        )}
                        <div className="flex flex-row items-center gap-3 font-semibold text-nowrap">
                            <div className="flex items-center gap-2">
                                {bus.expected && bus.scheduled
                                    ? (() => {
                                          const aimed = new Date(
                                              bus.scheduled
                                          ).getTime();
                                          const expt = new Date(
                                              bus.expected
                                          ).getTime();
                                          const diff = Math.abs(expt - aimed);
                                          const isLate =
                                              expt > aimed && diff > 60000;
                                          return (
                                              <div className="flex gap-2">
                                                  {(isLate ||
                                                      bus.status ==
                                                          "cancelled") && (
                                                      <span className="line-through text-neutral-500">
                                                          {toTime(
                                                              bus.scheduled
                                                          )}
                                                      </span>
                                                  )}
                                                  {bus.status !=
                                                      "cancelled" && (
                                                      <span
                                                          className={
                                                              "text-link-400"
                                                          }>
                                                          {toTime(bus.expected)}
                                                      </span>
                                                  )}
                                              </div>
                                          );
                                      })()
                                    : "-"}
                            </div>
                            {bus.status === "cancelled" ? (
                                <span className="font-bold text-red-400">
                                    Cancelled
                                </span>
                            ) : (
                                <>
                                    {isTrackedBus(bus) && (
                                        <span
                                            className={`text-${
                                                bus.delay >= 60
                                                    ? "red"
                                                    : "green"
                                            }-400`}>
                                            {lateness(bus ? bus.delay : 0)}
                                        </span>
                                    )}
                                    {!bus.started && (
                                        <span className="text-sm font-medium opacity-70">
                                            {bus.status === "not_tracking"
                                                ? "Upcoming"
                                                : bus.status === "waiting"
                                                ? "Not Started"
                                                : "On prev. trip"}
                                        </span>
                                    )}
                                    {bus.started && (
                                        <div className="relative w-5 h-5">
                                            <FontAwesomeIcon
                                                icon={faSatelliteDish}
                                                beatFade={gettingLiveData}
                                                className={clsx(
                                                    "absolute top-0 left-0 w-5 h-5",
                                                    gettingLiveData
                                                        ? "text-neutral-500"
                                                        : {
                                                              "text-primary-400 opacity-40":
                                                                  bus.status ===
                                                                  "not_tracking",
                                                              "text-link":
                                                                  bus.status ===
                                                                  "tracking",
                                                              "text-emerald-500":
                                                                  bus.status ===
                                                                  "user_tracking",
                                                          }
                                                )}
                                            />
                                            {!gettingLiveData &&
                                                bus.status ===
                                                    "not_tracking" && (
                                                    <FontAwesomeIcon
                                                        icon={faSlash}
                                                        className="absolute top-0 left-0 w-5 h-5 text-red-500"
                                                    />
                                                )}
                                        </div>
                                    )}{" "}
                                </>
                            )}
                        </div>
                    </div>

                    <div className="flex items-center justify-center gap-1 p-1 ml-5 rounded-lg bg-neutral-800/50 w-15 min-w-fit h-fit">
                        <span className="text-sm font-bold text-nowrap">
                            {bus.status == "cancelled" ? "-" : bus.timeTo}
                        </span>
                    </div>
                </div>
            </div>
            {/* <Transition appear show={showExternalDialog} as={Fragment}>
                <Dialog
                    as="div"
                    className="relative z-50"
                    onClose={() => setShowExternalDialog(false)}>
                    <TransitionChild
                        as={Fragment}
                        enter="ease-out duration-200"
                        enterFrom="opacity-0"
                        enterTo="opacity-100"
                        leave="ease-in duration-150"
                        leaveFrom="opacity-100"
                        leaveTo="opacity-0">
                        <div className="fixed inset-0 bg-black/30" />
                    </TransitionChild>

                    <div className="fixed inset-0 flex items-center justify-center p-2">
                        <TransitionChild
                            as={Fragment}
                            enter="ease-out duration-200"
                            enterFrom="opacity-0 scale-95"
                            enterTo="opacity-100 scale-100"
                            leave="ease-in duration-150"
                            leaveFrom="opacity-100 scale-100"
                            leaveTo="opacity-0 scale-95">
                            <DialogPanel className="w-full max-w-sm p-4 text-center shadow-lg rounded-2xl bg-neutral-900">
                                <DialogTitle className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                    Leaving nextbus
                                </DialogTitle>
                                <Description className="mt-2 text-sm text-neutral-300">
                                    You're about to visit{" "}
                                    <span className="font-bold">
                                        bustimes.org
                                    </span>
                                    , which is an external website that is not
                                    part of nextbus.
                                </Description>

                                <div className="flex justify-center gap-3 mt-6">
                                    <button
                                        onClick={() =>
                                            setShowExternalDialog(false)
                                        }
                                        className="px-4 py-2 text-sm font-medium rounded-lg bg-neutral-700 hover:bg-neutral-600">
                                        Cancel
                                    </button>
                                    <button
                                        onClick={() => {
                                            if (externalUrl)
                                                window.open(
                                                    externalUrl,
                                                    "_blank"
                                                );
                                            setShowExternalDialog(false);
                                        }}
                                        className="px-4 py-2 text-sm font-medium rounded-lg cursor-pointer bg-primary hover:bg-primary-700">
                                        Continue
                                    </button>
                                </div>
                            </DialogPanel>
                        </TransitionChild>
                    </div>
                </Dialog>
            </Transition> */}
        </>
    );
}

function DepartureBoard({ stop_id, closest, filter }: Props) {
    const [buses, setBuses] = useState<Departure[]>([]);
    const [stop, setStop] = useState<BTStop>();
    const [stopID, setStopID] = useState<string>("");
    const [loading, setLoading] = useState(true);
    const [gettingLiveData, setGettingLiveData] = useState(true);
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
                        timeTo: timeTo(bus),
                    };
                })
                .filter(
                    (bus) =>
                        new Date(new Date(bus.expected).getTime() + 60 * 1000) >
                        now
                );

            setBuses(newBuses);
        }, 1000);
        return () => clearInterval(interval);
    }, [lastRefreshed, buses]);

    useEffect(() => {
        let interval: any;
        let ws: WebSocketManager | null = null;

        const getData = async (id: string) => {
            if (fetching) {
                return;
            }
            setFetching(true);
            try {
                const stopPromise = getStopData(id);
                const schedDeparturesPromise = fetchDepartures(
                    id,
                    "scheduled",
                    filter
                );

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
                    const closestStop = await getClosestStops([
                        pos.coords.latitude,
                        pos.coords.longitude,
                    ]);
                    stop_id = closestStop[0].stop_id;
                    if (!stop_id) {
                        setMsg("No stop found nearby");
                        setLoading(false);
                        setFetching(false);
                    }
                }
                setStopID(stop_id);

                await getData(stop_id);

                ws = WebSocketManager.getInstance(`stop/${stop_id}`);
                ws.clearCallbacks();
                ws.reconnect();
                ws.onOpen(() => {
                    console.log("WS connected");
                });

                ws.onMessage(async (msg) => {
                    if (msg.type === "departures") {
                        console.log("Got departures", msg.data);
                        const buses = await parseDepartures(msg.data, filter);

                        if (buses) {
                            setBuses(buses.updatedBuses);
                            setRefreshed(buses.timestamp);
                            setMsg("");
                            setLoading(false);
                            setGettingLiveData(false);
                        }
                    }
                });
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get location or stop data.");
                setLoading(false);
                setFetching(false);
            }
        };

        init(stop_id);

        return () => {
            clearInterval(interval);
            if (ws) {
                ws.clearCallbacks();
                ws.close();
            }
        };
    }, [stop_id, closest]);

    return (
        <div className="min-w-[350px] w-full sm:w-[25vw]">
            <Card>
                <div className="flex flex-col gap-2">
                    <div
                        className="flex flex-col justify-center gap-1 cursor-pointer"
                        onClick={() => navigate(`/buses/stops/${stopID}`)}>
                        {closest && (
                            <div className="flex items-center justify-center gap-1 px-1 bg-indigo-800 rounded-lg w-fit h-fit">
                                <span className="text-xs font-bold ">
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
                        <div className="flex items-center justify-center h-10 min-w-[300px]">
                            <span className="text-neutral-400">
                                Loading Buses...
                            </span>
                        </div>
                    ) : (
                        <>
                            <div className="">
                                <div className="flex flex-col overflow-y-auto max-h-[200px]">
                                    {msg ? (
                                        <div className="flex justify-center">
                                            <span className="text-red-400">
                                                {msg}
                                            </span>
                                        </div>
                                    ) : (
                                        <AnimatePresence>
                                            {buses.map((bus, idx) => (
                                                <motion.div
                                                    key={bus.trip}
                                                    layout
                                                    initial={{
                                                        opacity: 0,
                                                        y: 20,
                                                    }}
                                                    animate={{
                                                        opacity: 1,
                                                        y: 0,
                                                    }}
                                                    exit={{
                                                        opacity: 0,
                                                        y: -20,
                                                    }}
                                                    transition={{
                                                        type: "spring",
                                                        stiffness: 500,
                                                        damping: 40,
                                                    }}>
                                                    <BusCard
                                                        bus={bus}
                                                        gettingLiveData={
                                                            gettingLiveData
                                                        }
                                                    />
                                                    {idx !==
                                                        buses.length - 1 && (
                                                        <div className="flex items-center gap-2 mb-0.5">
                                                            <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                                            <span className="text-[10px] text-neutral-600">
                                                                nextbus
                                                            </span>
                                                            <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                                        </div>
                                                    )}
                                                </motion.div>
                                            ))}
                                            {buses.length === 0 ? (
                                                <div className="flex justify-center">
                                                    <span className="text-neutral-400">
                                                        No more departures!
                                                    </span>
                                                </div>
                                            ) : null}
                                        </AnimatePresence>
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
