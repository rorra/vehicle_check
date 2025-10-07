/**
 * Annual Inspection Management Page
 *
 * Allows users to manage annual vehicle inspections.
 * - CLIENT: Can view inspections for their own vehicles (read-only, inspections are created automatically by backend)
 * - INSPECTOR: Can view all inspections (read-only)
 * - ADMIN: Can view, create, update status, and delete all inspections
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
  Select,
  useDisclosure,
  Text,
} from '@chakra-ui/react'
import { annualInspectionService } from '../services/annualInspectionService'
import { vehicleService } from '../services/vehicleService'
import { getApiErrorMessage } from '../utils/validation'
import { useAuth } from '../context/AuthContext'

const AnnualInspectionManagementPage = () => {
  const { user } = useAuth()
  const [inspections, setInspections] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const toast = useToast()

  // Modal state
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [isCreateMode, setIsCreateMode] = useState(false)
  const [editingInspection, setEditingInspection] = useState(null)
  const [formData, setFormData] = useState({
    vehicle_id: '',
    year: new Date().getFullYear(),
    status: 'PENDING',
  })
  const [formLoading, setFormLoading] = useState(false)
  const [formError, setFormError] = useState('')

  // Vehicle selector state
  const [vehicles, setVehicles] = useState([])
  const [loadingVehicles, setLoadingVehicles] = useState(false)

  const isAdmin = user?.role === 'ADMIN'
  const isInspector = user?.role === 'INSPECTOR'
  const isClient = user?.role === 'CLIENT'

  useEffect(() => {
    if (user) {
      loadInspections()
    }
  }, [user])

  const loadInspections = async () => {
    setLoading(true)
    setError('')

    try {
      const data = await annualInspectionService.listAnnualInspections()
      const inspectionsList = data.inspections || data
      // Sort by year descending (newest first)
      const sortedInspections = inspectionsList.sort((a, b) => b.year - a.year)
      setInspections(sortedInspections)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const loadVehicles = async () => {
    setLoadingVehicles(true)
    try {
      if (isAdmin) {
        const data = await vehicleService.listVehiclesWithOwners()
        setVehicles(data)
      } else {
        const data = await vehicleService.listVehicles()
        setVehicles(data.vehicles || data)
      }
    } catch (err) {
      console.error('Failed to load vehicles:', err)
    } finally {
      setLoadingVehicles(false)
    }
  }

  const handleCreate = () => {
    setIsCreateMode(true)
    setEditingInspection(null)
    setFormData({
      vehicle_id: '',
      year: new Date().getFullYear(),
      status: 'PENDING',
    })
    setFormError('')
    onOpen()
    loadVehicles()
  }

  const handleEdit = (inspection) => {
    setIsCreateMode(false)
    setEditingInspection(inspection)
    setFormData({
      vehicle_id: inspection.vehicle_id,
      year: inspection.year,
      status: inspection.status,
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

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    setFormError('')
    setFormLoading(true)

    try {
      if (isCreateMode) {
        await annualInspectionService.createAnnualInspection({
          vehicle_id: formData.vehicle_id,
          year: parseInt(formData.year, 10),
        })
        toast({
          title: 'Inspección anual creada',
          description: 'La inspección anual ha sido creada correctamente.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        })
      } else {
        // Only status can be updated
        await annualInspectionService.updateAnnualInspection(editingInspection.id, {
          status: formData.status,
        })
        toast({
          title: 'Inspección actualizada',
          description: 'La inspección ha sido actualizada correctamente.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        })
      }
      onClose()
      loadInspections()
    } catch (err) {
      setFormError(getApiErrorMessage(err))
    } finally {
      setFormLoading(false)
    }
  }

  const handleDelete = async (inspectionId, vehiclePlate) => {
    if (!window.confirm(`¿Estás seguro de eliminar la inspección anual del vehículo "${vehiclePlate}"? Esto eliminará todos los turnos y resultados asociados.`)) {
      return
    }

    try {
      await annualInspectionService.deleteAnnualInspection(inspectionId)
      toast({
        title: 'Inspección eliminada',
        description: 'La inspección anual ha sido eliminada correctamente.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      })
      loadInspections()
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

  const getStatusColor = (status) => {
    const colors = {
      PENDING: 'yellow',
      IN_PROGRESS: 'blue',
      PASSED: 'green',
      FAILED: 'red',
    }
    return colors[status] || 'gray'
  }

  const getStatusLabel = (status) => {
    const labels = {
      PENDING: 'Pendiente',
      IN_PROGRESS: 'En Progreso',
      PASSED: 'Aprobada',
      FAILED: 'Reprobada',
    }
    return labels[status] || status
  }

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between">
          <Heading size="xl">
            {isAdmin ? 'Gestión de Inspecciones Anuales' :
             isInspector ? 'Inspecciones Anuales' :
             'Mis Inspecciones Anuales'}
          </Heading>
          <HStack>
            {isAdmin && (
              <Button colorScheme="green" onClick={handleCreate}>
                Crear Inspección
              </Button>
            )}
            <Button colorScheme="blue" onClick={loadInspections} isLoading={loading}>
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

        {/* Inspections Table */}
        <Box bg="white" borderRadius="lg" shadow="md" overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Año</Th>
                <Th>Vehículo</Th>
                {isAdmin && <Th>Propietario</Th>}
                <Th>Estado</Th>
                <Th>Intentos</Th>
                <Th>Turnos</Th>
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
              ) : inspections.length === 0 ? (
                <Tr>
                  <Td colSpan={isAdmin ? 7 : 6} textAlign="center">
                    No hay inspecciones anuales
                  </Td>
                </Tr>
              ) : (
                inspections.map((inspection) => (
                  <Tr key={inspection.id}>
                    <Td fontWeight="bold">{inspection.year}</Td>
                    <Td>
                      <Text fontWeight="medium">{inspection.vehicle_plate}</Text>
                      <Text fontSize="sm" color="gray.600">
                        {inspection.vehicle_make} {inspection.vehicle_model} ({inspection.vehicle_year})
                      </Text>
                    </Td>
                    {isAdmin && (
                      <Td>
                        {inspection.owner_name}{' '}
                        <Text as="span" fontSize="sm" color="gray.600">
                          ({inspection.owner_email})
                        </Text>
                      </Td>
                    )}
                    <Td>
                      <Badge colorScheme={getStatusColor(inspection.status)}>
                        {getStatusLabel(inspection.status)}
                      </Badge>
                    </Td>
                    <Td>{inspection.attempt_count}</Td>
                    <Td>{inspection.total_appointments}</Td>
                    <Td>
                      <HStack spacing={2}>
                        {isAdmin && (
                          <>
                            <Button
                              size="sm"
                              colorScheme="blue"
                              onClick={() => handleEdit(inspection)}
                            >
                              Editar
                            </Button>
                            <Button
                              size="sm"
                              colorScheme="red"
                              onClick={() => handleDelete(inspection.id, inspection.vehicle_plate)}
                            >
                              Eliminar
                            </Button>
                          </>
                        )}
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
            {isCreateMode ? 'Crear Inspección Anual' : 'Editar Inspección'}
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
                {isCreateMode && (
                  <>
                    <FormControl isRequired>
                      <FormLabel>Vehículo</FormLabel>
                      <Select
                        name="vehicle_id"
                        value={formData.vehicle_id}
                        onChange={handleFormChange}
                        isDisabled={formLoading || loadingVehicles}
                        placeholder="Seleccionar vehículo"
                      >
                        {vehicles.map((vehicle) => (
                          <option key={vehicle.id} value={vehicle.id}>
                            {vehicle.plate_number} - {vehicle.make} {vehicle.model}
                            {isAdmin && vehicle.owner_name && ` (${vehicle.owner_name})`}
                          </option>
                        ))}
                      </Select>
                    </FormControl>

                    <FormControl isRequired>
                      <FormLabel>Año</FormLabel>
                      <Input
                        type="number"
                        name="year"
                        value={formData.year}
                        onChange={handleFormChange}
                        isDisabled={formLoading}
                        min={new Date().getFullYear() - 1}
                        max={new Date().getFullYear() + 1}
                      />
                      <Text fontSize="xs" color="gray.500" mt={1}>
                        Año debe estar entre {new Date().getFullYear() - 1} y {new Date().getFullYear() + 1}
                      </Text>
                    </FormControl>
                  </>
                )}

                {!isCreateMode && isAdmin && (
                  <FormControl isRequired>
                    <FormLabel>Estado</FormLabel>
                    <Select
                      name="status"
                      value={formData.status}
                      onChange={handleFormChange}
                      isDisabled={formLoading}
                    >
                      <option value="PENDING">Pendiente</option>
                      <option value="IN_PROGRESS">En Progreso</option>
                      <option value="PASSED">Aprobada</option>
                      <option value="FAILED">Reprobada</option>
                    </Select>
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

export default AnnualInspectionManagementPage
