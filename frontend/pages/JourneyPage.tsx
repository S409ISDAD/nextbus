import { useEffect, useRef, useState } from "react";
import type { Journey } from "../models/Journey";
import getBus from "../utils/getBus";
import { useNavigate, useParams } from "react-router";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { lateness } from "../utils/timeTo";
import generateWholeTrack from "../utils/locations";
import {
    faBus,
    faCalendarXmark,
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

const LocateControlComponent: React.FC<{ busLatLng: LatLngExpression }> = ({
    busLatLng,
}) => {
    const map = useMap();

    useEffect(() => {
        // @ts-ignore
        const locateControl = new LocateControl({
            position: "topright",
            showPopup: false,
            strings: {
                title: "Show me where I am",
            },
            setView: false, // Don't auto-center
        });
        locateControl.addTo(map);

        const onLocationFound = (e: any) => {
            const userLatLng = e.latlng;
            const bounds = L.latLngBounds([userLatLng, busLatLng]);
            map.fitBounds(bounds, { padding: [50, 50] });
        };

        map.on("locationfound", onLocationFound);

        return () => {
            locateControl.remove();
            map.off("locationfound", onLocationFound);
        };
    }, [map, busLatLng]);

    return null;
};

const ResetZoomControl: React.FC = () => {
    const map = useMap();

    useEffect(() => {
        const control = L.Control.extend({
            options: { position: "topright" },
            onAdd: function () {
                const container = L.DomUtil.create("div", "leaflet-bar");

                const link = L.DomUtil.create("a", "", container);
                link.innerHTML = "<i class='fa-solid fa-magnifying-glass'></i>";
                link.href = "#";
                link.title = "Reset Zoom";

                L.DomEvent.on(link, "click", L.DomEvent.stopPropagation)
                    .on(link, "click", L.DomEvent.preventDefault)
                    .on(link, "click", () => {
                        map.setZoom(15);
                    });

                return container;
            },
        });

        const instance = new control();
        instance.addTo(map);

        return () => {
            instance.remove();
        };
    }, [map]);

    return null;
};

type MapInfoProps = {
    text: string;
    style?: React.CSSProperties;
};

const MapInfo: React.FC<MapInfoProps> = ({ text, style }) => {
    const map = useMap();

    useEffect(() => {
        const infoControl = new L.Control({ position: "bottomright" });

        infoControl.onAdd = () => {
            const container = L.DomUtil.create("div", "leaflet-bar");

            const link = L.DomUtil.create("a", "", container);
            link.innerHTML = text;
            link.style.width = "100%";
            link.style.padding = "0 5px 0 5px";
            link.style.color = style?.color || "black";
            return container;
        };

        infoControl.addTo(map);

        return () => {
            infoControl.remove();
        };
    }, [map, text, style]);

    return null;
};

type MapViewProps = {
    lat: number;
    lng: number;
    bus: Bus;
    accuracy: string;
    track: LatLngExpression[];
};

const MapCenterUpdater: React.FC<{ lat: number; lng: number }> = ({
    lat,
    lng,
}) => {
    const map = useMap();

    useEffect(() => {
        map.setView([lat, lng]);
    }, [lat, lng, map]);

    return null;
};

import L, { type LatLngExpression } from "leaflet";

const busIcon = L.divIcon({
    html: `<div style="
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #f87171;
    border-radius: 9999px;
    width: 24px;
    height: 24px;
  ">
    <i class="fas fa-bus" style="color: white; font-size: 12px;"></i>
  </div>`,
    className: "",
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12],
});

const pinIcon = L.divIcon({
    html: `<i class="fas fa-circle"></i>`,
    className: "text-blue-500",
    iconSize: [12, 12],
    iconAnchor: [12, 12],
    popupAnchor: [-6, -6],
});

const MapView: React.FC<MapViewProps> = ({
    lat,
    lng,
    bus,
    accuracy,
    track = [],
}) => {
    return (
        <div className="">
            <MapContainer
                center={[lat, lng]}
                zoom={15}
                style={{ height: "200px", width: "100vw" }}>
                <TileLayer
                    attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a>'
                    url="https://tile-{s}.openstreetmap.fr/hot/{z}/{x}/{y}.png"
                />
                <Marker
                    position={[lat, lng]}
                    icon={busIcon}
                    zIndexOffset={1000}>
                    <Popup>Bus is here</Popup>
                </Marker>
                {bus.journey.stops.map((stop) => (
                    <Marker
                        key={stop.stop_id}
                        position={[stop.coords[0], stop.coords[1]]}
                        icon={pinIcon}>
                        <Popup>
                            <div className="flex flex-col">
                                <span>{stop.name}</span>
                                Expt:{" "}
                                {stop.expt_time?.toLocaleTimeString([], {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                })}
                            </div>
                        </Popup>
                    </Marker>
                ))}
                <Polyline
                    positions={track}
                    pathOptions={{
                        color: "black",
                        weight: 4,
                        opacity: 0.7,
                    }}
                />
                <MapCenterUpdater lat={lat} lng={lng}></MapCenterUpdater>
                <MapInfo
                    text={`Accuracy: ${accuracy}`}
                    style={{
                        color:
                            accuracy === "high"
                                ? "green"
                                : accuracy === "med"
                                ? "darkorange"
                                : "red",
                    }}
                />
                <LocateControlComponent busLatLng={[lat, lng]} />
                <ResetZoomControl />
            </MapContainer>
        </div>
    );
};

const JourneyPage: React.FC = () => {
    const { bus_id } = useParams();

    const navigate = useNavigate();

    const [bus, setBus] = useState<Bus>();
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

    const BusProgress = () => {
        const sectionLength = 72;

        const translateY = (sequence + progress) * sectionLength;

        return (
            <div className="absolute top-0 left-0 h-full mt-[15px] z-11 w-9 ">
                <div
                    className="absolute transition-all duration-300 ease-in-out  translate-x-[-15px]"
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

            if (bus?.timestamp) {
                const age = Math.floor(
                    (now.getTime() - bus?.timestamp.getTime()) / 1000
                );
                let accuracy = "unknown";

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
                setSeq(bus?.progress ? bus.progress.sequence : 0);
                setProg(bus?.progress ? bus.progress.progress : 0);
                const lat = bus?.coords?.[1] ?? 0;
                const lng = bus?.coords?.[0] ?? 0;
                setLoc([lat, lng]);
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
                <div className="flex flex-col gap-2 top-0 grow p-5 pb-1 pt-15 z-12  bg-[#111111] rounded-b-2xl fixed w-full">
                    {bus ? (
                        <div className="flex flex-col items-center justify-center gap-2">
                            <div className="fixed flex items-center gap-3 p-2 px-3 my-1 shadow-2xl z-10000000 top-15 bg-neutral-800 rounded-2xl">
                                <span className="text-3xl font-bold text-white wrap-normal">
                                    {journey?.route_name} to{" "}
                                    {journey?.destination}
                                </span>
                            </div>
                            <MapView
                                lat={location[0]}
                                lng={location[1]}
                                bus={bus}
                                accuracy={accuracy}
                                track={generateWholeTrack(
                                    bus.journey?.stops
                                )}></MapView>
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
                                            background:
                                                bus?.livery?.css ||
                                                "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 200' fill='none' xmlns:xlink='http://www.w3.org/1999/xlink'><rect width='300' height='200' fill='%23222222'/><text x='150' y='110' text-anchor='middle' fill='%23999999' font-size='80' font-family='sans-serif' dy='.35em'>?</text></svg>\")",
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
                    <div className="flex flex-row gap-2">
                        <div className="relative flex mx-5 mt-48 md:mx-40">
                            <div className="relative flex flex-col items-center py-8">
                                <BusProgress></BusProgress>
                                {journey?.stops.map((stop, idx) => (
                                    <div
                                        key={stop.stop_id}
                                        className="relative flex flex-col items-center">
                                        <div
                                            className={`z-10 w-1 h-1 bg-neutral-700 ${
                                                idx == 0
                                                    ? "rounded-tl-full"
                                                    : idx ==
                                                      journey.stops.length - 1
                                                    ? "rounded-bl-full"
                                                    : ""
                                            }`}></div>

                                        {idx < journey.stops.length - 1 && (
                                            <div className="w-[4px] bg-neutral-700 flex-1 min-h-[68px]"></div>
                                        )}
                                    </div>
                                ))}
                            </div>
                            <div className="flex flex-col gap-1">
                                {journey?.stops.map((stop, idx) => (
                                    <div
                                        key={stop.stop_id}
                                        className="flex flex-row items-center">
                                        <div className="w-4 bg-neutral-700 rounded-r-full h-[4px]"></div>
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
                    </div>
                )}
            </div>
        </div>
    );
};

export default JourneyPage;
