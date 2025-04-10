import axios from 'axios';

// Create axios instance WITHOUT a base URL.
// API calls will use relative paths (e.g., '/api/v1/auth/token').
// Nginx will handle proxying these requests to the backend container.
const api = axios.create({
  // baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000', // REMOVED
});

// Add request interceptor to include auth token in headers
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // Ensure relative URLs are used if baseURL was removed
  // (axios usually handles this automatically if baseURL is not set)
  // config.url = config.url?.startsWith('/') ? config.url : `/${config.url}`;
  return config;
});

export default api;
