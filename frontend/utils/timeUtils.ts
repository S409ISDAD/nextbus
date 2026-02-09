import type { Departure } from "../models/Bus";

export default function timeTo(bus: Departure) {
    const now = new Date()
    const diffMs = new Date(bus.expected).getTime() - now.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const minDiff = 'min_expected' in bus && bus.min_expected ? (new Date(bus.min_expected).getTime() / 1000 - Math.floor(now.getTime() / 1000)) : diffSec;
    const maxDiff = 'max_expected' in bus && bus.max_expected ? (new Date(bus.max_expected).getTime() / 1000 - Math.floor(now.getTime() / 1000)) : diffSec;

    return timeToDiff(diffSec, minDiff, maxDiff);

}

export function timeToDiff(standardDiff: number, minDiff: number, maxDiff: number) {
    const diff = maxDiff - minDiff;

    if (diff < 75) {
        return generateTimeTo(standardDiff);
    }
    minDiff = Math.max(0, minDiff);

    if (minDiff < 10) {
        return `Due`;
    }

    if (Math.floor(minDiff / 3600) >= 1 || Math.floor(maxDiff / 3600) >= 1) {
        return generateTimeTo(minDiff);
    }

    var min_num = "";
    var max_num = "";

    min_num = `${Math.ceil(minDiff / 60)}`;
    max_num = `${Math.ceil(maxDiff / 60)}`;

    return `${min_num}-${max_num} min`;

}

export function generateTimeTo(diffSec: number) {
    if (diffSec < 30) {
        return 'Due';
    } else if (diffSec < 3600) {
        const min = Math.ceil(diffSec / 60);
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

export function timedeltaDisplay(seconds: number) {
    if (seconds < 60) {
        return `${seconds} sec`;
    } else if (seconds < 3600) {
        const min = Math.ceil(seconds / 60);
        return `${min} min`;
    } else {
        const hr = Math.floor(seconds / 3600);
        const min = Math.floor((seconds % 3600) / 60);
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