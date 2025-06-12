import axios from "axios";

// const API_PORT = 8000;

export default axios.create({
    baseURL: '/api/v1',
})