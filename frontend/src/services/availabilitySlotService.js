/**
 * Availability Slot service for managing availability slots
 */

import api from './api'

export const availabilitySlotService = {
  /**
   * List availability slots
   * All users can list, but only admins can see booked slots
   */
  listSlots: async (params = {}) => {
    const response = await api.get('/available-slots', { params })
    return response.data
  },

  /**
   * Get slot by ID
   */
  getSlot: async (slotId) => {
    const response = await api.get(`/available-slots/${slotId}`)
    return response.data
  },

  /**
   * Create a new availability slot (ADMIN only)
   */
  createSlot: async (slotData) => {
    const response = await api.post('/available-slots', slotData)
    return response.data
  },

  /**
   * Delete a slot (ADMIN only)
   * Cannot delete booked slots
   */
  deleteSlot: async (slotId) => {
    const response = await api.delete(`/available-slots/${slotId}`)
    return response.data
  }
}
