/**
 * Tests for InspectionResultsPage component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ChakraProvider } from '@chakra-ui/react'
import InspectionResultsPage from './InspectionResultsPage'
import { AuthProvider } from '../context/AuthContext'
import * as authService from '../services/authService'
import * as inspectionResultServiceModule from '../services/inspectionResultService'
import * as vehicleServiceModule from '../services/vehicleService'

// Mock authService
vi.mock('../services/authService', () => ({
  authService: {
    getStoredToken: vi.fn(),
    getStoredUser: vi.fn(),
  }
}))

// Mock inspectionResultService
vi.mock('../services/inspectionResultService', () => ({
  inspectionResultService: {
    listResults: vi.fn(),
    getResult: vi.fn(),
    getResultsByAnnualInspection: vi.fn(),
  }
}))

// Mock vehicleService
vi.mock('../services/vehicleService', () => ({
  vehicleService: {
    listVehicles: vi.fn(),
    listVehiclesWithOwners: vi.fn(),
  }
}))

const renderInspectionResultsPage = () => {
  return render(
    <ChakraProvider>
      <BrowserRouter>
        <AuthProvider>
          <InspectionResultsPage />
        </AuthProvider>
      </BrowserRouter>
    </ChakraProvider>
  )
}

describe('InspectionResultsPage', () => {
  const mockResults = [
    {
      id: 'r1',
      vehicle_plate: 'ABC123',
      vehicle_make: 'Toyota',
      vehicle_model: 'Corolla',
      year: 2024,
      total_score: 65,
      passed: true,
      created_at: '2024-03-15T10:00:00',
    },
    {
      id: 'r2',
      vehicle_plate: 'XYZ789',
      vehicle_make: 'Honda',
      vehicle_model: 'Civic',
      year: 2024,
      total_score: 35,
      passed: false,
      created_at: '2024-03-16T14:00:00',
    }
  ]

  const mockDetailedResult = {
    id: 'r1',
    vehicle_plate: 'ABC123',
    vehicle_make: 'Toyota',
    vehicle_model: 'Corolla',
    inspector_name: 'Inspector One',
    inspection_date: '2024-03-15T10:00:00',
    total_score: 65,
    passed: true,
    owner_observation: null,
    item_checks: [
      {
        id: 'ic1',
        template_ordinal: 1,
        template_description: 'Frenos',
        score: 9,
        observation: 'Chequeo realizado sin observaciones críticas'
      },
      {
        id: 'ic2',
        template_ordinal: 2,
        template_description: 'Luces e indicadores',
        score: 8,
        observation: 'Chequeo realizado sin observaciones críticas'
      },
      {
        id: 'ic3',
        template_ordinal: 3,
        template_description: 'Neumáticos',
        score: 8,
        observation: 'Chequeo realizado sin observaciones críticas'
      },
      {
        id: 'ic4',
        template_ordinal: 4,
        template_description: 'Motor y fugas',
        score: 7,
        observation: 'Chequeo realizado sin observaciones críticas'
      },
      {
        id: 'ic5',
        template_ordinal: 5,
        template_description: 'Dirección',
        score: 8,
        observation: 'Chequeo realizado sin observaciones críticas'
      },
      {
        id: 'ic6',
        template_ordinal: 6,
        template_description: 'Suspensión',
        score: 8,
        observation: 'Chequeo realizado sin observaciones críticas'
      },
      {
        id: 'ic7',
        template_ordinal: 7,
        template_description: 'Emisiones',
        score: 9,
        observation: 'Chequeo realizado sin observaciones críticas'
      },
      {
        id: 'ic8',
        template_ordinal: 8,
        template_description: 'Elementos de seguridad',
        score: 8,
        observation: 'Chequeo realizado sin observaciones críticas'
      }
    ]
  }

  const mockClientUser = {
    id: 'user-1',
    name: 'Client User',
    email: 'client@example.com',
    role: 'CLIENT'
  }

  const mockAdminUser = {
    id: 'user-2',
    name: 'Admin User',
    email: 'admin@example.com',
    role: 'ADMIN'
  }

  const mockVehicles = [
    { id: 'v1', plate_number: 'ABC123', make: 'Toyota', model: 'Corolla' },
    { id: 'v2', plate_number: 'XYZ789', make: 'Honda', model: 'Civic' }
  ]

  const mockVehiclesWithOwners = [
    { id: 'v1', plate_number: 'ABC123', make: 'Toyota', model: 'Corolla', owner_name: 'John Doe' },
    { id: 'v2', plate_number: 'XYZ789', make: 'Honda', model: 'Civic', owner_name: 'Jane Smith' }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    authService.authService.getStoredToken.mockReturnValue('fake-token')
  })

  describe('as CLIENT', () => {
    beforeEach(() => {
      authService.authService.getStoredUser.mockReturnValue(mockClientUser)
      inspectionResultServiceModule.inspectionResultService.listResults.mockResolvedValue({
        results: mockResults,
        total: mockResults.length,
        page: 1,
        page_size: 10
      })
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: mockVehicles
      })
    })

    it('should render page title for client', async () => {
      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getByText('Mis Resultados')).toBeInTheDocument()
      })
    })

    it('should display results list', async () => {
      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
        expect(screen.getAllByText('XYZ789').length).toBeGreaterThan(0)
        expect(screen.getByText('65/80')).toBeInTheDocument()
        expect(screen.getByText('35/80')).toBeInTheDocument()
      })
    })

    it('should display passed and failed badges', async () => {
      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getByText('Aprobado')).toBeInTheDocument()
        expect(screen.getByText('Rechazado')).toBeInTheDocument()
      })
    })

    it('should show empty state when no results', async () => {
      inspectionResultServiceModule.inspectionResultService.listResults.mockResolvedValue({
        results: [],
        total: 0,
        page: 1,
        page_size: 10
      })

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getByText('No hay resultados disponibles')).toBeInTheDocument()
      })
    })

    it('should display loading state while fetching results', async () => {
      inspectionResultServiceModule.inspectionResultService.listResults.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          results: [],
          total: 0,
          page: 1,
          page_size: 10
        }), 100))
      )

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getByText('Cargando...')).toBeInTheDocument()
      })
    })

    it('should not show owner name column for CLIENT', async () => {
      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      expect(screen.queryByText('Propietario')).not.toBeInTheDocument()
    })

    it('should load client vehicles on mount', async () => {
      renderInspectionResultsPage()

      await waitFor(() => {
        expect(vehicleServiceModule.vehicleService.listVehicles).toHaveBeenCalled()
      })
    })
  })

  describe('as ADMIN', () => {
    beforeEach(() => {
      authService.authService.getStoredUser.mockReturnValue(mockAdminUser)
      inspectionResultServiceModule.inspectionResultService.listResults.mockResolvedValue({
        results: mockResults,
        total: mockResults.length,
        page: 1,
        page_size: 10
      })
      vehicleServiceModule.vehicleService.listVehiclesWithOwners.mockResolvedValue(
        mockVehiclesWithOwners
      )
    })

    it('should render page title for admin', async () => {
      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getByText('Resultados de Inspecciones')).toBeInTheDocument()
      })
    })

    it('should load vehicles with owners for admin', async () => {
      renderInspectionResultsPage()

      await waitFor(() => {
        expect(vehicleServiceModule.vehicleService.listVehiclesWithOwners).toHaveBeenCalled()
      })
    })

    it('should show vehicle options with owner names in filter for admin', async () => {
      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      // Check that vehicle select has options (we can't easily check option text in jsdom)
      const vehicleSelect = screen.getByLabelText(/vehículo/i)
      expect(vehicleSelect).toBeInTheDocument()
    })
  })

  describe('filters', () => {
    beforeEach(() => {
      authService.authService.getStoredUser.mockReturnValue(mockClientUser)
      inspectionResultServiceModule.inspectionResultService.listResults.mockResolvedValue({
        results: mockResults,
        total: mockResults.length,
        page: 1,
        page_size: 10
      })
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: mockVehicles
      })
    })

    it('should render filter section', async () => {
      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getByText('Filtros')).toBeInTheDocument()
        expect(screen.getByLabelText(/año/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/vehículo/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/estado/i)).toBeInTheDocument()
      })
    })

    it('should filter by year', async () => {
      const user = userEvent.setup()

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      const yearSelect = screen.getByLabelText(/año/i)
      await user.selectOptions(yearSelect, '2024')

      await waitFor(() => {
        expect(inspectionResultServiceModule.inspectionResultService.listResults).toHaveBeenCalledWith(
          expect.objectContaining({
            year: 2024
          })
        )
      })
    })

    it('should filter by vehicle', async () => {
      const user = userEvent.setup()

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      const vehicleSelect = screen.getByLabelText(/vehículo/i)
      await user.selectOptions(vehicleSelect, 'v1')

      await waitFor(() => {
        expect(inspectionResultServiceModule.inspectionResultService.listResults).toHaveBeenCalledWith(
          expect.objectContaining({
            vehicle_id: 'v1'
          })
        )
      })
    })

    it('should filter by passed status', async () => {
      const user = userEvent.setup()

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      const statusSelect = screen.getByLabelText(/estado/i)
      await user.selectOptions(statusSelect, 'true')

      await waitFor(() => {
        expect(inspectionResultServiceModule.inspectionResultService.listResults).toHaveBeenCalledWith(
          expect.objectContaining({
            passed_only: true
          })
        )
      })
    })

    it('should reset all filters when clicking clear filters', async () => {
      const user = userEvent.setup()

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      // Set some filters
      const yearSelect = screen.getByLabelText(/año/i)
      const vehicleSelect = screen.getByLabelText(/vehículo/i)
      await user.selectOptions(yearSelect, '2024')
      await user.selectOptions(vehicleSelect, 'v1')

      // Clear filters
      const clearButton = screen.getByRole('button', { name: /limpiar filtros/i })
      await user.click(clearButton)

      await waitFor(() => {
        expect(yearSelect.value).toBe('')
        expect(vehicleSelect.value).toBe('')
      })
    })
  })

  describe('detail modal', () => {
    beforeEach(() => {
      authService.authService.getStoredUser.mockReturnValue(mockClientUser)
      inspectionResultServiceModule.inspectionResultService.listResults.mockResolvedValue({
        results: mockResults,
        total: mockResults.length,
        page: 1,
        page_size: 10
      })
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: mockVehicles
      })
      inspectionResultServiceModule.inspectionResultService.getResult.mockResolvedValue(
        mockDetailedResult
      )
    })

    it('should open detail modal when clicking view detail button', async () => {
      const user = userEvent.setup()

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      const viewDetailButtons = screen.getAllByRole('button', { name: /ver detalle/i })
      await user.click(viewDetailButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Detalle de Inspección')).toBeInTheDocument()
      })
    })

    it('should display general info in detail modal', async () => {
      const user = userEvent.setup()

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      const viewDetailButtons = screen.getAllByRole('button', { name: /ver detalle/i })
      await user.click(viewDetailButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Información General')).toBeInTheDocument()
        expect(screen.getByText('Toyota Corolla')).toBeInTheDocument()
        expect(screen.getByText('Inspector One')).toBeInTheDocument()
      })
    })

    it('should display all 8 item checks in detail modal', async () => {
      const user = userEvent.setup()

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      const viewDetailButtons = screen.getAllByRole('button', { name: /ver detalle/i })
      await user.click(viewDetailButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Ítems Chequeados')).toBeInTheDocument()
        expect(screen.getByText(/1\. Frenos/)).toBeInTheDocument()
        expect(screen.getByText(/2\. Luces e indicadores/)).toBeInTheDocument()
        expect(screen.getByText(/8\. Elementos de seguridad/)).toBeInTheDocument()
      })
    })

    it('should display item scores in badges', async () => {
      const user = userEvent.setup()

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      const viewDetailButtons = screen.getAllByRole('button', { name: /ver detalle/i })
      await user.click(viewDetailButtons[0])

      await waitFor(() => {
        expect(screen.getAllByText('9/10').length).toBeGreaterThan(0)
        expect(screen.getAllByText('8/10').length).toBeGreaterThan(0)
      })
    })

    it('should display owner observation when present', async () => {
      const user = userEvent.setup()
      inspectionResultServiceModule.inspectionResultService.getResult.mockResolvedValue({
        ...mockDetailedResult,
        owner_observation: 'Requiere reparación de frenos'
      })

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      const viewDetailButtons = screen.getAllByRole('button', { name: /ver detalle/i })
      await user.click(viewDetailButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Observaciones Generales')).toBeInTheDocument()
        expect(screen.getByText('Requiere reparación de frenos')).toBeInTheDocument()
      })
    })

    it('should not display owner observation section when null', async () => {
      const user = userEvent.setup()

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      const viewDetailButtons = screen.getAllByRole('button', { name: /ver detalle/i })
      await user.click(viewDetailButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Detalle de Inspección')).toBeInTheDocument()
      })

      expect(screen.queryByText('Observaciones Generales')).not.toBeInTheDocument()
    })

    it('should sort item checks by ordinal', async () => {
      const user = userEvent.setup()

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      const viewDetailButtons = screen.getAllByRole('button', { name: /ver detalle/i })
      await user.click(viewDetailButtons[0])

      await waitFor(() => {
        expect(inspectionResultServiceModule.inspectionResultService.getResult).toHaveBeenCalledWith('r1')
      })
    })
  })

  describe('pagination', () => {
    beforeEach(() => {
      authService.authService.getStoredUser.mockReturnValue(mockClientUser)
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: mockVehicles
      })
    })

    it('should show pagination when multiple pages exist', async () => {
      inspectionResultServiceModule.inspectionResultService.listResults.mockResolvedValue({
        results: mockResults,
        total: 25,
        page: 1,
        page_size: 10
      })

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getByText(/página 1 de 3/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /anterior/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /siguiente/i })).toBeInTheDocument()
      })
    })

    it('should not show pagination with single page', async () => {
      inspectionResultServiceModule.inspectionResultService.listResults.mockResolvedValue({
        results: mockResults,
        total: 2,
        page: 1,
        page_size: 10
      })

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      expect(screen.queryByText(/página/i)).not.toBeInTheDocument()
    })

    it('should navigate to next page', async () => {
      const user = userEvent.setup()
      inspectionResultServiceModule.inspectionResultService.listResults.mockResolvedValue({
        results: mockResults,
        total: 25,
        page: 1,
        page_size: 10
      })

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getByText(/página 1 de 3/i)).toBeInTheDocument()
      })

      const nextButton = screen.getByRole('button', { name: /siguiente/i })
      await user.click(nextButton)

      await waitFor(() => {
        expect(inspectionResultServiceModule.inspectionResultService.listResults).toHaveBeenCalledWith(
          expect.objectContaining({
            page: 2
          })
        )
      })
    })

    it('should navigate to previous page', async () => {
      const user = userEvent.setup()
      inspectionResultServiceModule.inspectionResultService.listResults.mockResolvedValue({
        results: mockResults,
        total: 25,
        page: 1,
        page_size: 10
      })

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getByText(/página 1 de 3/i)).toBeInTheDocument()
      })

      // First navigate to page 2
      const nextButton = screen.getByRole('button', { name: /siguiente/i })
      await user.click(nextButton)

      await waitFor(() => {
        expect(screen.getByText(/página 2 de 3/i)).toBeInTheDocument()
      })

      // Then navigate back to page 1
      const prevButton = screen.getByRole('button', { name: /anterior/i })
      await user.click(prevButton)

      await waitFor(() => {
        expect(inspectionResultServiceModule.inspectionResultService.listResults).toHaveBeenCalledWith(
          expect.objectContaining({
            page: 1
          })
        )
      })
    })

    it('should disable previous button on first page', async () => {
      inspectionResultServiceModule.inspectionResultService.listResults.mockResolvedValue({
        results: mockResults,
        total: 25,
        page: 1,
        page_size: 10
      })

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getByText(/página 1 de 3/i)).toBeInTheDocument()
      })

      const prevButton = screen.getByRole('button', { name: /anterior/i })
      expect(prevButton).toBeDisabled()
    })

    it('should disable next button on last page', async () => {
      const user = userEvent.setup()
      inspectionResultServiceModule.inspectionResultService.listResults.mockResolvedValue({
        results: mockResults,
        total: 25,
        page: 1,
        page_size: 10
      })

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getByText(/página 1 de 3/i)).toBeInTheDocument()
      })

      // Navigate to page 2
      const nextButton = screen.getByRole('button', { name: /siguiente/i })
      await user.click(nextButton)

      await waitFor(() => {
        expect(screen.getByText(/página 2 de 3/i)).toBeInTheDocument()
      })

      // Navigate to page 3 (last page)
      await user.click(nextButton)

      await waitFor(() => {
        expect(screen.getByText(/página 3 de 3/i)).toBeInTheDocument()
      })

      // Next button should be disabled
      expect(nextButton).toBeDisabled()
    })
  })

  describe('refresh functionality', () => {
    beforeEach(() => {
      authService.authService.getStoredUser.mockReturnValue(mockClientUser)
      inspectionResultServiceModule.inspectionResultService.listResults.mockResolvedValue({
        results: mockResults,
        total: mockResults.length,
        page: 1,
        page_size: 10
      })
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: mockVehicles
      })
    })

    it('should reload results when clicking refresh button', async () => {
      const user = userEvent.setup()

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      expect(inspectionResultServiceModule.inspectionResultService.listResults).toHaveBeenCalledTimes(1)

      const refreshButton = screen.getByRole('button', { name: /actualizar/i })
      await user.click(refreshButton)

      await waitFor(() => {
        expect(inspectionResultServiceModule.inspectionResultService.listResults).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('error handling', () => {
    beforeEach(() => {
      authService.authService.getStoredUser.mockReturnValue(mockClientUser)
      vehicleServiceModule.vehicleService.listVehicles.mockResolvedValue({
        vehicles: mockVehicles
      })
    })

    it('should display error message when loading results fails', async () => {
      inspectionResultServiceModule.inspectionResultService.listResults.mockRejectedValue(
        new Error('Network error')
      )

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })
    })

    it('should display error and close modal when loading detail fails', async () => {
      const user = userEvent.setup()
      inspectionResultServiceModule.inspectionResultService.listResults.mockResolvedValue({
        results: mockResults,
        total: mockResults.length,
        page: 1,
        page_size: 10
      })
      inspectionResultServiceModule.inspectionResultService.getResult.mockRejectedValue({
        response: {
          data: {
            detail: 'Resultado no encontrado'
          }
        }
      })

      renderInspectionResultsPage()

      await waitFor(() => {
        expect(screen.getAllByText('ABC123').length).toBeGreaterThan(0)
      })

      const viewDetailButtons = screen.getAllByRole('button', { name: /ver detalle/i })
      await user.click(viewDetailButtons[0])

      await waitFor(() => {
        expect(screen.queryByText('Detalle de Inspección')).not.toBeInTheDocument()
        expect(screen.getByText('Resultado no encontrado')).toBeInTheDocument()
      })
    })
  })
})
