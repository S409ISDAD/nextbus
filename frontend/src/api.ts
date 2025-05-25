import axios from "axios";

const API_PORT = 8000;

export default axios.create({
    baseURL: `${window.location.protocol}//${window.location.hostname}:${API_PORT}/api/v1`,
})