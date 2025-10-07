/**
 * User Service
 *
 * API calls for user profile operations (for current logged-in user).
 */

import api from './api'

export const userService = {
  /**
   * Get current user profile
   * GET /users/me
   */
  getCurrentProfile: async () => {
    const response = await api.get('/users/me')
    return response.data
  },

  /**
   * Update own profile
   * PUT /users/me
   * @param {Object} userData - Updated user data (name, email)
   */
  updateProfile: async (userData) => {
    const response = await api.put('/users/me', userData)
    return response.data
  },

  /**
   * Change own password
   * POST /users/me/change-password
   * @param {Object} passwordData - { current_password, new_password }
   */
  changePassword: async (passwordData) => {
    const response = await api.post('/users/me/change-password', passwordData)
    return response.data
  },
}
