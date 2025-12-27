import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { blockRegistry, blockCategories } from './index'
import type { LibraryBlockDefinition } from '../types/library'
import type { BlockCategory } from '../types/block'

// Helper to create a mock library block definition
function createMockLibraryBlock(overrides: Partial<LibraryBlockDefinition> = {}): LibraryBlockDefinition {
  return {
    type: 'mock_library_block',
    name: 'Mock Library Block',
    category: 'sources' as BlockCategory,
    description: 'A mock library block for testing',
    inputs: [],
    outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
    parameters: [],
    isLibraryBlock: true,
    libraryId: 'mock-library-id',
    libraryName: 'Mock Library',
    originalName: 'MockBlock',
    implementation: {
      blocks: [],
      connections: [],
      portMappings: [],
    },
    ...overrides,
  }
}

describe('blockRegistry', () => {
  // Clean up library blocks after each test
  afterEach(() => {
    blockRegistry.clearLibraryBlocks()
  })

  describe('built-in blocks', () => {
    it('has all built-in blocks registered', () => {
      // Check that common built-in blocks exist
      expect(blockRegistry.has('constant')).toBe(true)
      expect(blockRegistry.has('scope')).toBe(true)
      expect(blockRegistry.has('integrator')).toBe(true)
      expect(blockRegistry.has('sum')).toBe(true)
      expect(blockRegistry.has('gain')).toBe(true)
      expect(blockRegistry.has('subsystem')).toBe(true)
    })

    it('returns undefined for non-existent blocks', () => {
      expect(blockRegistry.get('non_existent_block')).toBeUndefined()
    })

    it('gets a block definition by type', () => {
      const constant = blockRegistry.get('constant')
      expect(constant).toBeDefined()
      expect(constant?.type).toBe('constant')
      expect(constant?.name).toBe('Constant')
      expect(constant?.category).toBe('sources')
    })

    it('returns all built-in blocks', () => {
      const allBlocks = blockRegistry.getAll()
      expect(allBlocks.length).toBeGreaterThan(0)

      // Check that common blocks are included
      const types = allBlocks.map(b => b.type)
      expect(types).toContain('constant')
      expect(types).toContain('scope')
      expect(types).toContain('integrator')
    })

    it('filters blocks by category', () => {
      const sourceBlocks = blockRegistry.getByCategory('sources')
      expect(sourceBlocks.length).toBeGreaterThan(0)
      sourceBlocks.forEach(block => {
        expect(block.category).toBe('sources')
      })

      const sinkBlocks = blockRegistry.getByCategory('sinks')
      expect(sinkBlocks.length).toBeGreaterThan(0)
      sinkBlocks.forEach(block => {
        expect(block.category).toBe('sinks')
      })
    })

    it('has blocks for all categories', () => {
      for (const category of blockCategories) {
        const blocks = blockRegistry.getByCategory(category)
        expect(blocks.length).toBeGreaterThan(0)
      }
    })
  })

  describe('library blocks', () => {
    it('registers a library block', () => {
      const libraryBlock = createMockLibraryBlock()
      blockRegistry.registerLibraryBlock(libraryBlock)

      expect(blockRegistry.has('mock_library_block')).toBe(true)
      expect(blockRegistry.isLibraryBlock('mock_library_block')).toBe(true)
    })

    it('gets a library block definition', () => {
      const libraryBlock = createMockLibraryBlock()
      blockRegistry.registerLibraryBlock(libraryBlock)

      const retrieved = blockRegistry.get('mock_library_block')
      expect(retrieved).toBeDefined()
      expect(retrieved?.type).toBe('mock_library_block')
      expect(retrieved?.name).toBe('Mock Library Block')
    })

    it('registers multiple library blocks', () => {
      const blocks = [
        createMockLibraryBlock({ type: 'lib_block_1', name: 'Block 1' }),
        createMockLibraryBlock({ type: 'lib_block_2', name: 'Block 2' }),
        createMockLibraryBlock({ type: 'lib_block_3', name: 'Block 3' }),
      ]

      blockRegistry.registerLibraryBlocks(blocks)

      expect(blockRegistry.has('lib_block_1')).toBe(true)
      expect(blockRegistry.has('lib_block_2')).toBe(true)
      expect(blockRegistry.has('lib_block_3')).toBe(true)
    })

    it('unregisters a library block', () => {
      const libraryBlock = createMockLibraryBlock()
      blockRegistry.registerLibraryBlock(libraryBlock)

      expect(blockRegistry.has('mock_library_block')).toBe(true)

      blockRegistry.unregisterLibraryBlock('mock_library_block')

      expect(blockRegistry.has('mock_library_block')).toBe(false)
    })

    it('unregisters all blocks from a library', () => {
      const libraryId = 'test-library-id'
      const blocks = [
        createMockLibraryBlock({ type: 'lib_block_1', libraryId }),
        createMockLibraryBlock({ type: 'lib_block_2', libraryId }),
        createMockLibraryBlock({ type: 'lib_block_3', libraryId: 'other-library' }),
      ]

      blockRegistry.registerLibraryBlocks(blocks)

      blockRegistry.unregisterLibrary(libraryId)

      expect(blockRegistry.has('lib_block_1')).toBe(false)
      expect(blockRegistry.has('lib_block_2')).toBe(false)
      expect(blockRegistry.has('lib_block_3')).toBe(true) // Different library, still exists
    })

    it('gets all library blocks', () => {
      const blocks = [
        createMockLibraryBlock({ type: 'lib_block_1' }),
        createMockLibraryBlock({ type: 'lib_block_2' }),
      ]

      blockRegistry.registerLibraryBlocks(blocks)

      const libraryBlocks = blockRegistry.getLibraryBlocks()
      expect(libraryBlocks).toHaveLength(2)
    })

    it('gets blocks by library ID', () => {
      const libraryId = 'specific-library'
      const blocks = [
        createMockLibraryBlock({ type: 'lib_block_1', libraryId }),
        createMockLibraryBlock({ type: 'lib_block_2', libraryId }),
        createMockLibraryBlock({ type: 'lib_block_3', libraryId: 'other-library' }),
      ]

      blockRegistry.registerLibraryBlocks(blocks)

      const libraryBlocks = blockRegistry.getBlocksByLibrary(libraryId)
      expect(libraryBlocks).toHaveLength(2)
      libraryBlocks.forEach(b => {
        expect(b.libraryId).toBe(libraryId)
      })
    })

    it('includes library blocks in getAllWithLibrary', () => {
      const libraryBlock = createMockLibraryBlock()
      blockRegistry.registerLibraryBlock(libraryBlock)

      const allBlocks = blockRegistry.getAllWithLibrary()
      const types = allBlocks.map(b => b.type)

      expect(types).toContain('constant') // Built-in
      expect(types).toContain('mock_library_block') // Library
    })

    it('does not include library blocks in getAll', () => {
      const libraryBlock = createMockLibraryBlock()
      blockRegistry.registerLibraryBlock(libraryBlock)

      const builtInBlocks = blockRegistry.getAll()
      const types = builtInBlocks.map(b => b.type)

      expect(types).toContain('constant') // Built-in
      expect(types).not.toContain('mock_library_block') // Should not include library blocks
    })

    it('clears all library blocks', () => {
      const blocks = [
        createMockLibraryBlock({ type: 'lib_block_1' }),
        createMockLibraryBlock({ type: 'lib_block_2' }),
      ]

      blockRegistry.registerLibraryBlocks(blocks)
      expect(blockRegistry.getLibraryBlocks()).toHaveLength(2)

      blockRegistry.clearLibraryBlocks()
      expect(blockRegistry.getLibraryBlocks()).toHaveLength(0)
    })

    it('built-in blocks are not considered library blocks', () => {
      expect(blockRegistry.isLibraryBlock('constant')).toBe(false)
      expect(blockRegistry.isLibraryBlock('scope')).toBe(false)
      expect(blockRegistry.isLibraryBlock('integrator')).toBe(false)
    })
  })

  describe('subscription', () => {
    it('notifies listeners when library block is registered', () => {
      const listener = vi.fn()
      const unsubscribe = blockRegistry.subscribe(listener)

      const libraryBlock = createMockLibraryBlock()
      blockRegistry.registerLibraryBlock(libraryBlock)

      expect(listener).toHaveBeenCalled()

      unsubscribe()
    })

    it('notifies listeners when library blocks are unregistered', () => {
      const libraryBlock = createMockLibraryBlock()
      blockRegistry.registerLibraryBlock(libraryBlock)

      const listener = vi.fn()
      const unsubscribe = blockRegistry.subscribe(listener)

      blockRegistry.unregisterLibraryBlock('mock_library_block')

      expect(listener).toHaveBeenCalled()

      unsubscribe()
    })

    it('notifies listeners when library is unregistered', () => {
      const libraryBlock = createMockLibraryBlock()
      blockRegistry.registerLibraryBlock(libraryBlock)

      const listener = vi.fn()
      const unsubscribe = blockRegistry.subscribe(listener)

      blockRegistry.unregisterLibrary('mock-library-id')

      expect(listener).toHaveBeenCalled()

      unsubscribe()
    })

    it('notifies listeners when library blocks are cleared', () => {
      const libraryBlock = createMockLibraryBlock()
      blockRegistry.registerLibraryBlock(libraryBlock)

      const listener = vi.fn()
      const unsubscribe = blockRegistry.subscribe(listener)

      blockRegistry.clearLibraryBlocks()

      expect(listener).toHaveBeenCalled()

      unsubscribe()
    })

    it('stops notifying after unsubscribe', () => {
      const listener = vi.fn()
      const unsubscribe = blockRegistry.subscribe(listener)

      unsubscribe()

      const libraryBlock = createMockLibraryBlock()
      blockRegistry.registerLibraryBlock(libraryBlock)

      expect(listener).not.toHaveBeenCalled()
    })

    it('returns stable reference for getLibraryBlocks after changes', () => {
      // First registration
      blockRegistry.registerLibraryBlock(createMockLibraryBlock({ type: 'block_1' }))
      const ref1 = blockRegistry.getLibraryBlocks()

      // Second registration should create new reference
      blockRegistry.registerLibraryBlock(createMockLibraryBlock({ type: 'block_2' }))
      const ref2 = blockRegistry.getLibraryBlocks()

      // References should be different (new array after each notify)
      expect(ref1).not.toBe(ref2)
      expect(ref1).toHaveLength(1)
      expect(ref2).toHaveLength(2)
    })
  })
})

describe('blockCategories', () => {
  it('contains all expected categories', () => {
    const expectedCategories: BlockCategory[] = [
      'sources',
      'sinks',
      'continuous',
      'discrete',
      'math',
      'routing',
      'subsystems',
      'signal_processing',
      'nonlinear',
      'observers',
      'control_analysis',
    ]

    expect(blockCategories).toEqual(expectedCategories)
  })

  it('has correct number of categories', () => {
    expect(blockCategories).toHaveLength(11)
  })
})

// Import vi here since we use it in the subscription tests
import { vi } from 'vitest'
