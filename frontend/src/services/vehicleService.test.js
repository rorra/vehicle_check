/**
 * Tests for vehicleService
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { vehicleService } from './vehicleService'
import api from './api'

// Mock the api module
vi.mock('./api')

describe('vehicleService', () => {
  const mockVehicles = {
    vehicles: [
      { id: '1', plate_number: 'ABC123', make: 'Toyota', model: 'Corolla', year: 2020, owner_id: 'user-1' },
      { id: '2', plate_number: 'XYZ789', make: 'Honda', model: 'Civic', year: 2021, owner_id: 'user-2' }
    ],
    total: 2,
    page: 1,
    page_size: 10
  }

  const mockVehicle = {
    id: '1',
    plate_number: 'ABC123',
    make: 'Toyota',
    model: 'Corolla',
    year: 2020,
    owner_id: 'user-1',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z'
  }

  const vehicleData = {
    plate_number: 'ABC123',
    make: 'Toyota',
    model: 'Corolla',
    year: 2020,
    owner_id: 'user-1'
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch list of vehicles', async () => {
    api.get.mockResolvedValue({ data: mockVehicles })

    const result = await vehicleService.listVehicles({ page: 1 })

    expect(api.get).toHaveBeenCalledWith('/vehicles', {
      params: { page: 1 }
    })
    expect(result).toEqual(mockVehicles)
  })

  it('should fetch list of vehicles with owners (admin)', async () => {
    const mockVehiclesWithOwners = [
      { ...mockVehicle, owner_name: 'John Doe', owner_email: 'john@example.com' }
    ]
    api.get.mockResolvedValue({ data: mockVehiclesWithOwners })

    const result = await vehicleService.listVehiclesWithOwners()

    expect(api.get).toHaveBeenCalledWith('/vehicles/with-owners')
    expect(result).toEqual(mockVehiclesWithOwners)
  })

  it('should get vehicle by ID', async () => {
    api.get.mockResolvedValue({ data: mockVehicle })

    const result = await vehicleService.getVehicle('1')

    expect(api.get).toHaveBeenCalledWith('/vehicles/1')
    expect(result).toEqual(mockVehicle)
  })

  it('should get vehicle by plate number', async () => {
    api.get.mockResolvedValue({ data: mockVehicle })

    const result = await vehicleService.getVehicleByPlate('ABC123')

    expect(api.get).toHaveBeenCalledWith('/vehicles/plate/ABC123')
    expect(result).toEqual(mockVehicle)
  })

  it('should create a new vehicle', async () => {
    api.post.mockResolvedValue({ data: mockVehicle })

    const result = await vehicleService.createVehicle(vehicleData)

    expect(api.post).toHaveBeenCalledWith('/vehicles', vehicleData)
    expect(result).toEqual(mockVehicle)
  })

  it('should update a vehicle', async () => {
    const updateData = { make: 'Toyota', model: 'Camry' }
    const updatedVehicle = { ...mockVehicle, ...updateData }
    api.put.mockResolvedValue({ data: updatedVehicle })

    const result = await vehicleService.updateVehicle('1', updateData)

    expect(api.put).toHaveBeenCalledWith('/vehicles/1', updateData)
    expect(result).toEqual(updatedVehicle)
  })

  it('should delete a vehicle', async () => {
    const mockResponse = { message: 'Vehículo eliminado exitosamente' }
    api.delete.mockResolvedValue({ data: mockResponse })

    const result = await vehicleService.deleteVehicle('1')

    expect(api.delete).toHaveBeenCalledWith('/vehicles/1')
    expect(result).toEqual(mockResponse)
  })
})
