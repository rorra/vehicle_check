/**
 * Appointment Management Page
 *
 * Allows users to manage vehicle inspection appointments.
 * - CLIENT: Can view, create, and cancel appointments for their vehicles
 * - INSPECTOR: Can view their assigned appointments
 * - ADMIN: Can view, create, update, cancel all appointments, and assign inspectors
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
import { appointmentService } from '../services/appointmentService'
import { vehicleService } from '../services/vehicleService'
import { inspectorService } from '../services/inspectorService'
import { getApiErrorMessage } from '../utils/validation'
import { useAuth } from '../context/AuthContext'

const AppointmentManagementPage = () => {
  const { user } = useAuth()
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const toast = useToast()

  // Modal state
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [isCreateMode, setIsCreateMode] = useState(false)
  const [editingAppointment, setEditingAppointment] = useState(null)
  const [formData, setFormData] = useState({
    vehicle_id: '',
    slot_id: '',
    inspector_id: '',
  })
  const [formLoading, setFormLoading] = useState(false)
  const [formError, setFormError] = useState('')

  // Vehicle and Inspector lists for dropdowns
  const [vehicles, setVehicles] = useState([])
  const [inspectors, setInspectors] = useState([])
  const [availableSlots, setAvailableSlots] = useState([])
  const [loadingVehicles, setLoadingVehicles] = useState(false)
  const [loadingInspectors, setLoadingInspectors] = useState(false)
  const [loadingSlots, setLoadingSlots] = useState(false)

  const isAdmin = user?.role === 'ADMIN'
  const isInspector = user?.role === 'INSPECTOR'
  const isClient = user?.role === 'CLIENT'

  useEffect(() => {
    if (user) {
      loadAppointments()
    }
  }, [user])

  const loadAppointments = async () => {
    setLoading(true)
    setError('')

    try {
      const data = await appointmentService.listAppointments()
      const appointmentsList = data.appointments || data
      // Sort by date descending (newest first)
      const sortedAppointments = appointmentsList.sort((a, b) =>
        new Date(b.date_time) - new Date(a.date_time)
      )
      setAppointments(sortedAppointments)
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

  const loadInspectors = async () => {
    if (!isAdmin) return

    setLoadingInspectors(true)
    try {
      const data = await inspectorService.listInspectors({ active_only: true })
      setInspectors(data.inspectors || data)
    } catch (err) {
      console.error('Failed to load inspectors:', err)
    } finally {
      setLoadingInspectors(false)
    }
  }

  const loadAvailableSlots = async () => {
    setLoadingSlots(true)
    try {
      // Get slots for next 30 days
      const fromDate = new Date()
      const toDate = new Date()
      toDate.setDate(toDate.getDate() + 30)

      const params = {
        from_date: fromDate.toISOString(),
        to_date: toDate.toISOString(),
      }

      const data = await appointmentService.getAvailableSlots(params)
      // Filter out booked slots
      const availableOnly = data.filter(slot => !slot.is_booked)
      setAvailableSlots(availableOnly)
    } catch (err) {
      console.error('Failed to load available slots:', err)
    } finally {
      setLoadingSlots(false)
    }
  }

  const handleCreate = () => {
    setIsCreateMode(true)
    setEditingAppointment(null)
    setFormData({
      vehicle_id: '',
      slot_id: '',
      inspector_id: '',
    })
    setFormError('')
    onOpen()

    loadVehicles()
    loadAvailableSlots()
    if (isAdmin) {
      loadInspectors()
    }
  }

  const handleEdit = (appointment) => {
    setIsCreateMode(false)
    setEditingAppointment(appointment)

    setFormData({
      vehicle_id: appointment.vehicle_id,
      slot_id: '',
      inspector_id: appointment.inspector_id || '',
    })
    setFormError('')
    onOpen()

    // Both CLIENT and ADMIN must select from available slots
    loadAvailableSlots()

    if (isAdmin) {
      loadInspectors()
    }
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
        // For creating, use slot_id
        const submitData = {
          vehicle_id: formData.vehicle_id,
          slot_id: formData.slot_id,
        }

        // Only include inspector_id if admin and value provided
        if (isAdmin && formData.inspector_id) {
          submitData.inspector_id = formData.inspector_id
        }

        await appointmentService.createAppointment(submitData)
        toast({
          title: 'Turno creado',
          description: 'El turno ha sido creado correctamente.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        })
      } else {
        // For update - both CLIENT and ADMIN must select from available slots
        if (!formData.slot_id) {
          setFormError('Debe seleccionar un horario disponible')
          setFormLoading(false)
          return
        }

        // Find the selected slot to get its start_time
        const selectedSlot = availableSlots.find(slot => slot.id === formData.slot_id)
        if (!selectedSlot) {
          setFormError('Horario seleccionado no válido')
          setFormLoading(false)
          return
        }

        const updateData = {
          date_time: new Date(selectedSlot.start_time).toISOString(),
        }

        if (isAdmin && formData.inspector_id) {
          updateData.inspector_id = formData.inspector_id
        }

        await appointmentService.updateAppointment(editingAppointment.id, updateData)
        toast({
          title: 'Turno actualizado',
          description: 'El turno ha sido actualizado correctamente.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        })
      }
      onClose()
      loadAppointments()
    } catch (err) {
      setFormError(getApiErrorMessage(err))
    } finally {
      setFormLoading(false)
    }
  }

  const handleCancel = async (appointmentId, vehiclePlate) => {
    if (!window.confirm(`¿Estás seguro de cancelar el turno para el vehículo "${vehiclePlate}"?`)) {
      return
    }

    try {
      await appointmentService.cancelAppointment(appointmentId)
      toast({
        title: 'Turno cancelado',
        description: 'El turno ha sido cancelado correctamente.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      })
      loadAppointments()
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
      CONFIRMED: 'blue',
      COMPLETED: 'green',
      CANCELLED: 'red',
    }
    return colors[status] || 'gray'
  }

  const getStatusLabel = (status) => {
    const labels = {
      PENDING: 'Pendiente',
      CONFIRMED: 'Confirmado',
      COMPLETED: 'Completado',
      CANCELLED: 'Cancelado',
    }
    return labels[status] || status
  }

  const formatDateTime = (dateTime) => {
    const date = new Date(dateTime)
    return date.toLocaleString('es-AR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatSlotDisplay = (slot) => {
    const start = new Date(slot.start_time)
    const end = new Date(slot.end_time)
    const dateStr = start.toLocaleDateString('es-AR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
    const startTime = start.toLocaleTimeString('es-AR', {
      hour: '2-digit',
      minute: '2-digit',
    })
    const endTime = end.toLocaleTimeString('es-AR', {
      hour: '2-digit',
      minute: '2-digit',
    })
    return `${dateStr} - ${startTime} a ${endTime}`
  }

  const canEdit = (appointment) => {
    // Can't edit completed or cancelled appointments
    if (appointment.status === 'COMPLETED' || appointment.status === 'CANCELLED') {
      return false
    }
    // Admin can edit any appointment
    if (isAdmin) return true
    // Client can edit their own appointments
    if (isClient) return true
    // Inspector cannot edit
    return false
  }

  const canCancel = (appointment) => {
    // Can't cancel completed appointments
    if (appointment.status === 'COMPLETED') {
      return false
    }
    // Can't cancel already cancelled appointments
    if (appointment.status === 'CANCELLED') {
      return false
    }
    // Admin can cancel any appointment
    if (isAdmin) return true
    // Client can cancel their own appointments
    if (isClient) return true
    // Inspector cannot cancel
    return false
  }

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between">
          <Heading size="xl">
            {isAdmin ? 'Gestión de Turnos' :
             isInspector ? 'Mis Turnos Asignados' :
             'Mis Turnos'}
          </Heading>
          <HStack>
            {(isAdmin || isClient) && (
              <Button colorScheme="green" onClick={handleCreate}>
                Crear Turno
              </Button>
            )}
            <Button colorScheme="blue" onClick={loadAppointments} isLoading={loading}>
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

        {/* Appointments Table */}
        <Box bg="white" borderRadius="lg" shadow="md" overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Fecha y Hora</Th>
                <Th>Vehículo</Th>
                {isAdmin && <Th>Propietario</Th>}
                <Th>Inspector</Th>
                <Th>Estado</Th>
                <Th>Acciones</Th>
              </Tr>
            </Thead>
            <Tbody>
              {loading ? (
                <Tr>
                  <Td colSpan={isAdmin ? 6 : 5} textAlign="center">
                    Cargando...
                  </Td>
                </Tr>
              ) : appointments.length === 0 ? (
                <Tr>
                  <Td colSpan={isAdmin ? 6 : 5} textAlign="center">
                    No hay turnos
                  </Td>
                </Tr>
              ) : (
                appointments.map((appointment) => (
                  <Tr key={appointment.id}>
                    <Td>{formatDateTime(appointment.date_time)}</Td>
                    <Td>
                      <Text fontWeight="bold">{appointment.vehicle_plate}</Text>
                      {appointment.vehicle_make && appointment.vehicle_model && (
                        <Text fontSize="sm" color="gray.600">
                          {appointment.vehicle_make} {appointment.vehicle_model}
                        </Text>
                      )}
                    </Td>
                    {isAdmin && (
                      <Td>
                        <Text>{appointment.owner_name}</Text>
                        <Text fontSize="sm" color="gray.600">
                          ({appointment.owner_email})
                        </Text>
                      </Td>
                    )}
                    <Td>{appointment.inspector_name || '-'}</Td>
                    <Td>
                      <Badge colorScheme={getStatusColor(appointment.status)}>
                        {getStatusLabel(appointment.status)}
                      </Badge>
                    </Td>
                    <Td>
                      <HStack spacing={2}>
                        {canEdit(appointment) && (
                          <Button
                            size="sm"
                            colorScheme="blue"
                            onClick={() => handleEdit(appointment)}
                          >
                            Reprogramar
                          </Button>
                        )}
                        {canCancel(appointment) && (
                          <Button
                            size="sm"
                            colorScheme="red"
                            onClick={() => handleCancel(appointment.id, appointment.vehicle_plate)}
                          >
                            Cancelar
                          </Button>
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
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {isCreateMode ? 'Crear Turno' : 'Reprogramar Turno'}
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
                {/* Vehicle selector */}
                {isCreateMode && (
                  <FormControl isRequired>
                    <FormLabel>Vehículo</FormLabel>
                    <Select
                      name="vehicle_id"
                      value={formData.vehicle_id}
                      onChange={handleFormChange}
                      isDisabled={formLoading || loadingVehicles}
                      placeholder="Seleccione un vehículo"
                    >
                      {vehicles.map((vehicle) => (
                        <option key={vehicle.id} value={vehicle.id}>
                          {vehicle.plate_number}
                          {vehicle.make && vehicle.model && ` - ${vehicle.make} ${vehicle.model}`}
                          {isAdmin && vehicle.owner_name && ` (${vehicle.owner_name})`}
                        </option>
                      ))}
                    </Select>
                  </FormControl>
                )}

                {/* Slot selector - everyone must select from available slots */}
                <FormControl isRequired>
                  <FormLabel>Horario Disponible</FormLabel>
                  <Select
                    name="slot_id"
                    value={formData.slot_id}
                    onChange={handleFormChange}
                    isDisabled={formLoading || loadingSlots}
                    placeholder={loadingSlots ? 'Cargando horarios...' : 'Seleccione un horario'}
                  >
                    {availableSlots.map((slot) => (
                      <option key={slot.id} value={slot.id}>
                        {formatSlotDisplay(slot)}
                      </option>
                    ))}
                  </Select>
                  {availableSlots.length === 0 && !loadingSlots && (
                    <Text fontSize="sm" color="red.500" mt={1}>
                      No hay horarios disponibles en los próximos 30 días
                    </Text>
                  )}
                </FormControl>

                {/* Inspector selector (ADMIN only) */}
                {isAdmin && (
                  <FormControl>
                    <FormLabel>Inspector Asignado (Opcional)</FormLabel>
                    <Select
                      name="inspector_id"
                      value={formData.inspector_id}
                      onChange={handleFormChange}
                      isDisabled={formLoading || loadingInspectors}
                      placeholder="Sin asignar"
                    >
                      {inspectors.map((inspector) => (
                        <option key={inspector.id} value={inspector.id}>
                          {inspector.user_name} ({inspector.employee_id})
                        </option>
                      ))}
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

export default AppointmentManagementPage
