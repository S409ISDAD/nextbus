import type {Locality} from "../models/Locality"
import api from "../src/api"
import type {PossibleJourney} from "../models/PossibleJourneys";


export const getDestinations = async (position: number[], datetime: string | undefined) => {
    const response = await api.get<Locality[]>(`/planning/destinations?lat=${position[0]}&lon=${position[1]}${datetime ? `&datetime=${encodeURIComponent(datetime)}` : ""}`)

    return response.data
}

export const getLocality = async (id: string) => {
    const response = await api.get<Locality>(`/planning/locality/${id}`)

    return response.data
}


export const getPossibleJourneys = async (position: number[], locality: string, datetime: string | undefined) => {
    const response = await api.get<PossibleJourney[]>(`/planning/journeys?lat=${position[0]}&lon=${position[1]}&locality=${locality}${datetime ? `&datetime=${encodeURIComponent(datetime)}` : ""}`)

    return response.data;
}
