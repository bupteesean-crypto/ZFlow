import axios from "axios";

const request = axios.create({
  baseURL: "http://localhost:8000/api/v1",
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
