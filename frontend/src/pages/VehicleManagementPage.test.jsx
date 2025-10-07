/**
 * Tests for VehicleManagementPage component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ChakraProvider } from '@chakra-ui/react'
import VehicleManagementPage from './VehicleManagementPage'
import { AuthProvider } from '../context/AuthContext'
import * as authService from '../services/authService'
import * as vehicleServiceModule from '../services/vehicleService'
import * as clientServiceModule from '../services/clientService'

// Mock authService
vi.mock('../services/authService', () => ({
  authService: {
    getStoredToken: vi.fn(),
    getStoredUser: vi.fn(),
  }
}))

// Mock vehicleService
vi.mock('../services/vehicleService', () => ({
  vehicleService: {
    listVehicles: vi.fn(),
    listVehiclesWithOwners: vi.fn(),
    createVehicle: vi.fn(),
    updateVehicle: vi.fn(),
    deleteVehicle: vi.fn(),
  }
}))

// Mock clientService
vi.mock('../services/clientService', () => ({
  clientService: {
    listClients: vi.fn(),
  }
}))

// Mock window.confirm
global.confirm = vi.fn()

const renderVehicleManagementPage = () => {
  return render(
    <ChakraProvider>
      <BrowserRouter>
        <AuthProvider>
          <VehicleManagementPage />
        </AuthProvider>
      </BrowserRouter>
    </ChakraProvider>
  )
}

describe('VehicleManagementPage', () => {
  const mockVehicles = [
    {
      id: '1',
      plate_number: 'ABC123',
      make: 'Toyota',
      model: 'Corolla',
      year: 2020,
      owner_id: 'user-1',
      is_active: true
    },
    {
      id: '2',
      plate_number: 'XYZ789',
      make: 'Honda',
      model: 'Civic',
      year: 2021,
      owner_id: 'user-2',
      is_active: true
    }
  ]

  const mockVehiclesWithInactive = [
    {
      id: '1',
      plate_number: 'ABC123',
      make: 'Toyota',
      model: 'Corolla',
      year: 2020,
      owner_id: 'user-1',
      is_active: true
    },
    {
      id: '2',
      plate_number: 'XYZ789',
      make: 'Honda',
      model: 'Civic',
      year: 2021,
      owner_id: 'user-2',
      is_active: true
    },
    {
      id: '3',
      plate_number: 'OLD456',
      make: 'Ford',
      model: 'Focus',
      year: 2015,
      owner_id: 'user-1',
      is_active: false
    }
  ]

  const mockVehiclesWithOwners = [
    {
      id: '1',
      plate_number: 'ABC123',
      make: 'Toyota',
      model: 'Corolla',
      year: 2020,
      owner_id: 'client-1',
      owner_name: 'John Doe',
      owner_email: 'john@example.com',
      is_active: true
    },
    {
      id: '2',
      plate_number: 'XYZ789',
      make: 'Honda',
      model: 'Civic',
      year: 2021,
      owner_id: 'client-2',
      owner_name: 'Jane Smith',
      owner_email: 'jane@example.com',
      is_active: true
    }
  ]

  const mockVehiclesWithOwnersAndInactive = [
    {
      id: '1',
      plate_number: 'ABC123',
      make: 'Toyota',
      model: 'Corolla',
      year: 2020,
      owner_id: 'client-1',
      owner_name: 'John Doe',
      owner_email: 'john@example.com',
      is_active: true
    },
    {
      id: '2',
      plate_number: 'XYZ789',
      make: 'Honda',
      model: 'Civic',
      year: 2021,
      owner_id: 'client-2',
      owner_name: 'Jane Smith',
      owner_email: 'jane@example.com',
      is_active: true
    },
    {
      id: '3',
      plate_number: 'OLD456',
      make: 'Ford',
      model: 'Focus',
      year: 2015,
      owner_id: 'client-1',
      owner_name: 'John Doe',
      owner_email: 'john@example.com',
      is_active: false
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

  const mockClients = [
    {
      id: 'client-1',
      name: 'John Doe',
      email: 'john@example.com',
      role: 'CLIENT',
      is_active: true
    },
    {
      id: 'client-2',
      name: 'Jane Smith',
      email: 'jane@example.com',
      role: 'CLIENT',
      is_active: true
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    authService.authService.getStoredToken.mockReturnValue('fake-token')
  })

  describe('as CLIENT', () => {
    beforeEach(() => {
      authService.authService.getStoredUser.mockReturnValue(mockClientUser)
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: mockVehicles,
        total: mockVehicles.length
      })
    })

    it('should render vehicle management page with vehicle list', async () => {
      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('Mis Vehículos')).toBeInTheDocument()
        expect(screen.getByText('ABC123')).toBeInTheDocument()
        expect(screen.getByText('XYZ789')).toBeInTheDocument()
      })
    })

    it('should display vehicle details correctly', async () => {
      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('Toyota')).toBeInTheDocument()
        expect(screen.getByText('Corolla')).toBeInTheDocument()
        expect(screen.getByText('2020')).toBeInTheDocument()
      })
    })

    it('should open create modal when clicking create button', async () => {
      const user = userEvent.setup()
      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /crear vehículo/i })
      await user.click(createButton)

      // Wait for modal form fields to appear
      await waitFor(() => {
        expect(screen.getByLabelText(/matrícula/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/marca/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/modelo/i)).toBeInTheDocument()
      })
    })

    it('should not show owner_id field for CLIENT', async () => {
      const user = userEvent.setup()
      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /crear vehículo/i })
      await user.click(createButton)

      await waitFor(() => {
        expect(screen.getByLabelText(/matrícula/i)).toBeInTheDocument()
      })

      // Owner ID field should not be present for CLIENT
      expect(screen.queryByLabelText(/propietario/i)).not.toBeInTheDocument()
    })

    it('should create vehicle successfully', async () => {
      const user = userEvent.setup()
      const newVehicle = {
        id: '3',
        plate_number: 'NEW123',
        make: 'Ford',
        model: 'Focus',
        year: 2022,
        owner_id: 'user-1'
      }
      vehicleServiceModule.vehicleService.createVehicle.mockResolvedValue(newVehicle)

      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /crear vehículo/i })
      await user.click(createButton)

      await waitFor(() => {
        expect(screen.getByLabelText(/matrícula/i)).toBeInTheDocument()
      })

      const plateInput = screen.getByLabelText(/matrícula/i)
      await user.type(plateInput, 'NEW123')

      const makeInput = screen.getByLabelText(/marca/i)
      await user.type(makeInput, 'Ford')

      const modelInput = screen.getByLabelText(/modelo/i)
      await user.type(modelInput, 'Focus')

      const yearInput = screen.getByLabelText(/año/i)
      await user.type(yearInput, '2022')

      const saveButton = screen.getByRole('button', { name: /crear/i })
      await user.click(saveButton)

      await waitFor(() => {
        expect(vehicleServiceModule.vehicleService.createVehicle).toHaveBeenCalledWith(
          expect.objectContaining({
            plate_number: 'NEW123',
            make: 'Ford',
            model: 'Focus',
            year: 2022
          })
        )
      })
    })

    it('should update vehicle successfully', async () => {
      const user = userEvent.setup()
      vehicleServiceModule.vehicleService.updateVehicle.mockResolvedValue({
        ...mockVehicles[0],
        make: 'Nissan'
      })

      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      const editButtons = screen.getAllByRole('button', { name: /editar/i })
      await user.click(editButtons[0])

      await waitFor(() => {
        expect(screen.getByDisplayValue('Toyota')).toBeInTheDocument()
      })

      const makeInput = screen.getByDisplayValue('Toyota')
      await user.clear(makeInput)
      await user.type(makeInput, 'Nissan')

      const saveButton = screen.getByRole('button', { name: /guardar/i })
      await user.click(saveButton)

      await waitFor(() => {
        expect(vehicleServiceModule.vehicleService.updateVehicle).toHaveBeenCalledWith(
          '1',
          expect.objectContaining({
            make: 'Nissan'
          })
        )
      })
    })

    it('should show Deshabilitar button and soft delete confirmation for CLIENT', async () => {
      const user = userEvent.setup()
      global.confirm.mockReturnValue(true)
      vehicleServiceModule.vehicleService.deleteVehicle.mockResolvedValue()

      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      // CLIENT should see "Deshabilitar" not "Eliminar"
      const disableButtons = screen.getAllByRole('button', { name: /deshabilitar/i })
      expect(disableButtons.length).toBeGreaterThan(0)

      await user.click(disableButtons[0])

      await waitFor(() => {
        // Should show soft delete confirmation message
        expect(global.confirm).toHaveBeenCalledWith(
          expect.stringMatching(/deshabilitar.*ABC123.*volver a habilitar/i)
        )
        expect(vehicleServiceModule.vehicleService.deleteVehicle).toHaveBeenCalledWith('1')
      })
    })

    it('should display status badges for active and inactive vehicles', async () => {
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: mockVehiclesWithInactive,
        total: mockVehiclesWithInactive.length
      })

      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      // Should show status column
      expect(screen.getByText('Estado')).toBeInTheDocument()
      // Should show "Activo" badges
      const activeBadges = screen.getAllByText('Activo')
      expect(activeBadges.length).toBeGreaterThan(0)
    })

    it('should filter inactive vehicles with checkbox', async () => {
      const user = userEvent.setup()

      // Initially return only active vehicles
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: mockVehicles,
        total: mockVehicles.length
      })

      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      // Should show checkbox filter
      const checkbox = screen.getByRole('checkbox', { name: /incluir vehículos deshabilitados/i })
      expect(checkbox).toBeInTheDocument()
      expect(checkbox).not.toBeChecked()

      // When checkbox is clicked, should include inactive
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: mockVehiclesWithInactive,
        total: mockVehiclesWithInactive.length
      })

      await user.click(checkbox)

      await waitFor(() => {
        expect(vehicleServiceModule.vehicleService.listVehicles).toHaveBeenCalledWith(
          { include_inactive: true }
        )
      })
    })

    it('should disable edit button for inactive vehicles', async () => {
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: mockVehiclesWithInactive,
        total: mockVehiclesWithInactive.length
      })

      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('OLD456')).toBeInTheDocument()
      })

      // Get all edit buttons
      const editButtons = screen.getAllByRole('button', { name: /editar/i })

      // The inactive vehicle's edit button (third row) should be disabled
      const inactiveEditButton = editButtons[2]
      expect(inactiveEditButton).toBeDisabled()
    })

    it('should display error when fetching vehicles fails', async () => {
      const errorMessage = 'Failed to fetch vehicles'
      vehicleServiceModule.vehicleService.listVehicles.mockRejectedValue({
        response: {
          data: {
            detail: errorMessage
          }
        }
      })

      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument()
      })
    })
  })

  describe('as ADMIN', () => {
    beforeEach(() => {
      authService.authService.getStoredUser.mockReturnValue(mockAdminUser)
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: [],
        total: 0
      })
      vehicleServiceModule.vehicleService.listVehiclesWithOwners.mockResolvedValue(mockVehiclesWithOwners)
      clientServiceModule.clientService.listClients.mockResolvedValue({
        users: mockClients,
        total: mockClients.length
      })
    })

    it('should render admin view with all vehicles', async () => {
      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('Gestión de Vehículos')).toBeInTheDocument()
      })

      // Verify the correct endpoint is called
      await waitFor(() => {
        expect(vehicleServiceModule.vehicleService.listVehiclesWithOwners).toHaveBeenCalled()
      })

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
        expect(screen.getByText('XYZ789')).toBeInTheDocument()
      })
    })

    it('should show owner name with email in one column for ADMIN', async () => {
      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('Propietario')).toBeInTheDocument()
        // Email column should not exist
        expect(screen.queryByText('Email')).not.toBeInTheDocument()
        // Check that owner info is displayed with email in parentheses
        expect(screen.getByText('John Doe')).toBeInTheDocument()
        expect(screen.getByText(/\(john@example\.com\)/i)).toBeInTheDocument()
        expect(screen.getByText('Jane Smith')).toBeInTheDocument()
        expect(screen.getByText(/\(jane@example\.com\)/i)).toBeInTheDocument()
      })
    })

    it('should show required client selector when creating vehicle as ADMIN', async () => {
      const user = userEvent.setup()
      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /crear vehículo/i })
      await user.click(createButton)

      await waitFor(() => {
        const ownerLabel = screen.getByText(/propietario del vehículo/i)
        expect(ownerLabel).toBeInTheDocument()
        // Check that it's required (has asterisk)
        expect(ownerLabel.parentElement).toHaveTextContent('*')
        expect(clientServiceModule.clientService.listClients).toHaveBeenCalled()
      })
    })

    it('should filter and select client from searchable list', async () => {
      const user = userEvent.setup()
      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /crear vehículo/i })
      await user.click(createButton)

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/buscar cliente/i)).toBeInTheDocument()
      })

      // Type in search box
      const searchInput = screen.getByPlaceholderText(/buscar cliente/i)
      await user.type(searchInput, 'John')

      // Wait for filtered results
      await waitFor(() => {
        expect(screen.getAllByText('John Doe').length).toBeGreaterThan(0)
        expect(screen.getAllByText('john@example.com').length).toBeGreaterThan(0)
      })

      // Click on client in dropdown (last occurrence, as dropdown is rendered after table)
      const johnOptions = screen.getAllByText('John Doe')
      await user.click(johnOptions[johnOptions.length - 1])

      // Verify client is selected
      await waitFor(() => {
        expect(screen.queryByPlaceholderText(/buscar cliente/i)).not.toBeInTheDocument()
        // John Doe should still be in the table (so at least one occurrence exists)
        expect(screen.getAllByText('John Doe').length).toBeGreaterThan(0)
      })
    })

    it('should show Eliminar button and hard delete confirmation for ADMIN', async () => {
      const user = userEvent.setup()
      global.confirm.mockReturnValue(true)
      vehicleServiceModule.vehicleService.deleteVehicle.mockResolvedValue()

      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      // ADMIN should see "Eliminar" not "Deshabilitar"
      const deleteButtons = screen.getAllByRole('button', { name: /eliminar/i })
      expect(deleteButtons.length).toBeGreaterThan(0)

      await user.click(deleteButtons[0])

      await waitFor(() => {
        // Should show hard delete confirmation with cascade warning
        expect(global.confirm).toHaveBeenCalledWith(
          expect.stringMatching(/eliminar permanentemente.*ABC123.*inspecciones.*turnos.*resultados/i)
        )
        expect(vehicleServiceModule.vehicleService.deleteVehicle).toHaveBeenCalledWith('1')
      })
    })

    it('should display status badges and Estado column for ADMIN', async () => {
      vehicleServiceModule.vehicleService.listVehiclesWithOwners.mockResolvedValue(
        mockVehiclesWithOwnersAndInactive
      )

      renderVehicleManagementPage()

      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument()
      })

      // Should show status column
      expect(screen.getByText('Estado')).toBeInTheDocument()

      // Should show "Activo" and "Deshabilitado" badges
      const activeBadges = screen.getAllByText('Activo')
      expect(activeBadges.length).toBe(2)

      const inactiveBadges = screen.getAllByText('Deshabilitado')
      expect(inactiveBadges.length).toBe(1)
    })
  })
})
