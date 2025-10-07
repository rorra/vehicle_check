/**
 * Admin Service
 *
 * API calls for managing administrators (users with ADMIN role).
 */

import api from './api'

export const adminService = {
  /**
   * List all admins
   * GET /users?role=ADMIN
   * @param {Object} params - Query params (page, page_size)
   */
  listAdmins: async (params = {}) => {
    const response = await api.get('/users', {
      params: { ...params, role: 'ADMIN' }
    })
    return response.data
  },

  /**
   * Create new admin (ADMIN only)
   * POST /users
   * @param {Object} adminData - Admin data (name, email, password)
   */
  createAdmin: async (adminData) => {
    const response = await api.post('/users', {
      ...adminData,
      role: 'ADMIN'
    })
    return response.data
  },

  /**
   * Get admin by ID (ADMIN only)
   * GET /users/{user_id}
   * @param {string} userId - User ID
   */
  getAdminById: async (userId) => {
    const response = await api.get(`/users/${userId}`)
    return response.data
  },

  /**
   * Update admin (ADMIN only)
   * PUT /users/{user_id}
   * @param {string} userId - User ID
   * @param {Object} adminData - Updated admin data
   */
  updateAdmin: async (userId, adminData) => {
    const response = await api.put(`/users/${userId}`, adminData)
    return response.data
  },

  /**
   * Delete admin (ADMIN only)
   * DELETE /users/{user_id}
   * @param {string} userId - User ID
   */
  deleteAdmin: async (userId) => {
    await api.delete(`/users/${userId}`)
  },
}
