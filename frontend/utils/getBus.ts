import type { ProgressInfo } from "../models/ProgressInfo";
import type { ServiceInfo } from "../models/ServiceInfo";
import api from "../src/api"

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
    progress?: ProgressInfo;
    coords?: number[];
}

const getBus = async (bus_id: string) => {
    try {
        const response = await api.get<BusResponse>(
            `/buses/?bus_id=${bus_id}`
        );

        console.log(response.data)

        return response.data

    } catch (error) {
        console.error("failed to get bus", error);
        return null;
    }
};

export default getBus