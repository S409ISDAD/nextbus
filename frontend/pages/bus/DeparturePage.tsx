import { useEffect, useRef, useState } from "react";
import { getKey, isTrackedBus, type Departure } from "../../models/Bus";
import type { BTStop } from "../../models/Stop";
import fetchDepartures, {
    mostCommonDest,
    parseDepartures,
} from "../../utils/getDepartures";
import getStopData from "../../utils/getStopData";
import { useNavigate, useParams } from "react-router";
import { Skeleton } from "@radix-ui/themes";
import { Card } from "../../components/ui/Card";
import timeTo, { lateness, toTime } from "../../utils/timeUtils";
import { getClosestStops } from "../../utils/closestStop";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { motion, AnimatePresence } from "framer-motion";
import UsageManager from "../../usage/UsageManager";
import {
    faBus,
    faSatelliteDish,
    faSlash,
    faStar,
    faUpRightFromSquare,
    faWarning,
} from "@fortawesome/free-solid-svg-icons";
import { faStar as faStarRegular } from "@fortawesome/free-regular-svg-icons";
import clsx from "clsx";
import { WebSocketManager } from "../../websockets/ws_manager";
import getBus from "../../utils/getBus";
import type { Bus } from "../../models/Bus";
import useLocalStorageState from "use-local-storage-state";
import { useLocalSetting } from "../../src/settings";

// import {
//     Description,
//     Dialog,
//     DialogPanel,
//     DialogTitle,
//     Transition,
//     TransitionChild,
// } from "@headlessui/react";

const getBusDetail = async (bus: Departure) => {
    if (isTrackedBus(bus)) {
        const bus_response = await getBus(String(bus.id));
        return bus_response;
    }
};

export function formatBusType(bus: any, vegMode: boolean) {
    if (!vegMode) return bus.bus_type;

    const types = [bus.vehicle?.vehicle_type?.name, bus.bus_type]
        .filter(Boolean)
        .map((t) => t.replace(/(Double decker|Single decker),?/gi, "").trim())
        .filter(Boolean);

    return types.join(", ");
}

function BusCard({
    bus,
    stop_id,
    stop_name,
    stop_lat,
    stop_lon,
    usageManager,
    gettingLiveData,
    idx,
}: {
    bus: Departure;
    stop_id: string;
    stop_name: string;
    stop_lat: number;
    stop_lon: number;
    usageManager: Promise<UsageManager>;
    gettingLiveData: boolean;
    idx: number;
}) {
    const [busDetail, setBusDetail] = useState<Bus | null>(null);
    const [sequence, setSequence] = useState<number | null>(null);
    const [trackingBroken, setTrackingBroken] = useState(false);
    const [notLoggedOff, setNotLoggedOff] = useState(false);
    const [brokenDown, setBrokenDown] = useState(false);
    const [isOnDiversion, setIsOnDiversion] = useState(false);
    // const [showExternalDialog, setShowExternalDialog] = useState(false);
    // const [externalUrl, setExternalUrl] = useState<string | null>(null);
    const navigate = useNavigate();
    const [vegMode] = useLocalSetting("veg", false);

    useEffect(() => {
        let interval: ReturnType<typeof setInterval> | null = null;

        const fetchDetail = () => {
            if (idx === 0 && isTrackedBus(bus)) {
                getBusDetail(bus).then((detail) => {
                    if (detail) {
                        setBusDetail(detail);
                    }
                });
            }
        };

        fetchDetail();
        if (idx === 0 && isTrackedBus(bus)) {
            interval = setInterval(fetchDetail, 30000);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [idx === 0 && isTrackedBus(bus) ? bus.id : null]);

    const handleClick = async () => {
        if (
            isTrackedBus(bus) &&
            bus.status !== "on_prev_trip" &&
            bus.status !== "cancelled"
        ) {
            (await usageManager).logRoute(
                stop_id,
                stop_name,
                stop_lat,
                stop_lon,
                bus.service.id,
                bus.service.line_name,
                bus.service.description || "",
                bus.destination,
                "tracked"
            );
            navigate(`/buses/${bus.id}`);
        } else if (bus.db_journey) {
            navigate(`/buses/dbjourneys/${bus.db_journey}`);
        } else {
            navigate(`/buses/trips/${bus.trip}`);
        }
    };

    useEffect(() => {
        // Only fetch if idx is 0, isTrackedBus, and bus.id has changed
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
        if (
            idx === 0 &&
            isTrackedBus(bus) &&
            busDetail &&
            busDetail.predictions
        ) {
            const now = Date.now();
            const progressIdx = busDetail.predictions.findIndex(
                (p) => now < new Date(p.timestamp).getTime()
            );
            // If all timestamps are in the past, pick the last one
            const seq =
                progressIdx === -1
                    ? busDetail.predictions[busDetail.predictions.length - 1]
                          ?.sequence
                    : busDetail.predictions[Math.max(0, progressIdx - 1)]
                          ?.sequence;

            let adjustedSeq = seq;
            if (
                bus.target_seq !== undefined &&
                adjustedSeq !== undefined &&
                adjustedSeq !== null &&
                adjustedSeq >= bus.target_seq
            ) {
                adjustedSeq = bus.target_seq - 1;
            }
            setSequence(adjustedSeq ?? null);
        }
    }, [bus]);

    return (
        <>
            <div
                key={getKey(bus)}
                onClick={handleClick}
                className={clsx(
                    "cursor-pointer",
                    isTrackedBus(bus) &&
                        (bus.delay >= 2700 ||
                            trackingBroken ||
                            brokenDown ||
                            notLoggedOff ||
                            bus.status == "cancelled") &&
                        "opacity-75"
                )}>
                <div className="flex flex-row items-center justify-between gap-x-2">
                    <div className="flex flex-col justify-around gap-1">
                        <div className="flex flex-row items-stretch mb-1">
                            <div className="flex items-center px-3 py-1 bg-primary-700 rounded-l-2xl">
                                <span className="flex items-center justify-center text-xl font-bold text-center">
                                    {isTrackedBus(bus)
                                        ? bus.service.line_name
                                        : bus.line}
                                </span>
                            </div>
                            <div className="flex flex-col justify-center px-3 bg-neutral-800/50 rounded-r-2xl">
                                <span className="font-semibold text">
                                    {bus.destination}
                                </span>
                                {isTrackedBus(bus) && (
                                    <span className="mb-0.5 text-xs text-neutral-400">
                                        {formatBusType(bus, vegMode)}
                                    </span>
                                )}
                            </div>
                        </div>
                        {isTrackedBus(bus) &&
                            bus.delay >= 2700 &&
                            bus.status !== "cancelled" && (
                                <div className="flex items-center gap-1 text-xs ">
                                    <FontAwesomeIcon
                                        icon={faWarning}
                                        className="text-red-400"
                                    />
                                    This bus is quite late, it may not arrive.
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

                        <div className="flex flex-row items-center pl-2 font-semibold text gap-x-3 text-nowrap">
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
                                              expt > aimed && diff > 60000; // more than 1 min late
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
                                        <>
                                            {trackingBroken ? (
                                                <span className="text-sm font-medium opacity-70">
                                                    no data
                                                </span>
                                            ) : (
                                                <span
                                                    className={`text-${
                                                        bus.delay >= 60
                                                            ? "red"
                                                            : "green"
                                                    }-400`}>
                                                    {lateness(
                                                        bus ? bus.delay : 0
                                                    )}
                                                </span>
                                            )}
                                        </>
                                    )}
                                    {!bus.started && (
                                        <span
                                            className="text-sm font-medium opacity-70"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                isTrackedBus(bus) &&
                                                bus.status == "on_prev_trip"
                                                    ? navigate(
                                                          `/buses/${bus.id}`
                                                      )
                                                    : null;
                                            }}>
                                            {bus.status === "not_tracking"
                                                ? "Upcoming"
                                                : bus.status === "waiting"
                                                ? "Not Started"
                                                : "On prev. trip"}
                                        </span>
                                    )}
                                    {bus.started && !trackingBroken && (
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
                                    )}
                                </>
                            )}
                        </div>
                    </div>

                    <div className="flex flex-row flex-wrap items-center justify-end gap-2 md:gap-4 w-min md:w-auto">
                        {isTrackedBus(bus) && vegMode && (
                            <div className="flex justify-center px-2 py-1 rounded-lg bg-amber-400">
                                <span className="text-xs font-bold align-middle text-neutral-950 text-nowrap">
                                    {bus.vehicle.reg}
                                </span>
                            </div>
                        )}

                        <div className="flex items-center justify-center gap-1 p-[0.3rem] min-w-18 rounded-xl bg-neutral-800/50 h-fit">
                            {bus.status == "cancelled" ? (
                                <span className="text-lg font-bold text-nowrap">
                                    -
                                </span>
                            ) : (
                                <>
                                    {" "}
                                    <span className="text-lg font-bold text-nowrap">
                                        {bus.timeTo.split(" ")[0]}
                                    </span>
                                    <span className="self-end h-full mb-[0.15rem] text-sm font-bold ">
                                        {bus.timeTo.split(" ")[1]}
                                    </span>
                                </>
                            )}
                        </div>
                    </div>
                </div>
                <AnimatePresence>
                    {busDetail &&
                        idx === 0 &&
                        isTrackedBus(bus) &&
                        bus.target_seq !== undefined &&
                        sequence !== null &&
                        bus.status !== "cancelled" &&
                        (() => {
                            const startIdx = Math.max(0, bus.target_seq! - 5);
                            const endIdx = bus.target_seq! + 2;
                            const stopsSlice = busDetail.journey.stops.slice(
                                startIdx,
                                endIdx
                            );
                            return (
                                bus.target_seq - sequence <
                                    stopsSlice.length - 1 && (
                                    <motion.div
                                        key={`stop-sequence-${bus.id}`}
                                        className="flex flex-row items-center justify-center gap-1 p-3 pt-7 flex-nowrap overflow-clip lg:absolute lg:left-1/2 lg:-translate-x-1/2 lg:-translate-y-17"
                                        initial={{ opacity: 0, y: -10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        transition={{
                                            type: "spring",
                                            stiffness: 400,
                                            damping: 40,
                                        }}>
                                        {stopsSlice.map((_, index) => {
                                            const actualIndex =
                                                startIdx + index;
                                            return (
                                                <div
                                                    key={actualIndex}
                                                    className="flex items-center gap-1">
                                                    {actualIndex ===
                                                        sequence + 1 && (
                                                        <motion.div
                                                            layout
                                                            key={`bus-${bus.id}-${sequence}`} // unique for position changes
                                                            className="absolute translate-x-[-31px] flex items-center justify-center"
                                                            initial={{
                                                                x: -30,
                                                                opacity: 0,
                                                            }}
                                                            animate={{
                                                                x: 0,
                                                                opacity: 1,
                                                            }}
                                                            exit={{
                                                                x: 30,
                                                                opacity: 0,
                                                            }}
                                                            transition={{
                                                                type: "tween",
                                                                stiffness: 500,
                                                                damping: 40,
                                                            }}>
                                                            <span className="absolute text-xs translate-y-[-23px] text-nowrap text-neutral-400">
                                                                {bus.target_seq !==
                                                                    undefined &&
                                                                sequence !==
                                                                    null
                                                                    ? (() => {
                                                                          const stopsAway =
                                                                              bus.target_seq -
                                                                              sequence -
                                                                              1;
                                                                          if (
                                                                              stopsAway ===
                                                                              0
                                                                          )
                                                                              return "next stop";
                                                                          if (
                                                                              stopsAway ===
                                                                              1
                                                                          )
                                                                              return "1 stop away";
                                                                          if (
                                                                              stopsAway >
                                                                              1
                                                                          )
                                                                              return `${stopsAway} stops away`;
                                                                          return "Stop info unavailable";
                                                                      })()
                                                                    : "Stop info unavailable"}
                                                            </span>
                                                            <div className="z-10 flex items-center justify-center w-6 h-6 p-1 rounded-full bg-rose-500">
                                                                <FontAwesomeIcon
                                                                    icon={faBus}
                                                                    className="text-[0.8rem]"
                                                                />
                                                            </div>
                                                        </motion.div>
                                                    )}
                                                    <div
                                                        className={clsx(
                                                            "w-2 h-2 rounded-full",
                                                            actualIndex ===
                                                                bus.target_seq
                                                                ? "bg-link"
                                                                : "bg-neutral-600"
                                                        )}></div>
                                                    {index <
                                                        stopsSlice.length -
                                                            1 && (
                                                        <div className="min-w-[30px] bg-neutral-700 flex-1 h-[2px]"></div>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </motion.div>
                                )
                            );
                        })()}
                </AnimatePresence>
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

const DeparturePage: React.FC = () => {
    const { stop_id } = useParams();
    const params = new URLSearchParams(window.location.search);
    var filter = params.get("filter");

    const navigate = useNavigate();

    const firstFetch = useRef(true);

    const [buses, setBuses] = useState<Departure[]>([]);
    const [stop, setStop] = useState<BTStop>();
    const [closestStop, setClosest] = useState<string>();
    const [loading, setLoading] = useState(true);
    const [gettingLiveData, setGettingLiveData] = useState(true);
    const [fetching, setFetching] = useState(false);
    const [lastRefreshed, setRefreshed] = useState(new Date());
    const [elapsed, setElapsed] = useState<string>("0s");
    const [msg, setMsg] = useState<string>("");
    const usageManager = UsageManager.getInstance();

    const [favStops, setFavStops] = useLocalStorageState<
        Record<string, [number, number]>
    >("favStops", {
        defaultValue: {},
    });
    const isFav = !!favStops[stop_id || ""];

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
            setGettingLiveData(true);
            try {
                const stopPromise = getStopData(id);
                const schedDeparturesPromise = fetchDepartures(id, "scheduled");

                if (firstFetch.current) {
                    const stopData = await stopPromise;

                    if (stopData) {
                        setStop(stopData);
                        document.title = stopData.name;

                        (await usageManager).logStop(
                            stopData.stop_id,
                            stopData.name,
                            stopData.coords[0],
                            stopData.coords[1],
                            isFav,
                            "tapped"
                        );

                        const closestStop = await getClosestStops(
                            stopData.coords,
                            stop_id
                        );
                        setClosest(closestStop[0].stop_id);
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
                setLoading(false);
                setFetching(false);
            }
        };
        const init = async (stop_id: string) => {
            try {
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
                        const buses = await parseDepartures(msg.data);

                        if (buses) {
                            setBuses(buses.updatedBuses);
                            setRefreshed(buses.timestamp);
                            setMsg("");
                            setGettingLiveData(false);
                            setLoading(false);
                        }
                    }
                });
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

        return () => {
            clearInterval(interval);
            if (ws) {
                ws.clearCallbacks();
                ws.close();
            }
        };
    }, [stop_id]);

    return (
        <div className="p-5 md:mx-20">
            <div className="flex flex-col gap-4">
                <div className="flex flex-col items-center justify-center gap-3">
                    <span className="text-3xl font-bold text-center md:text-4xl">
                        {stop?.name}{" "}
                        {stop?.indicator
                            ? `(${stop.indicator})`
                            : stop?.bearing
                            ? `(${stop.bearing})`
                            : ""}
                    </span>
                    <div className="flex flex-wrap items-center justify-center gap-2 gap-y-1">
                        {closestStop && (
                            <div
                                className="flex items-center gap-2 p-2 cursor-pointer bg-neutral-800/50 w-fit rounded-2xl"
                                onClick={() => {
                                    setBuses([]);
                                    setLoading(true);
                                    firstFetch.current = true;
                                    navigate(`/buses/stops/${closestStop}`);
                                }}>
                                Nearest Stop{" "}
                                <FontAwesomeIcon
                                    icon={faUpRightFromSquare}
                                    width="20px"></FontAwesomeIcon>
                            </div>
                        )}

                        <div
                            className="flex items-center gap-2 p-2 cursor-pointer bg-neutral-800/50 w-fit rounded-2xl"
                            onClick={() => {
                                if (!stop_id || !stop?.coords) return;
                                if (isFav) {
                                    setFavStops((prev) => {
                                        const updated = { ...prev };
                                        delete updated[stop_id];
                                        return updated;
                                    });
                                } else {
                                    setFavStops((prev) => ({
                                        ...prev,
                                        [stop_id]: stop.coords as [
                                            number,
                                            number
                                        ],
                                    }));
                                }
                            }}>
                            {isFav ? "Favourited" : "Favourite"}{" "}
                            <FontAwesomeIcon
                                icon={isFav ? faStar : faStarRegular}
                            />
                        </div>
                        <a
                            className="underline text-link"
                            href={`https://bustimes.org/stops/${stop?.stop_id}`}
                            target="_blank">
                            View on bustimes.org
                        </a>

                        {/* <a
                            className="px-2 py-1 text-neutral-400 border-1 rounded-xl border-neutral-800 bg-neutral-900"
                            href={`/departureboard/${stop?.stop_id}`}>
                            board
                        </a> */}
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <div className="inline-flex justify-center min-w-full gap-1">
                        {stop?.services
                            .sort((a, b) =>
                                new Intl.Collator(undefined, {
                                    numeric: true,
                                    sensitivity: "base",
                                }).compare(a.line_name, b.line_name)
                            )
                            .map((service) =>
                                service.line_name === filter ? (
                                    <span
                                        key={service.id}
                                        className="flex items-center justify-center px-3 py-1 text-lg font-bold text-center border-2 cursor-pointer rounded-xl bg-emerald-900/50 border-emerald-800"
                                        onClick={() => {
                                            filter = null;
                                            navigate(`/buses/stops/${stop_id}`);
                                        }}>
                                        {service.line_name}
                                    </span>
                                ) : (
                                    <span
                                        key={service.id}
                                        className="flex items-center justify-center px-3 py-1 text-lg font-bold text-center cursor-pointer rounded-xl bg-neutral-800/50"
                                        onClick={async () => {
                                            filter = service.line_name;
                                            if (stop && buses.length > 0) {
                                                const dest = mostCommonDest(
                                                    buses,
                                                    filter
                                                );
                                                (await usageManager).logRoute(
                                                    stop.stop_id,
                                                    stop.name,
                                                    stop.coords[0],
                                                    stop.coords[1],
                                                    service.id,
                                                    service.line_name,
                                                    service.description || "",
                                                    dest,
                                                    "filter"
                                                );
                                            }
                                            navigate(
                                                `/buses/stops/${stop_id}?filter=${service.line_name}`
                                            );
                                        }}>
                                        {service.line_name}
                                    </span>
                                )
                            )}
                    </div>
                </div>

                <div className="flex justify-center gap-2">
                    <span className="text-xs text-neutral-400">
                        {loading ? "Loading..." : `Updated ${elapsed} ago`}
                    </span>
                    <span className="text-xs text-neutral-400">·</span>
                    <span className="text-xs text-neutral-400">
                        Updates every 20s
                    </span>
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
                        <AnimatePresence>
                            {buses
                                .filter(
                                    (bus) =>
                                        !filter || // no filter
                                        (isTrackedBus(bus)
                                            ? bus.service.line_name === filter
                                            : bus.line === filter)
                                )
                                .map((bus, idx) => (
                                    <motion.div
                                        key={getKey(bus)}
                                        layout // enables smooth reordering animations
                                        initial={{ opacity: 0, y: 20 }} // entry animation
                                        animate={{ opacity: 1, y: 0 }} // while present
                                        exit={{ opacity: 0, y: -20 }} // exit animation
                                        transition={{
                                            type: "spring",
                                            stiffness: 500,
                                            damping: 40,
                                        }}>
                                        <div className="flex items-center gap-2 mb-0.5">
                                            <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                            <span className="text-[10px] text-neutral-600">
                                                nextbus
                                            </span>
                                            <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                        </div>

                                        <BusCard
                                            bus={bus}
                                            stop_id={stop_id!}
                                            stop_name={stop?.name || ""}
                                            stop_lat={stop?.coords[0] || 0}
                                            stop_lon={stop?.coords[1] || 0}
                                            usageManager={usageManager}
                                            gettingLiveData={gettingLiveData}
                                            idx={idx}
                                        />
                                        {idx === buses.length - 1 && (
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
                            {buses.filter(
                                (bus) =>
                                    !filter ||
                                    (isTrackedBus(bus)
                                        ? bus.service.line_name === filter
                                        : bus.line === filter)
                            ).length === 0 && (
                                <div className="flex justify-center">
                                    <span className="text-neutral-400">
                                        No more departures!
                                    </span>
                                </div>
                            )}
                        </AnimatePresence>
                    )}
                </div>
            </div>
        </div>
    );
};

export default DeparturePage;
