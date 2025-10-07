/**
 * Vehicle service for managing vehicle operations
 */

import api from './api'

export const vehicleService = {
  /**
   * List vehicles with pagination
   * CLIENT: Only their own vehicles
   * ADMIN: All vehicles with optional filtering
   */
  listVehicles: async (params = {}) => {
    const response = await api.get('/vehicles', { params })
    return response.data
  },

  /**
   * List all vehicles with owner details (ADMIN only)
   */
  listVehiclesWithOwners: async () => {
    const response = await api.get('/vehicles/with-owners')
    return response.data
  },

  /**
   * Get vehicle by ID
   */
  getVehicle: async (vehicleId) => {
    const response = await api.get(`/vehicles/${vehicleId}`)
    return response.data
  },

  /**
   * Get vehicle by plate number
   */
  getVehicleByPlate: async (plateNumber) => {
    const response = await api.get(`/vehicles/plate/${plateNumber}`)
    return response.data
  },

  /**
   * Create a new vehicle
   * CLIENT: Creates for themselves (owner_id optional)
   * ADMIN: Can specify owner_id
   */
  createVehicle: async (vehicleData) => {
    const response = await api.post('/vehicles', vehicleData)
    return response.data
  },

  /**
   * Update vehicle details
   * CLIENT: Can only update their own vehicles
   * ADMIN: Can update any vehicle
   */
  updateVehicle: async (vehicleId, vehicleData) => {
    const response = await api.put(`/vehicles/${vehicleId}`, vehicleData)
    return response.data
  },

  /**
   * Delete a vehicle
   * CLIENT: Can only delete their own vehicles (if no inspections)
   * ADMIN: Can delete any vehicle (cascade to inspections)
   */
  deleteVehicle: async (vehicleId) => {
    const response = await api.delete(`/vehicles/${vehicleId}`)
    return response.data
  }
}
