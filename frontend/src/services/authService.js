/**
 * Authentication Service
 *
 * This service handles all authentication-related API calls:
 * - Register new users
 * - Login (get JWT token)
 * - Logout
 * - Get current user info
 * - Password reset flow
 *
 * All validation is done by the backend API.
 */

import api from './api'

export const authService = {
  /**
   * Register a new user
   * @param {Object} userData - { name, email, password, role }
   * @returns {Promise<Object>} User data
   */
  async register(userData) {
    const response = await api.post('/auth/register', userData)
    return response.data
  },

  /**
   * Login user and store JWT token
   * @param {Object} credentials - { email, password }
   * @returns {Promise<string>} JWT access token
   */
  async login(credentials) {
    const response = await api.post('/auth/login', credentials)
    const { access_token } = response.data
    // Store token in localStorage for persistence across page refreshes
    localStorage.setItem('token', access_token)
    return access_token
  },

  /**
   * Logout user and clear stored data
   * Uses try/finally to ensure cleanup even if API call fails
   */
  async logout() {
    try {
      // Notify backend to invalidate the session
      await api.post('/auth/logout')
    } finally {
      // Always clear local data, even if API call fails
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  },

  /**
   * Get current authenticated user's profile
   * @returns {Promise<Object>} User object with { id, name, email, role, is_active }
   */
  async getCurrentUser() {
    const response = await api.get('/users/me')
    const user = response.data
    // Store user data in localStorage for quick access
    localStorage.setItem('user', JSON.stringify(user))
    return user
  },

  /**
   * Get user from localStorage (no API call)
   * @returns {Object|null} User object or null if not found
   */
  getStoredUser() {
    const userStr = localStorage.getItem('user')
    return userStr ? JSON.parse(userStr) : null
  },

  /**
   * Get JWT token from localStorage (no API call)
   * @returns {string|null} Token or null if not found
   */
  getStoredToken() {
    return localStorage.getItem('token')
  },
}
