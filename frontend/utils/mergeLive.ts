import type { Departure } from "../models/Bus";

export default function mergeLive(scheduled: Departure[], live: Departure[]): Departure[] {
    const liveMap = new Map<number, Departure>(
        live.map(bus => [bus.trip, bus])
    );

    const merged = scheduled.map(bus => {
        const liveBus = liveMap.get(bus.trip);
        return liveBus ?? bus;
    });

    merged.sort((a, b) => a.expected.getTime() - b.expected.getTime());

    return merged;
}