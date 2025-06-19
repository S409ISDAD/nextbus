import api from "../src/api"
import type { Bus, ScheduledBus } from "../models/Bus"
import { generateTimeTo } from "./timeTo";

interface DeparturesResponse {
    timestamp: number;
    stop_name: string;
    buses: any[];
}

export interface Departures {
    buses: Bus[] | ScheduledBus[];
    stop_name: string;
    timestamp: Date;
}

const fetchDepartures = async (stop_id: string) => {
    try {
        const response = await api.get<DeparturesResponse>(
            `/departures/?stop_id=${stop_id}`
        );
        const now = new Date();
        const updatedBuses: Bus[] | ScheduledBus[] = response.data.buses
            .map((bus) => {
                const expected = new Date(bus.expected * 1000);
                const scheduled = new Date(bus.scheduled * 1000);

                const now = new Date()

                const diffSec = bus.expected - Math.floor(now.getTime() / 1000);

                return {
                    ...bus,
                    expected,
                    scheduled,
                    timeto: generateTimeTo(diffSec),
                };
            })
            .filter(
                (bus) => new Date(bus.expected.getTime() + 60 * 1000) > now
            ).sort(
                (a, b) => a.expected.getTime() - b.expected.getTime()
            );
        const stop_name = response.data.stop_name
        console.log(response.data.timestamp)
        const timestamp = new Date(response.data.timestamp * 1000)
        return { updatedBuses, stop_name, timestamp }

    } catch (error) {
        console.error("failed to get departures", error);
        return null;
    }
};

export default fetchDepartures