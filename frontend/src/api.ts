import axios from "axios";
import toast from "react-hot-toast";

// const API_PORT = 8000;

const api = axios.create({
    baseURL: '/api/v1',
})

let rateLimitToastId: string | null = null;

api.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        if (error.response && error.response.status === 429) {
            if (!rateLimitToastId) {
                rateLimitToastId = toast.error(
                    "You are being rate limited. Please slow down.",
                    {
                        icon: '⚠️',
                        style: {
                            borderRadius: '10px',
                            background: '#222',
                            color: '#fff',
                        },
                        id: 'rate-limit-toast',
                        duration: 4000,
                    }
                );
            }
        }
        return Promise.reject(error);
    }
);


export default api;