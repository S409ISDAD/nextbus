import type { Departure } from "../models/Bus";

export default function timeTo(bus: Departure) {
    const now = new Date()
    const diffMs = new Date(bus.expected).getTime() - now.getTime();
    const diffSec = Math.floor(diffMs / 1000);

    return generateTimeTo(diffSec)

}

export function generateTimeTo(diffSec: number) {
    if (diffSec < 30) {
        return 'Due';
    } else if (diffSec < 3600) {
        const min = Math.floor(diffSec / 60);
        return `${min} min`;
    } else {
        const hr = Math.floor(diffSec / 3600);
        const min = Math.floor((diffSec % 3600) / 60);
        if (min === 0) {
            return `${hr}h`;
        }
        return `${hr}h ${min}m`;
    }
}

export const toTime = (iso: string | undefined) =>
    iso ? new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "";

export function lateness(delay: number) {
    const n_delay = Math.abs(delay)

    let output = ""

    if (n_delay >= 60) {
        output += `${Math.floor(n_delay / 60)}m`
    } else {
        output += "On time"
    }

    if (delay <= -60) {
        output += " early"
    } else if (delay >= 60) {
        output += " late"
    }

    return output
}