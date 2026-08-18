import axios from "axios";

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    withCredentials: true,
    headers: {
        "Content-Type": "application/json"
    }
});

apiClient.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        if(error.response?.status === 401) {
            console.log("User is not authenticated");
        }

        return Promise.reject(error);
    }
);

export default apiClient;