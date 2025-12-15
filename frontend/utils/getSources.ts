import { type DataSource, type DetailedDataSource } from "../models/DataSource";
import api from "../src/api"

const getSources = async () => {
    try {
        const response = await api.get<DataSource[]>(
            `/sources/`
        );

        return response.data;
    } catch (error) {
        console.error("failed to get sources", error);
        return [];
    }
};

const getDataSource = async (source_id: number) => {
    try {
        const response = await api.get<DetailedDataSource>(
            `/sources/${source_id}/`
        );
        return response.data;
    } catch (error) {
        console.error("failed to get source", error);
        return null;
    }
};

export { getSources, getDataSource };