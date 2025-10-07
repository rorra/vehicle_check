/**
 * Tests for adminService
 *
 * Tests admin management API functions.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { adminService } from './adminService'
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

describe('adminService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('listAdmins', () => {
    it('should fetch list of admins with ADMIN role filter', async () => {
      const mockAdmins = {
        users: [
          { id: 1, name: 'Admin 1', email: 'admin1@example.com', role: 'ADMIN' },
          { id: 2, name: 'Admin 2', email: 'admin2@example.com', role: 'ADMIN' }
        ],
        total: 2
      }

      api.get.mockResolvedValue({ data: mockAdmins })

      const result = await adminService.listAdmins({ page: 1 })

      expect(api.get).toHaveBeenCalledWith('/users', {
        params: { page: 1, role: 'ADMIN' }
      })
      expect(result).toEqual(mockAdmins)
    })
  })

  describe('createAdmin', () => {
    it('should create a new admin with ADMIN role', async () => {
      const adminData = {
        name: 'New Admin',
        email: 'newadmin@example.com',
        password: 'password123'
      }
      const mockResponse = { id: 10, ...adminData, role: 'ADMIN' }

      api.post.mockResolvedValue({ data: mockResponse })

      const result = await adminService.createAdmin(adminData)

      expect(api.post).toHaveBeenCalledWith('/users', {
        ...adminData,
        role: 'ADMIN'
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('updateAdmin', () => {
    it('should update admin by ID', async () => {
      const userId = '123'
      const adminData = { name: 'Updated Admin' }
      const mockResponse = { id: userId, ...adminData, role: 'ADMIN' }

      api.put.mockResolvedValue({ data: mockResponse })

      const result = await adminService.updateAdmin(userId, adminData)

      expect(api.put).toHaveBeenCalledWith(`/users/${userId}`, adminData)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('deleteAdmin', () => {
    it('should delete admin by ID', async () => {
      const userId = '123'

      api.delete.mockResolvedValue({})

      await adminService.deleteAdmin(userId)

      expect(api.delete).toHaveBeenCalledWith(`/users/${userId}`)
    })
  })
})
