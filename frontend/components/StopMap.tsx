import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import { LocateControl } from "leaflet.locatecontrol";
import "leaflet.locatecontrol/dist/L.Control.Locate.min.css";

const LocateControlComponent: React.FC<{}> = () => {
    const map = useMap();

    useEffect(() => {
        // @ts-ignore
        const locateControl = new LocateControl({
            position: "topright",
            showPopup: false,
            strings: {
                title: "Show me where I am",
            },
        });
        locateControl.addTo(map);
    }, [map]);

    return null;
};

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
};

const getPinIcon = (bearing: number) =>
    L.divIcon({
        html: `<i class="fas fa-location-dot fa-xl" style="transform: rotate(${
            bearing + 180
        }deg);"></i>`,
        className: "text-red-500 opacity-80",
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [-6, -6],
    });

const getStopIcon = () =>
    L.divIcon({
        html: `<i class="fas fa-circle-dot"></i>`,
        className: "text-red-500 opacity-80",
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [-6, -6],
    });

import { useCallback } from "react";

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

const LoadingMsg: React.FC<{ loading: boolean }> = ({ loading }) => {
    if (loading) {
        return (
            <div
                style={{
                    position: "absolute",
                    top: 10,
                    left: 50,
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

const MapView: React.FC<
    MapViewProps & { onBoundsChange: (bounds: any, zoom: number) => void }
> = ({ lat, lng, stops, loading, onBoundsChange }) => {
    const [zoom, setZoom] = useState(10);

    const handleMove = useCallback(
        (map: L.Map) => {
            const bounds = map.getBounds();
            const z = map.getZoom();
            setZoom(z);
            onBoundsChange(bounds, z);
        },
        [onBoundsChange]
    );

    function MapEvents() {
        const map = useMap();
        useEffect(() => {
            handleMove(map);
            map.on("moveend", () => handleMove(map));
            map.on("zoomend", () => handleMove(map));
            return () => {
                map.off("moveend", () => handleMove(map));
                map.off("zoomend", () => handleMove(map));
            };
        }, [map]);
        return null;
    }

    return (
        <div className="" style={{ position: "relative" }}>
            <MapContainer
                center={[lat, lng]}
                zoom={zoom}
                style={{
                    width: "90vw",
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
                                    className="text-blue-500 hover:underline">
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
    // const fetchedBoundsRef = useRef<any>(null);
    const stopsTimeout = useRef<number | null>(null);

    // Store last bounds to avoid unnecessary fetches
    const lastBoundsRef = useRef<any>(null);

    useEffect(() => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    setCenter([pos.coords.latitude, pos.coords.longitude]);
                },
                () => {},
                { enableHighAccuracy: true, timeout: 10000 }
            );
        }
    }, []);

    const fetchStops = useCallback(async (bounds: any) => {
        setLoading(true);
        try {
            // bounds: { _northEast: {lat, lng}, _southWest: {lat, lng} }
            const ymax = bounds._northEast.lat;
            const ymin = bounds._southWest.lat;
            const xmax = bounds._northEast.lng;
            const xmin = bounds._southWest.lng;
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

    // function containsBounds(outer: any, inner: any) {
    //     if (!outer) return false;

    //     const BUFFER = 0.0005; // about ~50m buffer

    //     return (
    //         outer._southWest.lat - BUFFER <= inner._southWest.lat &&
    //         outer._southWest.lng - BUFFER <= inner._southWest.lng &&
    //         outer._northEast.lat + BUFFER >= inner._northEast.lat &&
    //         outer._northEast.lng + BUFFER >= inner._northEast.lng
    //     );
    // }

    // function mergeBounds(a: any, b: any) {
    //     return L.latLngBounds([
    //         [
    //             Math.min(a._southWest.lat, b._southWest.lat),
    //             Math.min(a._southWest.lng, b._southWest.lng),
    //         ],
    //         [
    //             Math.max(a._northEast.lat, b._northEast.lat),
    //             Math.max(a._northEast.lng, b._northEast.lng),
    //         ],
    //     ]);
    // }

    // const handleBoundsChange = useCallback(
    //     (bounds: any, zoom: number) => {
    //         const prev = lastBoundsRef.current;

    //         if (!prev) {
    //             lastBoundsRef.current = { bounds, zoom };
    //             fetchedBoundsRef.current = bounds;
    //             fetchStops(bounds, zoom);
    //             return;
    //         }

    //         const prevZoom = prev.zoom;

    //         const zoomOut = zoom < prevZoom;
    //         const zoomIn = zoom > prevZoom;

    //         const needsMore = !containsBounds(fetchedBoundsRef.current, bounds);

    //         console.log(
    //             "ZoomOut:",
    //             zoomOut,
    //             "ZoomIn:",
    //             zoomIn,
    //             "NeedsMore:",
    //             needsMore
    //         );

    //         const shouldFetch = zoomOut || (needsMore && !zoomIn);

    //         if (shouldFetch) {
    //             lastBoundsRef.current = { bounds, zoom };

    //             // grow the fetched bounds
    //             fetchedBoundsRef.current = mergeBounds(
    //                 fetchedBoundsRef.current,
    //                 bounds
    //             );

    //             if (stopsTimeout.current) clearTimeout(stopsTimeout.current);
    //             stopsTimeout.current = window.setTimeout(() => {
    //                 fetchStops(bounds, zoom);
    //             }, 200);
    //         }
    //     },
    //     [fetchStops]
    // );

    const handleBoundsChange = useCallback(
        (bounds: any, zoom: number) => {
            if (zoom < 13) {
                setStops([]);
                return;
            }
            const hasBoundsChanged =
                !lastBoundsRef.current ||
                lastBoundsRef.current._northEast.lat !==
                    bounds._northEast.lat ||
                lastBoundsRef.current._northEast.lng !==
                    bounds._northEast.lng ||
                lastBoundsRef.current._southWest.lat !==
                    bounds._southWest.lat ||
                lastBoundsRef.current._southWest.lng !== bounds._southWest.lng;

            if (hasBoundsChanged) {
                lastBoundsRef.current = bounds;

                if (stopsTimeout.current) clearTimeout(stopsTimeout.current);
                stopsTimeout.current = window.setTimeout(() => {
                    fetchStops(bounds);
                }, 400);
            }
        },
        [fetchStops]
    );

    return (
        <>
            <MapView
                lat={center[0]}
                lng={center[1]}
                stops={stops}
                loading={loading}
                onBoundsChange={handleBoundsChange}
            />
        </>
    );
};

export default StopMap;
