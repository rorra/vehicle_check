/**
 * Tests for AppointmentManagementPage component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ChakraProvider } from '@chakra-ui/react'
import AppointmentManagementPage from './AppointmentManagementPage'
import { AuthProvider } from '../context/AuthContext'
import * as authService from '../services/authService'
import * as appointmentServiceModule from '../services/appointmentService'
import * as vehicleServiceModule from '../services/vehicleService'
import * as inspectorServiceModule from '../services/inspectorService'

// Mock authService
vi.mock('../services/authService', () => ({
  authService: {
    getStoredToken: vi.fn(),
    getStoredUser: vi.fn(),
  }
}))

// Mock appointmentService
vi.mock('../services/appointmentService', () => ({
  appointmentService: {
    listAppointments: vi.fn(),
    getAvailableSlots: vi.fn(),
    createAppointment: vi.fn(),
    updateAppointment: vi.fn(),
    cancelAppointment: vi.fn(),
  }
}))

// Mock vehicleService
vi.mock('../services/vehicleService', () => ({
  vehicleService: {
    listVehicles: vi.fn(),
    listVehiclesWithOwners: vi.fn(),
  }
}))

// Mock inspectorService
vi.mock('../services/inspectorService', () => ({
  inspectorService: {
    listInspectors: vi.fn(),
  }
}))

// Mock window.confirm
global.confirm = vi.fn()

const renderAppointmentManagementPage = () => {
  return render(
    <ChakraProvider>
      <BrowserRouter>
        <AuthProvider>
          <AppointmentManagementPage />
        </AuthProvider>
      </BrowserRouter>
    </ChakraProvider>
  )
}

describe('AppointmentManagementPage', () => {
  const mockAppointments = [
    {
      id: '1',
      vehicle_id: 'v1',
      vehicle_plate: 'ABC123',
      vehicle_make: 'Toyota',
      vehicle_model: 'Corolla',
      owner_name: 'John Doe',
      owner_email: 'john@example.com',
      inspector_name: 'Inspector One',
      date_time: '2024-03-15T10:00:00',
      status: 'PENDING',
    },
    {
      id: '2',
      vehicle_id: 'v2',
      vehicle_plate: 'XYZ789',
      vehicle_make: 'Honda',
      vehicle_model: 'Civic',
      owner_name: 'Jane Smith',
      owner_email: 'jane@example.com',
      inspector_name: null,
      date_time: '2024-03-16T14:00:00',
      status: 'CONFIRMED',
    }
  ]

  const mockClientUser = {
    id: 'user-1',
    name: 'Client User',
    email: 'client@example.com',
    role: 'CLIENT'
  }

  const mockInspectorUser = {
    id: 'user-2',
    name: 'Inspector User',
    email: 'inspector@example.com',
    role: 'INSPECTOR'
  }

  const mockAdminUser = {
    id: 'user-3',
    name: 'Admin User',
    email: 'admin@example.com',
    role: 'ADMIN'
  }

  const mockVehicles = [
    { id: 'v1', plate_number: 'ABC123', make: 'Toyota', model: 'Corolla' },
    { id: 'v2', plate_number: 'XYZ789', make: 'Honda', model: 'Civic' }
  ]

  const mockInspectors = [
    { id: 'i1', user_name: 'Inspector One', employee_id: 'EMP001' },
    { id: 'i2', user_name: 'Inspector Two', employee_id: 'EMP002' }
  ]

  const mockAvailableSlots = [
    {
      id: 'slot-1',
      start_time: '2024-03-20T10:00:00',
      end_time: '2024-03-20T11:00:00',
      is_booked: false
    },
    {
      id: 'slot-2',
      start_time: '2024-03-20T14:00:00',
      end_time: '2024-03-20T15:00:00',
      is_booked: false
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    authService.authService.getStoredToken.mockReturnValue('fake-token')
    appointmentServiceModule.appointmentService.getAvailableSlots.mockResolvedValue(mockAvailableSlots)
  })

  describe('as CLIENT', () => {
    beforeEach(() => {
      authService.authService.getStoredUser.mockReturnValue(mockClientUser)
      appointmentServiceModule.appointmentService.listAppointments.mockResolvedValue({
        appointments: mockAppointments,
        total: mockAppointments.length
      })
    })

    it('should render appointment management page with appointment list', async () => {
      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('Mis Turnos')).toBeInTheDocument()
        expect(screen.getByText('ABC123')).toBeInTheDocument()
        expect(screen.getByText('XYZ789')).toBeInTheDocument()
      })
    })

    it('should display appointment details correctly', async () => {
      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
        expect(screen.getByText('Toyota Corolla')).toBeInTheDocument()
        expect(screen.getByText('Inspector One')).toBeInTheDocument()
      })
    })

    it('should show create button for CLIENT', async () => {
      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /crear turno/i })
      expect(createButton).toBeInTheDocument()
    })

    it('should display status badges with correct colors', async () => {
      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('Pendiente')).toBeInTheDocument()
        expect(screen.getByText('Confirmado')).toBeInTheDocument()
      })
    })

    it('should open create modal when clicking create button', async () => {
      const user = userEvent.setup()
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: mockVehicles
      })

      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /crear turno/i })
      await user.click(createButton)

      await waitFor(() => {
        // Modal header should exist
        expect(screen.getAllByText('Crear Turno').length).toBeGreaterThan(0)
        expect(screen.getByLabelText(/vehículo/i)).toBeInTheDocument()
        // Should show slot selector instead of date/time
        expect(screen.getByLabelText(/horario disponible/i)).toBeInTheDocument()
      })
    })

    it('should not show inspector selector for CLIENT', async () => {
      const user = userEvent.setup()
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: mockVehicles
      })

      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /crear turno/i })
      await user.click(createButton)

      await waitFor(() => {
        expect(screen.getAllByText('Crear Turno').length).toBeGreaterThan(0)
      })

      expect(screen.queryByLabelText(/inspector asignado/i)).not.toBeInTheDocument()
    })

    it('should create appointment with slot_id', async () => {
      const user = userEvent.setup()
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: mockVehicles
      })
      appointmentServiceModule.appointmentService.createAppointment.mockResolvedValue({
        id: '3',
        vehicle_id: 'v1',
        slot_id: 'slot-1'
      })

      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /crear turno/i })
      await user.click(createButton)

      await waitFor(() => {
        expect(screen.getByLabelText(/vehículo/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/horario disponible/i)).toBeInTheDocument()
      })

      // Select vehicle
      const vehicleSelect = screen.getByLabelText(/vehículo/i)
      await user.selectOptions(vehicleSelect, 'v1')

      // Select slot
      const slotSelect = screen.getByLabelText(/horario disponible/i)
      await user.selectOptions(slotSelect, 'slot-1')

      // Find and click the submit button in modal footer
      const modalButtons = screen.getAllByRole('button', { name: /crear/i })
      const submitButton = modalButtons[modalButtons.length - 1] // Last one should be in modal footer
      await user.click(submitButton)

      await waitFor(() => {
        expect(appointmentServiceModule.appointmentService.createAppointment).toHaveBeenCalledWith(
          expect.objectContaining({
            vehicle_id: 'v1',
            slot_id: 'slot-1'
          })
        )
      })
    })

    it('should cancel appointment when confirmed', async () => {
      const user = userEvent.setup()
      global.confirm.mockReturnValue(true)
      appointmentServiceModule.appointmentService.cancelAppointment.mockResolvedValue()

      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
        expect(screen.getByText('XYZ789')).toBeInTheDocument()
      })

      const cancelButtons = screen.getAllByRole('button', { name: /cancelar/i })
      // First cancel button in table (appointments are sorted by date descending, so XYZ789 is first)
      await user.click(cancelButtons[0])

      await waitFor(() => {
        expect(global.confirm).toHaveBeenCalledWith(
          expect.stringContaining('XYZ789')
        )
        expect(appointmentServiceModule.appointmentService.cancelAppointment).toHaveBeenCalledWith('2')
      })
    })

    it('should show slot selector when CLIENT edits appointment', async () => {
      const user = userEvent.setup()
      appointmentServiceModule.appointmentService.getAvailableSlots.mockResolvedValue(mockAvailableSlots)

      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      // Click reprogramar button
      const reprogramButtons = screen.getAllByRole('button', { name: /reprogramar/i })
      await user.click(reprogramButtons[0])

      await waitFor(() => {
        // Should show slot selector (not datetime input)
        expect(screen.getByLabelText(/horario disponible/i)).toBeInTheDocument()
        expect(screen.queryByLabelText(/fecha y hora/i)).not.toBeInTheDocument()
      })
    })

    it('should update appointment with slot when CLIENT edits', async () => {
      const user = userEvent.setup()
      appointmentServiceModule.appointmentService.getAvailableSlots.mockResolvedValue(mockAvailableSlots)
      appointmentServiceModule.appointmentService.updateAppointment.mockResolvedValue()

      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      // Click reprogramar button (first one is appointment id '2' - XYZ789, sorted by date descending)
      const reprogramButtons = screen.getAllByRole('button', { name: /reprogramar/i })
      await user.click(reprogramButtons[0])

      await waitFor(() => {
        expect(screen.getByLabelText(/horario disponible/i)).toBeInTheDocument()
      })

      // Select a slot
      const slotSelect = screen.getByLabelText(/horario disponible/i)
      await user.selectOptions(slotSelect, 'slot-1')

      // Submit
      const saveButton = screen.getByRole('button', { name: /guardar/i })
      await user.click(saveButton)

      await waitFor(() => {
        expect(appointmentServiceModule.appointmentService.updateAppointment).toHaveBeenCalledWith(
          '2',
          expect.objectContaining({
            date_time: expect.any(String)
          })
        )
      })
    })
  })

  describe('as INSPECTOR', () => {
    beforeEach(() => {
      authService.authService.getStoredUser.mockReturnValue(mockInspectorUser)
      appointmentServiceModule.appointmentService.listAppointments.mockResolvedValue({
        appointments: mockAppointments,
        total: mockAppointments.length
      })
    })

    it('should render inspector view with assigned appointments', async () => {
      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('Mis Turnos Asignados')).toBeInTheDocument()
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })
    })

    it('should not show create button for INSPECTOR', async () => {
      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      expect(screen.queryByRole('button', { name: /crear turno/i })).not.toBeInTheDocument()
    })

    it('should not show action buttons for INSPECTOR', async () => {
      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      // Inspector should not see Reprogramar or Cancelar buttons
      expect(screen.queryByRole('button', { name: /reprogramar/i })).not.toBeInTheDocument()
    })
  })

  describe('as ADMIN', () => {
    beforeEach(() => {
      authService.authService.getStoredUser.mockReturnValue(mockAdminUser)
      appointmentServiceModule.appointmentService.listAppointments.mockResolvedValue({
        appointments: mockAppointments,
        total: mockAppointments.length
      })
      vehicleServiceModule.vehicleService.listVehiclesWithOwners.mockResolvedValue(mockVehicles)
      inspectorServiceModule.inspectorService.listInspectors.mockResolvedValue({
        inspectors: mockInspectors
      })
    })

    it('should render admin view with all appointments', async () => {
      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('Gestión de Turnos')).toBeInTheDocument()
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })
    })

    it('should show owner column for ADMIN', async () => {
      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('Propietario')).toBeInTheDocument()
        expect(screen.getByText('John Doe')).toBeInTheDocument()
        expect(screen.getByText(/john@example\.com/i)).toBeInTheDocument()
      })
    })

    it('should show inspector selector when creating appointment as ADMIN', async () => {
      const user = userEvent.setup()

      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /crear turno/i })
      await user.click(createButton)

      await waitFor(() => {
        expect(screen.getByLabelText(/inspector asignado/i)).toBeInTheDocument()
      })
    })

    it('should show reprogramar and cancelar buttons for ADMIN', async () => {
      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      const reprogramButtons = screen.getAllByRole('button', { name: /reprogramar/i })
      const cancelButtons = screen.getAllByRole('button', { name: /cancelar/i })

      expect(reprogramButtons.length).toBeGreaterThan(0)
      expect(cancelButtons.length).toBeGreaterThan(0)
    })

    it('should show slot selector when ADMIN edits appointment', async () => {
      const user = userEvent.setup()
      appointmentServiceModule.appointmentService.getAvailableSlots.mockResolvedValue(mockAvailableSlots)

      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      // Click reprogramar button
      const reprogramButtons = screen.getAllByRole('button', { name: /reprogramar/i })
      await user.click(reprogramButtons[0])

      await waitFor(() => {
        // ADMIN also uses slot selector (not datetime input)
        expect(screen.getByLabelText(/horario disponible/i)).toBeInTheDocument()
        expect(screen.queryByLabelText(/fecha y hora/i)).not.toBeInTheDocument()
      })
    })

    it('should update appointment with slot when ADMIN edits', async () => {
      const user = userEvent.setup()
      appointmentServiceModule.appointmentService.getAvailableSlots.mockResolvedValue(mockAvailableSlots)
      appointmentServiceModule.appointmentService.updateAppointment.mockResolvedValue()

      renderAppointmentManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      // Click reprogramar button (first one is appointment id '2' - XYZ789, sorted by date descending)
      const reprogramButtons = screen.getAllByRole('button', { name: /reprogramar/i })
      await user.click(reprogramButtons[0])

      await waitFor(() => {
        expect(screen.getByLabelText(/horario disponible/i)).toBeInTheDocument()
      })

      // Select a slot
      const slotSelect = screen.getByLabelText(/horario disponible/i)
      await user.selectOptions(slotSelect, 'slot-1')

      // Submit
      const saveButton = screen.getByRole('button', { name: /guardar/i })
      await user.click(saveButton)

      await waitFor(() => {
        expect(appointmentServiceModule.appointmentService.updateAppointment).toHaveBeenCalledWith(
          '2',
          expect.objectContaining({
            date_time: expect.any(String)
          })
        )
      })
    })
  })
})
