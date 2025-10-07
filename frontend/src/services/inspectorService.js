/**
 * Inspector Service
 *
 * API calls for managing inspectors.
 * Inspectors have both a User account and an Inspector profile.
 */

import api from './api'

export const inspectorService = {
  /**
   * List all inspectors
   * GET /inspectors
   * @param {Object} params - Query params (page, page_size, active_only)
   */
  listInspectors: async (params = {}) => {
    const response = await api.get('/inspectors', { params })
    return response.data
  },

  /**
   * Create new inspector (ADMIN only)
   * Creates both user and inspector profile
   * @param {Object} inspectorData - { name, email, password, employee_id }
   */
  createInspector: async (inspectorData) => {
    // Step 1: Create user with INSPECTOR role
    const userResponse = await api.post('/users', {
      name: inspectorData.name,
      email: inspectorData.email,
      password: inspectorData.password,
      role: 'INSPECTOR'
    })

    // Step 2: Create inspector profile
    const inspectorResponse = await api.post('/inspectors', {
      user_id: userResponse.data.id,
      employee_id: inspectorData.employee_id
    })

    // Return combined data
    return {
      ...inspectorResponse.data,
      user_name: inspectorData.name,
      user_email: inspectorData.email,
      user_is_active: true
    }
  },

  /**
   * Get inspector by ID (ADMIN only)
   * GET /inspectors/{inspector_id}
   * @param {string} inspectorId - Inspector ID
   */
  getInspectorById: async (inspectorId) => {
    const response = await api.get(`/inspectors/${inspectorId}`)
    return response.data
  },

  /**
   * Update inspector (ADMIN only)
   * Updates both user and inspector profile
   * PUT /users/{user_id} and PUT /inspectors/{inspector_id}
   * @param {string} inspectorId - Inspector ID
   * @param {string} userId - User ID
   * @param {Object} inspectorData - Updated data
   */
  updateInspector: async (inspectorId, userId, inspectorData) => {
    // Update user info (name, email, is_active)
    if (inspectorData.name || inspectorData.email || inspectorData.user_is_active !== undefined) {
      await api.put(`/users/${userId}`, {
        name: inspectorData.name,
        email: inspectorData.email,
        is_active: inspectorData.user_is_active
      })
    }

    // Update inspector profile (employee_id, active)
    const inspectorUpdate = {}
    if (inspectorData.employee_id !== undefined) inspectorUpdate.employee_id = inspectorData.employee_id
    if (inspectorData.active !== undefined) inspectorUpdate.active = inspectorData.active

    if (Object.keys(inspectorUpdate).length > 0) {
      const response = await api.put(`/inspectors/${inspectorId}`, inspectorUpdate)
      return response.data
    }
  },

  /**
   * Delete inspector profile (ADMIN only)
   * DELETE /inspectors/{inspector_id}
   * Note: This only deletes the inspector profile, not the user account
   * @param {string} inspectorId - Inspector ID
   */
  deleteInspector: async (inspectorId) => {
    await api.delete(`/inspectors/${inspectorId}`)
  },
}
