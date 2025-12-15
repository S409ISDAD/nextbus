import type { Region, RegionDetails, AdminAreaDetails, DistrictDetails, LocalityDetails } from "../models/Places";
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
        const response = await api.get<RegionDetails>(
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
        const response = await api.get<AdminAreaDetails>(
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
        const response = await api.get<DistrictDetails>(
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
        const response = await api.get<LocalityDetails>(
            `/places/localities/${locality_id}/`
        );
        return response.data;
    } catch (error) {
        console.error("failed to get locality", error);
        return null;
    }
};

export { getRegions, getRegion, getAdminArea, getDistrict, getLocality };