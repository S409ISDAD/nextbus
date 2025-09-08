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
    timeout: 10000,
});

api.interceptors.request.use((config) => {
    config.headers = config.headers || {};
    config.headers['X-Client-Id'] = storedClientId;
    return config;
});

api.interceptors.response.use(
    (response) => {
        const version = response.headers['x-version'];
        if (version) {
            const prevVersion = localStorage.getItem("appVersion");
            const currentVersion = version;
            if (prevVersion && prevVersion !== currentVersion) {
                toast(`Version ${currentVersion} available! Refresh to update`, { id: 'version-update-toast', duration: 3000, icon: 'ℹ️' });
            }
        }
        return response;
    },
    (error) => {
        // Check if response exists
        if (error.response) {
            const status = error.response.status;

            if (status === 429) {
                toast.error("You are being rate limited. Please slow down.", {
                    id: 'rate-limit-toast',
                    duration: 3000,
                });
            } else if (status >= 500) {
                toast.error("A server error occurred. Please try again later.", {
                    id: 'server-error-toast',
                    duration: 3000,
                });
            } else if (status >= 400) {
                toast.error(`An error occurred: ${status}`, {
                    id: 'client-error-toast',
                    duration: 3000,
                });
            }

            return Promise.reject(error);
        } else if (error.request) {
            // Request was made but no response received
            if (!navigator.onLine) {
                toast.error("No internet connection. Please check your network.", {
                    id: 'offline-toast',
                    duration: 3000,
                });
            } else {
                toast.error("Network error. Please try again later.", {
                    id: 'network-error-toast',
                    duration: 3000,
                });
            }
            return Promise.reject(error);
        } else {
            // Something else happened while setting up the request
            toast.error(`Unexpected error: ${error.message}`, {
                id: 'unexpected-toast',
                duration: 3000,
            });
            return Promise.reject(error);
        }
    }
);


export default api;