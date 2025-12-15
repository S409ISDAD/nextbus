import type { SearchResponse } from "../models/Search"
import api from "../src/api"


const doSearch = async (query: string) => {
    const response = await api.get<SearchResponse>(`/search/?query=${encodeURIComponent(query)}`)

    return response.data

}

export default doSearch;