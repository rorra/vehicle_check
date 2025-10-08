/**
 * Tests for CheckItemManagementPage component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ChakraProvider } from '@chakra-ui/react'
import CheckItemManagementPage from './CheckItemManagementPage'
import { AuthProvider } from '../../context/AuthContext'
import * as authService from '../../services/authService'
import * as checkItemServiceModule from '../../services/checkItemService'

// Mock authService
vi.mock('../../services/authService', () => ({
  authService: {
    getStoredToken: vi.fn(),
    getStoredUser: vi.fn(),
  }
}))

// Mock checkItemService
vi.mock('../../services/checkItemService', () => ({
  checkItemService: {
    listTemplates: vi.fn(),
    getTemplate: vi.fn(),
    createTemplate: vi.fn(),
    updateTemplate: vi.fn(),
    deleteTemplate: vi.fn(),
  }
}))

const renderCheckItemManagementPage = () => {
  return render(
    <ChakraProvider>
      <BrowserRouter>
        <AuthProvider>
          <CheckItemManagementPage />
        </AuthProvider>
      </BrowserRouter>
    </ChakraProvider>
  )
}

describe('CheckItemManagementPage', () => {
  const mockTemplates = [
    {
      id: 't1',
      code: 'BRK',
      description: 'Frenos',
      ordinal: 1
    },
    {
      id: 't2',
      code: 'LGT',
      description: 'Luces e indicadores',
      ordinal: 2
    },
    {
      id: 't3',
      code: 'TIR',
      description: 'Neumáticos',
      ordinal: 3
    },
    {
      id: 't4',
      code: 'ENG',
      description: 'Motor y fugas',
      ordinal: 4
    },
    {
      id: 't5',
      code: 'STE',
      description: 'Dirección',
      ordinal: 5
    },
    {
      id: 't6',
      code: 'SUS',
      description: 'Suspensión',
      ordinal: 6
    },
    {
      id: 't7',
      code: 'EMI',
      description: 'Emisiones',
      ordinal: 7
    },
    {
      id: 't8',
      code: 'SAF',
      description: 'Elementos de seguridad',
      ordinal: 8
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
  })

  describe('rendering', () => {
    it('should render the page title', async () => {
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue([])

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByText('Gestión de Plantillas de Chequeo')).toBeInTheDocument()
      })
    })

    it('should render info alert about required templates', async () => {
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue([])

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByText(/se requieren 8 plantillas de chequeo/i)).toBeInTheDocument()
      })
    })

    it('should render create and refresh buttons', async () => {
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue([])

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /crear plantilla/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /actualizar/i })).toBeInTheDocument()
      })
    })
  })

  describe('template list', () => {
    it('should display all templates in the table', async () => {
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue(mockTemplates)

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByText('BRK')).toBeInTheDocument()
        expect(screen.getByText('Frenos')).toBeInTheDocument()
        expect(screen.getByText('LGT')).toBeInTheDocument()
        expect(screen.getByText('Luces e indicadores')).toBeInTheDocument()
        expect(screen.getByText('SAF')).toBeInTheDocument()
        expect(screen.getByText('Elementos de seguridad')).toBeInTheDocument()
      })
    })

    it('should display empty state when no templates exist', async () => {
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue([])

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByText('No hay plantillas de chequeo configuradas')).toBeInTheDocument()
      })
    })

    it('should display loading state while fetching templates', async () => {
      checkItemServiceModule.checkItemService.listTemplates.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve([]), 100))
      )

      renderCheckItemManagementPage()

      expect(screen.getByText('Cargando...')).toBeInTheDocument()
    })

    it('should display template count with checkmark when exactly 8 templates', async () => {
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue(mockTemplates)

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByText(/Total de plantillas: 8 ✓/i)).toBeInTheDocument()
      })
    })

    it('should display template count without checkmark when less than 8 templates', async () => {
      const partialTemplates = mockTemplates.slice(0, 5)
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue(partialTemplates)

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByText(/Total de plantillas: 5 \(se requieren 8\)/i)).toBeInTheDocument()
      })
    })

    it('should display edit button for each template', async () => {
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue(mockTemplates)

      renderCheckItemManagementPage()

      await waitFor(() => {
        const editButtons = screen.getAllByRole('button', { name: /editar/i })
        expect(editButtons).toHaveLength(8)
      })
    })

    it('should display error message when loading fails', async () => {
      checkItemServiceModule.checkItemService.listTemplates.mockRejectedValue(
        new Error('Network error')
      )

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })
    })
  })

  describe('create template', () => {
    it('should open create modal when clicking create button', async () => {
      const user = userEvent.setup()
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue(mockTemplates)

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByText('BRK')).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /crear plantilla/i })
      await user.click(createButton)

      await waitFor(() => {
        expect(screen.getByText('Crear Plantilla de Chequeo')).toBeInTheDocument()
        expect(screen.getByLabelText(/código/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/descripción/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/orden/i)).toBeInTheDocument()
      })
    })

    it('should create new template with valid data', async () => {
      const user = userEvent.setup()
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue([])
      checkItemServiceModule.checkItemService.createTemplate.mockResolvedValue({
        id: 't9',
        code: 'NEW',
        description: 'Nueva plantilla',
        ordinal: 1
      })

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /crear plantilla/i })).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /crear plantilla/i })
      await user.click(createButton)

      await waitFor(() => {
        expect(screen.getByLabelText(/código/i)).toBeInTheDocument()
      })

      // Fill form
      const codeInput = screen.getByLabelText(/código/i)
      const descInput = screen.getByLabelText(/descripción/i)
      const ordinalSelect = screen.getByLabelText(/orden/i)

      await user.clear(codeInput)
      await user.type(codeInput, 'new')
      await user.clear(descInput)
      await user.type(descInput, 'Nueva plantilla')
      await user.selectOptions(ordinalSelect, '1')

      // Submit
      const createModalButtons = screen.getAllByRole('button', { name: /crear/i })
      const submitButton = createModalButtons[createModalButtons.length - 1]
      await user.click(submitButton)

      await waitFor(() => {
        expect(checkItemServiceModule.checkItemService.createTemplate).toHaveBeenCalledWith({
          code: 'NEW',
          description: 'Nueva plantilla',
          ordinal: 1
        })
      })
    })

    it('should convert code to uppercase when creating', async () => {
      const user = userEvent.setup()
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue([])
      checkItemServiceModule.checkItemService.createTemplate.mockResolvedValue({
        id: 't9',
        code: 'TST',
        description: 'Test',
        ordinal: 1
      })

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /crear plantilla/i })).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /crear plantilla/i })
      await user.click(createButton)

      await waitFor(() => {
        expect(screen.getByLabelText(/código/i)).toBeInTheDocument()
      })

      const codeInput = screen.getByLabelText(/código/i)
      const descInput = screen.getByLabelText(/descripción/i)

      await user.clear(codeInput)
      await user.type(codeInput, 'tst')
      await user.clear(descInput)
      await user.type(descInput, 'Test')

      const createModalButtons = screen.getAllByRole('button', { name: /crear/i })
      const submitButton = createModalButtons[createModalButtons.length - 1]
      await user.click(submitButton)

      await waitFor(() => {
        expect(checkItemServiceModule.checkItemService.createTemplate).toHaveBeenCalledWith(
          expect.objectContaining({
            code: 'TST'
          })
        )
      })
    })

    it('should close modal after successful creation', async () => {
      const user = userEvent.setup()
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue([])
      checkItemServiceModule.checkItemService.createTemplate.mockResolvedValue({
        id: 't9',
        code: 'NEW',
        description: 'Nueva plantilla',
        ordinal: 1
      })

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /crear plantilla/i })).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /crear plantilla/i })
      await user.click(createButton)

      await waitFor(() => {
        expect(screen.getByLabelText(/código/i)).toBeInTheDocument()
      })

      const codeInput = screen.getByLabelText(/código/i)
      const descInput = screen.getByLabelText(/descripción/i)

      await user.clear(codeInput)
      await user.type(codeInput, 'new')
      await user.clear(descInput)
      await user.type(descInput, 'Nueva plantilla')

      const createModalButtons = screen.getAllByRole('button', { name: /crear/i })
      const submitButton = createModalButtons[createModalButtons.length - 1]
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.queryByText('Crear Plantilla de Chequeo')).not.toBeInTheDocument()
      })
    })

    it('should display error when creation fails', async () => {
      const user = userEvent.setup()
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue([])
      checkItemServiceModule.checkItemService.createTemplate.mockRejectedValue({
        response: {
          data: {
            detail: 'El código ya existe'
          }
        }
      })

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /crear plantilla/i })).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /crear plantilla/i })
      await user.click(createButton)

      await waitFor(() => {
        expect(screen.getByLabelText(/código/i)).toBeInTheDocument()
      })

      const codeInput = screen.getByLabelText(/código/i)
      const descInput = screen.getByLabelText(/descripción/i)

      await user.clear(codeInput)
      await user.type(codeInput, 'dup')
      await user.clear(descInput)
      await user.type(descInput, 'Duplicate')

      const createModalButtons = screen.getAllByRole('button', { name: /crear/i })
      const submitButton = createModalButtons[createModalButtons.length - 1]
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('El código ya existe')).toBeInTheDocument()
      })
    })
  })

  describe('edit template', () => {
    it('should open edit modal when clicking edit button', async () => {
      const user = userEvent.setup()
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue(mockTemplates)

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByText('BRK')).toBeInTheDocument()
      })

      const editButtons = screen.getAllByRole('button', { name: /editar/i })
      await user.click(editButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Editar Plantilla de Chequeo')).toBeInTheDocument()
        expect(screen.getByDisplayValue('BRK')).toBeInTheDocument()
        expect(screen.getByDisplayValue('Frenos')).toBeInTheDocument()
      })
    })

    it('should update template with modified data', async () => {
      const user = userEvent.setup()
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue(mockTemplates)
      checkItemServiceModule.checkItemService.updateTemplate.mockResolvedValue({
        id: 't1',
        code: 'BRK',
        description: 'Frenos y sistema de frenado',
        ordinal: 1
      })

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByText('BRK')).toBeInTheDocument()
      })

      const editButtons = screen.getAllByRole('button', { name: /editar/i })
      await user.click(editButtons[0])

      await waitFor(() => {
        expect(screen.getByDisplayValue('Frenos')).toBeInTheDocument()
      })

      const descInput = screen.getByLabelText(/descripción/i)
      await user.clear(descInput)
      await user.type(descInput, 'Frenos y sistema de frenado')

      const saveButton = screen.getByRole('button', { name: /guardar/i })
      await user.click(saveButton)

      await waitFor(() => {
        expect(checkItemServiceModule.checkItemService.updateTemplate).toHaveBeenCalledWith(
          't1',
          expect.objectContaining({
            description: 'Frenos y sistema de frenado'
          })
        )
      })
    })

    it('should close modal after successful update', async () => {
      const user = userEvent.setup()
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue(mockTemplates)
      checkItemServiceModule.checkItemService.updateTemplate.mockResolvedValue({
        id: 't1',
        code: 'BRK',
        description: 'Updated',
        ordinal: 1
      })

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByText('BRK')).toBeInTheDocument()
      })

      const editButtons = screen.getAllByRole('button', { name: /editar/i })
      await user.click(editButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Editar Plantilla de Chequeo')).toBeInTheDocument()
      })

      const descInput = screen.getByLabelText(/descripción/i)
      await user.clear(descInput)
      await user.type(descInput, 'Updated')

      const saveButton = screen.getByRole('button', { name: /guardar/i })
      await user.click(saveButton)

      await waitFor(() => {
        expect(screen.queryByText('Editar Plantilla de Chequeo')).not.toBeInTheDocument()
      })
    })
  })

  describe('refresh functionality', () => {
    it('should reload templates when clicking refresh button', async () => {
      const user = userEvent.setup()
      checkItemServiceModule.checkItemService.listTemplates.mockResolvedValue(mockTemplates)

      renderCheckItemManagementPage()

      await waitFor(() => {
        expect(screen.getByText('BRK')).toBeInTheDocument()
      })

      expect(checkItemServiceModule.checkItemService.listTemplates).toHaveBeenCalledTimes(1)

      const refreshButton = screen.getByRole('button', { name: /actualizar/i })
      await user.click(refreshButton)

      await waitFor(() => {
        expect(checkItemServiceModule.checkItemService.listTemplates).toHaveBeenCalledTimes(2)
      })
    })
  })
})
