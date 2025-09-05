import axios from "axios";
import toast from "react-hot-toast";
import { v4 as uuidv4 } from "uuid";

// const API_PORT = 8000;
let storedClientId = localStorage.getItem("ws-client-id");
if (!storedClientId) {
    storedClientId = uuidv4();
    localStorage.setItem("ws-client-id", storedClientId);
}

const api = axios.create({
    baseURL: '/api/v1',
});

api.interceptors.request.use((config) => {
    config.headers = config.headers || {};
    config.headers['X-Client-Id'] = storedClientId;
    return config;
});

api.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        if (error.response && error.response.status === 429) {
            toast.error(
                "You are being rate limited. Please slow down.",
                {
                    id: 'rate-limit-toast',
                    duration: 3000,
                }
            );
            return Promise.reject(error);
        } else if (error.response && error.response.status >= 500) {
            toast.error(
                "A server error occurred. Please try again later.",
                {
                    id: 'server-error-toast',
                    duration: 3000,
                }
            );
            return Promise.reject(error);
        }
    }
);


export default api;