import type { BlockDefinition, BlockInstance, Connection, Port } from './block'

/**
 * A library is a collection of reusable block definitions imported from
 * an external source (e.g., Simulink MDL library file).
 */
export interface Library {
  id: string
  name: string
  description: string
  version: string
  sourcePath?: string // Original file path (e.g., "quaternionLib.mdl")
  sourceFormat: 'mdl' | 'json' | 'native'
  importedAt: string
  blocks: LibraryBlockDefinition[]
}

/**
 * A library block definition extends the standard BlockDefinition with
 * library-specific metadata and internal implementation details.
 */
export interface LibraryBlockDefinition extends BlockDefinition {
  /** Marks this as a library block */
  isLibraryBlock: true
  /** Reference to the source library */
  libraryId: string
  /** Human-readable library name */
  libraryName: string
  /** Original block name from the library (may differ from display name) */
  originalName: string
  /** Internal implementation - the blocks inside this library block */
  implementation: LibraryBlockImplementation
}

/**
 * The internal implementation of a library block.
 * This is the "expanded" form that gets used during simulation.
 */
export interface LibraryBlockImplementation {
  /** Child blocks inside the library block */
  blocks: BlockInstance[]
  /** Connections between child blocks */
  connections: Connection[]
  /** Mapping from interface ports to internal Inport/Outport blocks */
  portMappings: LibraryPortMapping[]
}

/**
 * Maps an external port (on the library block interface) to an internal
 * Inport or Outport block within the implementation.
 */
export interface LibraryPortMapping {
  /** Port on the library block's external interface */
  externalPort: Omit<Port, 'id'>
  /** ID of the internal Inport/Outport block */
  internalBlockId: string
  /** Port number parameter of the Inport/Outport block */
  portNumber: number
  /** Direction: 'input' maps to Inport, 'output' maps to Outport */
  direction: 'input' | 'output'
}

/**
 * A reference to a library block placed in a model.
 * This extends BlockInstance with library-specific fields.
 */
export interface LibraryBlockReference extends BlockInstance {
  /** Marks this as a library block reference */
  isLibraryReference: true
  /** The library this block comes from */
  libraryId: string
  /** The block type within the library (for lookup) */
  libraryBlockType: string
}

/**
 * Type guard to check if a BlockDefinition is a LibraryBlockDefinition
 */
export function isLibraryBlockDefinition(
  def: BlockDefinition
): def is LibraryBlockDefinition {
  return 'isLibraryBlock' in def && def.isLibraryBlock === true
}

/**
 * Type guard to check if a BlockInstance is a LibraryBlockReference
 */
export function isLibraryBlockReference(
  block: BlockInstance
): block is LibraryBlockReference {
  return 'isLibraryReference' in block && block.isLibraryReference === true
}

/**
 * Result of importing a library file
 */
export interface LibraryImportResult {
  success: boolean
  library?: Library
  errors: string[]
  warnings: string[]
}

/**
 * Options for library import
 */
export interface LibraryImportOptions {
  /** Override library name (default: derived from filename) */
  name?: string
  /** Override library version (default: "1.0.0") */
  version?: string
  /** Whether to replace existing library with same name */
  replaceExisting?: boolean
}
