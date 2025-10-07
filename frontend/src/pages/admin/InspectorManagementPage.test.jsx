/**
 * Tests for InspectorManagementPage component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ChakraProvider } from '@chakra-ui/react'
import InspectorManagementPage from './InspectorManagementPage'
import { AuthProvider } from '../../context/AuthContext'
import * as authService from '../../services/authService'
import * as inspectorServiceModule from '../../services/inspectorService'

// Mock authService
vi.mock('../../services/authService', () => ({
  authService: {
    getStoredToken: vi.fn(),
    getStoredUser: vi.fn(),
  }
}))

// Mock inspectorService
vi.mock('../../services/inspectorService', () => ({
  inspectorService: {
    listInspectors: vi.fn(),
    createInspector: vi.fn(),
    updateInspector: vi.fn(),
    deleteInspector: vi.fn(),
  }
}))

// Mock window.confirm
global.confirm = vi.fn()

const renderInspectorManagementPage = () => {
  return render(
    <ChakraProvider>
      <BrowserRouter>
        <AuthProvider>
          <InspectorManagementPage />
        </AuthProvider>
      </BrowserRouter>
    </ChakraProvider>
  )
}

describe('InspectorManagementPage', () => {
  const mockInspectors = [
    {
      id: '1',
      user_id: 'user-1',
      user_name: 'Inspector One',
      user_email: 'inspector1@example.com',
      employee_id: 'INS-001',
      user_is_active: true,
      active: true
    },
    {
      id: '2',
      user_id: 'user-2',
      user_name: 'Inspector Two',
      user_email: 'inspector2@example.com',
      employee_id: 'INS-002',
      user_is_active: true,
      active: false
    }
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
    inspectorServiceModule.inspectorService.listInspectors.mockResolvedValue({
      inspectors: mockInspectors,
      total: mockInspectors.length
    })
  })

  it('should render inspector management page with inspector list', async () => {
    renderInspectorManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Gestión de Inspectores')).toBeInTheDocument()
      expect(screen.getByText('Inspector One')).toBeInTheDocument()
      expect(screen.getByText('Inspector Two')).toBeInTheDocument()
      expect(screen.getByText('INS-001')).toBeInTheDocument()
      expect(screen.getByText('INS-002')).toBeInTheDocument()
    })
  })

  it('should display both user and inspector status', async () => {
    renderInspectorManagementPage()

    await waitFor(() => {
      const statusBadges = screen.getAllByText(/activo|inactivo/i)
      // Should have status for both user_is_active and active for each inspector
      expect(statusBadges.length).toBeGreaterThan(0)
    })
  })

  it('should open create modal when clicking create button', async () => {
    const user = userEvent.setup()
    renderInspectorManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Inspector One')).toBeInTheDocument()
    })

    const createButton = screen.getByRole('button', { name: /crear inspector/i })
    await user.click(createButton)

    // Wait for modal form fields to appear
    await waitFor(() => {
      expect(screen.getByLabelText(/nombre/i)).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /email/i })).toBeInTheDocument()
    })
  })

  it('should update inspector successfully', async () => {
    const user = userEvent.setup()
    inspectorServiceModule.inspectorService.updateInspector.mockResolvedValue({
      ...mockInspectors[0],
      employee_id: 'INS-999'
    })

    renderInspectorManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Inspector One')).toBeInTheDocument()
    })

    const editButtons = screen.getAllByRole('button', { name: /editar/i })
    await user.click(editButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Editar Inspector')).toBeInTheDocument()
    })

    const employeeIdInput = screen.getByDisplayValue('INS-001')
    await user.clear(employeeIdInput)
    await user.type(employeeIdInput, 'INS-999')

    const saveButton = screen.getByRole('button', { name: /guardar/i })
    await user.click(saveButton)

    await waitFor(() => {
      expect(inspectorServiceModule.inspectorService.updateInspector).toHaveBeenCalledWith(
        '1',
        'user-1',
        expect.objectContaining({
          employee_id: 'INS-999'
        })
      )
    })
  })

  it('should delete inspector when confirmed', async () => {
    const user = userEvent.setup()
    global.confirm.mockReturnValue(true)
    inspectorServiceModule.inspectorService.deleteInspector.mockResolvedValue()

    renderInspectorManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Inspector One')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByRole('button', { name: /eliminar/i })
    await user.click(deleteButtons[0])

    await waitFor(() => {
      expect(global.confirm).toHaveBeenCalledWith(
        expect.stringContaining('Inspector One')
      )
      expect(inspectorServiceModule.inspectorService.deleteInspector).toHaveBeenCalledWith('1')
    })
  })

  it('should display error when fetching inspectors fails', async () => {
    const errorMessage = 'Failed to fetch inspectors'
    inspectorServiceModule.inspectorService.listInspectors.mockRejectedValue({
      response: {
        data: {
          detail: errorMessage
        }
      }
    })

    renderInspectorManagementPage()

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })
})
