/**
 * Inspection Results Page
 *
 * Allows users to view inspection results.
 * - CLIENT: Can view results for their own vehicles
 * - INSPECTOR: Can view all results
 * - ADMIN: Can view all results
 *
 * Features:
 * - List results with pagination
 * - View detailed result with item checks
 * - Filter by year, vehicle, passed status
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
  Badge,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Text,
  Select,
  FormControl,
  FormLabel,
  Grid,
  GridItem,
  Divider,
} from '@chakra-ui/react'
import { inspectionResultService } from '../services/inspectionResultService'
import { vehicleService } from '../services/vehicleService'
import { getApiErrorMessage } from '../utils/validation'
import { useAuth } from '../context/AuthContext'

const InspectionResultsPage = () => {
  const { user } = useAuth()
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)

  // Filters
  const [yearFilter, setYearFilter] = useState('')
  const [vehicleFilter, setVehicleFilter] = useState('')
  const [passedFilter, setPassedFilter] = useState('')
  const [vehicles, setVehicles] = useState([])

  // Detail modal
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [selectedResult, setSelectedResult] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const isAdmin = user?.role === 'ADMIN'
  const isClient = user?.role === 'CLIENT'

  useEffect(() => {
    if (user) {
      loadResults()
      if (isAdmin) {
        loadVehicles()
      } else if (isClient) {
        loadMyVehicles()
      }
    }
  }, [user, page, yearFilter, vehicleFilter, passedFilter])

  const loadResults = async () => {
    setLoading(true)
    setError('')

    try {
      const params = {
        page,
        page_size: 10,
      }

      if (yearFilter) params.year = parseInt(yearFilter)
      if (vehicleFilter) params.vehicle_id = vehicleFilter
      if (passedFilter) params.passed_only = passedFilter === 'true'

      const data = await inspectionResultService.listResults(params)
      setResults(data.results)
      setTotal(data.total)
      setTotalPages(Math.ceil(data.total / 10))
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const loadVehicles = async () => {
    try {
      const data = await vehicleService.listVehiclesWithOwners()
      setVehicles(data)
    } catch (err) {
      console.error('Failed to load vehicles:', err)
    }
  }

  const loadMyVehicles = async () => {
    try {
      const data = await vehicleService.listVehicles()
      setVehicles(data.vehicles || data)
    } catch (err) {
      console.error('Failed to load vehicles:', err)
    }
  }

  const handleViewDetail = async (resultId) => {
    setDetailLoading(true)
    onOpen()

    try {
      const data = await inspectionResultService.getResult(resultId)
      // Sort item checks by ordinal
      data.item_checks.sort((a, b) => a.template_ordinal - b.template_ordinal)
      setSelectedResult(data)
    } catch (err) {
      setError(getApiErrorMessage(err))
      onClose()
    } finally {
      setDetailLoading(false)
    }
  }

  const handleResetFilters = () => {
    setYearFilter('')
    setVehicleFilter('')
    setPassedFilter('')
    setPage(1)
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

  const getPassedLabel = (passed) => {
    return passed ? 'Aprobado' : 'Rechazado'
  }

  const getPassedColor = (passed) => {
    return passed ? 'green' : 'red'
  }

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between">
          <Heading size="xl">
            {isAdmin ? 'Resultados de Inspecciones' : 'Mis Resultados'}
          </Heading>
          <Button colorScheme="blue" onClick={loadResults} isLoading={loading}>
            Actualizar
          </Button>
        </HStack>

        {/* Error Alert */}
        {error && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            {error}
          </Alert>
        )}

        {/* Filters */}
        <Box bg="white" p={4} borderRadius="lg" shadow="md">
          <Heading size="sm" mb={3}>
            Filtros
          </Heading>
          <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
            <GridItem>
              <FormControl>
                <FormLabel>Año</FormLabel>
                <Select
                  value={yearFilter}
                  onChange={(e) => {
                    setYearFilter(e.target.value)
                    setPage(1)
                  }}
                  placeholder="Todos los años"
                >
                  {[...Array(5)].map((_, i) => {
                    const year = new Date().getFullYear() - i
                    return (
                      <option key={year} value={year}>
                        {year}
                      </option>
                    )
                  })}
                </Select>
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl>
                <FormLabel>Vehículo</FormLabel>
                <Select
                  value={vehicleFilter}
                  onChange={(e) => {
                    setVehicleFilter(e.target.value)
                    setPage(1)
                  }}
                  placeholder="Todos los vehículos"
                >
                  {vehicles.map((vehicle) => (
                    <option key={vehicle.id} value={vehicle.id}>
                      {vehicle.plate_number}
                      {isAdmin && vehicle.owner_name && ` (${vehicle.owner_name})`}
                    </option>
                  ))}
                </Select>
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl>
                <FormLabel>Estado</FormLabel>
                <Select
                  value={passedFilter}
                  onChange={(e) => {
                    setPassedFilter(e.target.value)
                    setPage(1)
                  }}
                  placeholder="Todos los estados"
                >
                  <option value="true">Aprobado</option>
                  <option value="false">Rechazado</option>
                </Select>
              </FormControl>
            </GridItem>

            <GridItem display="flex" alignItems="flex-end">
              <Button onClick={handleResetFilters} w="full">
                Limpiar Filtros
              </Button>
            </GridItem>
          </Grid>
        </Box>

        {/* Results Table */}
        <Box bg="white" borderRadius="lg" shadow="md" overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Fecha de Inspección</Th>
                <Th>Vehículo</Th>
                <Th>Año</Th>
                <Th>Puntaje</Th>
                <Th>Estado</Th>
                <Th>Acciones</Th>
              </Tr>
            </Thead>
            <Tbody>
              {loading ? (
                <Tr>
                  <Td colSpan={6} textAlign="center">
                    Cargando...
                  </Td>
                </Tr>
              ) : results.length === 0 ? (
                <Tr>
                  <Td colSpan={6} textAlign="center">
                    No hay resultados disponibles
                  </Td>
                </Tr>
              ) : (
                results.map((result) => (
                  <Tr key={result.id}>
                    <Td>{formatDateTime(result.created_at)}</Td>
                    <Td>{result.vehicle_plate}</Td>
                    <Td>{result.year}</Td>
                    <Td>
                      <Text fontWeight="bold">{result.total_score}/80</Text>
                    </Td>
                    <Td>
                      <Badge colorScheme={getPassedColor(result.passed)}>
                        {getPassedLabel(result.passed)}
                      </Badge>
                    </Td>
                    <Td>
                      <Button
                        size="sm"
                        colorScheme="blue"
                        onClick={() => handleViewDetail(result.id)}
                      >
                        Ver Detalle
                      </Button>
                    </Td>
                  </Tr>
                ))
              )}
            </Tbody>
          </Table>
        </Box>

        {/* Pagination */}
        {totalPages > 1 && (
          <HStack justify="center" spacing={2}>
            <Button
              onClick={() => setPage(page - 1)}
              isDisabled={page === 1}
              size="sm"
            >
              Anterior
            </Button>
            <Text>
              Página {page} de {totalPages} ({total} resultados)
            </Text>
            <Button
              onClick={() => setPage(page + 1)}
              isDisabled={page === totalPages}
              size="sm"
            >
              Siguiente
            </Button>
          </HStack>
        )}
      </VStack>

      {/* Detail Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Detalle de Inspección</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            {detailLoading ? (
              <Text>Cargando...</Text>
            ) : selectedResult ? (
              <VStack spacing={4} align="stretch">
                {/* General Info */}
                <Box>
                  <Heading size="sm" mb={2}>
                    Información General
                  </Heading>
                  <Grid templateColumns="repeat(2, 1fr)" gap={2}>
                    <Text>
                      <strong>Vehículo:</strong> {selectedResult.vehicle_plate}
                    </Text>
                    <Text>
                      <strong>Marca/Modelo:</strong>{' '}
                      {selectedResult.vehicle_make} {selectedResult.vehicle_model}
                    </Text>
                    <Text>
                      <strong>Inspector:</strong>{' '}
                      {selectedResult.inspector_name || 'Sin asignar'}
                    </Text>
                    <Text>
                      <strong>Fecha:</strong>{' '}
                      {formatDateTime(selectedResult.inspection_date)}
                    </Text>
                    <Text>
                      <strong>Puntaje Total:</strong>{' '}
                      <Badge colorScheme={getPassedColor(selectedResult.passed)}>
                        {selectedResult.total_score}/80
                      </Badge>
                    </Text>
                    <Text>
                      <strong>Estado:</strong>{' '}
                      <Badge colorScheme={getPassedColor(selectedResult.passed)}>
                        {getPassedLabel(selectedResult.passed)}
                      </Badge>
                    </Text>
                  </Grid>
                </Box>

                <Divider />

                {/* Item Checks */}
                <Box>
                  <Heading size="sm" mb={2}>
                    Ítems Chequeados
                  </Heading>
                  <VStack spacing={2} align="stretch">
                    {selectedResult.item_checks.map((item) => (
                      <Box
                        key={item.id}
                        p={3}
                        bg="gray.50"
                        borderRadius="md"
                        border="1px"
                        borderColor="gray.200"
                      >
                        <HStack justify="space-between" mb={1}>
                          <Text fontWeight="bold">
                            {item.template_ordinal}. {item.template_description}
                          </Text>
                          <Badge colorScheme="blue">{item.score}/10</Badge>
                        </HStack>
                        {item.observation && (
                          <Text fontSize="sm" color="gray.600">
                            <strong>Obs:</strong> {item.observation}
                          </Text>
                        )}
                      </Box>
                    ))}
                  </VStack>
                </Box>

                {/* Observation */}
                {selectedResult.owner_observation && (
                  <>
                    <Divider />
                    <Box>
                      <Heading size="sm" mb={2}>
                        Observaciones Generales
                      </Heading>
                      <Text>{selectedResult.owner_observation}</Text>
                    </Box>
                  </>
                )}
              </VStack>
            ) : null}
          </ModalBody>
        </ModalContent>
      </Modal>
    </Container>
  )
}

export default InspectionResultsPage
