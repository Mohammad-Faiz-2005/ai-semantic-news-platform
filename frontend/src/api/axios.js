/**
 * Configured Axios instance for all API communication.
 *
 * Features:
 *   - Base URL set from VITE_API_BASE_URL environment variable
 *   - Request interceptor: auto-attaches JWT Bearer token to every request
 *   - Response interceptor: handles 401 globally (clears storage + redirects)
 *   - 30 second timeout on all requests
 *
 * Usage:
 *   import api from "../api/axios";
 *   const { data } = await api.get("/auth/me");
 *   const { data } = await api.post("/search/semantic", { query, top_k });
 */

import axios from "axios";

// ── Create Instance ───────────────────────────────────────────────────────────

const api = axios.create({
  /**
   * Base URL for all requests.
   *
   * In development: reads from frontend/.env → VITE_API_BASE_URL
   *   e.g. http://localhost:8000/api/v1
   *
   * Falls back to "/api/v1" which is proxied by Vite to localhost:8000
   * (see vite.config.js proxy setting).
   */
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",

  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },

  // Abort requests that take longer than 30 seconds
  timeout: 30_000,
});

// ── Request Interceptor ───────────────────────────────────────────────────────

api.interceptors.request.use(
  (config) => {
    /**
     * Attach the JWT Bearer token to every outgoing request.
     *
     * Token is stored in localStorage by AuthContext after login/register.
     * If no token exists (user not logged in), the request is sent without it,
     * which will result in a 401 from any protected endpoint.
     */
    const token = localStorage.getItem("access_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    // Request setup failed — reject immediately
    return Promise.reject(error);
  }
);

// ── Response Interceptor ──────────────────────────────────────────────────────

api.interceptors.response.use(
  (response) => {
    /**
     * Pass successful responses through unchanged.
     * 2xx status codes land here.
     */
    return response;
  },
  (error) => {
    /**
     * Handle error responses globally.
     *
     * 401 Unauthorized:
     *   - Token is expired or invalid
     *   - Clear all auth data from localStorage
     *   - Redirect to /login page
     *   - The AuthContext will be reset on next page load
     *
     * All other errors:
     *   - Reject the promise so the calling component can handle it
     *   - Components use error.response?.data?.detail for the message
     */
    if (error.response?.status === 401) {
      // Clear stored credentials
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");

      // Only redirect if not already on login page (prevent redirect loop)
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

export default api;