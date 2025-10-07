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
 * - Clickable cards for navigation
 */

import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  SimpleGrid,
  Card,
  CardBody,
  Icon,
} from '@chakra-ui/react'
import {
  SettingsIcon,
  CalendarIcon,
  CheckCircleIcon,
  ViewIcon,
  StarIcon,
  EditIcon,
  TimeIcon,
} from '@chakra-ui/icons'

const DashboardPage = () => {
  const { user } = useAuth()
  const navigate = useNavigate()

  /**
   * Convert role enum to Spanish label
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
   * Define menu cards for each role
   */
  const getMenuItems = () => {
    if (user?.role === 'CLIENT') {
      return [
        {
          title: 'Mis Vehículos',
          description: 'Registrar y gestionar mis vehículos',
          icon: SettingsIcon,
          color: 'blue',
          path: '/vehicles',
        },
        {
          title: 'Inspecciones Anuales',
          description: 'Ver mis inspecciones anuales',
          icon: CheckCircleIcon,
          color: 'teal',
          path: '/annual-inspections',
        },
        {
          title: 'Mis Turnos',
          description: 'Solicitar y ver turnos de inspección',
          icon: CalendarIcon,
          color: 'green',
          path: '/appointments',
        },
        {
          title: 'Resultados',
          description: 'Ver resultados de inspecciones',
          icon: ViewIcon,
          color: 'purple',
          path: '/results',
        },
      ]
    }

    if (user?.role === 'INSPECTOR') {
      return [
        {
          title: 'Inspecciones Anuales',
          description: 'Ver inspecciones anuales',
          icon: CheckCircleIcon,
          color: 'teal',
          path: '/annual-inspections',
        },
        {
          title: 'Turnos Asignados',
          description: 'Ver mis turnos asignados',
          icon: CalendarIcon,
          color: 'green',
          path: '/appointments',
        },
        {
          title: 'Realizar Inspección',
          description: 'Completar inspecciones y registrar resultados',
          icon: CheckCircleIcon,
          color: 'orange',
          path: '/inspector/inspections',
        },
      ]
    }

    if (user?.role === 'ADMIN') {
      return [
        {
          title: 'Gestión de Clientes',
          description: 'Crear, editar y eliminar clientes',
          icon: SettingsIcon,
          color: 'blue',
          path: '/admin/clients',
        },
        {
          title: 'Gestión de Inspectores',
          description: 'Administrar inspectores del sistema',
          icon: StarIcon,
          color: 'teal',
          path: '/admin/inspectors',
        },
        {
          title: 'Gestión de Administradores',
          description: 'Administrar otros administradores',
          icon: ViewIcon,
          color: 'purple',
          path: '/admin/admins',
        },
        {
          title: 'Gestión de Vehículos',
          description: 'Ver y administrar todos los vehículos',
          icon: EditIcon,
          color: 'cyan',
          path: '/vehicles',
        },
        {
          title: 'Inspecciones Anuales',
          description: 'Administrar inspecciones anuales',
          icon: CheckCircleIcon,
          color: 'pink',
          path: '/annual-inspections',
        },
        {
          title: 'Gestión de Turnos',
          description: 'Asignar y administrar turnos',
          icon: CalendarIcon,
          color: 'green',
          path: '/appointments',
        },
        {
          title: 'Gestión de Horarios',
          description: 'Administrar horarios disponibles',
          icon: TimeIcon,
          color: 'yellow',
          path: '/admin/availability-slots',
        },
        {
          title: 'Resultados',
          description: 'Ver todos los resultados de inspecciones',
          icon: CheckCircleIcon,
          color: 'orange',
          path: '/admin/results',
        },
      ]
    }

    return []
  }

  const menuItems = getMenuItems()

  return (
    <Box minH="100vh" bg="gray.50">
      <Container maxW="7xl" py={8}>
        {/* Header with user greeting */}
        <VStack align="stretch" spacing={6}>
          <Box>
            <Heading size="xl" mb={1}>
              Dashboard
            </Heading>
            <Text fontSize="lg" color="gray.600">
              Bienvenido, {user?.name} ({getRoleLabel(user?.role)})
            </Text>
          </Box>

          {/* Menu Cards */}
          <Box>
            <Heading size="md" mb={4}>
              Menú Principal
            </Heading>
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
              {menuItems.map((item) => (
                <Card
                  key={item.path}
                  cursor="pointer"
                  _hover={{
                    transform: 'translateY(-4px)',
                    shadow: 'xl',
                  }}
                  transition="all 0.2s"
                  onClick={() => navigate(item.path)}
                >
                  <CardBody>
                    <VStack align="start" spacing={3}>
                      <Box
                        p={3}
                        bg={`${item.color}.50`}
                        borderRadius="lg"
                      >
                        <Icon
                          as={item.icon}
                          boxSize={8}
                          color={`${item.color}.500`}
                        />
                      </Box>
                      <Box>
                        <Heading size="md" mb={1}>
                          {item.title}
                        </Heading>
                        <Text fontSize="sm" color="gray.600">
                          {item.description}
                        </Text>
                      </Box>
                    </VStack>
                  </CardBody>
                </Card>
              ))}
            </SimpleGrid>
          </Box>
        </VStack>
      </Container>
    </Box>
  )
}

export default DashboardPage
