/**
 * Tests for AuthContext
 *
 * Tests the authentication context provider and useAuth hook.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { act } from 'react'
import { AuthProvider, useAuth } from './AuthContext'
import * as authService from '../services/authService'

// Mock authService module
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

// Test component that uses the useAuth hook
const TestComponent = () => {
  const { user, isAuthenticated, loading } = useAuth()

  if (loading) return <div>Loading...</div>
  if (user) return <div>User: {user.name}</div>
  return <div>No user</div>
}

describe('AuthContext', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks()
    // Clear localStorage
    localStorage.clear()
  })

  it('should provide auth context to children', async () => {
    authService.authService.getStoredToken.mockReturnValue(null)
    authService.authService.getStoredUser.mockReturnValue(null)

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    // Wait for loading to finish
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
    })

    expect(screen.getByText('No user')).toBeInTheDocument()
  })

  it('should restore user from localStorage on mount', async () => {
    const mockUser = { id: 1, name: 'Test User', email: 'test@example.com', role: 'CLIENT' }
    authService.authService.getStoredToken.mockReturnValue('fake-token')
    authService.authService.getStoredUser.mockReturnValue(mockUser)

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('User: Test User')).toBeInTheDocument()
    })
  })

  it('should handle login successfully', async () => {
    authService.authService.getStoredToken.mockReturnValue(null)
    authService.authService.getStoredUser.mockReturnValue(null)

    const mockUser = { id: 1, name: 'Test User', email: 'test@example.com', role: 'CLIENT' }
    authService.authService.login.mockResolvedValue()
    authService.authService.getCurrentUser.mockResolvedValue(mockUser)

    const LoginTestComponent = () => {
      const { login, user } = useAuth()

      const handleLogin = async () => {
        await login({ email: 'test@example.com', password: 'password' })
      }

      return (
        <div>
          <button onClick={handleLogin}>Login</button>
          {user && <div>User: {user.name}</div>}
        </div>
      )
    }

    render(
      <AuthProvider>
        <LoginTestComponent />
      </AuthProvider>
    )

    const loginButton = screen.getByText('Login')
    await act(async () => {
      loginButton.click()
    })

    await waitFor(() => {
      expect(screen.getByText('User: Test User')).toBeInTheDocument()
    })

    expect(authService.authService.login).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password'
    })
    expect(authService.authService.getCurrentUser).toHaveBeenCalled()
  })

  it('should handle logout successfully', async () => {
    const mockUser = { id: 1, name: 'Test User', email: 'test@example.com', role: 'CLIENT' }
    authService.authService.getStoredToken.mockReturnValue('fake-token')
    authService.authService.getStoredUser.mockReturnValue(mockUser)
    authService.authService.logout.mockResolvedValue()

    const LogoutTestComponent = () => {
      const { logout, user } = useAuth()

      return (
        <div>
          <button onClick={logout}>Logout</button>
          {user ? <div>User: {user.name}</div> : <div>No user</div>}
        </div>
      )
    }

    render(
      <AuthProvider>
        <LogoutTestComponent />
      </AuthProvider>
    )

    // Wait for user to be loaded
    await waitFor(() => {
      expect(screen.getByText('User: Test User')).toBeInTheDocument()
    })

    const logoutButton = screen.getByText('Logout')
    await act(async () => {
      logoutButton.click()
    })

    await waitFor(() => {
      expect(screen.getByText('No user')).toBeInTheDocument()
    })

    expect(authService.authService.logout).toHaveBeenCalled()
  })

  it('should throw error when useAuth is used outside AuthProvider', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => {
      render(<TestComponent />)
    }).toThrow('useAuth must be used within an AuthProvider')

    consoleSpy.mockRestore()
  })

  it('should provide isAuthenticated based on user state', async () => {
    authService.authService.getStoredToken.mockReturnValue(null)
    authService.authService.getStoredUser.mockReturnValue(null)

    const AuthTestComponent = () => {
      const { isAuthenticated } = useAuth()
      return <div>Authenticated: {isAuthenticated ? 'Yes' : 'No'}</div>
    }

    render(
      <AuthProvider>
        <AuthTestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('Authenticated: No')).toBeInTheDocument()
    })
  })
})
