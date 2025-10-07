/**
 * Tests for AvailabilitySlotManagementPage component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ChakraProvider } from '@chakra-ui/react'
import AvailabilitySlotManagementPage from './AvailabilitySlotManagementPage'
import { AuthProvider } from '../../context/AuthContext'
import * as authService from '../../services/authService'
import * as availabilitySlotServiceModule from '../../services/availabilitySlotService'

// Mock authService
vi.mock('../../services/authService', () => ({
  authService: {
    getStoredToken: vi.fn(),
    getStoredUser: vi.fn(),
  }
}))

// Mock availabilitySlotService
vi.mock('../../services/availabilitySlotService', () => ({
  availabilitySlotService: {
    listSlots: vi.fn(),
    createSlot: vi.fn(),
    deleteSlot: vi.fn(),
  }
}))

// Mock window.confirm
global.confirm = vi.fn()

const renderAvailabilitySlotManagementPage = () => {
  return render(
    <ChakraProvider>
      <BrowserRouter>
        <AuthProvider>
          <AvailabilitySlotManagementPage />
        </AuthProvider>
      </BrowserRouter>
    </ChakraProvider>
  )
}

describe('AvailabilitySlotManagementPage', () => {
  const mockSlots = [
    {
      id: '1',
      start_time: '2024-03-20T10:00:00',
      end_time: '2024-03-20T11:00:00',
      is_booked: false
    },
    {
      id: '2',
      start_time: '2024-03-20T14:00:00',
      end_time: '2024-03-20T15:00:00',
      is_booked: true
    },
    {
      id: '3',
      start_time: '2024-03-21T10:00:00',
      end_time: '2024-03-21T11:00:00',
      is_booked: false
    }
  ]

  const mockAdminUser = {
    id: 'user-1',
    name: 'Admin User',
    email: 'admin@example.com',
    role: 'ADMIN'
  }

  beforeEach(() => {
    vi.clearAllMocks()
    authService.authService.getStoredToken.mockReturnValue('fake-token')
    authService.authService.getStoredUser.mockReturnValue(mockAdminUser)
    availabilitySlotServiceModule.availabilitySlotService.listSlots.mockResolvedValue(mockSlots)
  })

  it('should render slot management page with slot list', async () => {
    renderAvailabilitySlotManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Gestión de Horarios Disponibles')).toBeInTheDocument()
    })

    // Should show slots
    await waitFor(() => {
      const availableBadges = screen.getAllByText('Disponible')
      const reservedBadges = screen.getAllByText('Reservado')
      expect(availableBadges.length).toBeGreaterThan(0)
      expect(reservedBadges.length).toBeGreaterThan(0)
    })
  })

  it('should display slot details correctly', async () => {
    renderAvailabilitySlotManagementPage()

    await waitFor(() => {
      // Should show available and booked badges
      const availableBadges = screen.getAllByText('Disponible')
      const reservedBadges = screen.getAllByText('Reservado')
      expect(availableBadges.length).toBe(2)
      expect(reservedBadges.length).toBe(1)
    })
  })

  it('should open create modal when clicking create button', async () => {
    const user = userEvent.setup()

    renderAvailabilitySlotManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Gestión de Horarios Disponibles')).toBeInTheDocument()
    })

    const createButton = screen.getByRole('button', { name: /crear horario/i })
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getAllByText('Crear Horario Disponible').length).toBeGreaterThan(0)
      expect(screen.getByLabelText(/hora de inicio/i)).toBeInTheDocument()
      // Should not show hora de fin (end_time is automatic)
      expect(screen.queryByLabelText(/hora de fin/i)).not.toBeInTheDocument()
    })
  })

  it('should create slot successfully', async () => {
    const user = userEvent.setup()
    availabilitySlotServiceModule.availabilitySlotService.createSlot.mockResolvedValue({
      id: '4',
      start_time: '2024-03-22T10:00:00',
      end_time: '2024-03-22T11:00:00',
      is_booked: false
    })

    renderAvailabilitySlotManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Gestión de Horarios Disponibles')).toBeInTheDocument()
    })

    const createButton = screen.getByRole('button', { name: /crear horario/i })
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getByLabelText(/hora de inicio/i)).toBeInTheDocument()
    })

    const startTimeInput = screen.getByLabelText(/hora de inicio/i)

    await user.clear(startTimeInput)
    await user.type(startTimeInput, '2024-03-22T10:00')

    const modalButtons = screen.getAllByRole('button', { name: /crear/i })
    const submitButton = modalButtons[modalButtons.length - 1]
    await user.click(submitButton)

    await waitFor(() => {
      expect(availabilitySlotServiceModule.availabilitySlotService.createSlot).toHaveBeenCalledWith(
        expect.objectContaining({
          start_time: expect.stringContaining('2024-03-22'),
        })
      )
      // Should not have end_time (it's automatic)
      expect(availabilitySlotServiceModule.availabilitySlotService.createSlot).not.toHaveBeenCalledWith(
        expect.objectContaining({
          end_time: expect.anything()
        })
      )
    })
  })

  it('should delete available slot when confirmed', async () => {
    const user = userEvent.setup()
    global.confirm.mockReturnValue(true)
    availabilitySlotServiceModule.availabilitySlotService.deleteSlot.mockResolvedValue()

    renderAvailabilitySlotManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Gestión de Horarios Disponibles')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByRole('button', { name: /eliminar/i })
    // First delete button should be for an available slot
    const firstDeleteButton = deleteButtons[0]
    expect(firstDeleteButton).not.toBeDisabled()

    await user.click(firstDeleteButton)

    await waitFor(() => {
      expect(global.confirm).toHaveBeenCalled()
      expect(availabilitySlotServiceModule.availabilitySlotService.deleteSlot).toHaveBeenCalled()
    })
  })

  it('should disable delete button for booked slots', async () => {
    renderAvailabilitySlotManagementPage()

    await waitFor(() => {
      expect(screen.getByText('Gestión de Horarios Disponibles')).toBeInTheDocument()
    })

    await waitFor(() => {
      const deleteButtons = screen.getAllByRole('button', { name: /eliminar/i })
      // Find the delete button for the booked slot (should be disabled)
      const bookedSlotDeleteButton = deleteButtons.find(btn => btn.disabled)
      expect(bookedSlotDeleteButton).toBeInTheDocument()
    })
  })

  it('should display error when fetching slots fails', async () => {
    const errorMessage = 'Failed to fetch slots'
    availabilitySlotServiceModule.availabilitySlotService.listSlots.mockRejectedValue({
      response: {
        data: {
          detail: errorMessage
        }
      }
    })

    renderAvailabilitySlotManagementPage()

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })
})
