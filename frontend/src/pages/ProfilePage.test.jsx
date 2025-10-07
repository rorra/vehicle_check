/**
 * Tests for ProfilePage component
 *
 * Tests profile viewing, editing, and password change functionality.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ChakraProvider } from '@chakra-ui/react'
import ProfilePage from './ProfilePage'
import { AuthProvider } from '../context/AuthContext'
import * as authService from '../services/authService'
import * as userServiceModule from '../services/userService'

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

// Mock userService
vi.mock('../services/userService', () => ({
  userService: {
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
  }
}))

// Helper to render component with providers
const renderProfilePage = () => {
  return render(
    <ChakraProvider>
      <BrowserRouter>
        <AuthProvider>
          <ProfilePage />
        </AuthProvider>
      </BrowserRouter>
    </ChakraProvider>
  )
}

describe('ProfilePage', () => {
  const mockUser = {
    id: 1,
    name: 'Test User',
    email: 'test@example.com',
    role: 'CLIENT'
  }

  beforeEach(() => {
    vi.clearAllMocks()
    authService.authService.getStoredToken.mockReturnValue('fake-token')
    authService.authService.getStoredUser.mockReturnValue(mockUser)
  })

  it('should render profile page with user data', async () => {
    renderProfilePage()

    await waitFor(() => {
      expect(screen.getByText('Mi Perfil')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Test User')).toBeInTheDocument()
      expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument()
      expect(screen.getByText(/Cliente/)).toBeInTheDocument()
    })
  })

  it('should display user role correctly', async () => {
    renderProfilePage()

    await waitFor(() => {
      expect(screen.getByText(/Rol:/)).toBeInTheDocument()
      expect(screen.getByText(/Cliente/)).toBeInTheDocument()
    })
  })

  it('should update profile successfully', async () => {
    const user = userEvent.setup()
    userServiceModule.userService.updateProfile.mockResolvedValue({
      ...mockUser,
      name: 'Updated Name'
    })

    renderProfilePage()

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test User')).toBeInTheDocument()
    })

    const nameInput = screen.getByDisplayValue('Test User')
    const saveButton = screen.getByRole('button', { name: /guardar cambios/i })

    await user.clear(nameInput)
    await user.type(nameInput, 'Updated Name')
    await user.click(saveButton)

    await waitFor(() => {
      expect(userServiceModule.userService.updateProfile).toHaveBeenCalledWith({
        name: 'Updated Name',
        email: 'test@example.com'
      })
    })
  })

  it('should display error when profile update fails', async () => {
    const user = userEvent.setup()
    const errorMessage = 'Email: Email already exists'

    userServiceModule.userService.updateProfile.mockRejectedValue({
      response: {
        data: {
          detail: errorMessage
        }
      }
    })

    renderProfilePage()

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test User')).toBeInTheDocument()
    })

    const nameInput = screen.getByDisplayValue('Test User')
    const saveButton = screen.getByRole('button', { name: /guardar cambios/i })

    await user.clear(nameInput)
    await user.type(nameInput, 'New Name')
    await user.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('should change password successfully', async () => {
    const user = userEvent.setup()
    userServiceModule.userService.changePassword.mockResolvedValue({
      message: 'Password changed'
    })

    renderProfilePage()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /cambiar contraseña/i })).toBeInTheDocument()
    })

    const currentPasswordInput = screen.getByLabelText(/contraseña actual/i)
    const newPasswordInput = screen.getByLabelText(/nueva contraseña/i)
    const changeButton = screen.getByRole('button', { name: /cambiar contraseña/i })

    await user.type(currentPasswordInput, 'oldpassword')
    await user.type(newPasswordInput, 'newpassword123')
    await user.click(changeButton)

    await waitFor(() => {
      expect(userServiceModule.userService.changePassword).toHaveBeenCalledWith({
        current_password: 'oldpassword',
        new_password: 'newpassword123'
      })
    })

    // Password fields should be cleared after success
    await waitFor(() => {
      expect(currentPasswordInput).toHaveValue('')
      expect(newPasswordInput).toHaveValue('')
    })
  })

  it('should display error when password change fails', async () => {
    const user = userEvent.setup()
    const errorMessage = 'Current_password: Invalid password'

    userServiceModule.userService.changePassword.mockRejectedValue({
      response: {
        data: {
          detail: [
            {
              loc: ['body', 'current_password'],
              msg: 'Invalid password'
            }
          ]
        }
      }
    })

    renderProfilePage()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /cambiar contraseña/i })).toBeInTheDocument()
    })

    const currentPasswordInput = screen.getByLabelText(/contraseña actual/i)
    const newPasswordInput = screen.getByLabelText(/nueva contraseña/i)
    const changeButton = screen.getByRole('button', { name: /cambiar contraseña/i })

    await user.type(currentPasswordInput, 'wrongpassword')
    await user.type(newPasswordInput, 'newpassword123')
    await user.click(changeButton)

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('should clear profile error when user types', async () => {
    const user = userEvent.setup()
    userServiceModule.userService.updateProfile.mockRejectedValue({
      response: {
        data: {
          detail: 'Error'
        }
      }
    })

    renderProfilePage()

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test User')).toBeInTheDocument()
    })

    const nameInput = screen.getByDisplayValue('Test User')
    const saveButton = screen.getByRole('button', { name: /guardar cambios/i })

    // Trigger error
    await user.click(saveButton)

    await waitFor(() => {
      expect(screen.getAllByText('Error')[0]).toBeInTheDocument()
    })

    // Type to clear error
    await user.type(nameInput, 'a')

    await waitFor(() => {
      expect(screen.queryByText('Error')).not.toBeInTheDocument()
    })
  })

  it('should clear password error when user types', async () => {
    const user = userEvent.setup()
    userServiceModule.userService.changePassword.mockRejectedValue({
      response: {
        data: {
          detail: 'Password error'
        }
      }
    })

    renderProfilePage()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /cambiar contraseña/i })).toBeInTheDocument()
    })

    const currentPasswordInput = screen.getByLabelText(/contraseña actual/i)
    const newPasswordInput = screen.getByLabelText(/nueva contraseña/i)
    const changeButton = screen.getByRole('button', { name: /cambiar contraseña/i })

    // Fill in required fields and trigger error
    await user.type(currentPasswordInput, 'wrong')
    await user.type(newPasswordInput, 'newpass')
    await user.click(changeButton)

    await waitFor(() => {
      expect(screen.getByText('Password error')).toBeInTheDocument()
    })

    // Type to clear error
    await user.type(currentPasswordInput, 'a')

    await waitFor(() => {
      expect(screen.queryByText('Password error')).not.toBeInTheDocument()
    })
  })
})
