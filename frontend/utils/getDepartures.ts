import api from "../src/api"
import type { Bus } from "../models/Bus"

interface DeparturesResponse {
    timestamp: number;
    stop_name: string;
    buses: any[];
}

export interface Departures {
    buses: Bus[];
    stop_name: string;
    timestamp: Date;
}

const fetchDepartures = async (stop_id: string) => {
    try {
        const response = await api.get<DeparturesResponse>(
            `/departures/?stop_id=${stop_id}`
        );
        const now = new Date();
        const updatedBuses: Bus[] = response.data.buses
            .map((bus) => {
                const expected = new Date(bus.expected * 1000);
                const scheduled = new Date(bus.scheduled * 1000);

                const diffMs = expected.getTime() - now.getTime();

                const min = Math.round(diffMs / 1000 / 60);

                return {
                    ...bus,
                    expected,
                    scheduled,
                    timeto: min < 1 ? "Due" : `${min} min`,
                };
            })
            .filter((bus) => bus.expected > now)
            .sort(
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