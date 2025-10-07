/**
 * Client Service
 *
 * API calls for managing clients (users with CLIENT role).
 */

import api from './api'

export const clientService = {
  /**
   * List all clients
   * GET /users?role=CLIENT
   * @param {Object} params - Query params (page, page_size)
   */
  listClients: async (params = {}) => {
    const response = await api.get('/users', {
      params: { ...params, role: 'CLIENT' }
    })
    return response.data
  },

  /**
   * Create new client (ADMIN only)
   * POST /users
   * @param {Object} clientData - Client data (name, email, password)
   */
  createClient: async (clientData) => {
    const response = await api.post('/users', {
      ...clientData,
      role: 'CLIENT'
    })
    return response.data
  },

  /**
   * Get client by ID (ADMIN only)
   * GET /users/{user_id}
   * @param {string} userId - User ID
   */
  getClientById: async (userId) => {
    const response = await api.get(`/users/${userId}`)
    return response.data
  },

  /**
   * Update client (ADMIN only)
   * PUT /users/{user_id}
   * @param {string} userId - User ID
   * @param {Object} clientData - Updated client data
   */
  updateClient: async (userId, clientData) => {
    const response = await api.put(`/users/${userId}`, clientData)
    return response.data
  },

  /**
   * Delete client (ADMIN only)
   * DELETE /users/{user_id}
   * @param {string} userId - User ID
   */
  deleteClient: async (userId) => {
    await api.delete(`/users/${userId}`)
  },
}
