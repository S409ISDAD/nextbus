import api from "../src/api"

import type { Timetable } from "../models/Timetable";


export const getTimetable = async (service_id: number, inbound: boolean = true) => {
    try {
        const response = await api.get<Timetable>(
            `/timetable/${service_id}?inbound=${inbound}`
        );

        return response.data;

    } catch (error) {
        console.error("failed to get timetable", error);
        return null;
    }
};