import axios from "axios";
import toast from "react-hot-toast";

// const API_PORT = 8000;

const api = axios.create({
    baseURL: '/api/v1',
})

api.interceptors.response.use(
    (response) => {
        return response;

    },
    (error) => {
        if (error.response && error.response.status === 429) {
            toast.error(
                "You are being rate limited. Please slow down.",
                {
                    style: {
                        borderRadius: '20px',
                        background: '#222',
                        color: '#fff',
                        border: '1px solid #363636',
                    },
                    id: 'rate-limit-toast',
                    duration: 3000,
                }
            );
            return Promise.reject(error);
        }
    }
);


export default api;