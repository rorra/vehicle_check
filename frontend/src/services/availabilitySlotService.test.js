/**
 * Tests for availabilitySlotService
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { availabilitySlotService } from './availabilitySlotService'
import api from './api'

vi.mock('./api')

describe('availabilitySlotService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should list slots', async () => {
    const mockSlots = [
      { id: '1', start_time: '2024-03-20T10:00:00', end_time: '2024-03-20T11:00:00', is_booked: false },
      { id: '2', start_time: '2024-03-20T14:00:00', end_time: '2024-03-20T15:00:00', is_booked: true }
    ]
    api.get.mockResolvedValue({ data: mockSlots })

    const result = await availabilitySlotService.listSlots({ include_booked: true })

    expect(api.get).toHaveBeenCalledWith('/available-slots', { params: { include_booked: true } })
    expect(result).toEqual(mockSlots)
  })

  it('should get slot by id', async () => {
    const mockSlot = { id: '1', start_time: '2024-03-20T10:00:00', end_time: '2024-03-20T11:00:00', is_booked: false }
    api.get.mockResolvedValue({ data: mockSlot })

    const result = await availabilitySlotService.getSlot('1')

    expect(api.get).toHaveBeenCalledWith('/available-slots/1')
    expect(result).toEqual(mockSlot)
  })

  it('should create slot', async () => {
    const slotData = {
      start_time: '2024-03-20T10:00:00',
      end_time: '2024-03-20T11:00:00'
    }
    const mockSlot = { id: '1', ...slotData, is_booked: false }
    api.post.mockResolvedValue({ data: mockSlot })

    const result = await availabilitySlotService.createSlot(slotData)

    expect(api.post).toHaveBeenCalledWith('/available-slots', slotData)
    expect(result).toEqual(mockSlot)
  })

  it('should delete slot', async () => {
    api.delete.mockResolvedValue({ data: { message: 'Slot eliminado' } })

    const result = await availabilitySlotService.deleteSlot('1')

    expect(api.delete).toHaveBeenCalledWith('/available-slots/1')
    expect(result).toEqual({ message: 'Slot eliminado' })
  })
})
