/**
 * Client Management Page (ADMIN only)
 *
 * Allows administrators to manage clients (users with CLIENT role).
 */

import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Container,
  Heading,
  VStack,
  HStack,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Alert,
  AlertIcon,
  useToast,
  Badge,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  FormControl,
  FormLabel,
  Input,
  useDisclosure,
} from '@chakra-ui/react'
import { clientService } from '../../services/clientService'
import { getApiErrorMessage } from '../../utils/validation'

const ClientManagementPage = () => {
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const toast = useToast()

  // Modal state
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [isCreateMode, setIsCreateMode] = useState(false)
  const [editingClient, setEditingClient] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    is_active: true,
  })
  const [formLoading, setFormLoading] = useState(false)
  const [formError, setFormError] = useState('')

  useEffect(() => {
    loadClients()
  }, [])

  const loadClients = async () => {
    setLoading(true)
    setError('')

    try {
      const data = await clientService.listClients()
      setClients(data.users || data)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setIsCreateMode(true)
    setEditingClient(null)
    setFormData({
      name: '',
      email: '',
      password: '',
      is_active: true,
    })
    setFormError('')
    onOpen()
  }

  const handleEdit = (client) => {
    setIsCreateMode(false)
    setEditingClient(client)
    setFormData({
      name: client.name,
      email: client.email,
      password: '',
      is_active: client.is_active,
    })
    setFormError('')
    onOpen()
  }

  const handleFormChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    })
    if (formError) setFormError('')
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    setFormError('')
    setFormLoading(true)

    try {
      if (isCreateMode) {
        await clientService.createClient(formData)
        toast({
          title: 'Cliente creado',
          description: 'El cliente ha sido creado correctamente.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        })
      } else {
        const updateData = { ...formData }
        if (!updateData.password) {
          delete updateData.password
        }
        await clientService.updateClient(editingClient.id, updateData)
        toast({
          title: 'Cliente actualizado',
          description: 'El cliente ha sido actualizado correctamente.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        })
      }
      onClose()
      loadClients()
    } catch (err) {
      setFormError(getApiErrorMessage(err))
    } finally {
      setFormLoading(false)
    }
  }

  const handleDelete = async (clientId, clientName) => {
    if (!window.confirm(`¿Estás seguro de eliminar al cliente "${clientName}"?`)) {
      return
    }

    try {
      await clientService.deleteClient(clientId)
      toast({
        title: 'Cliente eliminado',
        description: 'El cliente ha sido eliminado correctamente.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      })
      loadClients()
    } catch (err) {
      toast({
        title: 'Error',
        description: getApiErrorMessage(err),
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    }
  }

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between">
          <Heading size="xl">Gestión de Clientes</Heading>
          <HStack>
            <Button colorScheme="green" onClick={handleCreate}>
              Crear Cliente
            </Button>
            <Button colorScheme="blue" onClick={loadClients} isLoading={loading}>
              Actualizar
            </Button>
          </HStack>
        </HStack>

        {/* Error Alert */}
        {error && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            {error}
          </Alert>
        )}

        {/* Clients Table */}
        <Box bg="white" borderRadius="lg" shadow="md" overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>ID</Th>
                <Th>Nombre</Th>
                <Th>Email</Th>
                <Th>Estado</Th>
                <Th>Acciones</Th>
              </Tr>
            </Thead>
            <Tbody>
              {loading ? (
                <Tr>
                  <Td colSpan={5} textAlign="center">
                    Cargando...
                  </Td>
                </Tr>
              ) : clients.length === 0 ? (
                <Tr>
                  <Td colSpan={5} textAlign="center">
                    No hay clientes
                  </Td>
                </Tr>
              ) : (
                clients.map((client) => (
                  <Tr key={client.id}>
                    <Td>{client.id}</Td>
                    <Td>{client.name}</Td>
                    <Td>{client.email}</Td>
                    <Td>
                      <Badge colorScheme={client.is_active ? 'green' : 'red'}>
                        {client.is_active ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </Td>
                    <Td>
                      <HStack spacing={2}>
                        <Button
                          size="sm"
                          colorScheme="blue"
                          onClick={() => handleEdit(client)}
                        >
                          Editar
                        </Button>
                        <Button
                          size="sm"
                          colorScheme="red"
                          onClick={() => handleDelete(client.id, client.name)}
                        >
                          Eliminar
                        </Button>
                      </HStack>
                    </Td>
                  </Tr>
                ))
              )}
            </Tbody>
          </Table>
        </Box>
      </VStack>

      {/* Create/Edit Modal */}
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {isCreateMode ? 'Crear Cliente' : 'Editar Cliente'}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {formError && (
              <Alert status="error" borderRadius="md" mb={4}>
                <AlertIcon />
                {formError}
              </Alert>
            )}

            <Box as="form" onSubmit={handleFormSubmit}>
              <VStack spacing={4}>
                <FormControl isRequired>
                  <FormLabel>Nombre</FormLabel>
                  <Input
                    name="name"
                    value={formData.name}
                    onChange={handleFormChange}
                    isDisabled={formLoading}
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Email</FormLabel>
                  <Input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleFormChange}
                    isDisabled={formLoading}
                  />
                </FormControl>

                <FormControl isRequired={isCreateMode}>
                  <FormLabel>
                    {isCreateMode ? 'Contraseña' : 'Contraseña (dejar vacío para no cambiar)'}
                  </FormLabel>
                  <Input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleFormChange}
                    isDisabled={formLoading}
                    placeholder={isCreateMode ? '' : 'Dejar vacío para mantener la actual'}
                  />
                </FormControl>
              </VStack>
            </Box>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancelar
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleFormSubmit}
              isLoading={formLoading}
            >
              {isCreateMode ? 'Crear' : 'Guardar'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Container>
  )
}

export default ClientManagementPage
