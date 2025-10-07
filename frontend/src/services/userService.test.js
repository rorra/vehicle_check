/**
 * Tests for userService
 *
 * Tests user profile API functions.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { userService } from './userService'
import api from './api'

// Mock the api module
vi.mock('./api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  }
}))

describe('userService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getCurrentProfile', () => {
    it('should fetch current user profile', async () => {
      const mockProfile = {
        id: 1,
        name: 'Test User',
        email: 'test@example.com',
        role: 'CLIENT'
      }

      api.get.mockResolvedValue({ data: mockProfile })

      const result = await userService.getCurrentProfile()

      expect(api.get).toHaveBeenCalledWith('/users/me')
      expect(result).toEqual(mockProfile)
    })
  })

  describe('updateProfile', () => {
    it('should update user profile', async () => {
      const userData = { name: 'Updated Name', email: 'updated@example.com' }
      const mockResponse = { ...userData, id: 1, role: 'CLIENT' }

      api.put.mockResolvedValue({ data: mockResponse })

      const result = await userService.updateProfile(userData)

      expect(api.put).toHaveBeenCalledWith('/users/me', userData)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('changePassword', () => {
    it('should change user password', async () => {
      const passwordData = {
        current_password: 'oldpass',
        new_password: 'newpass'
      }
      const mockResponse = { message: 'Password changed successfully' }

      api.post.mockResolvedValue({ data: mockResponse })

      const result = await userService.changePassword(passwordData)

      expect(api.post).toHaveBeenCalledWith('/users/me/change-password', passwordData)
      expect(result).toEqual(mockResponse)
    })
  })
})
