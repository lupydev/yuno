import axios from "axios";

const apiBackClient = axios.create({
    baseURL:
        import.meta.env.VITE_API_BASE_URL ||
        "https://sara-bi-back-658525748312.us-east1.run.app/api",
    timeout: import.meta.env.VITE_API_TIMEOUT
        ? Number.parseInt(import.meta.env.VITE_API_TIMEOUT)
        : 30000,
    withCredentials: true,
});

apiBackClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            console.warn(
                "⚠️ Session expired or invalid. Redirecting to login..."
            );
        }
        return Promise.reject(error);
    }
);

export default apiBackClient;
