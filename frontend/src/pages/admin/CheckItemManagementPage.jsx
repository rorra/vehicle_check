/**
 * Check Item Template Management Page (ADMIN only)
 *
 * Allows administrators to manage check item templates used in inspections.
 * - Create new templates (8 items required for inspections)
 * - View all templates ordered by ordinal
 * - Update template details
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
  Select,
  useDisclosure,
  Text,
} from '@chakra-ui/react'
import { checkItemService } from '../../services/checkItemService'
import { getApiErrorMessage } from '../../utils/validation'

const CheckItemManagementPage = () => {
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const toast = useToast()

  // Modal state
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [isCreateMode, setIsCreateMode] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState(null)
  const [formData, setFormData] = useState({
    code: '',
    description: '',
    ordinal: '',
  })
  const [formLoading, setFormLoading] = useState(false)
  const [formError, setFormError] = useState('')

  useEffect(() => {
    loadTemplates()
  }, [])

  const loadTemplates = async () => {
    setLoading(true)
    setError('')

    try {
      const data = await checkItemService.listTemplates()
      setTemplates(data)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setIsCreateMode(true)
    setEditingTemplate(null)
    setFormData({
      code: '',
      description: '',
      ordinal: templates.length + 1,
    })
    setFormError('')
    onOpen()
  }

  const handleEdit = (template) => {
    setIsCreateMode(false)
    setEditingTemplate(template)
    setFormData({
      code: template.code,
      description: template.description,
      ordinal: template.ordinal,
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
      const submitData = {
        code: formData.code.trim().toUpperCase(),
        description: formData.description.trim(),
        ordinal: parseInt(formData.ordinal),
      }

      if (isCreateMode) {
        await checkItemService.createTemplate(submitData)
        toast({
          title: 'Plantilla creada',
          description: 'La plantilla de chequeo ha sido creada correctamente.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        })
      } else {
        await checkItemService.updateTemplate(editingTemplate.id, submitData)
        toast({
          title: 'Plantilla actualizada',
          description: 'La plantilla de chequeo ha sido actualizada correctamente.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        })
      }
      onClose()
      loadTemplates()
    } catch (err) {
      setFormError(getApiErrorMessage(err))
    } finally {
      setFormLoading(false)
    }
  }


  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between">
          <Heading size="xl">Gestión de Plantillas de Chequeo</Heading>
          <HStack>
            <Button colorScheme="green" onClick={handleCreate}>
              Crear Plantilla
            </Button>
            <Button colorScheme="blue" onClick={loadTemplates} isLoading={loading}>
              Actualizar
            </Button>
          </HStack>
        </HStack>

        {/* Info Alert */}
        <Alert status="info" borderRadius="md">
          <AlertIcon />
          Se requieren 8 plantillas de chequeo para realizar inspecciones. Cada una se califica de 0 a 10 puntos.
        </Alert>

        {/* Error Alert */}
        {error && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            {error}
          </Alert>
        )}

        {/* Templates Table */}
        <Box bg="white" borderRadius="lg" shadow="md" overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Orden</Th>
                <Th>Código</Th>
                <Th>Descripción</Th>
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
              ) : templates.length === 0 ? (
                <Tr>
                  <Td colSpan={4} textAlign="center">
                    No hay plantillas de chequeo configuradas
                  </Td>
                </Tr>
              ) : (
                templates.map((template) => (
                  <Tr key={template.id}>
                    <Td>{template.ordinal}</Td>
                    <Td fontWeight="bold">{template.code}</Td>
                    <Td>{template.description}</Td>
                    <Td>
                      <Button
                        size="sm"
                        colorScheme="blue"
                        onClick={() => handleEdit(template)}
                      >
                        Editar
                      </Button>
                    </Td>
                  </Tr>
                ))
              )}
            </Tbody>
          </Table>
        </Box>

        {templates.length > 0 && (
          <Text fontSize="sm" color="gray.600">
            Total de plantillas: {templates.length} {templates.length === 8 ? '✓' : `(se requieren 8)`}
          </Text>
        )}
      </VStack>

      {/* Create/Edit Modal */}
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {isCreateMode ? 'Crear Plantilla de Chequeo' : 'Editar Plantilla de Chequeo'}
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
                  <FormLabel>Código</FormLabel>
                  <Input
                    name="code"
                    value={formData.code}
                    onChange={handleFormChange}
                    isDisabled={formLoading}
                    placeholder="ej: BRK, LGT, TIR"
                    maxLength={10}
                  />
                  <Text fontSize="xs" color="gray.500" mt={1}>
                    Código único para identificar el ítem (se convertirá a mayúsculas)
                  </Text>
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Descripción</FormLabel>
                  <Textarea
                    name="description"
                    value={formData.description}
                    onChange={handleFormChange}
                    isDisabled={formLoading}
                    placeholder="ej: Frenos y sistema de frenado"
                    maxLength={200}
                    rows={3}
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Orden (1-8)</FormLabel>
                  <Select
                    name="ordinal"
                    value={formData.ordinal}
                    onChange={handleFormChange}
                    isDisabled={formLoading}
                  >
                    {[1, 2, 3, 4, 5, 6, 7, 8].map((num) => (
                      <option key={num} value={num}>
                        {num}
                      </option>
                    ))}
                  </Select>
                  <Text fontSize="xs" color="gray.500" mt={1}>
                    Orden de presentación en la inspección
                  </Text>
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

export default CheckItemManagementPage
