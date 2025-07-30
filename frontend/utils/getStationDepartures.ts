import api from "../src/api"
import { generateTimeTo } from "./timeTo";
import type { Train, TrainResponse } from "../models/Trains";

export const operatorMap: Record<string, { code: string, color: string }> = {
    "South Western Railway": { code: "SWR", color: "#007CAD" },
    "CrossCountry": { code: "XC", color: "#6e2067" },
    "Great Western Railway": { code: "GWR", color: "#0A493E" },
    "LNER": { code: "LNER", color: "#d50032" },
    "Avanti West Coast": { code: "AWC", color: "#00747a" },
    "TransPennine Express": { code: "TPE", color: "#512698" },
    "Northern": { code: "NT", color: "#1d1d1b" },
    "East Midlands Railway": { code: "EMR", color: "#660099" },
    "Greater Anglia": { code: "GA", color: "#e41f13" },
    "West Midlands Trains": { code: "WMT", color: "#ff8200" },
    "Chiltern Railways": { code: "CH", color: "#003366" },
    "London Overground": { code: "LO", color: "#ff6600" },
    "Thameslink": { code: "TL", color: "#e6007e" },
    "Southern": { code: "SN", color: "#00703c" },
    "Southeastern": { code: "SE", color: "#003366" },
    "c2c": { code: "C2C", color: "#e6007e" },
    "Merseyrail": { code: "ME", color: "#ffcb05" },
    "ScotRail": { code: "SR", color: "#003366" },
    "Transport for Wales": { code: "TfW", color: "#d30731" },
    "Heathrow Express": { code: "HX", color: "#5C226C" },
    "Hull Trains": { code: "HT", color: "#CC0066" },
    "Grand Central": { code: "GC", color: "#ff8200" },
    "Elizabeth line": { code: "EL", color: "#6950a1" },
    "Great Northern": { code: "GN", color: "#43165C" },
    "Lumo": { code: "LMO", color: "#0047CB" },
};

export const parseTrains = async (trains: TrainResponse) => {
    try {
        const parseTime = (timeStr: string) => {
            if (!timeStr) {
                return undefined;
            }
            const padded = timeStr.padEnd(6, "0");
            const hours = parseInt(padded.slice(0, 2), 10);
            const minutes = parseInt(padded.slice(2, 4), 10);
            const seconds = parseInt(padded.slice(4, 6), 10);
            const currentDate = new Date();
            const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), hours, minutes, seconds);
            // If the time is more than 12 hours behind now, assume it's for the next day (overnight trains)
            if (date.getTime() - currentDate.getTime() < -12 * 60 * 60 * 1000) {
                date.setDate(date.getDate() + 1);
            }
            return date;
        };

        if (!trains.services) {
            return { ...trains, services: [] };
        }

        const updatedTrains: Train[] = trains.services
            .map((train) => {

                const parseOperator = (atocName: string) => {
                    if (!atocName) return { code: "Unknown", color: "#888888" };
                    if (atocName == "Unknown") return { code: "Unknown", color: "#888888" };
                    if (operatorMap[atocName]) return operatorMap[atocName];
                    const code = atocName
                        .split(' ')
                        .map(w => w.slice(0, 1).toUpperCase())
                        .join('');
                    console.log("Unknown operator:", atocName);
                    return { code, color: "#1447E6" };
                };

                let expectedDeparture = parseTime(train.locationDetail?.realtimeDeparture ?? "");
                const scheduledDeparture = parseTime(train.locationDetail?.gbttBookedDeparture ?? "");

                let expectedArrival = parseTime(train.locationDetail?.realtimeArrival ?? "");
                const scheduledArrival = parseTime(train.locationDetail?.gbttBookedArrival ?? "");

                if (!expectedDeparture) {
                    expectedDeparture = scheduledDeparture;
                }

                if (!expectedArrival) {
                    expectedArrival = scheduledArrival;
                }

                console.log("expectedArrival", scheduledArrival, expectedArrival);
                const operator = parseOperator(train.atocName);

                console.log();

                const now = new Date();

                let delay = 0;
                let diffSec = 0;

                if (!expectedDeparture || !scheduledDeparture) {
                    delay = (expectedArrival && scheduledArrival) ? (expectedArrival.getTime() / 1000) - (scheduledArrival.getTime() / 1000) : 0;
                    diffSec = expectedArrival ? expectedArrival.getTime() / 1000 - Math.floor(now.getTime() / 1000) : 0;
                } else {
                    delay = (expectedDeparture && scheduledDeparture) ? (expectedDeparture.getTime() / 1000) - (scheduledDeparture.getTime() / 1000) : 0;
                    diffSec = expectedDeparture ? expectedDeparture.getTime() / 1000 - Math.floor(now.getTime() / 1000) : 0;
                }

                return {
                    ...train,
                    expectedDeparture,
                    scheduledDeparture,
                    expectedArrival,
                    scheduledArrival,
                    atocCode: operator.code,
                    atocColor: operator.color,
                    timeto: generateTimeTo(diffSec),
                    delay,
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
            if (!train.expectedDeparture && !train.scheduledDeparture) {
                return false; // Skip this train if no departure info
            }
            return true;
        })
        .filter(
            (train) => ((train.expectedDeparture ?? train.scheduledDeparture)?.getTime?.() ?? 0) - now.getTime() < 43200000
        )
        .filter(
            (train) => {
                const departure = train.expectedDeparture ?? train.scheduledDeparture;
                return departure && new Date(departure.getTime() + 60 * 1000) > now;
            }
        ).sort(
            (a, b) => {
                const aTime = (a.expectedDeparture ?? a.scheduledDeparture)?.getTime?.() ?? 0;
                const bTime = (b.expectedDeparture ?? b.scheduledDeparture)?.getTime?.() ?? 0;
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
            if (!train.expectedArrival && !train.scheduledArrival) {
                return false; // Skip this train if no arrival info
            }
            return true;
        })
        .filter(
            (train) => ((train.expectedArrival ?? train.scheduledArrival)?.getTime?.() ?? 0) - now.getTime() < 43200000
        )
        .filter(
            (train) => {
                const arrival = train.expectedArrival ?? train.scheduledArrival;
                return arrival && new Date(arrival.getTime() + 60 * 1000) > now;
            }
        ).sort(
            (a, b) => {
                const aTime = (a.expectedArrival ?? a.scheduledArrival)?.getTime?.() ?? 0;
                const bTime = (b.expectedArrival ?? b.scheduledArrival)?.getTime?.() ?? 0;
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


