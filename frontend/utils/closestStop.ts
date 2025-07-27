import api from "../src/api"


interface closestStop {
    stop_id: string;
    dist: number;
    lat: number;
    lng: number;
}



export const getClosestStop = async (position: number[], ignore?: string) => {
    const lat = position[0]
    const lng = position[1]

    const response = await api.get<closestStop>(`/location/closest?lat=${lat}&lng=${lng}&dist=0.01&ignore=${ignore}`)

    const stop_id = response.data.stop_id

    return stop_id

}

export const getClosestStopForService = async (position: number[], service_id: string) => {
    const lat = position[0]
    const lng = position[1]

    const response = await api.get<closestStop>(`/location/closestforservice?lat=${lat}&lng=${lng}&dist=0.01&service_id=${service_id}`)
    console.log("closest_stop_for_service", response)

    const stop_id = response.data.stop_id

    return stop_id

}