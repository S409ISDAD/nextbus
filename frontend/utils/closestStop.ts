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

const getClosestStop = async (position: GeolocationPosition) => {
    const lat = position.coords.latitude
    const lng = position.coords.longitude

    try {
        const response = await api.get<closestStop>(`/location/closest?lat=${lat}&lng=${lng}`)

        const stop_id = response.data.stop_id

        return stop_id
    } catch (error) {
        console.error(error)
        return "Unable to get closest stop."
    }
}

export default getClosestStop;
export { getCurrentPosition };