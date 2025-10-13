import api from "../src/api"

import type { ServiceInfo } from "../models/ServiceInfo";
import type { ServiceResult } from "../models/Search";


export const getService = async (service_id: string) => {
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

export const getDBService = async (service_id: string) => {
    try {
        const response = await api.get<ServiceResult>(
            `/lines/${service_id}`
        );

        var data = response.data;

        const bothEmpty = data.outbound_description === "" && data.inbound_description === "";

        if (bothEmpty) {
            data.outbound_description = data.destination !== "" ? `To ${data.destination}` : "Outbound";
            data.inbound_description = data.origin !== "" ? `To ${data.origin}` : "Inbound";
        }

        return data;

    } catch (error) {
        console.error("failed to get service", error);
        return null;
    }
};