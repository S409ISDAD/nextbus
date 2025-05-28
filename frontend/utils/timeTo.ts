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