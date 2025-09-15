import api from "../src/api"
import type { Bus, ScheduledBus } from "../models/Bus"
import { timeToDiff } from "./timeUtils";


export interface Departures {
    buses: Bus[] | ScheduledBus[];
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
                    timeTo: timeToDiff(minDiff, maxDiff),
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
            );
        const timestamp = new Date(departures.timestamp);
        return { updatedBuses, timestamp };

    } catch (error) {
        console.error("failed to get departures", error);
        return null;
    }
};

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