/**
 * Authentication Context
 *
 * This provides global authentication state to the entire app using React Context API.
 *
 * What it does:
 * - Stores current user data in state
 * - Provides login/logout/register functions
 * - Checks for existing session on app load
 * - Makes auth state available to all components via useAuth() hook
 *
 * Usage: const { user, login, logout, isAuthenticated } = useAuth()
 */

import { createContext, useContext, useState, useEffect } from 'react'
import { authService } from '../services/authService'

// Create context with null as default value
const AuthContext = createContext(null)

/**
 * AuthProvider Component
 * Wraps the app and provides authentication state to all children
 */
export const AuthProvider = ({ children }) => {
  // State: current user data (null if not logged in)
  const [user, setUser] = useState(null)
  // State: loading flag (true while checking for existing session)
  const [loading, setLoading] = useState(true)

  // Effect: Run once on component mount to check for existing session
  useEffect(() => {
    // Check if user is already logged in (from localStorage)
    const initAuth = async () => {
      const token = authService.getStoredToken()
      const storedUser = authService.getStoredUser()

      // If both token and user exist in localStorage, restore the session
      if (token && storedUser) {
        setUser(storedUser)
      }

      // Done loading (show the app)
      setLoading(false)
    }

    initAuth()
  }, []) // Empty dependency array = run only once on mount

  /**
   * Login function
   * Calls API, stores token, fetches user data, updates state
   */
  const login = async (credentials) => {
    // Call login API (stores token in localStorage)
    await authService.login(credentials)
    // Fetch current user data
    const user = await authService.getCurrentUser()
    // Update state with user data
    setUser(user)
    return user
  }

  /**
   * Logout function
   * Calls API to invalidate session, clears state
   */
  const logout = async () => {
    // Call logout API (removes token from localStorage)
    await authService.logout()
    // Clear user from state
    setUser(null)
  }

  /**
   * Register function
   * Creates new user account (doesn't log them in automatically)
   */
  const register = async (userData) => {
    const newUser = await authService.register(userData)
    return newUser
  }

  // Value object that will be available to all consuming components
  const value = {
    user,                      // Current user object or null
    login,                     // Login function
    logout,                    // Logout function
    register,                  // Register function
    isAuthenticated: !!user,   // Boolean: true if user is logged in
    loading,                   // Boolean: true while checking session
  }

  // Provide the value to all children components
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/**
 * useAuth Hook
 * Custom hook to access auth context in any component
 *
 * Usage: const { user, login, logout } = useAuth()
 *
 * Throws error if used outside AuthProvider (prevents bugs)
 */
// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
