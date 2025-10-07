/**
 * Admin Management Page (ADMIN only)
 *
 * Allows administrators to manage other admins (users with ADMIN role).
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
import { adminService } from '../../services/adminService'
import { getApiErrorMessage } from '../../utils/validation'

const AdminManagementPage = () => {
  const [admins, setAdmins] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const toast = useToast()

  // Modal state
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [isCreateMode, setIsCreateMode] = useState(false)
  const [editingAdmin, setEditingAdmin] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    is_active: true,
  })
  const [formLoading, setFormLoading] = useState(false)
  const [formError, setFormError] = useState('')

  useEffect(() => {
    loadAdmins()
  }, [])

  const loadAdmins = async () => {
    setLoading(true)
    setError('')

    try {
      const data = await adminService.listAdmins()
      setAdmins(data.users || data)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setIsCreateMode(true)
    setEditingAdmin(null)
    setFormData({
      name: '',
      email: '',
      password: '',
      is_active: true,
    })
    setFormError('')
    onOpen()
  }

  const handleEdit = (admin) => {
    setIsCreateMode(false)
    setEditingAdmin(admin)
    setFormData({
      name: admin.name,
      email: admin.email,
      password: '',
      is_active: admin.is_active,
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
        await adminService.createAdmin(formData)
        toast({
          title: 'Administrador creado',
          description: 'El administrador ha sido creado correctamente.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        })
      } else {
        const updateData = { ...formData }
        if (!updateData.password) {
          delete updateData.password
        }
        await adminService.updateAdmin(editingAdmin.id, updateData)
        toast({
          title: 'Administrador actualizado',
          description: 'El administrador ha sido actualizado correctamente.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        })
      }
      onClose()
      loadAdmins()
    } catch (err) {
      setFormError(getApiErrorMessage(err))
    } finally {
      setFormLoading(false)
    }
  }

  const handleDelete = async (adminId, adminName) => {
    if (!window.confirm(`¿Estás seguro de eliminar al administrador "${adminName}"?`)) {
      return
    }

    try {
      await adminService.deleteAdmin(adminId)
      toast({
        title: 'Administrador eliminado',
        description: 'El administrador ha sido eliminado correctamente.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      })
      loadAdmins()
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
          <Heading size="xl">Gestión de Administradores</Heading>
          <HStack>
            <Button colorScheme="green" onClick={handleCreate}>
              Crear Administrador
            </Button>
            <Button colorScheme="blue" onClick={loadAdmins} isLoading={loading}>
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

        {/* Admins Table */}
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
              ) : admins.length === 0 ? (
                <Tr>
                  <Td colSpan={5} textAlign="center">
                    No hay administradores
                  </Td>
                </Tr>
              ) : (
                admins.map((admin) => (
                  <Tr key={admin.id}>
                    <Td>{admin.id}</Td>
                    <Td>{admin.name}</Td>
                    <Td>{admin.email}</Td>
                    <Td>
                      <Badge colorScheme={admin.is_active ? 'green' : 'red'}>
                        {admin.is_active ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </Td>
                    <Td>
                      <HStack spacing={2}>
                        <Button
                          size="sm"
                          colorScheme="blue"
                          onClick={() => handleEdit(admin)}
                        >
                          Editar
                        </Button>
                        <Button
                          size="sm"
                          colorScheme="red"
                          onClick={() => handleDelete(admin.id, admin.name)}
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
            {isCreateMode ? 'Crear Administrador' : 'Editar Administrador'}
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

export default AdminManagementPage
