import api from "../src/api"
import { isTrackedBus, type TrackedBus, type Departure, type ScheduledBus } from "../models/Bus"
import { timeToDiff } from "./timeUtils";


export interface Departures {
    buses: TrackedBus[] | ScheduledBus[];
    timestamp: string;
}

export const parseDepartures = async (departures: Departures, filter?: string) => {
    try {
        const now = new Date();
        const updatedBuses = departures.buses
            .map((bus) => {
                const expected = new Date(bus.expected);

                const now = new Date();

                const diffSec = expected.getTime() / 1000 - Math.floor(now.getTime() / 1000);
                const minDiff = 'min_expected' in bus && bus.min_expected ? (new Date(bus.min_expected).getTime() / 1000 - Math.floor(now.getTime() / 1000)) : diffSec;
                const maxDiff = 'max_expected' in bus && bus.max_expected ? (new Date(bus.max_expected).getTime() / 1000 - Math.floor(now.getTime() / 1000)) : diffSec;

                return {
                    ...bus,
                    timestamp: departures.timestamp,
                    timeTo: timeToDiff(diffSec, minDiff, maxDiff),
                };
            })
            .filter((bus) => {
                if (!filter) return true;

                if ('service' in bus && bus.service && bus.service.line_name) {
                    return bus.service.line_name == filter;
                }
                if ('line' in bus) {
                    return bus.line == filter;
                }
                return false;
            })
            .filter(
                (bus) => new Date(bus.expected).getTime() - now.getTime() < 43200000
            )
            .filter(
                (bus) => new Date(new Date(bus.expected).getTime() + 90 * 1000) > now
            )
            .sort(
                (a, b) => new Date(a.expected).getTime() - new Date(b.expected).getTime()
            )
            .sort((a, b) => {
                if (a.status === "cancelled" && b.status !== "cancelled") return -1;
                if (b.status === "cancelled" && a.status !== "cancelled") return 1;
                return 0;
            });
        const timestamp = new Date(departures.timestamp);
        return { updatedBuses, timestamp };

    } catch (error) {
        console.error("failed to get departures", error);
        return null;
    }
};

export const mostCommonDest = (departures: Departure[], lineName?: string) => {

    const destCount: { [dest: string]: number } = {};

    departures.forEach((bus) => {
        let busLineName = '';
        let busDest = '';

        if (isTrackedBus(bus)) {
            busLineName = bus.service.line_name;
        } else {
            busLineName = bus.line;
        }
        busDest = bus.destination;

        if (lineName && busLineName !== lineName) return;

        if (destCount[busDest]) {
            destCount[busDest] += 1;
        } else {
            destCount[busDest] = 1;
        }
    });

    let mostCommon = '';
    let highestCount = 0;
    for (const dest in destCount) {
        if (destCount[dest] > highestCount) {
            highestCount = destCount[dest];
            mostCommon = dest;
        }
    }
    console.log(`Most common destination for line ${lineName || 'all lines'} is ${mostCommon} with count ${highestCount}`);
    return mostCommon;
}

const fetchDepartures = async (stop_id: string, type: string, filter?: string) => {
    try {
        const response = await api.get<Departures>(
            `/departures/${type}?stop_id=${stop_id}`
        );
        return parseDepartures(response.data, filter)

    } catch (error) {
        console.error("failed to get departures", error);
        return null;
    }
};

export default fetchDepartures