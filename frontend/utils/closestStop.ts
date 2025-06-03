import api from "../src/api"


interface closestStop {
    stop_id: string;
    dist: number;
    lat: number;
    lng: number;
}

function getCurrentPosition(): Promise<GeolocationPosition> {
    return new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject);
    });
}

const getClosestStop = async (position: number[], ignore?: string) => {
    const lat = position[0]
    const lng = position[1]

    const response = await api.get<closestStop>(`/location/closest?lat=${lat}&lng=${lng}&ignore=${ignore}`)

    const stop_id = response.data.stop_id

    return stop_id

}

export default getClosestStop;
export { getCurrentPosition };