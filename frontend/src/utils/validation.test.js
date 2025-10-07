/**
 * Tests for validation.js utility
 *
 * Tests the getApiErrorMessage function which extracts error messages
 * from API responses in different formats.
 */

import { describe, it, expect } from 'vitest'
import { getApiErrorMessage } from './validation'

describe('getApiErrorMessage', () => {
  it('should extract simple string error from API response', () => {
    const error = {
      response: {
        data: {
          detail: 'Invalid credentials'
        }
      }
    }

    expect(getApiErrorMessage(error)).toBe('Invalid credentials')
  })

  it('should extract error from validation array with field names', () => {
    const error = {
      response: {
        data: {
          detail: [
            {
              loc: ['body', 'password'],
              msg: 'String should have at least 6 characters'
            }
          ]
        }
      }
    }

    expect(getApiErrorMessage(error)).toBe('Password: String should have at least 6 characters')
  })

  it('should extract multiple validation errors', () => {
    const error = {
      response: {
        data: {
          detail: [
            {
              loc: ['body', 'email'],
              msg: 'Invalid email format'
            },
            {
              loc: ['body', 'password'],
              msg: 'String should have at least 6 characters'
            }
          ]
        }
      }
    }

    expect(getApiErrorMessage(error)).toBe('Email: Invalid email format, Password: String should have at least 6 characters')
  })

  it('should handle validation errors without loc field', () => {
    const error = {
      response: {
        data: {
          detail: [
            {
              msg: 'Validation error'
            }
          ]
        }
      }
    }

    expect(getApiErrorMessage(error)).toBe('Validation error')
  })

  it('should return status-based message for 400 error', () => {
    const error = {
      response: {
        status: 400,
        data: {}
      }
    }

    expect(getApiErrorMessage(error)).toBe('Datos inválidos')
  })

  it('should return status-based message for 401 error', () => {
    const error = {
      response: {
        status: 401,
        data: {}
      }
    }

    expect(getApiErrorMessage(error)).toBe('No autorizado')
  })

  it('should return status-based message for 422 error', () => {
    const error = {
      response: {
        status: 422,
        data: {}
      }
    }

    expect(getApiErrorMessage(error)).toBe('Error de validación')
  })

  it('should return default message for network error', () => {
    const error = {
      message: 'Network Error'
    }

    expect(getApiErrorMessage(error)).toBe('Error en la conexión con el servidor')
  })

  it('should capitalize field name correctly', () => {
    const error = {
      response: {
        data: {
          detail: [
            {
              loc: ['body', 'name'],
              msg: 'Field is required'
            }
          ]
        }
      }
    }

    expect(getApiErrorMessage(error)).toBe('Name: Field is required')
  })
})
