/**
 * Tests for LoginPage component
 *
 * Tests the login form functionality including:
 * - Form rendering
 * - User input handling
 * - Login submission
 * - Error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ChakraProvider } from '@chakra-ui/react'
import LoginPage from './LoginPage'
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

// Helper function to render LoginPage with all providers
const renderLoginPage = () => {
  return render(
    <ChakraProvider>
      <BrowserRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </BrowserRouter>
    </ChakraProvider>
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    authService.authService.getStoredToken.mockReturnValue(null)
    authService.authService.getStoredUser.mockReturnValue(null)
  })

  it('should render login form', async () => {
    renderLoginPage()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /iniciar sesión/i })).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /correo electrónico/i })).toBeInTheDocument()
      expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument()
    })
  })

  it('should show link to registration page', async () => {
    renderLoginPage()

    await waitFor(() => {
      const registerLink = screen.getByText('Regístrate aquí')
      expect(registerLink).toBeInTheDocument()
      expect(registerLink.closest('a')).toHaveAttribute('href', '/register')
    })
  })

  it('should handle successful login', async () => {
    const user = userEvent.setup()
    const mockUser = { id: 1, name: 'Test User', email: 'test@example.com', role: 'CLIENT' }

    authService.authService.login.mockResolvedValue()
    authService.authService.getCurrentUser.mockResolvedValue(mockUser)

    renderLoginPage()

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: /correo electrónico/i })).toBeInTheDocument()
    })

    const emailInput = screen.getByRole('textbox', { name: /correo electrónico/i })
    const passwordInput = screen.getByLabelText(/contraseña/i)
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(authService.authService.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      })
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  it('should display error message on login failure', async () => {
    const user = userEvent.setup()
    const errorMessage = 'Credenciales inválidas'

    authService.authService.login.mockRejectedValue({
      response: {
        data: {
          detail: errorMessage
        }
      }
    })

    renderLoginPage()

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: /correo electrónico/i })).toBeInTheDocument()
    })

    const emailInput = screen.getByRole('textbox', { name: /correo electrónico/i })
    const passwordInput = screen.getByLabelText(/contraseña/i)
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })

    await user.type(emailInput, 'wrong@example.com')
    await user.type(passwordInput, 'wrongpassword')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('should clear error when user types in email field', async () => {
    const user = userEvent.setup()
    authService.authService.login.mockRejectedValue({
      response: {
        data: {
          detail: 'Error'
        }
      }
    })

    renderLoginPage()

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: /correo electrónico/i })).toBeInTheDocument()
    })

    const emailInput = screen.getByRole('textbox', { name: /correo electrónico/i })
    const passwordInput = screen.getByLabelText(/contraseña/i)
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })

    // Trigger error
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument()
    })

    // Type in email field should clear error
    await user.clear(emailInput)
    await user.type(emailInput, 'new')

    await waitFor(() => {
      expect(screen.queryByText('Error')).not.toBeInTheDocument()
    })
  })

  it('should clear error when user types in password field', async () => {
    const user = userEvent.setup()
    authService.authService.login.mockRejectedValue({
      response: {
        data: {
          detail: 'Error'
        }
      }
    })

    renderLoginPage()

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: /correo electrónico/i })).toBeInTheDocument()
    })

    const emailInput = screen.getByRole('textbox', { name: /correo electrónico/i })
    const passwordInput = screen.getByLabelText(/contraseña/i)
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })

    // Trigger error
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument()
    })

    // Type in password field should clear error
    await user.clear(passwordInput)
    await user.type(passwordInput, 'new')

    await waitFor(() => {
      expect(screen.queryByText('Error')).not.toBeInTheDocument()
    })
  })

  it('should disable form inputs while loading', async () => {
    const user = userEvent.setup()

    // Make login take a long time
    authService.authService.login.mockImplementation(() => {
      return new Promise(resolve => setTimeout(resolve, 1000))
    })

    renderLoginPage()

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: /correo electrónico/i })).toBeInTheDocument()
    })

    const emailInput = screen.getByRole('textbox', { name: /correo electrónico/i })
    const passwordInput = screen.getByLabelText(/contraseña/i)
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    // Check that inputs are disabled during loading
    await waitFor(() => {
      expect(emailInput).toBeDisabled()
      expect(passwordInput).toBeDisabled()
    })
  })
})
