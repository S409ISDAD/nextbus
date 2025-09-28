import type { Locality, Region, AdminArea, District } from "../models/Places";
import api from "../src/api"

const getRegions = async () => {
    try {
        const response = await api.get<Region[]>(
            `/places/regions/`
        );

        return response.data;
    } catch (error) {
        console.error("failed to get regions", error);
        return [];
    }
};

const getRegion = async (region_id: string) => {
    try {
        const response = await api.get<Region>(
            `/places/regions/${region_id}/`
        );
        return response.data;
    } catch (error) {
        console.error("failed to get region", error);
        return null;
    }
};

const getAdminArea = async (admin_area_id: string) => {
    try {
        const response = await api.get<AdminArea>(
            `/places/admin_areas/${admin_area_id}/`
        );
        return response.data;
    } catch (error) {
        console.error("failed to get admin area", error);
        return null;
    }
};

const getDistrict = async (district_id: string) => {
    try {
        const response = await api.get<District>(
            `/places/districts/${district_id}/`
        );
        return response.data;
    } catch (error) {
        console.error("failed to get district", error);
        return null;
    }
};

const getLocality = async (locality_id: string) => {
    try {
        const response = await api.get<Locality>(
            `/places/localities/${locality_id}/`
        );
        return response.data;
    } catch (error) {
        console.error("failed to get locality", error);
        return null;
    }
};

export { getRegions, getRegion, getAdminArea, getDistrict, getLocality };