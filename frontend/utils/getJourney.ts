import api from "../src/api"

import type { Trip } from "../models/Journey";


export const getDBJourney = async (journey_id: number) => {
    try {
        const response = await api.get<Trip>(
            `/journeys/dbjourney/${journey_id}`
        );

        return response.data;

    } catch (error) {
        console.error("failed to get journey", error);
        return null;
    }
};


export const getTrip = async (trip_id: number) => {
    try {
        const response = await api.get<Trip>(
            `/journeys/trip/${trip_id}`
        );
        return response.data;

    } catch (error) {
        console.error("failed to get trip", error);
        return null;
    }
}