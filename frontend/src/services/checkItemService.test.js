/**
 * Tests for checkItemService
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { checkItemService } from './checkItemService'
import api from './api'

vi.mock('./api')

describe('checkItemService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should list all check item templates', async () => {
    const mockTemplates = [
      { id: '1', code: 'BRK', description: 'Frenos', ordinal: 1 },
      { id: '2', code: 'LGT', description: 'Luces', ordinal: 2 }
    ]
    api.get.mockResolvedValue({ data: mockTemplates })

    const result = await checkItemService.listTemplates()

    expect(api.get).toHaveBeenCalledWith('/check-items')
    expect(result).toEqual(mockTemplates)
  })

  it('should get check item template by id', async () => {
    const mockTemplate = { id: '1', code: 'BRK', description: 'Frenos', ordinal: 1 }
    api.get.mockResolvedValue({ data: mockTemplate })

    const result = await checkItemService.getTemplate('1')

    expect(api.get).toHaveBeenCalledWith('/check-items/1')
    expect(result).toEqual(mockTemplate)
  })

  it('should create check item template', async () => {
    const templateData = { code: 'TIR', description: 'Neumáticos', ordinal: 3 }
    const mockTemplate = { id: '3', ...templateData }
    api.post.mockResolvedValue({ data: mockTemplate })

    const result = await checkItemService.createTemplate(templateData)

    expect(api.post).toHaveBeenCalledWith('/check-items', templateData)
    expect(result).toEqual(mockTemplate)
  })

  it('should update check item template', async () => {
    const templateData = { code: 'BRK', description: 'Frenos actualizados', ordinal: 1 }
    const mockTemplate = { id: '1', ...templateData }
    api.put.mockResolvedValue({ data: mockTemplate })

    const result = await checkItemService.updateTemplate('1', templateData)

    expect(api.put).toHaveBeenCalledWith('/check-items/1', templateData)
    expect(result).toEqual(mockTemplate)
  })
})
