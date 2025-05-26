import api from "../src/api"

interface Progress {
    sequence: number;
    prev_stop: string;
    next_stop: string;
    progress: number;
}

export interface BusResponse {
    progress: Progress
}

const getBus = async (bus_id: string) => {
    try {
        const response = await api.get<[BusResponse]>(
            `/buses/?bus_id=${bus_id}`
        );

        console.log(response.data[0])

        return response.data[0]

    } catch (error) {
        console.error("failed to get bus", error);
        return null;
    }
};

export default getBus