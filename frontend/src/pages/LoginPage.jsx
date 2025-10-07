/**
 * Login Page Component
 *
 * Allows users to log in with email and password.
 * On successful login, redirects to dashboard.
 *
 * Features:
 * - Form state management (email, password)
 * - Error handling (displays API errors in Spanish)
 * - Loading state (disables form while submitting)
 * - Link to registration page
 * - Uses Chakra UI components for styling
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
} from '@chakra-ui/react'
import { useAuth } from '../context/AuthContext'
import { getApiErrorMessage } from '../utils/validation'

const LoginPage = () => {
  // Form state
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('') // Error message to display
  const [loading, setLoading] = useState(false) // Disable form while submitting

  // Hooks
  const { login } = useAuth() // Get login function from auth context
  const navigate = useNavigate() // For programmatic navigation

  /**
   * Handle form submission
   * Prevents default form behavior, calls login API, handles errors
   */
  const handleSubmit = async (e) => {
    e.preventDefault() // Prevent page reload on form submit
    setError('') // Clear previous errors
    setLoading(true) // Show loading state

    try {
      // Call login function (from AuthContext)
      // This will call the API, store the token, and update auth state
      await login({ email, password })
      // On success, redirect to dashboard
      navigate('/')
    } catch (err) {
      // On error, extract and display error message from API response
      setError(getApiErrorMessage(err))
    } finally {
      // Always stop loading state (whether success or error)
      setLoading(false)
    }
  }

  return (
    <Container maxW="md" py={12}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <Box textAlign="center">
          <Heading size="xl" mb={2}>
            Iniciar Sesión
          </Heading>
          <Text color="gray.600">Sistema de Inspección Vehicular</Text>
        </Box>

        {/* Error Alert */}
        {error && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            {error}
          </Alert>
        )}

        {/* Login Form */}
        <Box as="form" onSubmit={handleSubmit}>
          <VStack spacing={4}>
            {/* Email Field */}
            <FormControl isRequired>
              <FormLabel>Correo Electrónico</FormLabel>
              <Input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  if (error) setError('') // Clear error when user types
                }}
                isDisabled={loading}
              />
            </FormControl>

            {/* Password Field */}
            <FormControl isRequired>
              <FormLabel>Contraseña</FormLabel>
              <Input
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value)
                  if (error) setError('') // Clear error when user types
                }}
                isDisabled={loading}
              />
            </FormControl>

            {/* Submit Button */}
            <Button
              type="submit"
              colorScheme="blue"
              width="full"
              isLoading={loading}
              loadingText="Iniciando sesión..."
            >
              Iniciar Sesión
            </Button>
          </VStack>
        </Box>

        {/* Register Link */}
        <Text textAlign="center" color="gray.600">
          ¿No tienes cuenta?{' '}
          <Link as={RouterLink} to="/register" color="blue.500" fontWeight="medium">
            Regístrate aquí
          </Link>
        </Text>
      </VStack>
    </Container>
  )
}

export default LoginPage
