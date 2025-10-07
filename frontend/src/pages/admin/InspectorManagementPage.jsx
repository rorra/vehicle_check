/**
 * Inspector Management Page (ADMIN only)
 *
 * Allows administrators to manage inspectors.
 * Inspectors have both user accounts and inspector profiles.
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
import { inspectorService } from '../../services/inspectorService'
import { getApiErrorMessage } from '../../utils/validation'

const InspectorManagementPage = () => {
  const [inspectors, setInspectors] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const toast = useToast()

  // Modal state
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [isCreateMode, setIsCreateMode] = useState(false)
  const [editingInspector, setEditingInspector] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    employee_id: '',
    user_is_active: true,
    active: true,
  })
  const [formLoading, setFormLoading] = useState(false)
  const [formError, setFormError] = useState('')

  useEffect(() => {
    loadInspectors()
  }, [])

  const loadInspectors = async () => {
    setLoading(true)
    setError('')

    try {
      const data = await inspectorService.listInspectors()
      setInspectors(data.inspectors || data)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setIsCreateMode(true)
    setEditingInspector(null)
    setFormData({
      name: '',
      email: '',
      password: '',
      employee_id: '',
      user_is_active: true,
      active: true,
    })
    setFormError('')
    onOpen()
  }

  const handleEdit = (inspector) => {
    setIsCreateMode(false)
    setEditingInspector(inspector)
    setFormData({
      name: inspector.user_name,
      email: inspector.user_email,
      password: '',
      employee_id: inspector.employee_id,
      user_is_active: inspector.user_is_active,
      active: inspector.active,
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
        await inspectorService.createInspector(formData)
        toast({
          title: 'Inspector creado',
          description: 'El inspector ha sido creado correctamente.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        })
      } else {
        const updateData = { ...formData }
        if (!updateData.password) {
          delete updateData.password
        }
        await inspectorService.updateInspector(
          editingInspector.id,
          editingInspector.user_id,
          updateData
        )
        toast({
          title: 'Inspector actualizado',
          description: 'El inspector ha sido actualizado correctamente.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        })
      }
      onClose()
      loadInspectors()
    } catch (err) {
      setFormError(getApiErrorMessage(err))
    } finally {
      setFormLoading(false)
    }
  }

  const handleDelete = async (inspectorId, inspectorName) => {
    if (!window.confirm(`¿Estás seguro de eliminar al inspector "${inspectorName}"?`)) {
      return
    }

    try {
      await inspectorService.deleteInspector(inspectorId)
      toast({
        title: 'Inspector eliminado',
        description: 'El inspector ha sido eliminado correctamente.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      })
      loadInspectors()
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
          <Heading size="xl">Gestión de Inspectores</Heading>
          <HStack>
            <Button colorScheme="green" onClick={handleCreate}>
              Crear Inspector
            </Button>
            <Button colorScheme="blue" onClick={loadInspectors} isLoading={loading}>
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

        {/* Inspectors Table */}
        <Box bg="white" borderRadius="lg" shadow="md" overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>ID</Th>
                <Th>Nombre</Th>
                <Th>Email</Th>
                <Th>ID Empleado</Th>
                <Th>Estado Usuario</Th>
                <Th>Estado Inspector</Th>
                <Th>Acciones</Th>
              </Tr>
            </Thead>
            <Tbody>
              {loading ? (
                <Tr>
                  <Td colSpan={7} textAlign="center">
                    Cargando...
                  </Td>
                </Tr>
              ) : inspectors.length === 0 ? (
                <Tr>
                  <Td colSpan={7} textAlign="center">
                    No hay inspectores
                  </Td>
                </Tr>
              ) : (
                inspectors.map((inspector) => (
                  <Tr key={inspector.id}>
                    <Td>{inspector.id}</Td>
                    <Td>{inspector.user_name}</Td>
                    <Td>{inspector.user_email}</Td>
                    <Td>{inspector.employee_id}</Td>
                    <Td>
                      <Badge colorScheme={inspector.user_is_active ? 'green' : 'red'}>
                        {inspector.user_is_active ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </Td>
                    <Td>
                      <Badge colorScheme={inspector.active ? 'green' : 'red'}>
                        {inspector.active ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </Td>
                    <Td>
                      <HStack spacing={2}>
                        <Button
                          size="sm"
                          colorScheme="blue"
                          onClick={() => handleEdit(inspector)}
                        >
                          Editar
                        </Button>
                        <Button
                          size="sm"
                          colorScheme="red"
                          onClick={() => handleDelete(inspector.id, inspector.user_name)}
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
            {isCreateMode ? 'Crear Inspector' : 'Editar Inspector'}
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

                <FormControl isRequired>
                  <FormLabel>ID de Empleado</FormLabel>
                  <Input
                    name="employee_id"
                    value={formData.employee_id}
                    onChange={handleFormChange}
                    isDisabled={formLoading}
                    placeholder="INS-001"
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

export default InspectorManagementPage
