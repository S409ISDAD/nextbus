import type { ProgressInfo } from "../models/ProgressInfo";
import type { ServiceInfo } from "../models/ServiceInfo";
import type { Prediction } from "../models/Bus";
import type { Livery } from "../models/Livery"
import api from "../src/api"
import type { StopTime } from "../models/StopTime";

export interface ResponseStopTime {
    stop_id: string
    name: string;
    aimed_time: number;
    actual_time?: number;
    expt_time?: number;
    minor: boolean;
}

export interface ResponseJourney {
    route_name: string;
    destination: string;
    stops: ResponseStopTime[]
}

export interface BusResponse {
    id: number;
    service: ServiceInfo;
    destination: string;
    reg: string;
    fleet_num: string;
    journey_id: number;
    delay: number;
    expected?: number;
    scheduled?: number;
    started: boolean;
    finished: boolean;
    progress?: ProgressInfo;
    predictions: Prediction[]
    journey: ResponseJourney
    livery?: Livery
    coords?: number[];
    timeto: number;
    status: string;
}

const getBus = async (bus_id: string) => {
    try {
        const response = await api.get<BusResponse>(
            `/buses/?bus_id=${bus_id}`
        );

        const bus = response.data;

        const expected = new Date(bus.expected ? bus.expected * 1000 : 0);
        const scheduled = new Date(bus.scheduled ? bus.scheduled * 1000 : 0);


        const stops: StopTime[] = bus.journey.stops.map((stop) => {
            return {
                stop_id: stop.stop_id,
                name: stop.name,
                aimed_time: new Date(stop.aimed_time * 1000),
                actual_time: stop.actual_time ? new Date(stop.actual_time * 1000) : undefined,
                expt_time: stop.expt_time ? new Date(stop.expt_time * 1000) : undefined,
                minor: stop.minor,
            };
        });

        return {
            ...bus,
            expected,
            scheduled,
            journey: {
                ...bus.journey,
                stops,
            },
            timeto: ""
        };

    } catch (error) {
        console.error("failed to get bus", error);
        return null;
    }
};

export default getBus