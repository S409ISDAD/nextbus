import api from "../src/api"


import type { StopTime } from "../models/StopTime";

export interface ResponseStopTime {
    atco_code: string
    name: string;
    aimed_departure_time: number;
    actual_departure_time?: number;
}

export interface ResponseJourney {
    route_name: string;
    destination: string;
    stops: ResponseStopTime[]
}

const getJourney = async (bus_id: string, journey_id: string) => {
    try {
        const response = await api.get<ResponseJourney>(
            `/journeys/?bus_id=${bus_id}&journey_id=${journey_id}`
        );

        const stops: StopTime[] = response.data.stops.map((stop) => {
            const aimed_departure_time = new Date(stop.aimed_departure_time * 1000);

            const actual_departure_time = stop.actual_departure_time ? new Date(stop.actual_departure_time * 1000) : undefined;

            const stop_id = stop.atco_code

            return {
                stop_id,
                ...stop,
                aimed_departure_time,
                actual_departure_time,
            };
        })

        const route_name = response.data.route_name
        const destination = response.data.destination

        return { route_name, destination, stops }

    } catch (error) {
        console.error("failed to get journey", error);
        return null;
    }
};

export default getJourney