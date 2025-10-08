/**
 * Inspector Inspections Page (INSPECTOR only)
 *
 * Allows inspectors to complete inspections for their assigned appointments.
 * - View assigned appointments that are CONFIRMED (ready for inspection)
 * - Complete inspection by scoring 8 check items (0-10 each)
 * - Submit inspection result with total score (0-80) and observations
 *
 * Pass/Fail Rules:
 * - PASS: Total score >= 40 AND all items >= 5
 * - FAIL: Total score < 40 OR any item < 5
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
  Textarea,
  Text,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Divider,
} from '@chakra-ui/react'
import { appointmentService } from '../../services/appointmentService'
import { checkItemService } from '../../services/checkItemService'
import { getApiErrorMessage } from '../../utils/validation'

const InspectorInspectionsPage = () => {
  const [appointments, setAppointments] = useState([])
  const [checkItems, setCheckItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const toast = useToast()

  // Inspection modal state
  const [isOpen, setIsOpen] = useState(false)
  const [selectedAppointment, setSelectedAppointment] = useState(null)
  const [itemScores, setItemScores] = useState(Array(8).fill(0))
  const [observation, setObservation] = useState('')
  const [formLoading, setFormLoading] = useState(false)
  const [formError, setFormError] = useState('')

  useEffect(() => {
    loadAppointments()
    loadCheckItems()
  }, [])

  const loadAppointments = async () => {
    setLoading(true)
    setError('')

    try {
      const data = await appointmentService.listAppointments()
      const appointmentsList = data.appointments || data

      // Filter only CONFIRMED appointments (ready for inspection)
      const confirmedAppointments = appointmentsList.filter(
        (apt) => apt.status === 'CONFIRMED'
      )

      // Sort by date ascending (earliest first)
      const sortedAppointments = confirmedAppointments.sort((a, b) =>
        new Date(a.date_time) - new Date(b.date_time)
      )

      setAppointments(sortedAppointments)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const loadCheckItems = async () => {
    try {
      const data = await checkItemService.listTemplates()
      setCheckItems(data)
    } catch (err) {
      console.error('Failed to load check items:', err)
    }
  }

  const handleStartInspection = (appointment) => {
    setSelectedAppointment(appointment)
    setItemScores(Array(8).fill(0))
    setObservation('')
    setFormError('')
    setIsOpen(true)
  }

  const handleScoreChange = (index, value) => {
    const newScores = [...itemScores]
    const numValue = parseInt(value) || 0
    // Clamp value between 0 and 10
    newScores[index] = Math.max(0, Math.min(10, numValue))
    setItemScores(newScores)
    if (formError) setFormError('')
  }

  const calculateTotalScore = () => {
    return itemScores.reduce((sum, score) => sum + score, 0)
  }

  const hasFailingItem = () => {
    return itemScores.some(score => score < 5)
  }

  const isPassed = () => {
    const total = calculateTotalScore()
    // Fail if total score < 40 OR any item has score < 5
    return total >= 40 && !hasFailingItem()
  }

  const handleSubmit = async () => {
    setFormError('')
    setFormLoading(true)

    try {
      const totalScore = calculateTotalScore()

      // Validation
      if (totalScore === 0) {
        setFormError('Debe asignar puntajes a los ítems de chequeo')
        setFormLoading(false)
        return
      }

      if (totalScore > 80) {
        setFormError('El puntaje total no puede exceder 80')
        setFormLoading(false)
        return
      }

      const resultData = {
        total_score: totalScore,
        item_scores: itemScores,
        owner_observation: observation.trim() || undefined,
      }

      await appointmentService.completeAppointment(selectedAppointment.id, resultData)

      const passed = isPassed()
      const failReason = hasFailingItem() ? ' (Uno o más ítems con puntaje menor a 5)' : ''

      toast({
        title: 'Inspección completada',
        description: `Puntaje total: ${totalScore}/80. ${passed ? 'Aprobado ✓' : `Rechazado ✗${failReason}`}`,
        status: passed ? 'success' : 'warning',
        duration: 5000,
        isClosable: true,
      })

      setIsOpen(false)
      loadAppointments()
    } catch (err) {
      setFormError(getApiErrorMessage(err))
    } finally {
      setFormLoading(false)
    }
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

  const totalScore = calculateTotalScore()
  const passed = isPassed()

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between">
          <Heading size="xl">Realizar Inspecciones</Heading>
          <Button colorScheme="blue" onClick={loadAppointments} isLoading={loading}>
            Actualizar
          </Button>
        </HStack>

        {/* Info Alert */}
        <Alert status="info" borderRadius="md">
          <AlertIcon />
          Aquí puede completar las inspecciones de los turnos confirmados que le han sido asignados.
        </Alert>

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
                <Th>Propietario</Th>
                <Th>Acciones</Th>
              </Tr>
            </Thead>
            <Tbody>
              {loading ? (
                <Tr>
                  <Td colSpan={4} textAlign="center">
                    Cargando...
                  </Td>
                </Tr>
              ) : appointments.length === 0 ? (
                <Tr>
                  <Td colSpan={4} textAlign="center">
                    No hay turnos confirmados pendientes de inspección
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
                    <Td>
                      <Text>{appointment.owner_name}</Text>
                      <Text fontSize="sm" color="gray.600">
                        ({appointment.owner_email})
                      </Text>
                    </Td>
                    <Td>
                      <Button
                        size="sm"
                        colorScheme="green"
                        onClick={() => handleStartInspection(appointment)}
                      >
                        Completar Inspección
                      </Button>
                    </Td>
                  </Tr>
                ))
              )}
            </Tbody>
          </Table>
        </Box>
      </VStack>

      {/* Inspection Modal */}
      <Modal isOpen={isOpen} onClose={() => setIsOpen(false)} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Completar Inspección</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {formError && (
              <Alert status="error" borderRadius="md" mb={4}>
                <AlertIcon />
                {formError}
              </Alert>
            )}

            {selectedAppointment && (
              <VStack spacing={4} align="stretch">
                {/* Appointment Info */}
                <Box bg="gray.50" p={3} borderRadius="md">
                  <Text fontWeight="bold">Vehículo: {selectedAppointment.vehicle_plate}</Text>
                  <Text fontSize="sm">
                    {selectedAppointment.vehicle_make} {selectedAppointment.vehicle_model}
                  </Text>
                  <Text fontSize="sm">Propietario: {selectedAppointment.owner_name}</Text>
                </Box>

                <Divider />

                {/* Check Items */}
                <Box>
                  <Heading size="sm" mb={3}>
                    Ítems de Chequeo (0-10 puntos cada uno)
                  </Heading>
                  <VStack spacing={3} align="stretch">
                    {checkItems.map((item, index) => (
                      <FormControl key={item.id} isRequired>
                        <HStack justify="space-between" mb={1}>
                          <FormLabel fontSize="sm" mb={0}>
                            {item.ordinal}. {item.description}
                          </FormLabel>
                          {itemScores[index] > 0 && itemScores[index] < 5 && (
                            <Badge colorScheme="red" fontSize="xs">
                              Reprobado
                            </Badge>
                          )}
                        </HStack>
                        <NumberInput
                          value={itemScores[index]}
                          onChange={(valueString) => handleScoreChange(index, valueString)}
                          min={0}
                          max={10}
                          isDisabled={formLoading}
                        >
                          <NumberInputField
                            borderColor={itemScores[index] > 0 && itemScores[index] < 5 ? 'red.300' : undefined}
                          />
                          <NumberInputStepper>
                            <NumberIncrementStepper />
                            <NumberDecrementStepper />
                          </NumberInputStepper>
                        </NumberInput>
                      </FormControl>
                    ))}
                  </VStack>
                </Box>

                <Divider />

                {/* Total Score */}
                <Box bg={passed ? 'green.50' : 'red.50'} p={3} borderRadius="md">
                  <HStack justify="space-between">
                    <Text fontWeight="bold" fontSize="lg">
                      Puntaje Total:
                    </Text>
                    <HStack>
                      <Badge
                        colorScheme={passed ? 'green' : 'red'}
                        fontSize="lg"
                        px={3}
                        py={1}
                      >
                        {totalScore}/80
                      </Badge>
                      <Badge colorScheme={passed ? 'green' : 'red'}>
                        {passed ? 'APROBADO' : 'RECHAZADO'}
                      </Badge>
                    </HStack>
                  </HStack>
                  <Text fontSize="xs" color="gray.600" mt={1}>
                    Se requieren 40 puntos o más para aprobar, y todos los ítems deben tener al menos 5 puntos
                  </Text>
                  {hasFailingItem() && (
                    <Text fontSize="xs" color="red.600" mt={1} fontWeight="bold">
                      ⚠️ Hay ítems con puntaje menor a 5
                    </Text>
                  )}
                </Box>

                {/* Observation */}
                <FormControl>
                  <FormLabel>Observaciones Generales (Opcional)</FormLabel>
                  <Textarea
                    value={observation}
                    onChange={(e) => setObservation(e.target.value)}
                    isDisabled={formLoading}
                    placeholder="Ingrese observaciones adicionales sobre la inspección..."
                    maxLength={500}
                    rows={4}
                  />
                  <Text fontSize="xs" color="gray.500" mt={1}>
                    {observation.length}/500 caracteres
                  </Text>
                </FormControl>
              </VStack>
            )}
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={() => setIsOpen(false)}>
              Cancelar
            </Button>
            <Button
              colorScheme="green"
              onClick={handleSubmit}
              isLoading={formLoading}
              isDisabled={totalScore === 0}
            >
              Completar Inspección
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Container>
  )
}

export default InspectorInspectionsPage
