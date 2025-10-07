/**
 * Tests for annualInspectionService
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { annualInspectionService } from './annualInspectionService'
import api from './api'

// Mock the api module
vi.mock('./api')

describe('annualInspectionService', () => {
  const mockInspections = {
    inspections: [
      {
        id: '1',
        vehicle_id: 'vehicle-1',
        year: 2024,
        status: 'PENDING',
        attempt_count: 0,
        vehicle_plate: 'ABC123',
        vehicle_make: 'Toyota',
        vehicle_model: 'Corolla',
        vehicle_year: 2020,
        owner_name: 'John Doe',
        owner_email: 'john@example.com',
        total_appointments: 0,
        last_appointment_date: null
      },
      {
        id: '2',
        vehicle_id: 'vehicle-2',
        year: 2024,
        status: 'PASSED',
        attempt_count: 1,
        vehicle_plate: 'XYZ789',
        vehicle_make: 'Honda',
        vehicle_model: 'Civic',
        vehicle_year: 2021,
        owner_name: 'Jane Smith',
        owner_email: 'jane@example.com',
        total_appointments: 1,
        last_appointment_date: '2024-01-15T10:00:00Z'
      }
    ],
    total: 2,
    page: 1,
    page_size: 10
  }

  const mockInspection = {
    id: '1',
    vehicle_id: 'vehicle-1',
    year: 2024,
    status: 'PENDING',
    attempt_count: 0,
    vehicle_plate: 'ABC123',
    vehicle_make: 'Toyota',
    vehicle_model: 'Corolla',
    vehicle_year: 2020,
    owner_name: 'John Doe',
    owner_email: 'john@example.com',
    total_appointments: 0,
    last_appointment_date: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }

  const inspectionData = {
    vehicle_id: 'vehicle-1',
    year: 2024
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch list of annual inspections', async () => {
    api.get.mockResolvedValue({ data: mockInspections })

    const result = await annualInspectionService.listAnnualInspections({ page: 1 })

    expect(api.get).toHaveBeenCalledWith('/annual-inspections', {
      params: { page: 1 }
    })
    expect(result).toEqual(mockInspections)
  })

  it('should get annual inspection by ID', async () => {
    api.get.mockResolvedValue({ data: mockInspection })

    const result = await annualInspectionService.getAnnualInspection('1')

    expect(api.get).toHaveBeenCalledWith('/annual-inspections/1')
    expect(result).toEqual(mockInspection)
  })

  it('should create a new annual inspection', async () => {
    api.post.mockResolvedValue({ data: mockInspection })

    const result = await annualInspectionService.createAnnualInspection(inspectionData)

    expect(api.post).toHaveBeenCalledWith('/annual-inspections', inspectionData)
    expect(result).toEqual(mockInspection)
  })

  it('should update an annual inspection', async () => {
    const updateData = { status: 'PASSED' }
    const updatedInspection = { ...mockInspection, status: 'PASSED' }
    api.put.mockResolvedValue({ data: updatedInspection })

    const result = await annualInspectionService.updateAnnualInspection('1', updateData)

    expect(api.put).toHaveBeenCalledWith('/annual-inspections/1', updateData)
    expect(result).toEqual(updatedInspection)
  })

  it('should delete an annual inspection', async () => {
    const mockResponse = { message: 'Inspección anual eliminada exitosamente' }
    api.delete.mockResolvedValue({ data: mockResponse })

    const result = await annualInspectionService.deleteAnnualInspection('1')

    expect(api.delete).toHaveBeenCalledWith('/annual-inspections/1')
    expect(result).toEqual(mockResponse)
  })
})
