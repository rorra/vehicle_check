/**
 * Inspection Result service for managing inspection results
 */

import api from './api'

export const inspectionResultService = {
  /**
   * List inspection results with pagination and filters
   * All authenticated users can list (role-based filtering handled by backend)
   */
  listResults: async (params = {}) => {
    const response = await api.get('/inspection-results', { params })
    return response.data
  },

  /**
   * Get detailed inspection result by ID
   * CLIENT can only access their own results, INSPECTOR and ADMIN can access all
   */
  getResult: async (resultId) => {
    const response = await api.get(`/inspection-results/${resultId}`)
    return response.data
  },

  /**
   * Get all inspection results for a specific annual inspection
   * CLIENT can only access their own, INSPECTOR and ADMIN can access all
   */
  getResultsByAnnualInspection: async (annualInspectionId) => {
    const response = await api.get(`/inspection-results/annual-inspection/${annualInspectionId}`)
    return response.data
  }
}
