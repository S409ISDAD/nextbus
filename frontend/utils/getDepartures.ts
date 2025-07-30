import api from "../src/api"
import type { Bus, ScheduledBus } from "../models/Bus"
import { generateTimeTo } from "./timeUtils";

interface DeparturesResponse {
    timestamp: number;
    buses: any[];
}

export interface Departures {
    buses: Bus[] | ScheduledBus[];
    timestamp: Date;
}

export const parseDepartures = async (departures: DeparturesResponse, filter?: string) => {
    try {
        const now = new Date();
        const updatedBuses: Bus[] | ScheduledBus[] = departures.buses
            .map((bus) => {
                const expected = new Date(bus.expected * 1000);
                const scheduled = new Date(bus.scheduled * 1000);
                const timestamp = new Date(bus.timestamp * 1000);

                const now = new Date();

                const diffSec = bus.expected - Math.floor(now.getTime() / 1000);

                return {
                    ...bus,
                    expected,
                    scheduled,
                    timestamp,
                    timeto: generateTimeTo(diffSec),
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
                (bus) => bus.expected.getTime() - now.getTime() < 43200000
            )
            .filter(
                (bus) => new Date(bus.expected.getTime() + 60 * 1000) > now
            )
            .sort(
                (a, b) => a.expected.getTime() - b.expected.getTime()
            );
        const timestamp = new Date(departures.timestamp * 1000)
        return { updatedBuses, timestamp }

    } catch (error) {
        console.error("failed to get departures", error);
        return null;
    }
};

const fetchDepartures = async (stop_id: string, type: string, filter?: string) => {
    try {
        const response = await api.get<DeparturesResponse>(
            `/departures/${type}?stop_id=${stop_id}`
        );
        return parseDepartures(response.data, filter)

    } catch (error) {
        console.error("failed to get departures", error);
        return null;
    }
};

export default fetchDepartures