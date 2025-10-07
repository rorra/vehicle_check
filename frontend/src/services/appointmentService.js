/**
 * Appointment service for managing appointment operations
 */

import api from './api'

export const appointmentService = {
  /**
   * List appointments with pagination and filters
   * CLIENT: Only their own vehicle appointments
   * INSPECTOR: Their assigned appointments
   * ADMIN: All appointments
   */
  listAppointments: async (params = {}) => {
    const response = await api.get('/appointments', { params })
    return response.data
  },

  /**
   * Get appointment by ID
   */
  getAppointment: async (appointmentId) => {
    const response = await api.get(`/appointments/${appointmentId}`)
    return response.data
  },

  /**
   * Get available time slots for appointments
   */
  getAvailableSlots: async (params = {}) => {
    const response = await api.get('/appointments/available-slots', { params })
    return response.data
  },

  /**
   * Create a new appointment
   * CLIENT: Can create for their own vehicles
   * ADMIN: Can create for any vehicle and assign inspector
   */
  createAppointment: async (appointmentData) => {
    const response = await api.post('/appointments', appointmentData)
    return response.data
  },

  /**
   * Update appointment details
   * CLIENT: Can reschedule their own appointments (if not completed/cancelled)
   * ADMIN: Can update any appointment
   */
  updateAppointment: async (appointmentId, appointmentData) => {
    const response = await api.put(`/appointments/${appointmentId}`, appointmentData)
    return response.data
  },

  /**
   * Cancel an appointment
   * CLIENT: Can cancel their own appointments (if not completed)
   * ADMIN: Can cancel any appointment
   */
  cancelAppointment: async (appointmentId) => {
    const response = await api.delete(`/appointments/${appointmentId}`)
    return response.data
  },

  /**
   * Complete appointment with inspection results
   * INSPECTOR only: Complete their assigned appointments
   */
  completeAppointment: async (appointmentId, resultData) => {
    const response = await api.post(`/appointments/${appointmentId}/complete`, resultData)
    return response.data
  }
}
