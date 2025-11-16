import { useEffect, useRef, useState } from "react";
import type { Trip } from "../../models/Journey";
import { useNavigate, useParams } from "react-router";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { toTime } from "../../utils/timeUtils";
import {
    getTrip,
    getDBJourney,
    getBusOnPrevJourney,
} from "../../utils/getJourney";
import { generateWholeTrack, type Latlon } from "../../utils/locations";
import { faWarning } from "@fortawesome/free-solid-svg-icons";
import * as turf from "@turf/turf";
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
import { Card } from "../../components/ui/Card";
import { formatBusType } from "./DeparturePage";

type MapViewProps = {
    journey: Trip;
    track: Latlon[];
};
import React from "react";
import { Bus } from "../../models/Bus";
import { useLocalSetting } from "../../src/settings";

const MapView: React.FC<MapViewProps> = ({ journey, track = [] }) => {
    const [popup, setPopup] = React.useState<{
        coords: Latlon;
        content: React.ReactNode;
    } | null>(null);

    const mapRef = React.useRef<MapRef | null>(null);

    const handleMapLoad = () => {
        if (!mapRef.current || track.length === 0) return;
        try {
            const line = turf.lineString(track.map((p) => [p[1], p[0]]));
            const bbox = turf.bbox(line);
            mapRef.current.fitBounds(
                [
                    [bbox[0], bbox[1]],
                    [bbox[2], bbox[3]],
                ],
                { padding: 40, duration: 800 }
            );
        } catch (err) {
            console.error("Error fitting bounds:", err);
        }
    };

    return (
        <div className="relative w-screen h-[200px]">
            <MapGL
                ref={mapRef}
                initialViewState={{
                    longitude: 0,
                    latitude: 0,
                    zoom: 14,
                }}
                onLoad={handleMapLoad}
                attributionControl={false}
                // mapStyle="https://tiles.stadiamaps.com/styles/alidade_smooth_dark.json"
                mapStyle="https://tiles.stadiamaps.com/styles/osm_bright.json"
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

                {journey.stops.map((stop) => (
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
                                "line-color": "black",
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
        </div>
    );
};

const JourneyPage: React.FC = () => {
    const params = useParams();
    const isDBJourney = params.journey_id !== undefined;
    const journey_id = params.journey_id || params.trip_id;

    const navigate = useNavigate();

    const [journey, setJourney] = useState<Trip>();
    const [potentialBus, setPotentialBus] = useState<null | {
        away: number;
        bus: Bus;
    }>(null);
    const [loading, setLoading] = useState(true);
    const [fetching, setFetching] = useState(false);
    const [msg, setMsg] = useState<string>("");
    const [busInfoHeight, setBusInfoHeight] = useState(0);
    const busInfoRef = useRef<HTMLDivElement>(null);
    const showAppNav = useShowAppNav();
    const [vegMode] = useLocalSetting("veg", false);

    useEffect(() => {
        if (busInfoRef.current) {
            setBusInfoHeight(busInfoRef.current.clientHeight);
        }
    }, [busInfoRef, loading, potentialBus, msg]);
    useEffect(() => {
        const getData = async (journey_id: number) => {
            if (fetching) {
                return;
            }
            setFetching(true);
            try {
                var trip: Trip | null = null;
                if (isDBJourney) {
                    trip = await getDBJourney(journey_id);
                } else {
                    trip = await getTrip(journey_id);
                }

                if (trip) {
                    setJourney(trip);
                    document.title = `${trip.route_name} to ${trip.destination} | nextbus`;
                    setMsg("");
                } else {
                    setMsg("Failed to fetch trip. Try reloading the page");
                }
            } catch (error) {
                console.log("uh oh", error);
            } finally {
                setLoading(false);
                setFetching(false);
            }
        };
        const init = async (journey_id: number) => {
            try {
                await getData(journey_id);
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get journey data.");
                setLoading(false);
                setFetching(false);
            }
        };

        if (journey_id) {
            init(Number(journey_id));
        }
    }, [journey_id]);

    if (loading) {
        return <></>;
    }

    return (
        <div className="flex flex-col">
            <div
                className={`flex flex-col gap-2 top-0 grow px-5 pb-1 z-12 bg-[#111111] rounded-b-2xl fixed w-full ${
                    !showAppNav ? "pt-15" : ""
                }`}
                ref={busInfoRef}>
                {journey ? (
                    <div className="flex flex-col items-center justify-center gap-2">
                        <div
                            className={`fixed flex flex-row items-stretch p-2 px-3 my-1 mb-1 z-10000000 ${
                                !showAppNav ? "top-15" : "top-0"
                            }`}>
                            <div className="flex items-center px-3 py-1 bg-primary-700 rounded-l-2xl">
                                <span className="flex items-center justify-center text-xl font-bold text-center">
                                    {journey.route_name}
                                </span>
                            </div>
                            <div className="flex flex-col justify-center px-3 py-1 bg-neutral-800 rounded-r-2xl">
                                <span className="font-semibold text">
                                    {journey.destination}
                                </span>
                            </div>
                        </div>

                        <MapView
                            journey={journey}
                            track={generateWholeTrack(journey.stops)}></MapView>
                        <div className="flex gap-3">
                            {!isDBJourney && (
                                <a
                                    className="underline text-link"
                                    href={`https://bustimes.org/trips/${journey_id}`}
                                    target="_blank">
                                    View on bustimes.org
                                </a>
                            )}
                            <span className="text-center">
                                {journey?.stops.length} stops
                            </span>
                        </div>
                        {isDBJourney && (
                            <div className="flex flex-col items-center gap-3">
                                <button
                                    className="text-sm button max-w-fit"
                                    onClick={async () => {
                                        if (potentialBus) {
                                            setPotentialBus(null);
                                        } else {
                                            const bus =
                                                await getBusOnPrevJourney(
                                                    Number(journey_id)
                                                );
                                            if (!bus) {
                                                setMsg(
                                                    "No bus found on previous journey"
                                                );
                                                return;
                                            }
                                            setPotentialBus(bus);
                                        }
                                    }}>
                                    {potentialBus
                                        ? "hide bus info"
                                        : "what bus will i get?"}
                                </button>

                                {potentialBus && (
                                    <Card className="flex flex-col items-center gap-2 text-center">
                                        <div className="flex flex-row items-center gap-4 text-center">
                                            <div className="flex flex-col items-center gap-1">
                                                <span className="text-xs font-bold text-center">
                                                    {potentialBus.bus.vehicle
                                                        .livery
                                                        ? potentialBus.bus
                                                              ?.vehicle.livery
                                                              .name
                                                        : "No livery"}
                                                </span>
                                                <div
                                                    className="rounded shadow-2xl w-15 aspect-3/2"
                                                    style={{
                                                        background:
                                                            potentialBus.bus
                                                                ?.vehicle.livery
                                                                ?.right_css ||
                                                            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 200' fill='none' xmlns:xlink='http://www.w3.org/1999/xlink'><rect width='300' height='200' fill='%23222222'/><text x='150' y='110' text-anchor='middle' fill='%23999999' font-size='80' font-family='sans-serif' dy='.35em'>?</text></svg>\")",
                                                    }}></div>
                                            </div>
                                            <div className="flex flex-col items-center gap-2">
                                                <span className="text-sm font-bold text-center text-neutral-400">
                                                    {formatBusType(
                                                        potentialBus.bus,
                                                        vegMode
                                                    )}
                                                </span>
                                                <div className="flex justify-center px-2 py-1 rounded-lg w-fit bg-amber-400">
                                                    <span className="text-xs font-bold align-middle text-neutral-950">
                                                        {
                                                            potentialBus.bus
                                                                .vehicle.reg
                                                        }
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                        <span className="text-sm text-neutral-400">
                                            {potentialBus.away === 0
                                                ? "on this journey"
                                                : potentialBus.away === 1
                                                ? "next journey"
                                                : `${potentialBus.away} journeys away`}
                                        </span>
                                    </Card>
                                )}
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-row items-center justify-center h-30">
                        <div className="flex flex-row gap-3 p-3 border-2 border-red-400 bg-red-950 rounded-2xl">
                            <FontAwesomeIcon
                                icon={faWarning}
                                size="2x"
                                className="text-neutral-300"></FontAwesomeIcon>
                            <span className="text-2xl font-black text-neutral-300 wrap-normal">
                                No journey data found
                            </span>
                        </div>
                    </div>
                )}
                {msg ? (
                    <span className="text-center text-red-400">{msg}</span>
                ) : (
                    <></>
                )}
                <div className="flex items-center justify-center gap-2 text-sm text-neutral-500">
                    <div className="w-2 h-2 rounded-full bg-link"></div> =
                    timing point (bus waits here if early)
                </div>
            </div>
            <div
                style={{
                    marginTop: busInfoHeight - (showAppNav ? 0 : 50),
                }}>
                <div className="flex flex-row gap-2 px-3 md:px-0">
                    <div className="relative flex mx-5 md:mx-40">
                        <div className="relative flex flex-col items-center py-8">
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
                                    {/* {stop.timing_status === "PTP" && (
                                            <div className="absolute z-10 w-3 h-3 translate-y-[-30%] rounded-full bg-neutral-700 flex items-center justify-center"></div>
                                        )} */}
                                    {idx < journey.stops.length - 1 && (
                                        <div className="w-1 bg-neutral-700 flex-1 min-h-[68px]"></div>
                                    )}
                                </div>
                            ))}
                        </div>
                        <div className="flex flex-col gap-1">
                            {journey?.stops.map((stop) => (
                                <div
                                    key={stop.stop_id}
                                    className="flex flex-row items-center">
                                    <div
                                        className={`w-4 bg-neutral-700 rounded-r-full h-1`}></div>
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
                                            className={`flex items-stretch flex-col $`}>
                                            <div className="flex flex-row items-center gap-2 font-bold">
                                                {stop.timing_status ===
                                                    "PTP" && (
                                                    <div className="w-2 h-2 rounded-full bg-link"></div>
                                                )}{" "}
                                                {stop.name}
                                            </div>

                                            <div className="flex flex-row gap-6 font-bold text-">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-green-400">
                                                        {toTime(stop.expt_time)}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default JourneyPage;
