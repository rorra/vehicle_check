/**
 * Navbar Component
 *
 * Navigation bar shown to authenticated users.
 * Shows different links based on user role.
 */

import { Link as RouterLink, useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Flex,
  Button,
  HStack,
  Text,
  Badge,
} from '@chakra-ui/react'
import { useAuth } from '../../context/AuthContext'

const Navbar = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  /**
   * Handle logout
   */
  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  /**
   * Get role label in Spanish
   */
  const getRoleLabel = (role) => {
    const labels = {
      CLIENT: 'Cliente',
      INSPECTOR: 'Inspector',
      ADMIN: 'Administrador',
    }
    return labels[role] || role
  }

  /**
   * Get role color for badge
   */
  const getRoleColor = (role) => {
    const colors = {
      CLIENT: 'blue',
      INSPECTOR: 'green',
      ADMIN: 'purple',
    }
    return colors[role] || 'gray'
  }

  if (!user) return null

  return (
    <Box bg="blue.600" color="white" py={3} shadow="md">
      <Container maxW="7xl">
        <Flex justify="space-between" align="center">
          {/* Left: Navigation Links */}
          <HStack spacing={4}>
            <Button
              as={RouterLink}
              to="/"
              variant="ghost"
              colorScheme="whiteAlpha"
              size="sm"
            >
              Dashboard
            </Button>

            <Button
              as={RouterLink}
              to="/profile"
              variant="ghost"
              colorScheme="whiteAlpha"
              size="sm"
            >
              Mi Perfil
            </Button>
          </HStack>

          {/* Right: User Info and Logout */}
          <HStack spacing={4}>
            <HStack spacing={2}>
              <Text fontSize="sm">{user.name}</Text>
              <Badge colorScheme={getRoleColor(user.role)}>
                {getRoleLabel(user.role)}
              </Badge>
            </HStack>
            <Button
              onClick={handleLogout}
              colorScheme="red"
              size="sm"
            >
              Salir
            </Button>
          </HStack>
        </Flex>
      </Container>
    </Box>
  )
}

export default Navbar
