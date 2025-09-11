import type { Search } from "../models/Search"
import api from "../src/api"


const doSearch = async (query: string) => {
    const response = await api.get<Search>(`/search/?query=${encodeURIComponent(query)}`)

    return response.data

}

export default doSearch;