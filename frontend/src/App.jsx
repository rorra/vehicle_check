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
import ProfilePage from './pages/ProfilePage'
import VehicleManagementPage from './pages/VehicleManagementPage'
import AnnualInspectionManagementPage from './pages/AnnualInspectionManagementPage'
import AppointmentManagementPage from './pages/AppointmentManagementPage'
import ClientManagementPage from './pages/admin/ClientManagementPage'
import InspectorManagementPage from './pages/admin/InspectorManagementPage'
import AdminManagementPage from './pages/admin/AdminManagementPage'
import AvailabilitySlotManagementPage from './pages/admin/AvailabilitySlotManagementPage'
import CheckItemManagementPage from './pages/admin/CheckItemManagementPage'
import InspectionResultsPage from './pages/InspectionResultsPage'
import InspectorInspectionsPage from './pages/inspector/InspectorInspectionsPage'
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
            <Route path="/profile" element={<ProfilePage />} />
          </Route>

          {/* Vehicle routes - accessible by CLIENT and ADMIN */}
          <Route element={<ProtectedRoute allowedRoles={['CLIENT', 'ADMIN']} />}>
            <Route path="/vehicles" element={<VehicleManagementPage />} />
          </Route>

          {/* Annual Inspection routes - accessible by all authenticated users */}
          <Route element={<ProtectedRoute />}>
            <Route path="/annual-inspections" element={<AnnualInspectionManagementPage />} />
          </Route>

          {/* Appointment routes - accessible by all authenticated users */}
          <Route element={<ProtectedRoute />}>
            <Route path="/appointments" element={<AppointmentManagementPage />} />
          </Route>

          {/* Inspection Results routes - accessible by all authenticated users */}
          <Route element={<ProtectedRoute />}>
            <Route path="/results" element={<InspectionResultsPage />} />
          </Route>

          {/* Inspector-only routes */}
          <Route element={<ProtectedRoute allowedRoles={['INSPECTOR']} />}>
            <Route path="/inspector/inspections" element={<InspectorInspectionsPage />} />
          </Route>

          {/* Admin-only routes */}
          <Route element={<ProtectedRoute allowedRoles={['ADMIN']} />}>
            <Route path="/admin/clients" element={<ClientManagementPage />} />
            <Route path="/admin/inspectors" element={<InspectorManagementPage />} />
            <Route path="/admin/admins" element={<AdminManagementPage />} />
            <Route path="/admin/availability-slots" element={<AvailabilitySlotManagementPage />} />
            <Route path="/admin/check-items" element={<CheckItemManagementPage />} />
            <Route path="/admin/results" element={<InspectionResultsPage />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App
