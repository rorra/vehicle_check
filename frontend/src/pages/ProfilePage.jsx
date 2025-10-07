/**
 * Profile Page Component
 *
 * Allows users to view and edit their own profile information.
 * Features:
 * - View profile (name, email, role)
 * - Edit name and email
 * - Change password
 */

import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Container,
  FormControl,
  FormLabel,
  Heading,
  Input,
  VStack,
  HStack,
  Text,
  Alert,
  AlertIcon,
  useToast,
  Divider,
} from '@chakra-ui/react'
import { useAuth } from '../context/AuthContext'
import { userService } from '../services/userService'
import { getApiErrorMessage } from '../utils/validation'

const ProfilePage = () => {
  const { user } = useAuth()
  const toast = useToast()

  // Profile form state
  const [profileData, setProfileData] = useState({
    name: '',
    email: '',
  })
  const [profileError, setProfileError] = useState('')
  const [profileLoading, setProfileLoading] = useState(false)

  // Password form state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
  })
  const [passwordError, setPasswordError] = useState('')
  const [passwordLoading, setPasswordLoading] = useState(false)

  // Load user profile on mount
  useEffect(() => {
    if (user) {
      setProfileData({
        name: user.name || '',
        email: user.email || '',
      })
    }
  }, [user])

  /**
   * Handle profile form input changes
   */
  const handleProfileChange = (e) => {
    setProfileData({
      ...profileData,
      [e.target.name]: e.target.value,
    })
    if (profileError) setProfileError('')
  }

  /**
   * Handle password form input changes
   */
  const handlePasswordChange = (e) => {
    setPasswordData({
      ...passwordData,
      [e.target.name]: e.target.value,
    })
    if (passwordError) setPasswordError('')
  }

  /**
   * Handle profile update submission
   */
  const handleProfileSubmit = async (e) => {
    e.preventDefault()
    setProfileError('')
    setProfileLoading(true)

    try {
      await userService.updateProfile(profileData)
      toast({
        title: 'Perfil actualizado',
        description: 'Tu información ha sido actualizada correctamente.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      })
    } catch (err) {
      setProfileError(getApiErrorMessage(err))
    } finally {
      setProfileLoading(false)
    }
  }

  /**
   * Handle password change submission
   */
  const handlePasswordSubmit = async (e) => {
    e.preventDefault()
    setPasswordError('')
    setPasswordLoading(true)

    try {
      await userService.changePassword(passwordData)
      toast({
        title: 'Contraseña cambiada',
        description: 'Tu contraseña ha sido actualizada correctamente.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      })
      // Clear password fields
      setPasswordData({
        current_password: '',
        new_password: '',
      })
    } catch (err) {
      setPasswordError(getApiErrorMessage(err))
    } finally {
      setPasswordLoading(false)
    }
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

  return (
    <Container maxW="4xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <Heading size="xl">Mi Perfil</Heading>

        {/* Profile Information */}
        <Box bg="white" borderRadius="lg" shadow="md" p={6}>
          <Heading size="md" mb={4}>
            Información del Perfil
          </Heading>

          {/* Role (read-only) */}
          <Text mb={4} color="gray.600">
            <strong>Rol:</strong> {getRoleLabel(user?.role)}
          </Text>

          {/* Error Alert */}
          {profileError && (
            <Alert status="error" borderRadius="md" mb={4}>
              <AlertIcon />
              {profileError}
            </Alert>
          )}

          {/* Profile Form */}
          <Box as="form" onSubmit={handleProfileSubmit}>
            <VStack spacing={4}>
              {/* Name Field */}
              <FormControl isRequired>
                <FormLabel>Nombre</FormLabel>
                <Input
                  type="text"
                  name="name"
                  value={profileData.name}
                  onChange={handleProfileChange}
                  isDisabled={profileLoading}
                />
              </FormControl>

              {/* Email Field */}
              <FormControl isRequired>
                <FormLabel>Correo Electrónico</FormLabel>
                <Input
                  type="email"
                  name="email"
                  value={profileData.email}
                  onChange={handleProfileChange}
                  isDisabled={profileLoading}
                />
              </FormControl>

              {/* Submit Button */}
              <HStack width="full" justify="flex-end">
                <Button
                  type="submit"
                  colorScheme="blue"
                  isLoading={profileLoading}
                  loadingText="Guardando..."
                >
                  Guardar Cambios
                </Button>
              </HStack>
            </VStack>
          </Box>
        </Box>

        <Divider />

        {/* Change Password */}
        <Box bg="white" borderRadius="lg" shadow="md" p={6}>
          <Heading size="md" mb={4}>
            Cambiar Contraseña
          </Heading>

          {/* Error Alert */}
          {passwordError && (
            <Alert status="error" borderRadius="md" mb={4}>
              <AlertIcon />
              {passwordError}
            </Alert>
          )}

          {/* Password Form */}
          <Box as="form" onSubmit={handlePasswordSubmit}>
            <VStack spacing={4}>
              {/* Current Password */}
              <FormControl isRequired>
                <FormLabel>Contraseña Actual</FormLabel>
                <Input
                  type="password"
                  name="current_password"
                  value={passwordData.current_password}
                  onChange={handlePasswordChange}
                  isDisabled={passwordLoading}
                />
              </FormControl>

              {/* New Password */}
              <FormControl isRequired>
                <FormLabel>Nueva Contraseña</FormLabel>
                <Input
                  type="password"
                  name="new_password"
                  value={passwordData.new_password}
                  onChange={handlePasswordChange}
                  isDisabled={passwordLoading}
                />
              </FormControl>

              {/* Submit Button */}
              <HStack width="full" justify="flex-end">
                <Button
                  type="submit"
                  colorScheme="blue"
                  isLoading={passwordLoading}
                  loadingText="Cambiando..."
                >
                  Cambiar Contraseña
                </Button>
              </HStack>
            </VStack>
          </Box>
        </Box>
      </VStack>
    </Container>
  )
}

export default ProfilePage
