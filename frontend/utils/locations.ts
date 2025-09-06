import type { StopTime } from "../models/StopTime";
import toast from "react-hot-toast";

export function toLatLngArray(track?: number[][]): L.LatLngExpression[] {
    if (!track || !Array.isArray(track)) return [];

    return track
        .filter(
            (coord): coord is [number, number] =>
                Array.isArray(coord) && coord.length === 2 &&
                typeof coord[0] === "number" && typeof coord[1] === "number"
        );
}

export default function generateWholeTrack(stops: StopTime[]): L.LatLngExpression[] {
    return stops.flatMap(stop => toLatLngArray(stop.track));
}

export function getCurrentPosition(): Promise<GeolocationPosition> {
    return new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, (error) => {
            toast.error("Failed to get current position.", { id: 'geolocation-error-toast', duration: 3000 });
            reject(error);
        });
    });
}