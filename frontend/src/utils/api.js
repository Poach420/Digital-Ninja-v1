import axios from 'axios';

const envUrl = process.env.REACT_APP_BACKEND_URL;

// Prefer explicit env; else same-origin; else localhost:8000 for local dev
const inferredBase =
  envUrl ||
  (typeof window !== 'undefined' && window.location.origin
    ? `${window.location.origin}`
    : 'http://localhost:8000');

const BACKEND_URL = inferredBase;
const API = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', {
      url: error.config?.url,
      status: error.response?.status,
      data: error.response?.data
    });
    
    if (error.response?.status === 401) {
      // Only redirect if not already on login/callback pages
      const currentPath = window.location.pathname;
      if (!['/login', '/register', '/auth/callback'].includes(currentPath)) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export { api, API, BACKEND_URL };
export default api;