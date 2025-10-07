/**
 * Dashboard Page Component
 *
 * Main page after login. Shows different content based on user role:
 * - CLIENT: Can manage vehicles, book appointments, view results
 * - INSPECTOR: Can view assigned appointments and complete inspections
 * - ADMIN: Can manage users, inspectors, vehicles, and appointments
 *
 * Features:
 * - Role-based content display
 * - User greeting with name and role
 * - Logout functionality
 */

import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Button,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  List,
  ListItem,
  ListIcon,
} from '@chakra-ui/react'
import { CheckCircleIcon } from '@chakra-ui/icons'

const DashboardPage = () => {
  // Get user and logout function from auth context
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  /**
   * Handle logout button click
   * Calls logout API and redirects to login page
   */
  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  /**
   * Convert role enum to Spanish label
   * @param {string} role - User role (CLIENT, INSPECTOR, ADMIN)
   * @returns {string} Spanish label
   */
  const getRoleLabel = (role) => {
    const labels = {
      CLIENT: 'Cliente',
      INSPECTOR: 'Inspector',
      ADMIN: 'Administrador',
    }
    return labels[role] || role
  }

  return (
    <Box minH="100vh" bg="gray.50">
      <Container maxW="7xl" py={8}>
        {/* Header with user greeting and logout button */}
        <HStack justify="space-between" mb={8} flexWrap="wrap" gap={4}>
          <Box>
            <Heading size="xl" mb={1}>
              Dashboard
            </Heading>
            <Text fontSize="sm" color="gray.600">
              Bienvenido, {user?.name} ({getRoleLabel(user?.role)})
            </Text>
          </Box>
          <Button colorScheme="red" onClick={handleLogout}>
            Cerrar Sesión
          </Button>
        </HStack>

        {/* Main content card */}
        <Box bg="white" borderRadius="lg" shadow="md" p={6}>
          <Heading size="lg" mb={4}>
            Sistema de Inspección Vehicular
          </Heading>

          {/* CLIENT role features */}
          {user?.role === 'CLIENT' && (
            <VStack align="stretch" mt={6} spacing={3}>
              <Heading size="md" mb={2}>
                Funcionalidades disponibles:
              </Heading>
              <List spacing={2}>
                <ListItem>
                  <ListIcon as={CheckCircleIcon} color="green.500" />
                  Registrar vehículos
                </ListItem>
                <ListItem>
                  <ListIcon as={CheckCircleIcon} color="green.500" />
                  Solicitar turnos para inspección
                </ListItem>
                <ListItem>
                  <ListIcon as={CheckCircleIcon} color="green.500" />
                  Ver resultados de inspecciones
                </ListItem>
              </List>
            </VStack>
          )}

          {/* INSPECTOR role features */}
          {user?.role === 'INSPECTOR' && (
            <VStack align="stretch" mt={6} spacing={3}>
              <Heading size="md" mb={2}>
                Funcionalidades disponibles:
              </Heading>
              <List spacing={2}>
                <ListItem>
                  <ListIcon as={CheckCircleIcon} color="green.500" />
                  Ver turnos asignados
                </ListItem>
                <ListItem>
                  <ListIcon as={CheckCircleIcon} color="green.500" />
                  Completar inspecciones
                </ListItem>
                <ListItem>
                  <ListIcon as={CheckCircleIcon} color="green.500" />
                  Registrar resultados con puntajes
                </ListItem>
              </List>
            </VStack>
          )}

          {/* ADMIN role features */}
          {user?.role === 'ADMIN' && (
            <VStack align="stretch" mt={6} spacing={3}>
              <Heading size="md" mb={2}>
                Funcionalidades disponibles:
              </Heading>
              <List spacing={2}>
                <ListItem>
                  <ListIcon as={CheckCircleIcon} color="green.500" />
                  Gestionar usuarios
                </ListItem>
                <ListItem>
                  <ListIcon as={CheckCircleIcon} color="green.500" />
                  Gestionar inspectores
                </ListItem>
                <ListItem>
                  <ListIcon as={CheckCircleIcon} color="green.500" />
                  Gestionar vehículos
                </ListItem>
                <ListItem>
                  <ListIcon as={CheckCircleIcon} color="green.500" />
                  Asignar turnos
                </ListItem>
                <ListItem>
                  <ListIcon as={CheckCircleIcon} color="green.500" />
                  Ver todos los resultados
                </ListItem>
              </List>
            </VStack>
          )}
        </Box>
      </Container>
    </Box>
  )
}

export default DashboardPage
