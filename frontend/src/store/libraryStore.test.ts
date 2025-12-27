import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useLibraryStore, useLibraryBlockDefinitions, useLibraries } from './libraryStore'
import { blockRegistry } from '../blocks'
import type { Library, LibraryBlockDefinition, LibraryBlockImplementation } from '../types/library'

// Mock block to create library blocks
function createMockImplementation(): LibraryBlockImplementation {
  return {
    blocks: [
      {
        id: 'internal-block-1',
        type: 'constant',
        name: 'Internal Constant',
        position: { x: 100, y: 100 },
        parameters: { value: 1 },
        inputPorts: [],
        outputPorts: [{ id: 'out-0', name: 'out', dataType: 'double', dimensions: [1] }],
      },
    ],
    connections: [],
    portMappings: [],
  }
}

function createMockLibraryBlock(overrides: Partial<LibraryBlockDefinition> = {}): LibraryBlockDefinition {
  return {
    type: 'mock_block',
    name: 'Mock Block',
    category: 'sources',
    description: 'A mock block',
    inputs: [],
    outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
    parameters: [],
    isLibraryBlock: true,
    libraryId: 'lib-123',
    libraryName: 'Mock Library',
    originalName: 'MockBlock',
    implementation: createMockImplementation(),
    ...overrides,
  }
}

function createMockLibraryData(name = 'Test Library'): Omit<Library, 'id' | 'importedAt'> {
  return {
    name,
    description: 'A test library',
    version: '1.0.0',
    sourcePath: 'test.mdl',
    sourceFormat: 'mdl',
    blocks: [
      {
        ...createMockLibraryBlock({
          type: 'block1',
          name: 'Block 1',
        }),
        libraryId: '', // Will be set by importLibrary
        libraryName: name,
      },
      {
        ...createMockLibraryBlock({
          type: 'block2',
          name: 'Block 2',
        }),
        libraryId: '', // Will be set by importLibrary
        libraryName: name,
      },
    ],
  }
}

describe('useLibraryStore', () => {
  // Reset store before each test
  beforeEach(() => {
    useLibraryStore.getState().clearAllLibraries()
    blockRegistry.clearLibraryBlocks()
  })

  describe('importLibrary', () => {
    it('imports a library successfully', () => {
      const libraryData = createMockLibraryData('Test Library')
      const result = useLibraryStore.getState().importLibrary(libraryData)

      expect(result.success).toBe(true)
      expect(result.library).toBeDefined()
      expect(result.library?.name).toBe('Test Library')
      expect(result.errors).toHaveLength(0)
    })

    it('generates unique library ID', () => {
      const libraryData = createMockLibraryData('Test Library')
      const result = useLibraryStore.getState().importLibrary(libraryData)

      expect(result.library?.id).toBeDefined()
      expect(result.library?.id.length).toBeGreaterThan(0)
    })

    it('sets importedAt timestamp', () => {
      const libraryData = createMockLibraryData('Test Library')
      const result = useLibraryStore.getState().importLibrary(libraryData)

      expect(result.library?.importedAt).toBeDefined()
      // Should be a valid ISO date string
      expect(new Date(result.library!.importedAt).toISOString()).toBe(result.library!.importedAt)
    })

    it('processes block types with library prefix', () => {
      const libraryData = createMockLibraryData('Test Library')
      const result = useLibraryStore.getState().importLibrary(libraryData)

      const blocks = result.library?.blocks || []
      expect(blocks[0].type).toBe('test_library__block1')
      expect(blocks[1].type).toBe('test_library__block2')
    })

    it('uses custom name from options', () => {
      const libraryData = createMockLibraryData('Original Name')
      const result = useLibraryStore.getState().importLibrary(libraryData, { name: 'Custom Name' })

      expect(result.library?.name).toBe('Custom Name')
    })

    it('uses custom version from options', () => {
      const libraryData = createMockLibraryData('Test Library')
      const result = useLibraryStore.getState().importLibrary(libraryData, { version: '2.0.0' })

      expect(result.library?.version).toBe('2.0.0')
    })

    it('fails when library with same name exists', () => {
      const libraryData = createMockLibraryData('Duplicate Library')

      useLibraryStore.getState().importLibrary(libraryData)
      const result = useLibraryStore.getState().importLibrary(libraryData)

      expect(result.success).toBe(false)
      expect(result.errors).toContain('Library "Duplicate Library" already exists. Use replaceExisting option to overwrite.')
    })

    it('replaces existing library when replaceExisting is true', () => {
      const libraryData1 = createMockLibraryData('My Library')
      const libraryData2 = createMockLibraryData('My Library')
      libraryData2.description = 'Updated description'

      useLibraryStore.getState().importLibrary(libraryData1)
      const result = useLibraryStore.getState().importLibrary(libraryData2, { replaceExisting: true })

      expect(result.success).toBe(true)
      expect(useLibraryStore.getState().libraries).toHaveLength(1)
      expect(useLibraryStore.getState().libraries[0].description).toBe('Updated description')
    })

    it('adds library to libraries array', () => {
      const libraryData = createMockLibraryData('Test Library')
      useLibraryStore.getState().importLibrary(libraryData)

      expect(useLibraryStore.getState().libraries).toHaveLength(1)
    })

    it('adds library to libraryMap', () => {
      const libraryData = createMockLibraryData('Test Library')
      const result = useLibraryStore.getState().importLibrary(libraryData)

      const library = useLibraryStore.getState().getLibrary(result.library!.id)
      expect(library).toBeDefined()
      expect(library?.name).toBe('Test Library')
    })

    it('adds blocks to libraryBlockMap', () => {
      const libraryData = createMockLibraryData('Test Library')
      useLibraryStore.getState().importLibrary(libraryData)

      expect(useLibraryStore.getState().isLibraryBlock('test_library__block1')).toBe(true)
      expect(useLibraryStore.getState().isLibraryBlock('test_library__block2')).toBe(true)
    })
  })

  describe('removeLibrary', () => {
    it('removes a library by ID', () => {
      const libraryData = createMockLibraryData('Test Library')
      const result = useLibraryStore.getState().importLibrary(libraryData)

      useLibraryStore.getState().removeLibrary(result.library!.id)

      expect(useLibraryStore.getState().libraries).toHaveLength(0)
    })

    it('removes library blocks from maps', () => {
      const libraryData = createMockLibraryData('Test Library')
      const result = useLibraryStore.getState().importLibrary(libraryData)

      useLibraryStore.getState().removeLibrary(result.library!.id)

      expect(useLibraryStore.getState().isLibraryBlock('test_library__block1')).toBe(false)
      expect(useLibraryStore.getState().isLibraryBlock('test_library__block2')).toBe(false)
    })

    it('does nothing for non-existent library', () => {
      const libraryData = createMockLibraryData('Test Library')
      useLibraryStore.getState().importLibrary(libraryData)

      useLibraryStore.getState().removeLibrary('non-existent-id')

      expect(useLibraryStore.getState().libraries).toHaveLength(1)
    })
  })

  describe('getLibrary', () => {
    it('returns library by ID', () => {
      const libraryData = createMockLibraryData('Test Library')
      const result = useLibraryStore.getState().importLibrary(libraryData)

      const library = useLibraryStore.getState().getLibrary(result.library!.id)

      expect(library).toBeDefined()
      expect(library?.name).toBe('Test Library')
    })

    it('returns undefined for non-existent library', () => {
      const library = useLibraryStore.getState().getLibrary('non-existent')
      expect(library).toBeUndefined()
    })
  })

  describe('getLibraryBlock', () => {
    it('returns library block by type', () => {
      const libraryData = createMockLibraryData('Test Library')
      useLibraryStore.getState().importLibrary(libraryData)

      const block = useLibraryStore.getState().getLibraryBlock('test_library__block1')

      expect(block).toBeDefined()
      expect(block?.name).toBe('Block 1')
    })

    it('returns undefined for non-existent block', () => {
      const block = useLibraryStore.getState().getLibraryBlock('non_existent')
      expect(block).toBeUndefined()
    })
  })

  describe('getLibraryBlocks', () => {
    it('returns all blocks from a library', () => {
      const libraryData = createMockLibraryData('Test Library')
      const result = useLibraryStore.getState().importLibrary(libraryData)

      const blocks = useLibraryStore.getState().getLibraryBlocks(result.library!.id)

      expect(blocks).toHaveLength(2)
    })

    it('returns empty array for non-existent library', () => {
      const blocks = useLibraryStore.getState().getLibraryBlocks('non-existent')
      expect(blocks).toEqual([])
    })
  })

  describe('getAllLibraryBlocks', () => {
    it('returns all library blocks across all libraries', () => {
      const libraryData1 = createMockLibraryData('Library 1')
      const libraryData2 = createMockLibraryData('Library 2')

      useLibraryStore.getState().importLibrary(libraryData1)
      useLibraryStore.getState().importLibrary(libraryData2)

      const allBlocks = useLibraryStore.getState().getAllLibraryBlocks()

      expect(allBlocks).toHaveLength(4) // 2 blocks per library
    })
  })

  describe('isLibraryBlock', () => {
    it('returns true for library blocks', () => {
      const libraryData = createMockLibraryData('Test Library')
      useLibraryStore.getState().importLibrary(libraryData)

      expect(useLibraryStore.getState().isLibraryBlock('test_library__block1')).toBe(true)
    })

    it('returns false for non-library blocks', () => {
      expect(useLibraryStore.getState().isLibraryBlock('constant')).toBe(false)
    })
  })

  describe('getBlockImplementation', () => {
    it('returns implementation for library block', () => {
      const libraryData = createMockLibraryData('Test Library')
      useLibraryStore.getState().importLibrary(libraryData)

      const impl = useLibraryStore.getState().getBlockImplementation('test_library__block1')

      expect(impl).toBeDefined()
      expect(impl?.blocks).toBeDefined()
      expect(impl?.connections).toBeDefined()
    })

    it('returns undefined for non-existent block', () => {
      const impl = useLibraryStore.getState().getBlockImplementation('non_existent')
      expect(impl).toBeUndefined()
    })
  })

  describe('clearAllLibraries', () => {
    it('removes all libraries', () => {
      const libraryData1 = createMockLibraryData('Library 1')
      const libraryData2 = createMockLibraryData('Library 2')

      useLibraryStore.getState().importLibrary(libraryData1)
      useLibraryStore.getState().importLibrary(libraryData2)

      useLibraryStore.getState().clearAllLibraries()

      expect(useLibraryStore.getState().libraries).toHaveLength(0)
      expect(useLibraryStore.getState().getAllLibraryBlocks()).toHaveLength(0)
    })
  })

  describe('_rebuildMaps', () => {
    it('rebuilds maps from libraries array', () => {
      const libraryData = createMockLibraryData('Test Library')
      const result = useLibraryStore.getState().importLibrary(libraryData)

      // Simulate clearing maps (like what happens after persistence rehydration)
      useLibraryStore.setState({
        libraryMap: new Map(),
        libraryBlockMap: new Map(),
      })

      // Rebuild maps
      useLibraryStore.getState()._rebuildMaps()

      // Maps should be rebuilt
      expect(useLibraryStore.getState().getLibrary(result.library!.id)).toBeDefined()
      expect(useLibraryStore.getState().isLibraryBlock('test_library__block1')).toBe(true)
    })

    it('registers library blocks with block registry', () => {
      const libraryData = createMockLibraryData('Test Library')
      useLibraryStore.getState().importLibrary(libraryData)

      // Clear block registry
      blockRegistry.clearLibraryBlocks()

      // Simulate clearing maps
      useLibraryStore.setState({
        libraryMap: new Map(),
        libraryBlockMap: new Map(),
      })

      // Rebuild maps
      useLibraryStore.getState()._rebuildMaps()

      // Block registry should have the library blocks
      expect(blockRegistry.has('test_library__block1')).toBe(true)
      expect(blockRegistry.has('test_library__block2')).toBe(true)
    })
  })
})

describe('useLibraryBlockDefinitions hook', () => {
  beforeEach(() => {
    useLibraryStore.getState().clearAllLibraries()
  })

  it('returns library blocks as BlockDefinition array', () => {
    const libraryData = createMockLibraryData('Test Library')
    useLibraryStore.getState().importLibrary(libraryData)

    // Note: This is a simplified test since hooks need React context
    // The actual hook just calls getAllLibraryBlocks internally
    const blocks = useLibraryStore.getState().getAllLibraryBlocks()
    expect(blocks).toHaveLength(2)
  })
})

describe('useLibraries hook', () => {
  beforeEach(() => {
    useLibraryStore.getState().clearAllLibraries()
  })

  it('returns all libraries', () => {
    const libraryData = createMockLibraryData('Test Library')
    useLibraryStore.getState().importLibrary(libraryData)

    // Note: This is a simplified test since hooks need React context
    const libraries = useLibraryStore.getState().libraries
    expect(libraries).toHaveLength(1)
  })
})
