/**
 * API Error Handling Utility
 *
 * IMPORTANT: All validation is done by the backend API.
 * The frontend does NOT validate - it only displays errors from the API.
 *
 * This utility extracts error messages from API responses and formats them
 * in a user-friendly way (in Spanish).
 */

/**
 * Extract error message from Axios error object
 *
 * FastAPI returns errors in different formats:
 * - Simple string: { detail: "Error message" }
 * - Validation array: { detail: [{ loc: ["body", "field"], msg: "Error message" }] }
 *
 * @param {Object} error - Axios error object (from catch block)
 * @returns {string} User-friendly error message in Spanish
 */
export const getApiErrorMessage = (error) => {
  // Check if response has detail field (FastAPI format)
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail

    // Case 1: Detail is a simple string
    if (typeof detail === 'string') {
      return detail
    }

    // Case 2: Detail is an array of validation errors
    // Example: [{ loc: ["body", "password"], msg: "String should have at least 6 characters" }]
    if (Array.isArray(detail)) {
      // Map errors to include field name if available
      return detail.map(err => {
        const message = err.msg || err.message
        // Extract field name from loc array (usually last element)
        const field = err.loc ? err.loc[err.loc.length - 1] : null

        // If we have a field name, prepend it to the message
        if (field) {
          // Capitalize first letter of field name
          const fieldName = field.charAt(0).toUpperCase() + field.slice(1)
          return `${fieldName}: ${message}`
        }

        return message
      }).join(', ')
    }
  }

  // If no detail field, use generic messages based on HTTP status code
  const status = error.response?.status
  if (status === 400) return 'Datos inválidos'
  if (status === 401) return 'No autorizado'
  if (status === 403) return 'Acceso denegado'
  if (status === 404) return 'No encontrado'
  if (status === 422) return 'Error de validación'
  if (status === 500) return 'Error del servidor'

  // Fallback message for network errors or unknown errors
  return 'Error en la conexión con el servidor'
}
