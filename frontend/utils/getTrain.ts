import type { ServiceLocation, TrainService } from "../models/Trains";
import api from "../src/api";
import { generateTimeTo } from "./timeUtils";

export const parseTrain = async (train: TrainService) => {
    try {

        const updatedStops: ServiceLocation[] = train.locations
            .map((location) => {
                const now = new Date();
                let diffSec = 0;

                if (!location.expectedDeparture || !location.scheduledDeparture) {
                    diffSec = location.expectedArrival ? new Date(location.expectedArrival).getTime() / 1000 - Math.floor(now.getTime() / 1000) : 0;
                } else {

                    diffSec = location.expectedDeparture ? new Date(location.expectedDeparture).getTime() / 1000 - Math.floor(now.getTime() / 1000) : 0;
                }

                return {
                    ...location,
                    timeTo: generateTimeTo(diffSec),
                };
            })

        return {
            ...train,
            locations: updatedStops,
        };

    } catch (error) {
        console.error("failed to get departures", error);
        return null;
    }
};

export const fetchTrain = async (service_id: string) => {
    try {
        const response = await api.get<TrainService>(
            `/trains/service/?service_id=${service_id}`
        );

        console.log("train", response.data);
        const train = await parseTrain(response.data);
        return train;

    } catch (error) {
        console.error("failed to get arrivals", error);
        return null;
    }
};