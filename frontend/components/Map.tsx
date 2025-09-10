import { useRef, useState, useCallback, type JSX } from "react";
import {
    Map as MapGL,
    Marker,
    Popup,
    NavigationControl,
    GeolocateControl,
    type MapRef,
} from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import { useShowAppNav } from "../utils/AppNav";
import type { MapBus } from "../models/Bus";
import getLivery from "../utils/getLivery";
import { SHOW_BUSES } from "../src/settings";

type Stop = {
    stop_id: string;
    name: string;
    coords: [number, number];
    services: string[];
    bearing?: number;
};

type MapViewProps = {
    mapRef: React.Ref<MapRef>;
    stops: Stop[];
    buses: MapBus[];
    loading?: boolean;
    onBoundsChange: (bounds: L.LatLngBounds, zoom: number) => void;
};

const MapView: React.FC<MapViewProps> = ({
    mapRef,
    stops,
    buses,
    loading,
    onBoundsChange,
}) => {
    const [zoom, setZoom] = useState(9);

    const showAppNav = useShowAppNav();

    const [popup, setPopup] = useState<{
        lngLat: [number, number];
        content: JSX.Element;
    } | null>(null);

    const handleMove = useCallback(
        (e: any) => {
            const { viewState } = e;
            setZoom(viewState.zoom);

            const bounds = e.target.getBounds();
            onBoundsChange(bounds, viewState.zoom);
        },
        [onBoundsChange]
    );

    return (
        <div
            style={{
                height: showAppNav
                    ? "calc(100vh - 74px)"
                    : "calc(100vh - 60px)",
                width: "100%",
            }}>
            <MapGL
                ref={mapRef}
                initialViewState={{
                    latitude: 51,
                    longitude: -1,
                    zoom: 9,
                }}
                style={{
                    height: "100%",
                    width: "100%",
                    borderRadius: "8px",
                }}
                touchPitch={false}
                pitchWithRotate={false}
                dragRotate={false}
                maxPitch={0}
                maxZoom={18}
                minZoom={4}
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
                onMoveEnd={handleMove}>
                <NavigationControl position="top-right" />

                <GeolocateControl
                    position="top-right"
                    trackUserLocation={true}
                    showAccuracyCircle={true}
                />
                {stops.map((stop) => (
                    <Marker
                        key={stop.stop_id}
                        longitude={stop.coords[1]}
                        latitude={stop.coords[0]}
                        onClick={(e) => {
                            e.originalEvent.stopPropagation();
                            setPopup({
                                lngLat: [stop.coords[1], stop.coords[0]],
                                content: (
                                    <div className="flex flex-col text-white bg-[#222]">
                                        <span className="font-semibold text-white">
                                            {stop.name}
                                        </span>
                                        <span className="text-xs text-gray-300">
                                            {stop.services.join(", ")}
                                        </span>
                                        <a
                                            href={`/buses/stops/${stop.stop_id}`}
                                            className="text-xs text-sky-400 hover:underline">
                                            View Stop
                                        </a>
                                    </div>
                                ),
                            });
                        }}>
                        <i
                            className={`text-blue-500 fas ${
                                stop.bearing
                                    ? "fa-location-dot scale-130"
                                    : "fa-circle-dot"
                            } opacity-80`}
                            style={{
                                transform: `rotate(${
                                    (stop.bearing ?? 0) - 180
                                }deg)`,
                            }}
                        />
                    </Marker>
                ))}

                {buses.map((bus) => (
                    <Marker
                        key={bus.trip_id}
                        longitude={bus.coords[1]}
                        latitude={bus.coords[0]}
                        anchor="center"
                        onClick={() =>
                            setPopup({
                                lngLat: [bus.coords[1], bus.coords[0]],
                                content: (
                                    <div className="flex flex-col">
                                        <span>
                                            {bus.service.line_name} to{" "}
                                            {bus.destination}
                                        </span>
                                        <span className="text-sm text-gray-500">
                                            {bus.vehicle.features}
                                        </span>
                                        <span className="text-sm text-gray-500">
                                            {bus.vehicle.name}
                                        </span>
                                    </div>
                                ),
                            })
                        }>
                        <div
                            style={{
                                width: 24,
                                height: 16,
                                background: bus?.livery?.left_css ?? "#222",
                                transform: `rotate(${bus.heading - 90}deg)`,
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                            }}>
                            <span className="text-xs font-bold text-black">
                                {bus.service.line_name}
                            </span>
                        </div>
                    </Marker>
                ))}

                {popup && (
                    <Popup
                        longitude={popup.lngLat[0]}
                        latitude={popup.lngLat[1]}
                        closeOnClick={true}
                        anchor="bottom"
                        maxWidth="250px"
                        onClose={() => setPopup(null)}>
                        {popup.content}
                    </Popup>
                )}
            </MapGL>
            {zoom < 13 && (
                <div
                    className="absolute px-4 py-2 text-sm font-semibold text-gray-600 transform -translate-x-1/2 bg-white rounded shadow left-1/2"
                    style={{ top: showAppNav ? 10 : 70 }}>
                    Zoom in to see bus stops
                </div>
            )}
            {loading && (
                <div
                    className="absolute px-4 py-2 text-sm font-semibold text-gray-500 transform -translate-x-1/2 bg-white rounded shadow left-1/2"
                    style={{ top: showAppNav ? 10 : 70 }}>
                    Loading...
                </div>
            )}
        </div>
    );
};

const Map: React.FC = () => {
    const [stops, setStops] = useState<Stop[]>([]);
    const [buses, setBuses] = useState<MapBus[]>([]);
    const [loading, setLoading] = useState(false);
    const stopsTimeout = useRef<number | null>(null);
    const busesTimeout = useRef<number | null>(null);
    const mapRef = useRef<MapRef>(null);

    // useEffect(() => {
    //     if (navigator.geolocation) {
    //         navigator.geolocation.getCurrentPosition(
    //             (pos) => setCenter([pos.coords.latitude, pos.coords.longitude]),
    //             () => {},
    //             { enableHighAccuracy: true, timeout: 10000 }
    //         );
    //     }
    // }, []);

    const fetchStops = useCallback(async (bounds: maplibregl.LngLatBounds) => {
        setLoading(true);
        try {
            const sw = bounds.getSouthWest();
            const ne = bounds.getNorthEast();
            const xmin = sw.lng,
                ymin = sw.lat;
            const xmax = ne.lng,
                ymax = ne.lat;

            const url = `https://bustimes.org/stops.json?ymax=${ymax}&xmax=${xmax}&ymin=${ymin}&xmin=${xmin}`;
            const res = await fetch(url);
            const geojson = await res.json();
            const features = geojson.features || [];
            const stopsData: Stop[] = features.map((feature: any) => ({
                stop_id: feature.properties.url.split("/").pop(),
                name: feature.properties.name || feature.properties.commonName,
                coords: [
                    feature.geometry.coordinates[1],
                    feature.geometry.coordinates[0],
                ],
                services: feature.properties.services || [],
                bearing: feature.properties.bearing,
            }));
            setStops(stopsData);
        } catch (err) {
            console.error("Failed to fetch stops", err);
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchBuses = useCallback(async (bounds: maplibregl.LngLatBounds) => {
        setLoading(true);
        try {
            const sw = bounds.getSouthWest();
            const ne = bounds.getNorthEast();
            const xmin = sw.lng,
                ymin = sw.lat;
            const xmax = ne.lng,
                ymax = ne.lat;

            const url = `https://bustimes.org/vehicles.json?ymax=${ymax}&xmax=${xmax}&ymin=${ymin}&xmin=${xmin}`;
            const res = await fetch(url);
            const geojson = await res.json();
            const busesData: MapBus[] = await Promise.all(
                geojson.map(async (feature: any) => ({
                    id: feature.id,
                    coords: [feature.coordinates[1], feature.coordinates[0]],
                    heading: feature.heading,
                    updated: new Date(feature.datetime),
                    destination: feature.destination,
                    trip_id: feature.trip_id,
                    service_id: feature.service_id,
                    service: feature.service,
                    vehicle: feature.vehicle,
                    livery: await getLivery(feature.vehicle.livery),
                }))
            );
            console.log(busesData);
            setBuses(busesData);
        } catch (err) {
            console.error("Failed to fetch buses", err);
        } finally {
            setLoading(false);
        }
    }, []);

    const handleBoundsChange = useCallback(() => {
        const map = mapRef.current?.getMap();
        if (!map) return;

        const bounds = map.getBounds();
        const zoom = map.getZoom();

        if (zoom < 13) {
            if (stops.length > 0) setStops([]);
            return;
        }

        if (stopsTimeout.current) clearTimeout(stopsTimeout.current);
        stopsTimeout.current = window.setTimeout(() => fetchStops(bounds), 400);

        if (SHOW_BUSES) {
            if (busesTimeout.current) clearTimeout(busesTimeout.current);
            busesTimeout.current = window.setTimeout(
                () => fetchBuses(bounds),
                1000
            );
        }
    }, [fetchStops, fetchBuses, stops.length]);

    return (
        <MapView
            mapRef={mapRef}
            stops={stops}
            buses={buses}
            loading={loading}
            onBoundsChange={handleBoundsChange}
        />
    );
};

export default Map;
