/**
 * Tests for inspectionResultService
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { inspectionResultService } from './inspectionResultService'
import api from './api'

vi.mock('./api')

describe('inspectionResultService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should list inspection results with pagination', async () => {
    const mockResults = {
      results: [
        { id: '1', vehicle_plate: 'ABC123', total_score: 65, passed: true },
        { id: '2', vehicle_plate: 'XYZ789', total_score: 35, passed: false }
      ],
      total: 2,
      page: 1,
      page_size: 10
    }
    api.get.mockResolvedValue({ data: mockResults })

    const result = await inspectionResultService.listResults({ page: 1, page_size: 10 })

    expect(api.get).toHaveBeenCalledWith('/inspection-results', { params: { page: 1, page_size: 10 } })
    expect(result).toEqual(mockResults)
  })

  it('should get inspection result by id', async () => {
    const mockResult = {
      id: '1',
      vehicle_plate: 'ABC123',
      total_score: 65,
      passed: true,
      item_checks: []
    }
    api.get.mockResolvedValue({ data: mockResult })

    const result = await inspectionResultService.getResult('1')

    expect(api.get).toHaveBeenCalledWith('/inspection-results/1')
    expect(result).toEqual(mockResult)
  })

  it('should get results by annual inspection', async () => {
    const mockResults = [
      { id: '1', vehicle_plate: 'ABC123', total_score: 65, passed: true },
      { id: '2', vehicle_plate: 'ABC123', total_score: 70, passed: true }
    ]
    api.get.mockResolvedValue({ data: mockResults })

    const result = await inspectionResultService.getResultsByAnnualInspection('annual-1')

    expect(api.get).toHaveBeenCalledWith('/inspection-results/annual-inspection/annual-1')
    expect(result).toEqual(mockResults)
  })
})
