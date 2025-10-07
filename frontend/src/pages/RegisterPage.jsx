/**
 * Register Page Component
 *
 * Allows new users to create an account.
 * After successful registration, redirects to login page.
 *
 * Features:
 * - Multi-field form (name, email, password, role)
 * - Form state management with single state object
 * - Error handling (displays API errors in Spanish)
 * - Loading state
 * - Role selection (CLIENT, INSPECTOR, ADMIN)
 */

import { useState } from 'react'
import { useNavigate, Link as RouterLink } from 'react-router-dom'
import {
  Box,
  Button,
  Container,
  FormControl,
  FormLabel,
  Heading,
  Input,
  VStack,
  Text,
  Alert,
  AlertIcon,
  Link,
  Select,
  useToast,
} from '@chakra-ui/react'
import { useAuth } from '../context/AuthContext'
import { getApiErrorMessage } from '../utils/validation'

const RegisterPage = () => {
  // Form state - single object for all fields
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'CLIENT', // Default role
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Hooks
  const { register } = useAuth()
  const navigate = useNavigate()
  const toast = useToast() // Chakra UI toast for success messages

  /**
   * Handle input changes
   * Updates formData state for any form field
   * Uses [e.target.name] to dynamically update the right field
   */
  const handleChange = (e) => {
    setFormData({
      ...formData, // Keep all existing values
      [e.target.name]: e.target.value, // Update only the changed field
    })
    // Clear error when user types
    if (error) setError('')
  }

  /**
   * Handle form submission
   * Calls register API, shows success message, redirects to login
   */
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Call register function from AuthContext
      await register(formData)
      // Show success message using Chakra UI toast
      toast({
        title: 'Registro exitoso',
        description: 'Por favor inicia sesión.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      })
      // Redirect to login page
      navigate('/login')
    } catch (err) {
      // Display error from API
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container maxW="md" py={12}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <Box textAlign="center">
          <Heading size="xl" mb={2}>
            Registro
          </Heading>
          <Text color="gray.600">Crea tu cuenta en el sistema</Text>
        </Box>

        {/* Error Alert */}
        {error && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            {error}
          </Alert>
        )}

        {/* Registration Form */}
        <Box as="form" onSubmit={handleSubmit}>
          <VStack spacing={4}>
            {/* Name Field */}
            <FormControl isRequired>
              <FormLabel>Nombre Completo</FormLabel>
              <Input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                isDisabled={loading}
              />
            </FormControl>

            {/* Email Field */}
            <FormControl isRequired>
              <FormLabel>Correo Electrónico</FormLabel>
              <Input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                isDisabled={loading}
              />
            </FormControl>

            {/* Password Field */}
            <FormControl isRequired>
              <FormLabel>Contraseña</FormLabel>
              <Input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                isDisabled={loading}
              />
            </FormControl>

            {/* Role Selection */}
            <FormControl isRequired>
              <FormLabel>Tipo de Usuario</FormLabel>
              <Select
                name="role"
                value={formData.role}
                onChange={handleChange}
                isDisabled={loading}
              >
                <option value="CLIENT">Cliente</option>
                <option value="INSPECTOR">Inspector</option>
                <option value="ADMIN">Administrador</option>
              </Select>
            </FormControl>

            {/* Submit Button */}
            <Button
              type="submit"
              colorScheme="blue"
              width="full"
              isLoading={loading}
              loadingText="Registrando..."
            >
              Registrarse
            </Button>
          </VStack>
        </Box>

        {/* Login Link */}
        <Text textAlign="center" color="gray.600">
          ¿Ya tienes cuenta?{' '}
          <Link as={RouterLink} to="/login" color="blue.500" fontWeight="medium">
            Inicia sesión aquí
          </Link>
        </Text>
      </VStack>
    </Container>
  )
}

export default RegisterPage
