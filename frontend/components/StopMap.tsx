import { useEffect, useRef, useState, useCallback } from "react";
import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import { LocateControl } from "leaflet.locatecontrol";
import "leaflet.locatecontrol/dist/L.Control.Locate.min.css";

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
    if (zoom < 13) {
        return (
            <div
                style={{
                    position: "absolute",
                    top: 10,
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
    if (loading) {
        return (
            <div
                style={{
                    position: "absolute",
                    top: 10,
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
    loading,
    onBoundsChange,
}) => {
    const [zoom, setZoom] = useState(10);

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
        <div style={{ position: "relative", zIndex: 0, width: "100%" }}>
            <MapContainer
                center={[lat, lng]}
                zoom={zoom}
                style={{
                    aspectRatio:
                        typeof window !== "undefined" && window.innerWidth < 640
                            ? 1 / 1.3
                            : 2 / 1,
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
                                    href={`/departures/${stop.stop_id}`}
                                    className="text-sky-500 hover:underline">
                                    View Stop
                                </a>
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

const StopMap: React.FC = () => {
    const [stops, setStops] = useState<Stop[]>([]);
    const [loading, setLoading] = useState(false);
    const [center, setCenter] = useState<[number, number]>([51, -1]);
    const lastBoundsRef = useRef<L.LatLngBounds | null>(null);
    const stopsTimeout = useRef<number | null>(null);

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
            }
        },
        [fetchStops, stops.length]
    );

    return (
        <MapView
            lat={center[0]}
            lng={center[1]}
            stops={stops}
            loading={loading}
            onBoundsChange={handleBoundsChange}
        />
    );
};

export default StopMap;
