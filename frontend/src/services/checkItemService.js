/**
 * Check Item Template service for managing check item templates
 */

import api from './api'

export const checkItemService = {
  /**
   * List all check item templates ordered by ordinal
   * All authenticated users can list
   */
  listTemplates: async () => {
    const response = await api.get('/check-items')
    return response.data
  },

  /**
   * Get check item template by ID
   * All authenticated users can get
   */
  getTemplate: async (templateId) => {
    const response = await api.get(`/check-items/${templateId}`)
    return response.data
  },

  /**
   * Create a new check item template (ADMIN only)
   */
  createTemplate: async (templateData) => {
    const response = await api.post('/check-items', templateData)
    return response.data
  },

  /**
   * Update check item template (ADMIN only)
   */
  updateTemplate: async (templateId, templateData) => {
    const response = await api.put(`/check-items/${templateId}`, templateData)
    return response.data
  },

  /**
   * Delete check item template (ADMIN only)
   * Warning: This affects all existing inspection results that reference this template
   */
  deleteTemplate: async (templateId) => {
    const response = await api.delete(`/check-items/${templateId}`)
    return response.data
  }
}
