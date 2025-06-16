import type { Bus } from "../models/Bus";

export default function timeTo(bus: Bus) {
    const now = new Date()
    const diffMs = bus.expected.getTime() - now.getTime();
    const diffSec = Math.floor(diffMs / 1000);

    return generateTimeTo(diffSec)

}

export function generateTimeTo(diffSec: number) {
    if (diffSec <= 0) {
        return 'Due';
    } else if (diffSec < 60) {
        return '1 min';
    } else if (diffSec < 3600) {
        const min = Math.floor(diffSec / 60);
        return `${min} min`;
    } else {
        const hr = Math.floor(diffSec / 3600);
        return `${hr} h`;
    }
}

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