import { useEffect, useRef, useState } from "react";
import type { LiveJourney } from "../../models/Journey";
import getBus from "../../utils/getBus";
import { useNavigate, useParams } from "react-router";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { lateness, toTime } from "../../utils/timeUtils";
import { generateWholeTrack, type Latlon } from "../../utils/locations";
import {
    faBus,
    faCalendarCheck,
    faCalendarXmark,
    faWarning,
} from "@fortawesome/free-solid-svg-icons";
import type { Bus, Prediction } from "../../models/Bus";
import {
    Map as MapGL,
    Marker,
    Popup,
    NavigationControl,
    Source,
    Layer,
    type MapRef,
} from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import { useShowAppNav } from "../../utils/AppNav";

type MapInfoProps = {
    text: string;
    color?: string;
};

const MapInfo: React.FC<MapInfoProps> = ({ text, color = "black" }) => {
    return (
        <div
            className="absolute px-2 py-1 text-sm rounded-md shadow bottom-2 left-2 bg-bg-medium"
            style={{ color }}>
            {text}
        </div>
    );
};

type MapViewProps = {
    lat: number;
    lon: number;
    bus: Bus;
    accuracy: "high" | "med" | "low" | "unknown";
    track: Latlon[];
};
import React from "react";
import { Pulse } from "../../components/ui/Pulse";

const MapView: React.FC<MapViewProps> = ({
    lat,
    lon,
    bus,
    accuracy,
    track = [],
}) => {
    const [popup, setPopup] = React.useState<{
        coords: Latlon;
        content: React.ReactNode;
    } | null>(null);

    const mapRef = React.useRef<MapRef | null>(null);

    React.useEffect(() => {
        if (
            mapRef.current &&
            lat !== 0 &&
            lon !== 0 &&
            !mapRef.current.isMoving() &&
            !mapRef.current.isZooming()
        ) {
            mapRef.current.flyTo({
                center: [lon, lat],
                zoom:
                    mapRef.current.getZoom() < 9 ? 9 : mapRef.current.getZoom(),
                bearing: 0,
                duration: 500,
                essential: false,
            });
        }
    }, [lat, lon]);

    const accuracyColor =
        accuracy === "high"
            ? "limegreen"
            : accuracy === "med"
            ? "darkorange"
            : "red";
    return (
        <div className="relative w-[100vw] h-[200px]">
            <MapGL
                ref={mapRef}
                initialViewState={{
                    longitude: lon,
                    latitude: lat,
                    zoom: 14,
                }}
                attributionControl={false}
                mapStyle="https://tiles.stadiamaps.com/styles/alidade_smooth_dark.json"
                // mapStyle={{
                //     version: 8,
                //     sources: {
                //         osm: {
                //             type: "raster",
                //             tiles: [
                //                 "https://tile-a.openstreetmap.fr/hot/{z}/{x}/{y}.png",
                //                 "https://tile-b.openstreetmap.fr/hot/{z}/{x}/{y}.png",
                //                 "https://tile-c.openstreetmap.fr/hot/{z}/{x}/{y}.png",
                //             ],
                //             tileSize: 256,
                //             attribution:
                //                 '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                //         },
                //     },
                //     layers: [
                //         {
                //             id: "osm",
                //             type: "raster",
                //             source: "osm",
                //             minzoom: 0,
                //             maxzoom: 19,
                //         },
                //     ],
                // }}
                style={{ width: "100%", height: "100%" }}>
                <NavigationControl position="top-right" />

                <Marker longitude={lon} latitude={lat} anchor="center">
                    <div className="flex items-center justify-center w-6 h-6 rounded-full shadow-lg bg-rose-600">
                        <i className="text-xs text-white fas fa-bus" />
                    </div>
                </Marker>
                {bus.journey.stops.map((stop) => (
                    <Marker
                        key={stop.stop_id}
                        longitude={stop.coords[1]}
                        latitude={stop.coords[0]}
                        anchor="center"
                        onClick={(e) => {
                            e.originalEvent.stopPropagation();
                            setPopup({
                                coords: [stop.coords[1], stop.coords[0]],
                                content: (
                                    <div className="flex flex-col text-white bg-[#222]">
                                        <a
                                            className="font-semibold"
                                            href={`/buses/stops/${stop.stop_id}`}>
                                            {stop.name}
                                        </a>
                                        <span className="text-xs opacity-80">
                                            Expt:{" "}
                                            {stop.expt_time
                                                ? new Date(
                                                      stop.expt_time
                                                  ).toLocaleTimeString([], {
                                                      hour: "2-digit",
                                                      minute: "2-digit",
                                                  })
                                                : "-"}
                                        </span>
                                    </div>
                                ),
                            });
                        }}>
                        <div className="text-primary-500">
                            <i className="fas fa-circle text-[12px]" />
                        </div>
                    </Marker>
                ))}

                {track.length > 0 && (
                    <Source
                        id="track"
                        type="geojson"
                        data={{
                            type: "Feature",
                            geometry: {
                                type: "LineString",
                                coordinates: track.map((p) => [p[1], p[0]]),
                            },
                            properties: {},
                        }}>
                        <Layer
                            id="track-line"
                            type="line"
                            paint={{
                                "line-color": "white",
                                "line-width": 4,
                                "line-opacity": 0.7,
                            }}
                        />
                    </Source>
                )}

                {popup && (
                    <Popup
                        longitude={popup.coords[0]}
                        latitude={popup.coords[1]}
                        closeOnClick={true}
                        anchor="top"
                        onClose={() => setPopup(null)}>
                        {popup.content}
                    </Popup>
                )}
            </MapGL>

            <MapInfo text={`Accuracy: ${accuracy}`} color={accuracyColor} />
        </div>
    );
};

export const BusProgress: React.FC<{
    sequence: number;
    progress: number;
    busRef: React.RefObject<HTMLDivElement | null>;
}> = React.memo(({ sequence, progress, busRef }) => {
    const sectionLength = 72;
    const translateY = (sequence + progress) * sectionLength;
    const showAppNav = useShowAppNav();

    return (
        <div className="absolute top-0 left-0 h-full mt-[15px] z-11 w-9">
            <div
                className="absolute transition-all duration-500 ease-in-out translate-x-[-16px]"
                style={{ transform: `translateY(${translateY}px)` }}>
                <div className="relative flex items-center justify-center">
                    <Pulse size={34} color="bg-rose-400" duration={2} />
                    <div className="relative z-10 flex items-center justify-center p-2 text-white rounded-full bg-rose-500 w-9 h-9">
                        <FontAwesomeIcon icon={faBus} />
                        <div
                            style={{
                                position: "absolute",
                                top: showAppNav ? "0px" : "-50px",
                                left: 0,
                                width: "100%",
                                height: 0,
                            }}>
                            <div ref={busRef}></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
});

const LiveJourneyPage: React.FC = () => {
    const { bus_id } = useParams();

    const navigate = useNavigate();

    const [bus, setBus] = useState<Bus>();
    const [predictions, setPredictions] = useState<Prediction[]>();
    const [sequence, setSeq] = useState<number>(0);
    const [progress, setProg] = useState<number>(0);
    const [location, setLoc] = useState<number[]>([0, 0]);
    const [accuracy, setAccuracy] = useState<
        "high" | "med" | "low" | "unknown"
    >("unknown");
    const [liveJourney, setLiveJourney] = useState<LiveJourney>();
    const [loading, setLoading] = useState(true);
    const [fetching, setFetching] = useState(false);
    const [lastRefreshed, setRefreshed] = useState(new Date());
    const [elapsed, setElapsed] = useState<string>("0s");
    const [msg, setMsg] = useState<string>("");
    const [busInfoHeight, setBusInfoHeight] = useState(0);
    const busInfoRef = useRef<HTMLDivElement>(null);
    const showAppNav = useShowAppNav();

    useEffect(() => {
        if (busInfoRef.current) {
            setBusInfoHeight(busInfoRef.current.clientHeight);
        }
    }, [busInfoRef, loading]);

    useEffect(() => {
        const interval = setInterval(() => {
            const now = new Date();
            const diffSec = Math.floor(
                (now.getTime() - lastRefreshed.getTime()) / 1000
            );
            const min = Math.floor(diffSec / 60);
            const sec = diffSec % 60;

            setElapsed(min > 0 ? `${min}m ${sec}s` : `${sec}s`);

            if (bus?.timestamp) {
                const age = Math.floor(
                    (now.getTime() - new Date(bus?.timestamp).getTime()) / 1000
                );
                let accuracy: "high" | "med" | "low" | "unknown" = "unknown";

                if (age <= 45) {
                    accuracy = "high";
                } else if (age <= 90) {
                    accuracy = "med";
                } else {
                    accuracy = "low";
                }

                setAccuracy(accuracy);
            }
        }, 1000);
        return () => clearInterval(interval);
    }, [lastRefreshed]);

    useEffect(() => {
        const interval = setInterval(() => {
            const now = new Date();

            if (!predictions || predictions.length < 2) {
                if (bus?.started) {
                    setSeq(bus?.progress ? bus.progress.sequence : 0);
                    setProg(bus?.progress ? bus.progress.progress : 0);
                } else {
                    setSeq(0);
                    setProg(0);
                }
                const lat = bus?.coords?.[1] ?? 0;
                const lon = bus?.coords?.[0] ?? 0;
                setLoc([lat, lon]);
                return;
            }

            const upcoming = predictions.find((pred) => {
                const nextTime = new Date(pred.timestamp);
                return nextTime > now;
            });

            if (!upcoming) return;

            const idx = predictions.indexOf(upcoming);

            const prev = predictions[idx - 1];

            const newProgress = upcoming.progress;
            const prevProgress = prev.progress;

            const newCoords = upcoming.location;
            const prevCoords = prev.location;

            const progressDelta = newProgress - prevProgress;

            const timeDelta =
                new Date(upcoming.timestamp).getTime() - now.getTime();
            const predictionDuration =
                (new Date(upcoming.timestamp).getTime() -
                    new Date(prev.timestamp).getTime()) *
                1000;

            const interpolatedProgress =
                prevProgress +
                -Math.abs(progressDelta * -(timeDelta / predictionDuration));

            setProg(interpolatedProgress);

            setSeq(upcoming.sequence);

            const latDelta = newCoords[0] - prevCoords[0];
            const lonDelta = newCoords[1] - prevCoords[1];

            const lat =
                prevCoords[0] + latDelta * (-timeDelta / predictionDuration);

            const lon =
                prevCoords[1] + lonDelta * (-timeDelta / predictionDuration);

            setLoc([lat, lon]);
        }, 200);
        return () => clearInterval(interval);
    }, [predictions]);

    const busRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (liveJourney && busRef.current) {
            requestAnimationFrame(() => {
                busRef.current?.scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                });
            });
        }
    }, [sequence, liveJourney]);

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
                    setLiveJourney(bus_response.journey);
                    document.title = `${bus_response.journey.route_name} to ${bus_response.journey.destination} - ${bus_response.reg}`;
                    setMsg("");
                    setRefreshed(now);
                    setTimeout(() => {
                        requestAnimationFrame(() => {
                            busRef.current?.scrollIntoView({
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
        <div className="flex flex-col">
            <div
                className={`flex flex-col gap-2 top-0 grow px-5 pb-1 z-12 bg-bg-main rounded-b-2xl fixed w-full ${
                    !showAppNav ? "pt-15" : ""
                }`}
                ref={busInfoRef}>
                {bus ? (
                    <div className="flex flex-col items-center justify-center gap-2">
                        <div
                            className={`fixed flex flex-row items-stretch p-2 px-3 my-1 mb-1 z-10000000 ${
                                !showAppNav ? "top-15" : "top-0"
                            }`}>
                            <div className="flex items-center px-3 py-1 bg-primary-700 rounded-l-2xl">
                                <span className="flex items-center justify-center text-xl font-bold text-center text-white">
                                    {bus.service.line_name}
                                </span>
                            </div>
                            <div className="flex flex-col justify-center px-3 py-1 bg-bg-light rounded-r-2xl">
                                <span className="font-semibold text">
                                    {bus.destination}
                                </span>

                                <span className="mb-0.5 text-xs text-text-light">
                                    {bus.bus_type}
                                </span>
                            </div>
                        </div>
                        <MapView
                            lat={location[0]}
                            lon={location[1]}
                            bus={bus}
                            accuracy={accuracy}
                            track={generateWholeTrack(
                                bus.journey?.stops
                            )}></MapView>
                        <div className="flex gap-3">
                            <a
                                className="underline text-link"
                                href={`https://bustimes.org/vehicles/${bus?.id}#journeys/${bus?.journey_id}`}
                                target="_blank">
                                View on bustimes.org
                            </a>
                            <span className="text-center">
                                {liveJourney?.stops.length} stops
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
                                <span className="text-xs font-bold text-center">
                                    {bus.livery
                                        ? bus?.livery.name
                                        : "No livery"}
                                </span>
                                <div
                                    className="rounded shadow-2xl w-15 aspect-3/2"
                                    style={{
                                        background:
                                            bus?.livery?.right_css ||
                                            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 200' fill='none' xmlns:xlink='http://www.w3.org/1999/xlink'><rect width='300' height='200' fill='%23222222'/><text x='150' y='110' text-anchor='middle' fill='%23999999' font-size='80' font-family='sans-serif' dy='.35em'>?</text></svg>\")",
                                    }}></div>
                            </div>

                            <div className="flex justify-center px-2 py-1 rounded-lg bg-bg-light/50">
                                <span className="font-bold align-middle text">
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
                    <span className="text-center text-red">{msg}</span>
                ) : (
                    <></>
                )}
                <div className="flex items-center justify-center gap-2 text-sm text-neutral-500">
                    <div className="w-2 h-2 rounded-full bg-link"></div> =
                    timing point (bus waits here if early)
                </div>
                <div className="flex justify-center gap-2">
                    <span className="text-xs text-text-light">
                        Updated {elapsed} ago
                    </span>
                    <span className="text-xs text-text-light">·</span>
                    <span className="text-xs text-text-light">
                        Updates every 30s
                    </span>
                </div>
            </div>
            <div
                style={{
                    marginTop: busInfoHeight - (showAppNav ? 0 : 50),
                }}>
                {bus?.finished || !bus ? (
                    <div className="flex flex-col gap-3 mt-4 grow h-[60vh] md:max-h-[80vh] items-center justify-center">
                        <FontAwesomeIcon
                            icon={faCalendarXmark}
                            size="5x"
                            className="text-text-light"></FontAwesomeIcon>
                        <span className="text-xl font-bold text-neutral-500">
                            This service has ended.
                        </span>
                    </div>
                ) : (
                    <div className="flex flex-row gap-2 px-3 md:px-0">
                        <div className="relative flex mx-5 md:mx-40">
                            <div className="relative flex flex-col items-center py-8">
                                <BusProgress
                                    sequence={sequence}
                                    progress={progress}
                                    busRef={busRef}></BusProgress>
                                {liveJourney?.stops.map((stop, idx) => (
                                    <div
                                        key={stop.stop_id}
                                        className="relative flex flex-col items-center">
                                        <div
                                            className={`z-10 w-1 h-1 bg-neutral-700 ${
                                                idx == 0
                                                    ? "rounded-tl-full"
                                                    : idx ==
                                                      liveJourney.stops.length -
                                                          1
                                                    ? "rounded-bl-full"
                                                    : ""
                                            }`}></div>
                                        {/* {stop.timing_status === "PTP" && (
                                            <div className="absolute z-10 w-3 h-3 translate-y-[-30%] rounded-full bg-neutral-700 flex items-center justify-center"></div>
                                        )} */}
                                        {idx < liveJourney.stops.length - 1 && (
                                            <div className="w-[4px] bg-neutral-700 flex-1 min-h-[68px]"></div>
                                        )}
                                    </div>
                                ))}
                            </div>
                            <div className="flex flex-col gap-1">
                                {liveJourney?.stops.map((stop) => (
                                    <div
                                        key={stop.stop_id}
                                        className="flex flex-row items-center">
                                        <div
                                            className={`w-4 bg-neutral-700 rounded-r-full h-[4px]`}></div>
                                        <div
                                            className="p-2 w-fit h-17"
                                            onClick={() =>
                                                navigate(
                                                    `/buses/stops/${stop.stop_id}`
                                                )
                                            }
                                            style={{
                                                cursor: "pointer",
                                            }}>
                                            <div
                                                className={`flex items-stretch flex-col ${
                                                    stop.departed
                                                        ? "opacity-40"
                                                        : ""
                                                }`}>
                                                {/* <span className="px-2 py-1 font-bold bg-indigo-800 rounded-t-2xl">
                                                    {stop.name}
                                                </span> */}
                                                <div className="flex flex-row items-center gap-2 font-bold">
                                                    {stop.timing_status ===
                                                        "PTP" && (
                                                        <div className="w-2 h-2 rounded-full bg-link"></div>
                                                    )}{" "}
                                                    {stop.name}
                                                </div>
                                                {/* <div className="flex flex-row gap-6 px-2 py-1 font-bold bg-bg-light/50 rounded-b-2xl">
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
                                                        <span className="font-bold text-primary-400">
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
                                                        <span className="font-bold text-green ">
                                                            On Time
                                                        </span>
                                                    )}
                                                </div> */}
                                                <div className="flex flex-row gap-6 font-bold text-purple-500">
                                                    {stop.departed ? (
                                                        <div className="flex items-center gap-2">
                                                            <FontAwesomeIcon
                                                                icon={
                                                                    faCalendarCheck
                                                                }
                                                            />
                                                            <span className="text-text-dark">
                                                                {toTime(
                                                                    stop.aimed_time
                                                                )}
                                                            </span>
                                                            <span className="font-semibold text-green">
                                                                departed
                                                            </span>
                                                        </div>
                                                    ) : (
                                                        <div className="flex items-center gap-2">
                                                            {stop.expt_time &&
                                                            stop.aimed_time
                                                                ? (() => {
                                                                      const aimed =
                                                                          new Date(
                                                                              stop.aimed_time
                                                                          ).getTime();
                                                                      const expt =
                                                                          new Date(
                                                                              stop.expt_time
                                                                          ).getTime();
                                                                      const diff =
                                                                          Math.abs(
                                                                              expt -
                                                                                  aimed
                                                                          );
                                                                      const isLate =
                                                                          expt >
                                                                              aimed &&
                                                                          diff >
                                                                              60000;
                                                                      return (
                                                                          <div className="flex gap-3">
                                                                              {isLate && (
                                                                                  <span className="line-through text-text-light">
                                                                                      {toTime(
                                                                                          stop.aimed_time
                                                                                      )}
                                                                                  </span>
                                                                              )}
                                                                              <span
                                                                                  className={
                                                                                      isLate
                                                                                          ? "text-red"
                                                                                          : "text-green"
                                                                                  }>
                                                                                  {isLate
                                                                                      ? "expt: "
                                                                                      : ""}
                                                                                  {toTime(
                                                                                      stop.expt_time
                                                                                  )}
                                                                              </span>
                                                                          </div>
                                                                      );
                                                                  })()
                                                                : "-"}
                                                        </div>
                                                    )}
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

export default LiveJourneyPage;
