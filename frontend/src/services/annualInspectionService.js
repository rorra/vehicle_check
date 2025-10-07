/**
 * Annual Inspection service for managing annual vehicle inspections
 */

import api from './api'

export const annualInspectionService = {
  /**
   * List annual inspections with pagination and filters
   * CLIENT: Only their own vehicle inspections
   * INSPECTOR: All inspections
   * ADMIN: All inspections
   */
  listAnnualInspections: async (params = {}) => {
    const response = await api.get('/annual-inspections', { params })
    return response.data
  },

  /**
   * Get annual inspection by ID with full details
   */
  getAnnualInspection: async (inspectionId) => {
    const response = await api.get(`/annual-inspections/${inspectionId}`)
    return response.data
  },

  /**
   * Create a new annual inspection
   * ADMIN only (inspections are created automatically by backend for clients)
   */
  createAnnualInspection: async (inspectionData) => {
    const response = await api.post('/annual-inspections', inspectionData)
    return response.data
  },

  /**
   * Update annual inspection status
   * ADMIN only
   */
  updateAnnualInspection: async (inspectionId, inspectionData) => {
    const response = await api.put(`/annual-inspections/${inspectionId}`, inspectionData)
    return response.data
  },

  /**
   * Delete an annual inspection
   * ADMIN only
   * Note: Cascades to delete related appointments and results
   */
  deleteAnnualInspection: async (inspectionId) => {
    const response = await api.delete(`/annual-inspections/${inspectionId}`)
    return response.data
  }
}
