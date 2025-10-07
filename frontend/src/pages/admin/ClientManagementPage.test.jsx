/**
 * Tests for ClientManagementPage component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ChakraProvider } from '@chakra-ui/react'
import ClientManagementPage from './ClientManagementPage'
import { AuthProvider } from '../../context/AuthContext'
import * as authService from '../../services/authService'
import * as clientServiceModule from '../../services/clientService'

// Mock authService
vi.mock('../../services/authService', () => ({
  authService: {
    getStoredToken: vi.fn(),
    getStoredUser: vi.fn(),
  }
}))

// Mock clientService
vi.mock('../../services/clientService', () => ({
  clientService: {
    listClients: vi.fn(),
    createClient: vi.fn(),
    updateClient: vi.fn(),
    deleteClient: vi.fn(),
  }
}))

// Mock window.confirm
global.confirm = vi.fn()

const renderClientManagementPage = () => {
  return render(
    <ChakraProvider>
      <BrowserRouter>
        <AuthProvider>
          <ClientManagementPage />
        </AuthProvider>
      </BrowserRouter>
    </ChakraProvider>
  )
}

describe('ClientManagementPage', () => {
  const mockClients = [
    { id: 1, name: 'Client One', email: 'client1@example.com', role: 'CLIENT', is_active: true },
    { id: 2, name: 'Client Two', email: 'client2@example.com', role: 'CLIENT', is_active: false }
  ]

  const mockAdmin = {
    id: 99,
    name: 'Admin User',
    email: 'admin@example.com',
    role: 'ADMIN'
  }

  beforeEach(() => {
    vi.clearAllMocks()
    authService.authService.getStoredToken.mockReturnValue('fake-token')
    authService.authService.getStoredUser.mockReturnValue(mockAdmin)
    clientServiceModule.clientService.listClients.mockResolvedValue({
      users: mockClients,
      total: mockClients.length
    })
  })

  it('should render client management page with client list', async () => {
    renderClientManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Gestión de Clientes')).toBeInTheDocument()
      expect(screen.getByText('Client One')).toBeInTheDocument()
      expect(screen.getByText('Client Two')).toBeInTheDocument()
    })
  })

  it('should display client status correctly', async () => {
    renderClientManagementPage()

    await waitFor(() => {
      const statusBadges = screen.getAllByText(/activo|inactivo/i)
      expect(statusBadges.length).toBeGreaterThan(0)
    })
  })

  it('should open create modal when clicking create button', async () => {
    const user = userEvent.setup()
    renderClientManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Client One')).toBeInTheDocument()
    })

    const createButton = screen.getByRole('button', { name: /crear cliente/i })
    await user.click(createButton)

    // Wait for modal form fields to appear
    await waitFor(() => {
      expect(screen.getByLabelText(/nombre/i)).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /email/i })).toBeInTheDocument()
    })
  })

  it('should update client successfully', async () => {
    const user = userEvent.setup()
    clientServiceModule.clientService.updateClient.mockResolvedValue({
      ...mockClients[0],
      name: 'Updated Client'
    })

    renderClientManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Client One')).toBeInTheDocument()
    })

    const editButtons = screen.getAllByRole('button', { name: /editar/i })
    await user.click(editButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Editar Cliente')).toBeInTheDocument()
    })

    const nameInput = screen.getByDisplayValue('Client One')
    await user.clear(nameInput)
    await user.type(nameInput, 'Updated Client')

    const saveButton = screen.getByRole('button', { name: /guardar/i })
    await user.click(saveButton)

    await waitFor(() => {
      expect(clientServiceModule.clientService.updateClient).toHaveBeenCalledWith(
        1,
        expect.objectContaining({
          name: 'Updated Client'
        })
      )
    })
  })

  it('should delete client when confirmed', async () => {
    const user = userEvent.setup()
    global.confirm.mockReturnValue(true)
    clientServiceModule.clientService.deleteClient.mockResolvedValue()

    renderClientManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Client One')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByRole('button', { name: /eliminar/i })
    await user.click(deleteButtons[0])

    await waitFor(() => {
      expect(global.confirm).toHaveBeenCalledWith(
        expect.stringContaining('Client One')
      )
      expect(clientServiceModule.clientService.deleteClient).toHaveBeenCalledWith(1)
    })
  })

  it('should display error when fetching clients fails', async () => {
    const errorMessage = 'Failed to fetch clients'
    clientServiceModule.clientService.listClients.mockRejectedValue({
      response: {
        data: {
          detail: errorMessage
        }
      }
    })

    renderClientManagementPage()

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })
})
