/**
 * Tests for clientService
 *
 * Tests client management API functions.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { clientService } from './clientService'
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

describe('clientService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('listClients', () => {
    it('should fetch list of clients with CLIENT role filter', async () => {
      const mockClients = {
        users: [
          { id: 1, name: 'Client 1', email: 'client1@example.com', role: 'CLIENT' },
          { id: 2, name: 'Client 2', email: 'client2@example.com', role: 'CLIENT' }
        ],
        total: 2
      }

      api.get.mockResolvedValue({ data: mockClients })

      const result = await clientService.listClients({ page: 1 })

      expect(api.get).toHaveBeenCalledWith('/users', {
        params: { page: 1, role: 'CLIENT' }
      })
      expect(result).toEqual(mockClients)
    })
  })

  describe('createClient', () => {
    it('should create a new client with CLIENT role', async () => {
      const clientData = {
        name: 'New Client',
        email: 'newclient@example.com',
        password: 'password123'
      }
      const mockResponse = { id: 10, ...clientData, role: 'CLIENT' }

      api.post.mockResolvedValue({ data: mockResponse })

      const result = await clientService.createClient(clientData)

      expect(api.post).toHaveBeenCalledWith('/users', {
        ...clientData,
        role: 'CLIENT'
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('updateClient', () => {
    it('should update client by ID', async () => {
      const userId = '123'
      const clientData = { name: 'Updated Client' }
      const mockResponse = { id: userId, ...clientData, role: 'CLIENT' }

      api.put.mockResolvedValue({ data: mockResponse })

      const result = await clientService.updateClient(userId, clientData)

      expect(api.put).toHaveBeenCalledWith(`/users/${userId}`, clientData)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('deleteClient', () => {
    it('should delete client by ID', async () => {
      const userId = '123'

      api.delete.mockResolvedValue({})

      await clientService.deleteClient(userId)

      expect(api.delete).toHaveBeenCalledWith(`/users/${userId}`)
    })
  })
})
