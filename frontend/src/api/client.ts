import axios from "axios";

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    headers: {
        "Content-Type": "application/json"
    }
});

apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem("access_token");

    if(token) {
        config.headers.setAuthorization(`Bearer ${token}`);
    }

    return config;
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