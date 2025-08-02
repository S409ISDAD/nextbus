import api from "../src/api"
import { generateTimeTo } from "./timeUtils";
import type { Train, StationResponse, TrainService } from "../models/Trains";

export const parseTrains = async (trains: StationResponse) => {
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
                    timeTo: generateTimeTo(diffSec),

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

export const parseTrainsRoute = async (trains: TrainService[]) => {
    try {

        if (!trains) {
            return [];
        }

        let fastest_train_idx = 0;
        let fastest_train_time = Infinity;

        const updatedTrains: TrainService[] = trains
            .map((train, idx) => {
                const now = new Date();
                let diffSec = 0;

                if (!train.fromStop || !train.fromStop.expectedDeparture || !train.fromStop.scheduledDeparture) {
                    diffSec = train.fromStop && train.fromStop.expectedArrival ? new Date(train.fromStop.expectedArrival).getTime() / 1000 - Math.floor(now.getTime() / 1000) : 0;
                } else {
                    diffSec = train.fromStop.expectedDeparture ? new Date(train.fromStop.expectedDeparture).getTime() / 1000 - Math.floor(now.getTime() / 1000) : 0;
                }
                if (train.duration && train.duration < fastest_train_time) {
                    fastest_train_time = train.duration;
                    fastest_train_idx = idx;
                }

                return {
                    ...train,
                    timeTo: generateTimeTo(diffSec),
                    fastest: false,

                };
            }).filter((train) => train.serviceType === "train")

        if (updatedTrains.length > 0) {
            updatedTrains[fastest_train_idx].fastest = true;
        }

        return updatedTrains;

    } catch (error) {
        console.error("failed to get departures", error);
        return [];
    }
};

export const filterDepartures = (trains: StationResponse) => {
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

export const filterRoute = (trains: TrainService[]) => {
    const now = new Date();
    const newTrains = (trains ?? [])
        .filter((train) => {
            if (!train.fromStop || (!train.fromStop.expectedDeparture && !train.fromStop.scheduledDeparture)) {
                return false; // Skip this train if no departure info
            }
            return true;
        })
        .filter(
            (train) => (new Date(train.fromStop?.expectedDeparture ?? train.fromStop?.scheduledDeparture ?? "")?.getTime?.() ?? 0) - now.getTime() < 43200000
        )
        .filter(
            (train) => {
                const departure = train.fromStop?.expectedDeparture ?? train.fromStop?.scheduledDeparture;
                return departure && new Date(new Date(departure).getTime() + 60 * 1000) > now;
            }
        ).sort(
            (a, b) => {
                const aTime = new Date(a.toStop?.expectedArrival ?? a.toStop?.scheduledDeparture ?? "")?.getTime?.() ?? 0;
                const bTime = new Date(b.toStop?.expectedArrival ?? b.toStop?.scheduledDeparture ?? "")?.getTime?.() ?? 0;
                return aTime - bTime;
            }
        );

    return newTrains
};

export const filterArrivals = (trains: StationResponse) => {
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

export const fetchRoute = async (from: string, to: string) => {
    try {
        const response = await api.get<TrainService[]>(
            `/trains/${from}/to/${to}`
        );
        const trains = await parseTrainsRoute(response.data);
        if (!trains) {
            return null;
        }

        return filterRoute(trains);

    } catch (error) {
        console.error("failed to get departures", error);
        return null;
    }
};

export const fetchDepartures = async (station_id: string) => {
    try {
        const response = await api.get<StationResponse>(
            `/trains/station/${station_id}?type=departures`
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
        const response = await api.get<StationResponse>(
            `/trains/station/${station_id}?type=arrivals`
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


