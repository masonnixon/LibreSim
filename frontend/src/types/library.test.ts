import { describe, it, expect } from 'vitest'
import {
  isLibraryBlockDefinition,
  isLibraryBlockReference,
} from './library'
import type {
  BlockDefinition,
  BlockInstance,
} from './block'
import type { LibraryBlockDefinition, LibraryBlockReference } from './library'

describe('isLibraryBlockDefinition', () => {
  it('returns true for a library block definition', () => {
    const libraryBlock: LibraryBlockDefinition = {
      type: 'library_block',
      name: 'Library Block',
      category: 'sources',
      description: 'A library block',
      inputs: [],
      outputs: [],
      parameters: [],
      isLibraryBlock: true,
      libraryId: 'lib-123',
      libraryName: 'Test Library',
      originalName: 'OriginalBlock',
      implementation: {
        blocks: [],
        connections: [],
        portMappings: [],
      },
    }

    expect(isLibraryBlockDefinition(libraryBlock)).toBe(true)
  })

  it('returns false for a regular block definition', () => {
    const regularBlock: BlockDefinition = {
      type: 'constant',
      name: 'Constant',
      category: 'sources',
      description: 'A constant value',
      inputs: [],
      outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
      parameters: [{ name: 'value', label: 'Value', type: 'number', default: 0 }],
    }

    expect(isLibraryBlockDefinition(regularBlock)).toBe(false)
  })

  it('returns false when isLibraryBlock is false', () => {
    const block = {
      type: 'block',
      name: 'Block',
      category: 'sources',
      description: 'A block',
      inputs: [],
      outputs: [],
      parameters: [],
      isLibraryBlock: false, // Explicitly false
    } as BlockDefinition

    expect(isLibraryBlockDefinition(block)).toBe(false)
  })

  it('returns false when isLibraryBlock property is missing', () => {
    const block: BlockDefinition = {
      type: 'block',
      name: 'Block',
      category: 'sources',
      description: 'A block',
      inputs: [],
      outputs: [],
      parameters: [],
    }

    expect(isLibraryBlockDefinition(block)).toBe(false)
  })
})

describe('isLibraryBlockReference', () => {
  it('returns true for a library block reference', () => {
    const libraryRef: LibraryBlockReference = {
      id: 'block-123',
      type: 'library_block',
      name: 'Library Block Instance',
      position: { x: 100, y: 100 },
      parameters: {},
      inputPorts: [],
      outputPorts: [],
      isLibraryReference: true,
      libraryId: 'lib-123',
      libraryBlockType: 'original_block_type',
    }

    expect(isLibraryBlockReference(libraryRef)).toBe(true)
  })

  it('returns false for a regular block instance', () => {
    const regularBlock: BlockInstance = {
      id: 'block-123',
      type: 'constant',
      name: 'Constant1',
      position: { x: 100, y: 100 },
      parameters: { value: 5 },
      inputPorts: [],
      outputPorts: [{ id: 'out-0', name: 'out', dataType: 'double', dimensions: [1] }],
    }

    expect(isLibraryBlockReference(regularBlock)).toBe(false)
  })

  it('returns false when isLibraryReference is false', () => {
    const block = {
      id: 'block-123',
      type: 'block',
      name: 'Block',
      position: { x: 100, y: 100 },
      parameters: {},
      inputPorts: [],
      outputPorts: [],
      isLibraryReference: false, // Explicitly false
    } as BlockInstance

    expect(isLibraryBlockReference(block)).toBe(false)
  })

  it('returns false when isLibraryReference property is missing', () => {
    const block: BlockInstance = {
      id: 'block-123',
      type: 'block',
      name: 'Block',
      position: { x: 100, y: 100 },
      parameters: {},
      inputPorts: [],
      outputPorts: [],
    }

    expect(isLibraryBlockReference(block)).toBe(false)
  })
})
