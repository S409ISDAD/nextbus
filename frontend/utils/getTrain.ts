import type { ServiceLocation, TrainService } from "../models/Trains";
import api from "../src/api";
import { operatorMap } from "../utils/getStationDepartures";
import { generateTimeTo } from "./timeTo";

export const parseTrain = async (train: TrainService) => {
    try {
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
        const parseTime = (timeStr: string) => {
            if (!timeStr) {
                return null;
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

        const operator = parseOperator(train.atocName);

        const updatedStops: ServiceLocation[] = train.locations
            .map((location) => {

                let expectedDeparture = parseTime(location?.realtimeDeparture ?? "") || undefined;
                const scheduledDeparture = parseTime(location?.gbttBookedDeparture ?? "") || undefined;

                let expectedArrival = parseTime(location?.realtimeArrival ?? "") || undefined;
                const scheduledArrival = parseTime(location?.gbttBookedArrival ?? "") || undefined;

                if (!expectedDeparture) {
                    expectedDeparture = scheduledDeparture;
                }

                if (!expectedArrival) {
                    expectedArrival = scheduledArrival;
                }

                console.log("expectedArrival", scheduledArrival, expectedArrival);

                console.log();

                const now = new Date();

                let departed = false;

                if (expectedDeparture && expectedDeparture.getTime() < now.getTime()) {
                    departed = true;
                }

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
                    ...location,
                    expectedDeparture,
                    scheduledDeparture,
                    expectedArrival,
                    scheduledArrival,
                    delay,
                    departed,
                    timeTo: generateTimeTo(diffSec),
                };
            })

        const nextStation = updatedStops.find(stop => !stop.departed);
        const sequence = nextStation ? updatedStops.indexOf(nextStation) : updatedStops.length;
        const delay = nextStation ? nextStation.delay : updatedStops[updatedStops.length - 1].delay;



        return {
            ...train,
            locations: updatedStops,
            atocCode: operator.code,
            atocColor: operator.color,
            delay,
            sequence,
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

        const train = await parseTrain(response.data);
        return train;

    } catch (error) {
        console.error("failed to get arrivals", error);
        return null;
    }
};