import api from "../src/api"


interface closestStop {
    stop_id: string;
    dist: number;
    lat: number;
    lon: number;
    active_now: boolean;
}



export const getClosestStops = async (position: number[], ignore?: string, limit: number = 1) => {
    const lat = position[0]
    const lon = position[1]

    const response = await api.post<closestStop[]>(`/location/closest?dist=0.01&ignore=${ignore}&limit=${limit}`,
        {
            lat: lat,
            lon: lon,
        }
    )

    return response.data

}

export const getClosestStopForService = async (position: number[], service_id: string) => {
    const lat = position[0]
    const lon = position[1]

    const response = await api.post<closestStop>(`/location/closestforservice?dist=0.01&service_id=${service_id}`,
        { lat: lat, lon: lon }
    )
    console.log("closest_stop_for_service", response)

    const stop_id = response.data.stop_id

    return stop_id

}