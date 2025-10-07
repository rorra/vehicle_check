/**
 * Availability Slot Management Page (ADMIN only)
 *
 * Allows administrators to manage availability slots for appointments.
 * - Create new slots with start and end time
 * - View all slots (including booked ones)
 * - Delete available slots (cannot delete booked slots)
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
  Text,
} from '@chakra-ui/react'
import { availabilitySlotService } from '../../services/availabilitySlotService'
import { getApiErrorMessage } from '../../utils/validation'

const AvailabilitySlotManagementPage = () => {
  const [slots, setSlots] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const toast = useToast()

  // Modal state
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [formData, setFormData] = useState({
    start_time: '',
  })
  const [formLoading, setFormLoading] = useState(false)
  const [formError, setFormError] = useState('')

  useEffect(() => {
    loadSlots()
  }, [])

  const loadSlots = async () => {
    setLoading(true)
    setError('')

    try {
      // Admin can see all slots including booked ones
      const data = await availabilitySlotService.listSlots({ include_booked: true })
      // Sort by start_time ascending (earliest first)
      const sortedSlots = data.sort((a, b) =>
        new Date(a.start_time) - new Date(b.start_time)
      )
      setSlots(sortedSlots)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    // Set default time to next available hour (on the hour)
    const now = new Date()
    now.setMinutes(0, 0, 0)
    now.setHours(now.getHours() + 1)

    const startTime = now.toISOString().slice(0, 16)

    setFormData({
      start_time: startTime,
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
      // Parse the datetime and ensure minutes and seconds are zero
      const startDate = new Date(formData.start_time)
      startDate.setMinutes(0, 0, 0)

      const submitData = {
        start_time: startDate.toISOString(),
      }

      await availabilitySlotService.createSlot(submitData)
      toast({
        title: 'Horario creado',
        description: 'El horario ha sido creado correctamente (duración: 1 hora).',
        status: 'success',
        duration: 5000,
        isClosable: true,
      })
      onClose()
      loadSlots()
    } catch (err) {
      setFormError(getApiErrorMessage(err))
    } finally {
      setFormLoading(false)
    }
  }

  const handleDelete = async (slotId, startTime, isBooked) => {
    if (isBooked) {
      toast({
        title: 'No se puede eliminar',
        description: 'No se pueden eliminar horarios que ya están reservados.',
        status: 'warning',
        duration: 5000,
        isClosable: true,
      })
      return
    }

    const formattedTime = formatDateTime(startTime)
    if (!window.confirm(`¿Estás seguro de eliminar el horario "${formattedTime}"?`)) {
      return
    }

    try {
      await availabilitySlotService.deleteSlot(slotId)
      toast({
        title: 'Horario eliminado',
        description: 'El horario ha sido eliminado correctamente.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      })
      loadSlots()
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

  const formatDateTime = (dateTime) => {
    const date = new Date(dateTime)
    return date.toLocaleString('es-AR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatTimeRange = (startTime, endTime) => {
    const start = new Date(startTime)
    const end = new Date(endTime)

    const dateStr = start.toLocaleDateString('es-AR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })

    const startStr = start.toLocaleTimeString('es-AR', {
      hour: '2-digit',
      minute: '2-digit',
    })

    const endStr = end.toLocaleTimeString('es-AR', {
      hour: '2-digit',
      minute: '2-digit',
    })

    return `${dateStr} - ${startStr} a ${endStr}`
  }

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between">
          <Heading size="xl">Gestión de Horarios Disponibles</Heading>
          <HStack>
            <Button colorScheme="green" onClick={handleCreate}>
              Crear Horario
            </Button>
            <Button colorScheme="blue" onClick={loadSlots} isLoading={loading}>
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

        {/* Slots Table */}
        <Box bg="white" borderRadius="lg" shadow="md" overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Fecha y Horario</Th>
                <Th>Hora Inicio</Th>
                <Th>Hora Fin</Th>
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
              ) : slots.length === 0 ? (
                <Tr>
                  <Td colSpan={5} textAlign="center">
                    No hay horarios disponibles
                  </Td>
                </Tr>
              ) : (
                slots.map((slot) => (
                  <Tr key={slot.id} opacity={slot.is_booked ? 0.7 : 1}>
                    <Td>{formatTimeRange(slot.start_time, slot.end_time)}</Td>
                    <Td>{new Date(slot.start_time).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })}</Td>
                    <Td>{new Date(slot.end_time).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })}</Td>
                    <Td>
                      <Badge colorScheme={slot.is_booked ? 'red' : 'green'}>
                        {slot.is_booked ? 'Reservado' : 'Disponible'}
                      </Badge>
                    </Td>
                    <Td>
                      <Button
                        size="sm"
                        colorScheme="red"
                        onClick={() => handleDelete(slot.id, slot.start_time, slot.is_booked)}
                        isDisabled={slot.is_booked}
                      >
                        Eliminar
                      </Button>
                    </Td>
                  </Tr>
                ))
              )}
            </Tbody>
          </Table>
        </Box>
      </VStack>

      {/* Create Modal */}
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Crear Horario Disponible</ModalHeader>
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
                  <FormLabel>Hora de Inicio</FormLabel>
                  <Input
                    type="datetime-local"
                    name="start_time"
                    value={formData.start_time}
                    onChange={handleFormChange}
                    isDisabled={formLoading}
                  />
                  <Text fontSize="xs" color="gray.500" mt={1}>
                    La hora debe ser en punto (ej: 09:00, 11:00). Los minutos se ajustarán a :00
                  </Text>
                </FormControl>

                <Text fontSize="sm" color="gray.600">
                  El horario tendrá una duración de 1 hora automáticamente. Estará disponible para que los clientes puedan reservar turnos.
                </Text>
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
              Crear
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Container>
  )
}

export default AvailabilitySlotManagementPage
