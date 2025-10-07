/**
 * Axios API Instance
 *
 * This file creates a configured Axios instance for making HTTP requests to the backend.
 * It includes:
 * - Base URL configuration
 * - Request interceptor (adds JWT token to all requests)
 * - Response interceptor (handles 401 unauthorized errors)
 */

import axios from 'axios'

// Create axios instance with default configuration
const api = axios.create({
  // Get base URL from environment variable (.env file)
  // Falls back to localhost if not defined
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Request Interceptor
 * Runs before every request is sent
 * Automatically adds JWT token to Authorization header if it exists
 */
api.interceptors.request.use(
  (config) => {
    // Get JWT token from localStorage
    const token = localStorage.getItem('token')
    if (token) {
      // Add token to request headers
      // Format: "Authorization: Bearer <token>"
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    // If request setup fails, reject the promise
    return Promise.reject(error)
  }
)

/**
 * Response Interceptor
 * Runs after every response is received
 * Handles 401 (Unauthorized) errors by logging user out
 */
api.interceptors.response.use(
  // If response is successful, just return it
  (response) => response,
  (error) => {
    // If response status is 401 (Unauthorized), token is invalid or expired
    // Don't redirect if it's the login endpoint (expected 401 for invalid credentials)
    const isLoginEndpoint = error.config?.url?.includes('/auth/login')

    if (error.response?.status === 401 && !isLoginEndpoint) {
      // Clear authentication data from localStorage
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      // Redirect to login page
      window.location.href = '/login'
    }
    // Reject the promise with the error
    return Promise.reject(error)
  }
)

export default api
