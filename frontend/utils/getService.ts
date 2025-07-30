import api from "../src/api"

import type { ServiceInfo } from "../models/ServiceInfo";


const getService = async (service_id: string) => {
    try {
        const response = await api.get<ServiceInfo>(
            `/services/?service_id=${service_id}`
        );

        const id = response.data.id
        const line_name = response.data.line_name
        const detail = response.data.detail

        return { id, line_name, detail };

    } catch (error) {
        console.error("failed to get stop", error);
        return null;
    }
};

export default getService