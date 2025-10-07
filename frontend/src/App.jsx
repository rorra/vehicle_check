/**
 * Main App Component
 *
 * This is the root component of the application.
 * It sets up:
 * - Authentication context (global auth state)
 * - Routing (navigation between pages)
 * - Protected routes (requires login)
 */

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import ProtectedRoute from './components/auth/ProtectedRoute'

function App() {
  return (
    // AuthProvider wraps the entire app to provide authentication state
    // This makes user/auth info available to all components via useAuth() hook
    <AuthProvider>
      {/* Router enables navigation between pages */}
      <Router>
        <Routes>
          {/* Public routes - accessible without login */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes - requires authentication */}
          {/* ProtectedRoute checks if user is logged in before rendering children */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<DashboardPage />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App
