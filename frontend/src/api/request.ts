import axios from "axios";

const baseURL =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD ? "/api/v1" : "http://localhost:8000/api/v1");

const request = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

request.interceptors.request.use(config => {
  const token = sessionStorage.getItem('session_token') || sessionStorage.getItem('sessionToken');
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default request;
