import { useEffect, useRef, useState, useCallback } from "react";
import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import { LocateControl } from "leaflet.locatecontrol";
import "leaflet.locatecontrol/dist/L.Control.Locate.min.css";
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
    lat: number;
    lng: number;
    stops: Stop[];
    buses: MapBus[];
    loading?: boolean;
    onBoundsChange: (bounds: L.LatLngBounds, zoom: number) => void;
};

const getPinIcon = (bearing: number) =>
    L.divIcon({
        html: `<i class="fas fa-location-dot fa-xl" style="transform: rotate(${
            bearing + 180
        }deg);"></i>`,
        className: "text-blue-500 opacity-80",
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [-6, -6],
    });

const getStopIcon = () =>
    L.divIcon({
        html: `<i class="fas fa-circle-dot"></i>`,
        className: "text-blue-500 opacity-80",
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [-6, -6],
    });

const getBusIcon = (bus: MapBus) =>
    L.divIcon({
        html: `<div class="z-100 w-[24px] h-[16px] flex items-center justify-center" style="transform: rotate(${
            bus.heading - 90
        }deg); background: ${
            bus?.livery?.left_css
                ? bus.livery.left_css
                : "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 200' fill='none'><rect width='300' height='200' fill='%23222222'/><text x='150' y='110' text-anchor='middle' fill='%23999999' font-size='80' font-family='sans-serif' dy='.35em'>?</text></svg>\")"
        };"><span class="font-bold text-black">${
            bus.service.line_name
        }</span></div>`,
        className: "opacity-100",
        iconSize: [24, 16],
        iconAnchor: [12, 8],
        popupAnchor: [0, -8],
    });

// Leaflet locate control
const LocateControlComponent: React.FC = () => {
    const map = useMap();
    useEffect(() => {
        // @ts-ignore
        const locateControl = new LocateControl({
            position: "topright",
            showPopup: false,
            strings: { title: "Show me where I am" },
        });
        locateControl.addTo(map);
    }, [map]);
    return null;
};

// Zoom prompt overlay
const ZoomPrompt: React.FC<{ zoom: number }> = ({ zoom }) => {
    const showAppNav = useShowAppNav();
    if (zoom < 13) {
        return (
            <div
                style={{
                    position: "absolute",
                    top: showAppNav ? 10 : 70,
                    left: "50%",
                    transform: "translateX(-50%)",
                    background: "rgba(255,255,255,0.95)",
                    padding: "8px 16px",
                    borderRadius: "8px",
                    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                    zIndex: 1000,
                }}
                className="text-sm font-semibold text-gray-600">
                Zoom in to see bus stops
            </div>
        );
    }
    return null;
};

// Loading overlay
const LoadingMsg: React.FC<{ loading: boolean }> = ({ loading }) => {
    const showAppNav = useShowAppNav();
    if (loading) {
        return (
            <div
                style={{
                    position: "absolute",
                    top: showAppNav ? 10 : 70,
                    left: "50%",
                    transform: "translateX(-50%)",
                    background: "rgba(255,255,255,0.95)",
                    padding: "8px 16px",
                    borderRadius: "8px",
                    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                    zIndex: 1000,
                }}
                className="text-sm font-semibold text-gray-500">
                Loading...
            </div>
        );
    }
    return null;
};

const MapView: React.FC<MapViewProps> = ({
    lat,
    lng,
    stops,
    buses,
    loading,
    onBoundsChange,
}) => {
    const [zoom, setZoom] = useState(9);

    const showAppNav = useShowAppNav();

    const handleMove = useCallback(
        (map: L.Map) => {
            const bounds = map.getBounds();
            const z = map.getZoom();

            setZoom((prevZoom) => (prevZoom !== z ? z : prevZoom)); // only update zoom if changed
            onBoundsChange(bounds, z);
        },
        [onBoundsChange]
    );

    const MapEvents: React.FC = () => {
        const map = useMap();

        useEffect(() => {
            const onMoveEnd = () => handleMove(map);
            map.on("moveend", onMoveEnd);
            map.on("zoomend", onMoveEnd);

            // call once on mount
            handleMove(map);

            return () => {
                map.off("moveend", onMoveEnd);
                map.off("zoomend", onMoveEnd);
            };
        }, [map, handleMove]);

        return null;
    };

    return (
        <div
            className="w-full"
            style={{
                height: showAppNav
                    ? "calc(100vh - 74px)"
                    : "calc(100vh - 60px)",
            }}>
            <MapContainer
                center={[lat, lng]}
                zoom={zoom}
                style={{
                    height: "100%",
                    width: "100%",
                    borderRadius: "8px",
                }}>
                <TileLayer
                    attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a>'
                    url="https://tile-{s}.openstreetmap.fr/hot/{z}/{x}/{y}.png"
                />

                {stops.map((stop) => (
                    <Marker
                        key={stop.stop_id}
                        position={[stop.coords[0], stop.coords[1]]}
                        icon={
                            stop.bearing != null
                                ? getPinIcon(stop.bearing)
                                : getStopIcon()
                        }>
                        <Popup>
                            <div className="flex flex-col">
                                <span>{stop.name}</span>
                                <span className="text-sm text-gray-500">
                                    {stop.services.join(", ")}
                                </span>
                                <a
                                    href={`/buses/stops/${stop.stop_id}`}
                                    className="text-sky-500 hover:underline">
                                    View Stop
                                </a>
                            </div>
                        </Popup>
                    </Marker>
                ))}

                {buses.map((bus) => (
                    <Marker
                        key={bus.trip_id}
                        position={[bus.coords[0], bus.coords[1]]}
                        icon={getBusIcon(bus)}>
                        <Popup>
                            <div className="flex flex-col">
                                <span>
                                    {bus.service.line_name} to {bus.destination}
                                </span>
                                <span className="text-sm text-gray-500">
                                    {bus.vehicle.features}
                                </span>
                                <span className="text-sm text-gray-500">
                                    {bus.vehicle.name}
                                </span>
                            </div>
                        </Popup>
                    </Marker>
                ))}

                <LocateControlComponent />
                <MapEvents />
            </MapContainer>
            <ZoomPrompt zoom={zoom} />
            <LoadingMsg loading={!!loading} />
        </div>
    );
};

const Map: React.FC = () => {
    const [stops, setStops] = useState<Stop[]>([]);
    const [buses, setBuses] = useState<MapBus[]>([]);
    const [loading, setLoading] = useState(false);
    const [center] = useState<[number, number]>([51, -1]);
    const lastBoundsRef = useRef<L.LatLngBounds | null>(null);
    const stopsTimeout = useRef<number | null>(null);
    const busesTimeout = useRef<number | null>(null);

    // useEffect(() => {
    //     if (navigator.geolocation) {
    //         navigator.geolocation.getCurrentPosition(
    //             (pos) => setCenter([pos.coords.latitude, pos.coords.longitude]),
    //             () => {},
    //             { enableHighAccuracy: true, timeout: 10000 }
    //         );
    //     }
    // }, []);

    const fetchStops = useCallback(async (bounds: L.LatLngBounds) => {
        setLoading(true);
        try {
            const ymax = bounds.getNorth();
            const ymin = bounds.getSouth();
            const xmax = bounds.getEast();
            const xmin = bounds.getWest();

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

    const fetchBuses = useCallback(async (bounds: L.LatLngBounds) => {
        setLoading(true);
        try {
            const ymax = bounds.getNorth();
            const ymin = bounds.getSouth();
            const xmax = bounds.getEast();
            const xmin = bounds.getWest();

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

    const handleBoundsChange = useCallback(
        (bounds: L.LatLngBounds, zoom: number) => {
            if (zoom < 13) {
                if (stops.length > 0) setStops([]);
                return;
            }

            // Only fetch if bounds changed
            if (
                !lastBoundsRef.current ||
                !lastBoundsRef.current.equals(bounds)
            ) {
                lastBoundsRef.current = bounds;

                if (stopsTimeout.current) clearTimeout(stopsTimeout.current);
                stopsTimeout.current = window.setTimeout(
                    () => fetchStops(bounds),
                    400
                );

                if (SHOW_BUSES) {
                    if (busesTimeout.current)
                        clearTimeout(busesTimeout.current);
                    busesTimeout.current = window.setTimeout(
                        () => fetchBuses(bounds),
                        1000
                    );
                }
            }
        },
        [fetchStops, stops.length]
    );

    return (
        <MapView
            lat={center[0]}
            lng={center[1]}
            stops={stops}
            buses={buses}
            loading={loading}
            onBoundsChange={handleBoundsChange}
        />
    );
};

export default Map;
