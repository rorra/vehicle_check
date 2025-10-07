/**
 * Tests for AnnualInspectionManagementPage component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ChakraProvider } from '@chakra-ui/react'
import AnnualInspectionManagementPage from './AnnualInspectionManagementPage'
import { AuthProvider } from '../context/AuthContext'
import * as authService from '../services/authService'
import * as annualInspectionServiceModule from '../services/annualInspectionService'
import * as vehicleServiceModule from '../services/vehicleService'

// Mock authService
vi.mock('../services/authService', () => ({
  authService: {
    getStoredToken: vi.fn(),
    getStoredUser: vi.fn(),
  }
}))

// Mock annualInspectionService
vi.mock('../services/annualInspectionService', () => ({
  annualInspectionService: {
    listAnnualInspections: vi.fn(),
    createAnnualInspection: vi.fn(),
    updateAnnualInspection: vi.fn(),
    deleteAnnualInspection: vi.fn(),
  }
}))

// Mock vehicleService
vi.mock('../services/vehicleService', () => ({
  vehicleService: {
    listVehicles: vi.fn(),
    listVehiclesWithOwners: vi.fn(),
  }
}))

// Mock window.confirm
global.confirm = vi.fn()

const renderAnnualInspectionManagementPage = () => {
  return render(
    <ChakraProvider>
      <BrowserRouter>
        <AuthProvider>
          <AnnualInspectionManagementPage />
        </AuthProvider>
      </BrowserRouter>
    </ChakraProvider>
  )
}

describe('AnnualInspectionManagementPage', () => {
  const mockInspections = [
    {
      id: '1',
      vehicle_id: 'vehicle-1',
      year: 2024,
      status: 'PENDING',
      attempt_count: 0,
      vehicle_plate: 'ABC123',
      vehicle_make: 'Toyota',
      vehicle_model: 'Corolla',
      vehicle_year: 2020,
      owner_name: 'John Doe',
      owner_email: 'john@example.com',
      total_appointments: 0,
      last_appointment_date: null
    },
    {
      id: '2',
      vehicle_id: 'vehicle-2',
      year: 2024,
      status: 'PASSED',
      attempt_count: 1,
      vehicle_plate: 'XYZ789',
      vehicle_make: 'Honda',
      vehicle_model: 'Civic',
      vehicle_year: 2021,
      owner_name: 'Jane Smith',
      owner_email: 'jane@example.com',
      total_appointments: 1,
      last_appointment_date: '2024-01-15T10:00:00Z'
    }
  ]

  const mockClientUser = {
    id: 'user-1',
    name: 'Client User',
    email: 'client@example.com',
    role: 'CLIENT'
  }

  const mockAdminUser = {
    id: 'user-99',
    name: 'Admin User',
    email: 'admin@example.com',
    role: 'ADMIN'
  }

  const mockVehicles = [
    { id: 'vehicle-1', plate_number: 'ABC123', make: 'Toyota', model: 'Corolla', year: 2020 },
    { id: 'vehicle-2', plate_number: 'XYZ789', make: 'Honda', model: 'Civic', year: 2021 }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    authService.authService.getStoredToken.mockReturnValue('fake-token')
  })

  describe('as CLIENT', () => {
    beforeEach(() => {
      authService.authService.getStoredUser.mockReturnValue(mockClientUser)
      annualInspectionServiceModule.annualInspectionService.listAnnualInspections.mockResolvedValue({
        inspections: mockInspections,
        total: mockInspections.length
      })
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: mockVehicles,
        total: mockVehicles.length
      })
    })

    it('should render annual inspection page with inspection list', async () => {
      renderAnnualInspectionManagementPage()

      await waitFor(() => {
        expect(screen.getByText('Mis Inspecciones Anuales')).toBeInTheDocument()
        expect(screen.getByText('ABC123')).toBeInTheDocument()
        expect(screen.getByText('XYZ789')).toBeInTheDocument()
      })
    })

    it('should display inspection status correctly', async () => {
      renderAnnualInspectionManagementPage()

      await waitFor(() => {
        expect(screen.getByText('Pendiente')).toBeInTheDocument()
        expect(screen.getByText('Aprobada')).toBeInTheDocument()
      })
    })

    it('should not show create button for clients', async () => {
      renderAnnualInspectionManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      // Create button should not be present for CLIENT
      expect(screen.queryByRole('button', { name: /crear inspección/i })).not.toBeInTheDocument()
    })
  })

  describe('as ADMIN', () => {
    beforeEach(() => {
      authService.authService.getStoredUser.mockReturnValue(mockAdminUser)
      annualInspectionServiceModule.annualInspectionService.listAnnualInspections.mockResolvedValue({
        inspections: mockInspections,
        total: mockInspections.length
      })
      vehicleServiceModule.vehicleService.listVehiclesWithOwners.mockResolvedValue(mockVehicles)
    })

    it('should render admin view with all inspections', async () => {
      renderAnnualInspectionManagementPage()

      await waitFor(() => {
        expect(screen.getByText('Gestión de Inspecciones Anuales')).toBeInTheDocument()
        expect(screen.getByText('ABC123')).toBeInTheDocument()
        expect(screen.getByText('XYZ789')).toBeInTheDocument()
      })
    })

    it('should show owner information for admin', async () => {
      renderAnnualInspectionManagementPage()

      await waitFor(() => {
        expect(screen.getByText('Propietario')).toBeInTheDocument()
        expect(screen.getByText('John Doe')).toBeInTheDocument()
        expect(screen.getByText(/john@example\.com/i)).toBeInTheDocument()
      })
    })

    it('should show create button for admin', async () => {
      const user = userEvent.setup()
      renderAnnualInspectionManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      // Create button should be present for ADMIN
      const createButton = screen.getByRole('button', { name: /crear inspección/i })
      expect(createButton).toBeInTheDocument()

      await user.click(createButton)

      await waitFor(() => {
        expect(screen.getByLabelText(/vehículo/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/año/i)).toBeInTheDocument()
      })
    })

    it('should delete inspection when confirmed', async () => {
      const user = userEvent.setup()
      global.confirm.mockReturnValue(true)
      annualInspectionServiceModule.annualInspectionService.deleteAnnualInspection.mockResolvedValue()

      renderAnnualInspectionManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      const deleteButtons = screen.getAllByRole('button', { name: /eliminar/i })
      await user.click(deleteButtons[0])

      await waitFor(() => {
        expect(global.confirm).toHaveBeenCalledWith(
          expect.stringContaining('ABC123')
        )
        expect(annualInspectionServiceModule.annualInspectionService.deleteAnnualInspection).toHaveBeenCalledWith('1')
      })
    })
  })
})
