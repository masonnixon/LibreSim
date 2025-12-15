import type { BlockDefinition, BlockCategory } from '../types/block'
import type { LibraryBlockDefinition } from '../types/library'
import { sourceBlocks } from './sources'
import { sinkBlocks } from './sinks'
import { continuousBlocks } from './continuous'
import { discreteBlocks } from './discrete'
import { mathBlocks } from './math'
import { routingBlocks } from './routing'
import { subsystemBlocks } from './subsystems'
import { signalProcessingBlocks } from './signal_processing'
import { nonlinearBlocks } from './nonlinear'
import { observerBlocks } from './observers'

// All built-in block definitions
const builtInBlocks: BlockDefinition[] = [
  ...sourceBlocks,
  ...sinkBlocks,
  ...continuousBlocks,
  ...discreteBlocks,
  ...mathBlocks,
  ...routingBlocks,
  ...subsystemBlocks,
  ...signalProcessingBlocks,
  ...nonlinearBlocks,
  ...observerBlocks,
]

// Block registry for quick lookup - supports dynamic addition of library blocks
class BlockRegistry {
  private blocks: Map<string, BlockDefinition>
  private libraryBlocks: Map<string, LibraryBlockDefinition>
  private listeners: Set<() => void>

  constructor(definitions: BlockDefinition[]) {
    this.blocks = new Map()
    this.libraryBlocks = new Map()
    this.listeners = new Set()
    definitions.forEach((def) => {
      this.blocks.set(def.type, def)
    })
  }

  /**
   * Get a block definition by type (checks both built-in and library blocks)
   */
  get(type: string): BlockDefinition | undefined {
    return this.blocks.get(type) || this.libraryBlocks.get(type)
  }

  /**
   * Get all block definitions (built-in only, not library blocks)
   */
  getAll(): BlockDefinition[] {
    return Array.from(this.blocks.values())
  }

  /**
   * Get all block definitions including library blocks
   */
  getAllWithLibrary(): BlockDefinition[] {
    return [...Array.from(this.blocks.values()), ...Array.from(this.libraryBlocks.values())]
  }

  /**
   * Get blocks by category (built-in only)
   */
  getByCategory(category: BlockCategory): BlockDefinition[] {
    return this.getAll().filter((def) => def.category === category)
  }

  /**
   * Check if a block type exists (built-in or library)
   */
  has(type: string): boolean {
    return this.blocks.has(type) || this.libraryBlocks.has(type)
  }

  /**
   * Check if a block type is from a library
   */
  isLibraryBlock(type: string): boolean {
    return this.libraryBlocks.has(type)
  }

  /**
   * Register a library block definition
   */
  registerLibraryBlock(definition: LibraryBlockDefinition): void {
    this.libraryBlocks.set(definition.type, definition)
    this.notifyListeners()
  }

  /**
   * Register multiple library block definitions
   */
  registerLibraryBlocks(definitions: LibraryBlockDefinition[]): void {
    definitions.forEach((def) => {
      this.libraryBlocks.set(def.type, def)
    })
    this.notifyListeners()
  }

  /**
   * Unregister a library block by type
   */
  unregisterLibraryBlock(type: string): void {
    this.libraryBlocks.delete(type)
    this.notifyListeners()
  }

  /**
   * Unregister all blocks from a specific library
   */
  unregisterLibrary(libraryId: string): void {
    for (const [type, def] of this.libraryBlocks.entries()) {
      if (def.libraryId === libraryId) {
        this.libraryBlocks.delete(type)
      }
    }
    this.notifyListeners()
  }

  /**
   * Get all library blocks
   */
  getLibraryBlocks(): LibraryBlockDefinition[] {
    return Array.from(this.libraryBlocks.values())
  }

  /**
   * Get library blocks by library ID
   */
  getBlocksByLibrary(libraryId: string): LibraryBlockDefinition[] {
    return Array.from(this.libraryBlocks.values()).filter(
      (def) => def.libraryId === libraryId
    )
  }

  /**
   * Subscribe to registry changes (for UI updates)
   */
  subscribe(listener: () => void): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private notifyListeners(): void {
    this.listeners.forEach((listener) => listener())
  }

  /**
   * Clear all library blocks (useful for testing or resetting)
   */
  clearLibraryBlocks(): void {
    this.libraryBlocks.clear()
    this.notifyListeners()
  }
}

export const blockRegistry = new BlockRegistry(builtInBlocks)

export const blockCategories: BlockCategory[] = [
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
]

export { sourceBlocks } from './sources'
export { sinkBlocks } from './sinks'
export { continuousBlocks } from './continuous'
export { discreteBlocks } from './discrete'
export { mathBlocks } from './math'
export { routingBlocks } from './routing'
export { subsystemBlocks } from './subsystems'
export { signalProcessingBlocks } from './signal_processing'
export { nonlinearBlocks } from './nonlinear'
export { observerBlocks } from './observers'
