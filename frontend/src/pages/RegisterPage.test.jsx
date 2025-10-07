/**
 * Tests for RegisterPage component
 *
 * Tests the registration form functionality including:
 * - Form rendering
 * - User input handling
 * - Registration submission
 * - Error handling
 * - Success toast notification
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ChakraProvider } from '@chakra-ui/react'
import RegisterPage from './RegisterPage'
import { AuthProvider } from '../context/AuthContext'
import * as authService from '../services/authService'

// Mock authService
vi.mock('../services/authService', () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    getCurrentUser: vi.fn(),
    getStoredToken: vi.fn(),
    getStoredUser: vi.fn(),
  }
}))

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Helper function to render RegisterPage with all providers
const renderRegisterPage = () => {
  return render(
    <ChakraProvider>
      <BrowserRouter>
        <AuthProvider>
          <RegisterPage />
        </AuthProvider>
      </BrowserRouter>
    </ChakraProvider>
  )
}

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    authService.authService.getStoredToken.mockReturnValue(null)
    authService.authService.getStoredUser.mockReturnValue(null)
  })

  it('should render registration form', async () => {
    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /registro/i })).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /nombre completo/i })).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /correo electrónico/i })).toBeInTheDocument()
      expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument()
      expect(screen.getByRole('combobox', { name: /tipo de usuario/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /registrarse/i })).toBeInTheDocument()
    })
  })

  it('should show link to login page', async () => {
    renderRegisterPage()

    await waitFor(() => {
      const loginLink = screen.getByText('Inicia sesión aquí')
      expect(loginLink).toBeInTheDocument()
      expect(loginLink.closest('a')).toHaveAttribute('href', '/login')
    })
  })

  it('should have CLIENT as default role', async () => {
    renderRegisterPage()

    await waitFor(() => {
      const roleSelect = screen.getByRole('combobox', { name: /tipo de usuario/i })
      expect(roleSelect).toHaveValue('CLIENT')
    })
  })

  it('should allow selecting different roles', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByRole('combobox', { name: /tipo de usuario/i })).toBeInTheDocument()
    })

    const roleSelect = screen.getByRole('combobox', { name: /tipo de usuario/i })

    // Test INSPECTOR role
    await user.selectOptions(roleSelect, 'INSPECTOR')
    expect(roleSelect).toHaveValue('INSPECTOR')

    // Test ADMIN role
    await user.selectOptions(roleSelect, 'ADMIN')
    expect(roleSelect).toHaveValue('ADMIN')

    // Test CLIENT role
    await user.selectOptions(roleSelect, 'CLIENT')
    expect(roleSelect).toHaveValue('CLIENT')
  })

  it('should handle successful registration', async () => {
    const user = userEvent.setup()
    const mockUser = { id: 1, name: 'New User', email: 'new@example.com', role: 'CLIENT' }

    authService.authService.register.mockResolvedValue(mockUser)

    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: /nombre completo/i })).toBeInTheDocument()
    })

    const nameInput = screen.getByRole('textbox', { name: /nombre completo/i })
    const emailInput = screen.getByRole('textbox', { name: /correo electrónico/i })
    const passwordInput = screen.getByLabelText(/contraseña/i)
    const roleSelect = screen.getByRole('combobox', { name: /tipo de usuario/i })
    const submitButton = screen.getByRole('button', { name: /registrarse/i })

    await user.type(nameInput, 'New User')
    await user.type(emailInput, 'new@example.com')
    await user.type(passwordInput, 'password123')
    await user.selectOptions(roleSelect, 'CLIENT')
    await user.click(submitButton)

    await waitFor(() => {
      expect(authService.authService.register).toHaveBeenCalledWith({
        name: 'New User',
        email: 'new@example.com',
        password: 'password123',
        role: 'CLIENT'
      })
      expect(mockNavigate).toHaveBeenCalledWith('/login')
    })
  })

  it('should display error message on registration failure', async () => {
    const user = userEvent.setup()
    const errorMessage = 'Email: Email already exists'

    authService.authService.register.mockRejectedValue({
      response: {
        data: {
          detail: [
            {
              loc: ['body', 'email'],
              msg: 'Email already exists'
            }
          ]
        }
      }
    })

    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: /nombre completo/i })).toBeInTheDocument()
    })

    const nameInput = screen.getByRole('textbox', { name: /nombre completo/i })
    const emailInput = screen.getByRole('textbox', { name: /correo electrónico/i })
    const passwordInput = screen.getByLabelText(/contraseña/i)
    const submitButton = screen.getByRole('button', { name: /registrarse/i })

    await user.type(nameInput, 'Test User')
    await user.type(emailInput, 'existing@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('should clear error when user types in any field', async () => {
    const user = userEvent.setup()
    authService.authService.register.mockRejectedValue({
      response: {
        data: {
          detail: 'Error'
        }
      }
    })

    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: /nombre completo/i })).toBeInTheDocument()
    })

    const nameInput = screen.getByRole('textbox', { name: /nombre completo/i })
    const emailInput = screen.getByRole('textbox', { name: /correo electrónico/i })
    const passwordInput = screen.getByLabelText(/contraseña/i)
    const submitButton = screen.getByRole('button', { name: /registrarse/i })

    // Trigger error
    await user.type(nameInput, 'Test')
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument()
    })

    // Type in name field should clear error
    await user.type(nameInput, 'a')

    await waitFor(() => {
      expect(screen.queryByText('Error')).not.toBeInTheDocument()
    })
  })

  it('should disable form inputs while loading', async () => {
    const user = userEvent.setup()

    // Make registration take a long time
    authService.authService.register.mockImplementation(() => {
      return new Promise(resolve => setTimeout(resolve, 1000))
    })

    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: /nombre completo/i })).toBeInTheDocument()
    })

    const nameInput = screen.getByRole('textbox', { name: /nombre completo/i })
    const emailInput = screen.getByRole('textbox', { name: /correo electrónico/i })
    const passwordInput = screen.getByLabelText(/contraseña/i)
    const roleSelect = screen.getByRole('combobox', { name: /tipo de usuario/i })
    const submitButton = screen.getByRole('button', { name: /registrarse/i })

    await user.type(nameInput, 'Test User')
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    // Check that inputs are disabled during loading
    await waitFor(() => {
      expect(nameInput).toBeDisabled()
      expect(emailInput).toBeDisabled()
      expect(passwordInput).toBeDisabled()
      expect(roleSelect).toBeDisabled()
    })
  })

  it('should display validation error for short password', async () => {
    const user = userEvent.setup()

    authService.authService.register.mockRejectedValue({
      response: {
        data: {
          detail: [
            {
              loc: ['body', 'password'],
              msg: 'String should have at least 6 characters'
            }
          ]
        }
      }
    })

    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: /nombre completo/i })).toBeInTheDocument()
    })

    const nameInput = screen.getByRole('textbox', { name: /nombre completo/i })
    const emailInput = screen.getByRole('textbox', { name: /correo electrónico/i })
    const passwordInput = screen.getByLabelText(/contraseña/i)
    const submitButton = screen.getByRole('button', { name: /registrarse/i })

    await user.type(nameInput, 'Test User')
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, '123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Password: String should have at least 6 characters')).toBeInTheDocument()
    })
  })
})
