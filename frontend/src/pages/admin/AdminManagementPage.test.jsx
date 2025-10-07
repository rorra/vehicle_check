/**
 * Tests for AdminManagementPage component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ChakraProvider } from '@chakra-ui/react'
import AdminManagementPage from './AdminManagementPage'
import { AuthProvider } from '../../context/AuthContext'
import * as authService from '../../services/authService'
import * as adminServiceModule from '../../services/adminService'

// Mock authService
vi.mock('../../services/authService', () => ({
  authService: {
    getStoredToken: vi.fn(),
    getStoredUser: vi.fn(),
  }
}))

// Mock adminService
vi.mock('../../services/adminService', () => ({
  adminService: {
    listAdmins: vi.fn(),
    createAdmin: vi.fn(),
    updateAdmin: vi.fn(),
    deleteAdmin: vi.fn(),
  }
}))

// Mock window.confirm
global.confirm = vi.fn()

const renderAdminManagementPage = () => {
  return render(
    <ChakraProvider>
      <BrowserRouter>
        <AuthProvider>
          <AdminManagementPage />
        </AuthProvider>
      </BrowserRouter>
    </ChakraProvider>
  )
}

describe('AdminManagementPage', () => {
  const mockAdmins = [
    { id: 1, name: 'Admin One', email: 'admin1@example.com', role: 'ADMIN', is_active: true },
    { id: 2, name: 'Admin Two', email: 'admin2@example.com', role: 'ADMIN', is_active: true }
  ]

  const mockCurrentAdmin = {
    id: 99,
    name: 'Current Admin',
    email: 'current@example.com',
    role: 'ADMIN'
  }

  beforeEach(() => {
    vi.clearAllMocks()
    authService.authService.getStoredToken.mockReturnValue('fake-token')
    authService.authService.getStoredUser.mockReturnValue(mockCurrentAdmin)
    adminServiceModule.adminService.listAdmins.mockResolvedValue({
      users: mockAdmins,
      total: mockAdmins.length
    })
  })

  it('should render admin management page with admin list', async () => {
    renderAdminManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Gestión de Administradores')).toBeInTheDocument()
      expect(screen.getByText('Admin One')).toBeInTheDocument()
      expect(screen.getByText('Admin Two')).toBeInTheDocument()
    })
  })

  it('should display admin status correctly', async () => {
    renderAdminManagementPage()

    await waitFor(() => {
      const statusBadges = screen.getAllByText(/activo/i)
      expect(statusBadges.length).toBeGreaterThan(0)
    })
  })

  it('should open create modal when clicking create button', async () => {
    const user = userEvent.setup()
    renderAdminManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Admin One')).toBeInTheDocument()
    })

    const createButton = screen.getByRole('button', { name: /crear administrador/i })
    await user.click(createButton)

    // Wait for modal form fields to appear
    await waitFor(() => {
      expect(screen.getByLabelText(/nombre/i)).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /email/i })).toBeInTheDocument()
    })
  })

  it('should update admin successfully', async () => {
    const user = userEvent.setup()
    adminServiceModule.adminService.updateAdmin.mockResolvedValue({
      ...mockAdmins[0],
      name: 'Updated Admin'
    })

    renderAdminManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Admin One')).toBeInTheDocument()
    })

    const editButtons = screen.getAllByRole('button', { name: /editar/i })
    await user.click(editButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Editar Administrador')).toBeInTheDocument()
    })

    const nameInput = screen.getByDisplayValue('Admin One')
    await user.clear(nameInput)
    await user.type(nameInput, 'Updated Admin')

    const saveButton = screen.getByRole('button', { name: /guardar/i })
    await user.click(saveButton)

    await waitFor(() => {
      expect(adminServiceModule.adminService.updateAdmin).toHaveBeenCalledWith(
        1,
        expect.objectContaining({
          name: 'Updated Admin'
        })
      )
    })
  })

  it('should delete admin when confirmed', async () => {
    const user = userEvent.setup()
    global.confirm.mockReturnValue(true)
    adminServiceModule.adminService.deleteAdmin.mockResolvedValue()

    renderAdminManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Admin One')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByRole('button', { name: /eliminar/i })
    await user.click(deleteButtons[0])

    await waitFor(() => {
      expect(global.confirm).toHaveBeenCalledWith(
        expect.stringContaining('Admin One')
      )
      expect(adminServiceModule.adminService.deleteAdmin).toHaveBeenCalledWith(1)
    })
  })

  it('should display error when fetching admins fails', async () => {
    const errorMessage = 'Failed to fetch admins'
    adminServiceModule.adminService.listAdmins.mockRejectedValue({
      response: {
        data: {
          detail: errorMessage
        }
      }
    })

    renderAdminManagementPage()

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })
})
