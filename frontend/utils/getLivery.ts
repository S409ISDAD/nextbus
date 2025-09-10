import type { Livery } from "../models/Livery"
import api from "../src/api"


const getLivery = async (id: number) => {
    const response = await api.get<Livery>(`/liveries/?id=${id}`)

    return response.data

}

export default getLivery;