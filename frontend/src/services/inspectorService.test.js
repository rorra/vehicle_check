/**
 * Tests for inspectorService
 *
 * Tests inspector management API functions.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { inspectorService } from './inspectorService'
import api from './api'

// Mock the api module
vi.mock('./api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}))

describe('inspectorService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('listInspectors', () => {
    it('should fetch list of inspectors', async () => {
      const mockInspectors = {
        inspectors: [
          { id: '1', user_name: 'Inspector 1', employee_id: 'INS-001' },
          { id: '2', user_name: 'Inspector 2', employee_id: 'INS-002' }
        ],
        total: 2
      }

      api.get.mockResolvedValue({ data: mockInspectors })

      const result = await inspectorService.listInspectors({ page: 1 })

      expect(api.get).toHaveBeenCalledWith('/inspectors', {
        params: { page: 1 }
      })
      expect(result).toEqual(mockInspectors)
    })
  })

  describe('createInspector', () => {
    it('should create both user and inspector profile', async () => {
      const inspectorData = {
        name: 'New Inspector',
        email: 'inspector@example.com',
        password: 'password123',
        employee_id: 'INS-003'
      }

      // Mock user creation
      const mockUser = { id: 'user-123', name: inspectorData.name, email: inspectorData.email }
      api.post.mockResolvedValueOnce({ data: mockUser })

      // Mock inspector profile creation
      const mockInspector = {
        id: 'inspector-123',
        user_id: 'user-123',
        employee_id: 'INS-003'
      }
      api.post.mockResolvedValueOnce({ data: mockInspector })

      const result = await inspectorService.createInspector(inspectorData)

      // Verify user creation
      expect(api.post).toHaveBeenNthCalledWith(1, '/users', {
        name: inspectorData.name,
        email: inspectorData.email,
        password: inspectorData.password,
        role: 'INSPECTOR'
      })

      // Verify inspector profile creation
      expect(api.post).toHaveBeenNthCalledWith(2, '/inspectors', {
        user_id: 'user-123',
        employee_id: 'INS-003'
      })

      expect(result).toEqual({
        ...mockInspector,
        user_name: inspectorData.name,
        user_email: inspectorData.email,
        user_is_active: true
      })
    })
  })

  describe('updateInspector', () => {
    it('should update both user and inspector profile', async () => {
      const inspectorId = 'inspector-123'
      const userId = 'user-123'
      const updateData = {
        name: 'Updated Name',
        employee_id: 'INS-999'
      }

      api.put.mockResolvedValue({ data: {} })

      await inspectorService.updateInspector(inspectorId, userId, updateData)

      // Verify user update
      expect(api.put).toHaveBeenCalledWith(`/users/${userId}`, {
        name: 'Updated Name',
        email: undefined,
        is_active: undefined
      })

      // Verify inspector update
      expect(api.put).toHaveBeenCalledWith(`/inspectors/${inspectorId}`, {
        employee_id: 'INS-999'
      })
    })
  })

  describe('deleteInspector', () => {
    it('should delete inspector profile', async () => {
      const inspectorId = 'inspector-123'

      api.delete.mockResolvedValue({})

      await inspectorService.deleteInspector(inspectorId)

      expect(api.delete).toHaveBeenCalledWith(`/inspectors/${inspectorId}`)
    })
  })
})
