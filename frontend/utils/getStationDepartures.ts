import api from "../src/api"
import { generateTimeTo } from "./timeUtils";
import type { Train, TrainResponse } from "../models/Trains";

export const parseTrains = async (trains: TrainResponse) => {
    try {

        if (!trains.services) {
            return { ...trains, services: [] };
        }

        const updatedTrains: Train[] = trains.services
            .map((train) => {
                const now = new Date();
                let diffSec = 0;

                if (!train.locationDetail.expectedDeparture || !train.locationDetail.scheduledDeparture) {
                    diffSec = train.locationDetail.expectedArrival ? new Date(train.locationDetail.expectedArrival).getTime() / 1000 - Math.floor(now.getTime() / 1000) : 0;
                } else {
                    diffSec = train.locationDetail.expectedDeparture ? new Date(train.locationDetail.expectedDeparture).getTime() / 1000 - Math.floor(now.getTime() / 1000) : 0;
                }

                return {
                    ...train,
                    timeto: generateTimeTo(diffSec),

                };
            }).filter((train) => train.serviceType === "train")


        return {
            ...trains,
            services: updatedTrains
        };

    } catch (error) {
        console.error("failed to get departures", error);
        return null;
    }
};

export const filterDepartures = (trains: TrainResponse) => {
    const now = new Date();
    const newTrains = (trains.services ?? [])
        .filter((train) => {
            if (!train.locationDetail.expectedDeparture && !train.locationDetail.scheduledDeparture) {
                return false; // Skip this train if no departure info
            }
            return true;
        })
        .filter(
            (train) => (new Date(train.locationDetail.expectedDeparture ?? train.locationDetail.scheduledDeparture ?? "")?.getTime?.() ?? 0) - now.getTime() < 43200000
        )
        .filter(
            (train) => {
                const departure = train.locationDetail.expectedDeparture ?? train.locationDetail.scheduledDeparture;
                return departure && new Date(new Date(departure).getTime() + 60 * 1000) > now;
            }
        ).sort(
            (a, b) => {
                const aTime = new Date(a.locationDetail.expectedDeparture ?? a.locationDetail.scheduledDeparture ?? "")?.getTime?.() ?? 0;
                const bTime = new Date(b.locationDetail.expectedDeparture ?? b.locationDetail.scheduledDeparture ?? "")?.getTime?.() ?? 0;
                return aTime - bTime;
            }
        );

    return {
        ...trains,
        services: newTrains
    };
};

export const filterArrivals = (trains: TrainResponse) => {
    const now = new Date();
    const newTrains = (trains.services ?? [])
        .filter((train) => {
            if (!train.locationDetail.expectedArrival && !train.locationDetail.scheduledArrival) {
                return false; // Skip this train if no arrival info
            }
            return true;
        })
        .filter(
            (train) => (new Date(train.locationDetail.expectedArrival ?? train.locationDetail.scheduledArrival ?? "")?.getTime?.() ?? 0) - now.getTime() < 43200000
        )
        .filter(
            (train) => {
                const arrival = train.locationDetail.expectedArrival ?? train.locationDetail.scheduledArrival;
                return arrival && new Date(new Date(arrival).getTime() + 60 * 1000) > now;
            }
        ).sort(
            (a, b) => {
                const aTime = new Date(a.locationDetail.expectedArrival ?? a.locationDetail.scheduledArrival ?? "")?.getTime?.() ?? 0;
                const bTime = new Date(b.locationDetail.expectedArrival ?? b.locationDetail.scheduledArrival ?? "")?.getTime?.() ?? 0;
                return aTime - bTime;
            }
        );

    return {
        ...trains,
        services: newTrains
    };
};

export const fetchDepartures = async (station_id: string) => {
    try {
        const response = await api.get<TrainResponse>(
            `/trains/station/?station_code=${station_id}&type=departures`
        );
        const trains = await parseTrains(response.data);
        if (!trains) {
            return null;
        }

        return filterDepartures(trains);

    } catch (error) {
        console.error("failed to get departures", error);
        return null;
    }
};

export const fetchArrivals = async (station_id: string) => {
    try {
        const response = await api.get<TrainResponse>(
            `/trains/station/?station_code=${station_id}&type=arrivals`
        );
        const trains = await parseTrains(response.data);
        if (!trains) {
            return null;
        }
        return filterArrivals(trains);

    } catch (error) {
        console.error("failed to get arrivals", error);
        return null;
    }
};


