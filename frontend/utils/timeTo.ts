import type { Bus } from "../models/Bus";

export default function timeTo(bus: Bus) {
    const now = new Date()
    const diffMs = bus.expected.getTime() - now.getTime();

    const min = Math.floor(diffMs / 1000 / 60);

    if (min < 1) {
        return 'Due'
    } else if (min < 60) {
        return `${min} min`
    } else {
        return `${Math.floor(min / 60)} h`
    }
}

export function lateness(delay: number) {
    const n_delay = Math.abs(delay)

    var output = ""

    if (n_delay > 15 && n_delay < 60) {
        output += `${n_delay}s`
    } else if (n_delay >= 60) {
        output += `${Math.floor(n_delay / 60)}m`
    } else {
        output += "On time"
    }

    if (delay < -15) {
        output += " early"
    } else if (delay > 15) {
        output += " late"
    }

    return output
}