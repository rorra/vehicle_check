/**
 * ProtectedRoute Component
 *
 * This component wraps routes that require authentication.
 * It checks if:
 * 1. User is logged in (has valid session)
 * 2. User has the required role (if specified)
 *
 * If not authenticated → redirect to /login
 * If wrong role → show "Access Denied" message
 * If all checks pass → render the child route (via <Outlet />)
 *
 * Usage:
 * <Route element={<ProtectedRoute />}>
 *   <Route path="/dashboard" element={<Dashboard />} />
 * </Route>
 *
 * With role check:
 * <Route element={<ProtectedRoute allowedRoles={['ADMIN']} />}>
 *   <Route path="/admin" element={<AdminPanel />} />
 * </Route>
 */

import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Box, Container, Heading, Text, Spinner, VStack } from '@chakra-ui/react'

const ProtectedRoute = ({ allowedRoles }) => {
  // Get authentication state from context
  const { user, loading } = useAuth()

  // While checking for existing session, show loading spinner
  if (loading) {
    return (
      <Box minH="100vh" display="flex" alignItems="center" justifyContent="center" bg="gray.50">
        <VStack spacing={4}>
          {/* Chakra UI Spinner component */}
          <Spinner size="xl" color="blue.500" thickness="4px" />
          <Text color="gray.600">Cargando...</Text>
        </VStack>
      </Box>
    )
  }

  // If no user is logged in, redirect to login page
  // 'replace' prevents going back to this page with browser back button
  if (!user) {
    return <Navigate to="/login" replace />
  }

  // If allowedRoles is specified, check if user has required role
  // Example: allowedRoles = ['ADMIN', 'INSPECTOR']
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // User is logged in but doesn't have permission
    return (
      <Box minH="100vh" display="flex" alignItems="center" justifyContent="center" bg="gray.50">
        <Container maxW="md" textAlign="center">
          <Heading size="2xl" mb={4}>
            Acceso Denegado
          </Heading>
          <Text color="gray.600">No tienes permisos para acceder a esta página.</Text>
        </Container>
      </Box>
    )
  }

  // All checks passed - render the protected route
  // <Outlet /> renders the child route component
  return <Outlet />
}

export default ProtectedRoute
