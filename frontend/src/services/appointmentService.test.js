/**
 * Tests for appointmentService
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { appointmentService } from './appointmentService'
import api from './api'

vi.mock('./api')

describe('appointmentService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should list appointments', async () => {
    const mockData = {
      appointments: [{ id: '1', vehicle_plate: 'ABC123' }],
      total: 1
    }
    api.get.mockResolvedValue({ data: mockData })

    const result = await appointmentService.listAppointments()

    expect(api.get).toHaveBeenCalledWith('/appointments', { params: {} })
    expect(result).toEqual(mockData)
  })

  it('should get appointment by id', async () => {
    const mockAppointment = { id: '1', vehicle_plate: 'ABC123' }
    api.get.mockResolvedValue({ data: mockAppointment })

    const result = await appointmentService.getAppointment('1')

    expect(api.get).toHaveBeenCalledWith('/appointments/1')
    expect(result).toEqual(mockAppointment)
  })

  it('should get available slots', async () => {
    const mockSlots = [{ id: '1', start_time: '2024-03-15T10:00:00' }]
    api.get.mockResolvedValue({ data: mockSlots })

    const result = await appointmentService.getAvailableSlots()

    expect(api.get).toHaveBeenCalledWith('/appointments/available-slots', { params: {} })
    expect(result).toEqual(mockSlots)
  })

  it('should create appointment', async () => {
    const appointmentData = {
      vehicle_id: '1',
      date_time: '2024-03-15T10:00:00'
    }
    const mockAppointment = { id: '1', ...appointmentData }
    api.post.mockResolvedValue({ data: mockAppointment })

    const result = await appointmentService.createAppointment(appointmentData)

    expect(api.post).toHaveBeenCalledWith('/appointments', appointmentData)
    expect(result).toEqual(mockAppointment)
  })

  it('should update appointment', async () => {
    const appointmentData = { date_time: '2024-03-16T14:00:00' }
    const mockAppointment = { id: '1', ...appointmentData }
    api.put.mockResolvedValue({ data: mockAppointment })

    const result = await appointmentService.updateAppointment('1', appointmentData)

    expect(api.put).toHaveBeenCalledWith('/appointments/1', appointmentData)
    expect(result).toEqual(mockAppointment)
  })

  it('should cancel appointment', async () => {
    api.delete.mockResolvedValue({ data: { message: 'Turno cancelado' } })

    const result = await appointmentService.cancelAppointment('1')

    expect(api.delete).toHaveBeenCalledWith('/appointments/1')
    expect(result).toEqual({ message: 'Turno cancelado' })
  })

  it('should complete appointment', async () => {
    const resultData = {
      total_score: 65,
      item_scores: [8, 7, 9, 8, 7, 8, 9, 9],
      owner_observation: 'Vehículo en buenas condiciones'
    }
    const mockAppointment = { id: '1', status: 'COMPLETED' }
    api.post.mockResolvedValue({ data: mockAppointment })

    const result = await appointmentService.completeAppointment('1', resultData)

    expect(api.post).toHaveBeenCalledWith('/appointments/1/complete', resultData)
    expect(result).toEqual(mockAppointment)
  })
})
