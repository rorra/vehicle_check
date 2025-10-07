/**
 * Vehicle Management Page
 *
 * Allows users to manage their vehicles.
 * - CLIENT: Can only see and manage their own vehicles
 * - ADMIN: Can see and manage all vehicles, with option to specify owner
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
  Checkbox,
  useDisclosure,
  Text,
} from '@chakra-ui/react'
import { vehicleService } from '../services/vehicleService'
import { clientService } from '../services/clientService'
import { getApiErrorMessage } from '../utils/validation'
import { useAuth } from '../context/AuthContext'

const VehicleManagementPage = () => {
  const { user } = useAuth()
  const [vehicles, setVehicles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [includeInactive, setIncludeInactive] = useState(false)
  const toast = useToast()

  // Modal state
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [isCreateMode, setIsCreateMode] = useState(false)
  const [editingVehicle, setEditingVehicle] = useState(null)
  const [formData, setFormData] = useState({
    plate_number: '',
    make: '',
    model: '',
    year: '',
    owner_id: '',
  })
  const [formLoading, setFormLoading] = useState(false)
  const [formError, setFormError] = useState('')

  // Client selector state (for admin)
  const [clients, setClients] = useState([])
  const [clientSearch, setClientSearch] = useState('')
  const [selectedClient, setSelectedClient] = useState(null)
  const [loadingClients, setLoadingClients] = useState(false)

  const isAdmin = user?.role === 'ADMIN'

  useEffect(() => {
    // Only load vehicles once user is available
    if (user) {
      loadVehicles()
    }
  }, [user, includeInactive])

  const loadVehicles = async () => {
    setLoading(true)
    setError('')

    try {
      // Check user role at call time, not at component mount
      if (user?.role === 'ADMIN') {
        // Admin gets vehicles with owner details
        const data = await vehicleService.listVehiclesWithOwners()
        setVehicles(data)
      } else {
        // Client gets their own vehicles
        const params = includeInactive ? { include_inactive: true } : {}
        const data = await vehicleService.listVehicles(params)
        setVehicles(data.vehicles || data)
      }
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const loadClients = async () => {
    if (!isAdmin) return

    setLoadingClients(true)
    try {
      const data = await clientService.listClients()
      setClients(data.users || data)
    } catch (err) {
      console.error('Failed to load clients:', err)
    } finally {
      setLoadingClients(false)
    }
  }

  const handleCreate = () => {
    setIsCreateMode(true)
    setEditingVehicle(null)
    setFormData({
      plate_number: '',
      make: '',
      model: '',
      year: '',
      owner_id: '',
    })
    setFormError('')
    setClientSearch('')
    setSelectedClient(null)
    onOpen()

    // Load clients for admin
    if (isAdmin) {
      loadClients()
    }
  }

  const handleEdit = (vehicle) => {
    setIsCreateMode(false)
    setEditingVehicle(vehicle)
    setFormData({
      plate_number: vehicle.plate_number,
      make: vehicle.make || '',
      model: vehicle.model || '',
      year: vehicle.year || '',
      owner_id: vehicle.owner_id || '',
    })
    setFormError('')
    onOpen()
  }

  const handleFormChange = (e) => {
    const { name, value } = e.target
    setFormData({
      ...formData,
      [name]: value,
    })
    if (formError) setFormError('')
  }

  const handleClientSearch = (e) => {
    setClientSearch(e.target.value)
  }

  const handleClientSelect = (client) => {
    setSelectedClient(client)
    setFormData({
      ...formData,
      owner_id: client.id,
    })
    setClientSearch('')
  }

  const filteredClients = clients.filter((client) => {
    if (!clientSearch) return true
    const searchLower = clientSearch.toLowerCase()
    return (
      client.name.toLowerCase().includes(searchLower) ||
      client.email.toLowerCase().includes(searchLower)
    )
  })

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    setFormError('')
    setFormLoading(true)

    try {
      // Prepare data - remove empty values
      const submitData = {
        plate_number: formData.plate_number,
      }

      if (formData.make) submitData.make = formData.make
      if (formData.model) submitData.model = formData.model
      if (formData.year) submitData.year = parseInt(formData.year, 10)

      // Only include owner_id if admin and creating
      if (isAdmin && isCreateMode && formData.owner_id) {
        submitData.owner_id = formData.owner_id
      }

      if (isCreateMode) {
        await vehicleService.createVehicle(submitData)
        toast({
          title: 'Vehículo creado',
          description: 'El vehículo ha sido creado correctamente.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        })
      } else {
        // For update, we don't need owner_id
        delete submitData.owner_id
        await vehicleService.updateVehicle(editingVehicle.id, submitData)
        toast({
          title: 'Vehículo actualizado',
          description: 'El vehículo ha sido actualizado correctamente.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        })
      }
      onClose()
      loadVehicles()
    } catch (err) {
      setFormError(getApiErrorMessage(err))
    } finally {
      setFormLoading(false)
    }
  }

  const handleDelete = async (vehicleId, plateNumber, isActive) => {
    // Don't allow disabling already disabled vehicles
    if (isActive === false && !isAdmin) {
      return
    }

    const action = isAdmin ? 'eliminar' : 'deshabilitar'
    const actionPast = isAdmin ? 'eliminado' : 'deshabilitado'

    const confirmMessage = isAdmin
      ? `¿Estás seguro de eliminar permanentemente el vehículo con matrícula "${plateNumber}"? Esto eliminará también sus inspecciones anuales, turnos y resultados.`
      : `¿Estás seguro de deshabilitar el vehículo con matrícula "${plateNumber}"? Podrá volver a habilitarlo más tarde.`

    if (!window.confirm(confirmMessage)) {
      return
    }

    try {
      await vehicleService.deleteVehicle(vehicleId)
      toast({
        title: `Vehículo ${actionPast}`,
        description: `El vehículo ha sido ${actionPast} correctamente.`,
        status: 'success',
        duration: 5000,
        isClosable: true,
      })
      loadVehicles()
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
          <Heading size="xl">
            {isAdmin ? 'Gestión de Vehículos' : 'Mis Vehículos'}
          </Heading>
          <HStack>
            <Button colorScheme="green" onClick={handleCreate}>
              Crear Vehículo
            </Button>
            <Button colorScheme="blue" onClick={loadVehicles} isLoading={loading}>
              Actualizar
            </Button>
          </HStack>
        </HStack>

        {/* Filter Options */}
        <HStack>
          <Checkbox
            isChecked={includeInactive}
            onChange={(e) => setIncludeInactive(e.target.checked)}
          >
            Incluir vehículos deshabilitados
          </Checkbox>
        </HStack>

        {/* Error Alert */}
        {error && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            {error}
          </Alert>
        )}

        {/* Vehicles Table */}
        <Box bg="white" borderRadius="lg" shadow="md" overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Matrícula</Th>
                <Th>Marca</Th>
                <Th>Modelo</Th>
                <Th>Año</Th>
                {isAdmin && <Th>Propietario</Th>}
                <Th>Estado</Th>
                <Th>Acciones</Th>
              </Tr>
            </Thead>
            <Tbody>
              {loading ? (
                <Tr>
                  <Td colSpan={isAdmin ? 7 : 6} textAlign="center">
                    Cargando...
                  </Td>
                </Tr>
              ) : vehicles.length === 0 ? (
                <Tr>
                  <Td colSpan={isAdmin ? 7 : 6} textAlign="center">
                    No hay vehículos
                  </Td>
                </Tr>
              ) : (
                vehicles.map((vehicle) => (
                  <Tr key={vehicle.id} opacity={vehicle.is_active === false ? 0.6 : 1}>
                    <Td fontWeight="bold">{vehicle.plate_number}</Td>
                    <Td>{vehicle.make || '-'}</Td>
                    <Td>{vehicle.model || '-'}</Td>
                    <Td>{vehicle.year || '-'}</Td>
                    {isAdmin && (
                      <Td>
                        {vehicle.owner_name && vehicle.owner_email ? (
                          <>
                            {vehicle.owner_name}{' '}
                            <Text as="span" fontSize="sm" color="gray.600">
                              ({vehicle.owner_email})
                            </Text>
                          </>
                        ) : (
                          '-'
                        )}
                      </Td>
                    )}
                    <Td>
                      <Badge colorScheme={vehicle.is_active === false ? 'red' : 'green'}>
                        {vehicle.is_active === false ? 'Deshabilitado' : 'Activo'}
                      </Badge>
                    </Td>
                    <Td>
                      <HStack spacing={2}>
                        <Button
                          size="sm"
                          colorScheme="blue"
                          onClick={() => handleEdit(vehicle)}
                          isDisabled={vehicle.is_active === false}
                        >
                          Editar
                        </Button>
                        <Button
                          size="sm"
                          colorScheme="red"
                          onClick={() => handleDelete(vehicle.id, vehicle.plate_number, vehicle.is_active)}
                        >
                          {isAdmin ? 'Eliminar' : 'Deshabilitar'}
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
            {isCreateMode ? 'Crear Vehículo' : 'Editar Vehículo'}
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
                  <FormLabel>Matrícula</FormLabel>
                  <Input
                    name="plate_number"
                    value={formData.plate_number}
                    onChange={handleFormChange}
                    isDisabled={formLoading}
                    placeholder="ABC123"
                    textTransform="uppercase"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Marca</FormLabel>
                  <Input
                    name="make"
                    value={formData.make}
                    onChange={handleFormChange}
                    isDisabled={formLoading}
                    placeholder="Toyota, Honda, Ford..."
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Modelo</FormLabel>
                  <Input
                    name="model"
                    value={formData.model}
                    onChange={handleFormChange}
                    isDisabled={formLoading}
                    placeholder="Corolla, Civic, Focus..."
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Año</FormLabel>
                  <Input
                    type="number"
                    name="year"
                    value={formData.year}
                    onChange={handleFormChange}
                    isDisabled={formLoading}
                    placeholder="2020"
                    min="1900"
                    max="2100"
                  />
                </FormControl>

                {/* Client selector for ADMIN when creating */}
                {isAdmin && isCreateMode && (
                  <FormControl isRequired>
                    <FormLabel>Propietario del Vehículo</FormLabel>

                    {/* Show selected client */}
                    {selectedClient && (
                      <Box
                        p={3}
                        bg="blue.50"
                        borderRadius="md"
                        mb={2}
                        display="flex"
                        justifyContent="space-between"
                        alignItems="center"
                      >
                        <Box>
                          <Text fontWeight="bold">{selectedClient.name}</Text>
                          <Text fontSize="sm" color="gray.600">
                            {selectedClient.email}
                          </Text>
                        </Box>
                        <Button
                          size="sm"
                          colorScheme="red"
                          variant="ghost"
                          onClick={() => {
                            setSelectedClient(null)
                            setFormData({ ...formData, owner_id: '' })
                          }}
                        >
                          Cambiar
                        </Button>
                      </Box>
                    )}

                    {/* Search input when no client selected */}
                    {!selectedClient && (
                      <>
                        <Input
                          placeholder="Buscar cliente por nombre o email..."
                          value={clientSearch}
                          onChange={handleClientSearch}
                          isDisabled={formLoading || loadingClients}
                        />

                        {/* Client list */}
                        {clientSearch && (
                          <Box
                            mt={2}
                            maxH="200px"
                            overflowY="auto"
                            border="1px solid"
                            borderColor="gray.200"
                            borderRadius="md"
                          >
                            {loadingClients ? (
                              <Box p={3} textAlign="center">
                                <Text color="gray.500">Cargando clientes...</Text>
                              </Box>
                            ) : filteredClients.length === 0 ? (
                              <Box p={3} textAlign="center">
                                <Text color="gray.500">No se encontraron clientes</Text>
                              </Box>
                            ) : (
                              filteredClients.map((client) => (
                                <Box
                                  key={client.id}
                                  p={3}
                                  cursor="pointer"
                                  _hover={{ bg: 'gray.50' }}
                                  onClick={() => handleClientSelect(client)}
                                  borderBottom="1px solid"
                                  borderColor="gray.100"
                                >
                                  <Text fontWeight="medium">{client.name}</Text>
                                  <Text fontSize="sm" color="gray.600">
                                    {client.email}
                                  </Text>
                                </Box>
                              ))
                            )}
                          </Box>
                        )}

                        <Text fontSize="xs" color="gray.500" mt={1}>
                          Busca por nombre o email del cliente
                        </Text>
                      </>
                    )}
                  </FormControl>
                )}
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

export default VehicleManagementPage
