import { create } from 'zustand'
import { nanoid } from '../utils/nanoid'
import type { BlockInstance, Connection, BlockDefinition } from '../types/block'
import type { Model, ModelMetadata } from '../types/model'
import type { SimulationConfig } from '../types/simulation'
import { isLibraryBlockDefinition } from '../types/library'
import { propagateDimensions } from '../utils/mdlImporter'
import { useUIStore } from './uiStore'

/**
 * Parse a Constant block value to determine its dimensions.
 * Supports: numbers, arrays like [1,2,3], comma-separated values like 1,2,3
 */
function parseConstantValueDimensions(value: unknown): number[] {
  if (value === null || value === undefined) {
    return [1]
  }

  // Already an array
  if (Array.isArray(value)) {
    return [value.length]
  }

  // String value - parse to determine dimensions
  if (typeof value === 'string') {
    const trimmed = value.trim()

    // Try as simple number first
    if (!isNaN(Number(trimmed)) && trimmed !== '') {
      return [1]
    }

    // Array literal: [1, 2, 3] or [1 2 3]
    if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
      const inner = trimmed.slice(1, -1).trim()
      if (inner) {
        let parts: string[]
        if (inner.includes(',')) {
          parts = inner.split(',').map(p => p.trim()).filter(p => p !== '')
        } else if (inner.includes(';')) {
          parts = inner.split(';').map(p => p.trim()).filter(p => p !== '')
        } else {
          parts = inner.split(/\s+/).filter(p => p !== '')
        }
        if (parts.length > 0 && parts.every(p => !isNaN(Number(p)))) {
          return [parts.length]
        }
      }
    }

    // Comma-separated values without brackets: 1,2,3
    if (trimmed.includes(',')) {
      const parts = trimmed.split(',').map(p => p.trim()).filter(p => p !== '')
      if (parts.length > 1 && parts.every(p => !isNaN(Number(p)))) {
        return [parts.length]
      }
    }
  }

  // Default to scalar
  return [1]
}

// Path item for subsystem navigation
interface SubsystemPathItem {
  id: string
  name: string
}

// Maximum number of undo states to keep
const MAX_HISTORY_SIZE = 50

interface ModelState {
  // Current model
  model: Model | null
  isDirty: boolean

  // Undo/Redo history
  history: Model[]
  future: Model[]

  // Subsystem navigation - path of subsystem IDs from root to current view
  currentPath: SubsystemPathItem[]

  // Selection
  selectedBlockIds: string[]
  selectedConnectionIds: string[]

  // Actions
  createNewModel: (name: string) => void
  loadModel: (model: Model) => void
  saveModel: () => Model | null

  // Block operations
  addBlock: (definition: BlockDefinition, position: { x: number; y: number }) => string
  removeBlock: (blockId: string) => void
  updateBlockPosition: (blockId: string, position: { x: number; y: number }) => void
  updateBlockParameters: (blockId: string, parameters: Record<string, unknown>) => void
  renameBlock: (blockId: string, name: string) => void
  addScopeInput: (blockId: string) => string | null // Returns the new port ID

  // Connection operations
  addConnection: (connection: Omit<Connection, 'id'>) => string | null
  removeConnection: (connectionId: string) => void

  // Selection operations
  selectBlocks: (blockIds: string[]) => void
  selectConnections: (connectionIds: string[]) => void
  clearSelection: () => void

  // Subsystem operations
  createSubsystem: (blockIds: string[], name?: string) => string | null
  expandSubsystem: (subsystemId: string) => void
  toggleSubsystemExpanded: (subsystemId: string) => void

  // Subsystem navigation
  enterSubsystem: (subsystemId: string) => void
  exitSubsystem: () => void
  navigateToPath: (pathIndex: number) => void
  getCurrentBlocks: () => BlockInstance[]
  getCurrentConnections: () => Connection[]

  // Config
  updateSimulationConfig: (config: Partial<SimulationConfig>) => void
  updateMetadata: (metadata: Partial<ModelMetadata>) => void

  // Layout operations
  spreadBlocks: (factor: number) => void
  rotateSelectedBlocks: () => void

  // Undo/Redo operations
  pushHistory: () => void
  undo: () => void
  redo: () => void
  canUndo: () => boolean
  canRedo: () => boolean
}

const defaultSimulationConfig: SimulationConfig = {
  solver: 'rk4',
  startTime: 0,
  stopTime: 10,
  stepSize: 0.01,
}

const createDefaultMetadata = (name: string): ModelMetadata => ({
  name,
  description: '',
  author: '',
  createdAt: new Date().toISOString(),
  modifiedAt: new Date().toISOString(),
  version: '1.0.0',
})

// Helper to find a block by path through nested subsystems
function findBlockAtPath(
  blocks: BlockInstance[],
  path: SubsystemPathItem[]
): { blocks: BlockInstance[]; connections: Connection[] } | null {
  if (path.length === 0) {
    return null // At root level
  }

  let currentBlocks = blocks
  let currentConnections: Connection[] = []

  for (const pathItem of path) {
    const subsystem = currentBlocks.find(b => b.id === pathItem.id && b.type === 'subsystem')
    if (!subsystem || !subsystem.children) {
      return null
    }
    currentBlocks = subsystem.children
    currentConnections = subsystem.childConnections || []
  }

  return { blocks: currentBlocks, connections: currentConnections }
}

/**
 * Update a block's property at any level in the hierarchy.
 * Returns a new blocks array with the update applied immutably.
 */
function updateBlockInHierarchy(
  blocks: BlockInstance[],
  path: SubsystemPathItem[],
  blockId: string,
  updater: (block: BlockInstance) => BlockInstance
): BlockInstance[] {
  if (path.length === 0) {
    // At root level - update directly
    return blocks.map(b => b.id === blockId ? updater(b) : b)
  }

  // Need to update a block inside a subsystem
  const [first, ...rest] = path
  return blocks.map(b => {
    if (b.id === first.id && b.type === 'subsystem' && b.children) {
      return {
        ...b,
        children: updateBlockInHierarchy(b.children, rest, blockId, updater)
      }
    }
    return b
  })
}

/**
 * Add a connection at the current path level.
 * Returns a new model with the connection added.
 */
function addConnectionInHierarchy(
  model: Model,
  path: SubsystemPathItem[],
  connection: Connection
): Model {
  if (path.length === 0) {
    return { ...model, connections: [...model.connections, connection] }
  }

  // Need to add connection inside a subsystem
  const updateSubsystem = (blocks: BlockInstance[], remainingPath: SubsystemPathItem[]): BlockInstance[] => {
    if (remainingPath.length === 0) return blocks

    const [first, ...rest] = remainingPath
    return blocks.map(b => {
      if (b.id === first.id && b.type === 'subsystem') {
        if (rest.length === 0) {
          // This is the target subsystem
          return {
            ...b,
            childConnections: [...(b.childConnections || []), connection]
          }
        } else {
          // Go deeper
          return {
            ...b,
            children: updateSubsystem(b.children || [], rest)
          }
        }
      }
      return b
    })
  }

  return { ...model, blocks: updateSubsystem(model.blocks, path) }
}

/**
 * Remove a connection at the current path level.
 * Returns a new model with the connection removed.
 */
function removeConnectionInHierarchy(
  model: Model,
  path: SubsystemPathItem[],
  connectionId: string
): Model {
  if (path.length === 0) {
    return { ...model, connections: model.connections.filter(c => c.id !== connectionId) }
  }

  // Need to remove connection inside a subsystem
  const updateSubsystem = (blocks: BlockInstance[], remainingPath: SubsystemPathItem[]): BlockInstance[] => {
    if (remainingPath.length === 0) return blocks

    const [first, ...rest] = remainingPath
    return blocks.map(b => {
      if (b.id === first.id && b.type === 'subsystem') {
        if (rest.length === 0) {
          // This is the target subsystem
          return {
            ...b,
            childConnections: (b.childConnections || []).filter(c => c.id !== connectionId)
          }
        } else {
          // Go deeper
          return {
            ...b,
            children: updateSubsystem(b.children || [], rest)
          }
        }
      }
      return b
    })
  }

  return { ...model, blocks: updateSubsystem(model.blocks, path) }
}

export const useModelStore = create<ModelState>((set, get) => ({
  model: null,
  isDirty: false,
  history: [],
  future: [],
  currentPath: [],
  selectedBlockIds: [],
  selectedConnectionIds: [],

  createNewModel: (name: string) => {
    const newModel: Model = {
      id: nanoid(),
      metadata: createDefaultMetadata(name),
      blocks: [],
      connections: [],
      simulationConfig: { ...defaultSimulationConfig },
    }
    set({ model: newModel, isDirty: false, currentPath: [] })
  },

  loadModel: (model: Model) => {
    // Propagate signal dimensions when loading a model
    // This ensures all subsystem output ports have correct dimensions
    propagateDimensions(model.blocks, model.connections)
    set({ model, isDirty: false, currentPath: [], selectedBlockIds: [], selectedConnectionIds: [] })
  },

  saveModel: () => {
    const { model } = get()
    if (model) {
      const updatedModel = {
        ...model,
        metadata: {
          ...model.metadata,
          modifiedAt: new Date().toISOString(),
        },
      }
      set({ model: updatedModel, isDirty: false })
      return updatedModel
    }
    return null
  },

  addBlock: (definition: BlockDefinition, position: { x: number; y: number }) => {
    const { model, currentPath } = get()
    if (!model) return ''

    const blockId = nanoid()
    // Count blocks with the same base name at the current level
    // This ensures proper unique naming for library blocks (e.g., Quaternion, Quaternion2, Quaternion3)
    const currentBlocks = get().getCurrentBlocks()
    const baseName = definition.name

    // Find the highest number suffix for blocks with this base name
    let maxSuffix = 0
    const baseNamePattern = new RegExp(`^${baseName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(\\d*)$`)

    currentBlocks.forEach((b) => {
      const match = b.name.match(baseNamePattern)
      if (match) {
        const suffix = match[1] ? parseInt(match[1], 10) : 1
        maxSuffix = Math.max(maxSuffix, suffix)
      }
    })

    // Generate the new name with proper suffix
    const newName = maxSuffix === 0 ? baseName : `${baseName}${maxSuffix + 1}`

    // Build initial parameters from definition
    const initialParams = definition.parameters.reduce(
      (acc, param) => ({ ...acc, [param.name]: param.default }),
      {} as Record<string, unknown>
    )

    // Build output ports, handling special cases like Reshape
    let outputPorts = definition.outputs.map((output, idx) => ({
      ...output,
      id: `${blockId}-out-${idx}`,
    }))

    // For Reshape blocks, parse the outputDimensions parameter to set correct dimensions
    if (definition.type === 'reshape' && initialParams.outputDimensions) {
      let dims: number[] = [1]
      const dimStr = String(initialParams.outputDimensions)
      try {
        const parsed = JSON.parse(dimStr)
        if (Array.isArray(parsed) && parsed.every(n => typeof n === 'number')) {
          dims = parsed
        }
      } catch {
        const matches = dimStr.match(/\d+/g)
        if (matches) {
          dims = matches.map(Number)
        }
      }
      outputPorts = [{
        id: `${blockId}-out-0`,
        name: 'out',
        dataType: 'double' as const,
        dimensions: dims,
      }]
    }

    const newBlock: BlockInstance = {
      id: blockId,
      type: definition.type,
      name: newName,
      position,
      parameters: initialParams,
      inputPorts: definition.inputs.map((input, idx) => ({
        ...input,
        id: `${blockId}-in-${idx}`,
      })),
      outputPorts,
    }

    // If this is a library block, copy its implementation (children and connections)
    if (isLibraryBlockDefinition(definition)) {
      const impl = definition.implementation

      // Deep copy children with new IDs prefixed by block ID
      const idMap = new Map<string, string>() // old ID -> new ID
      // Also map old port IDs to new port IDs for each block
      const portIdMap = new Map<string, string>()

      // Calculate position normalization - find bounding box and normalize positions
      // to start from (100, 100) with minimum spacing of 150px between blocks
      let minX = Infinity, minY = Infinity
      impl.blocks.forEach((child) => {
        minX = Math.min(minX, child.position.x)
        minY = Math.min(minY, child.position.y)
      })

      // If all positions are the same (or very close), spread them out in a grid
      const positions = impl.blocks.map((b) => b.position)
      const uniquePositions = new Set(positions.map((p) => `${Math.round(p.x / 80)},${Math.round(p.y / 80)}`))
      const needsSpread = uniquePositions.size < impl.blocks.length * 0.7 // More than 30% overlap

      const children: BlockInstance[] = impl.blocks.map((child, index) => {
        const newChildId = `${blockId}__${nanoid()}`
        idMap.set(child.id, newChildId)

        // Map input port IDs
        const newInputPorts = child.inputPorts.map((port, idx) => {
          const newPortId = `${newChildId}-in-${idx}`
          portIdMap.set(port.id, newPortId)
          return { ...port, id: newPortId }
        })

        // Map output port IDs
        const newOutputPorts = child.outputPorts.map((port, idx) => {
          const newPortId = `${newChildId}-out-${idx}`
          portIdMap.set(port.id, newPortId)
          return { ...port, id: newPortId }
        })

        // Normalize position: offset so minimum is (100, 100), or spread if needed
        let newPosition: { x: number; y: number }
        if (needsSpread) {
          // Spread blocks in a grid pattern with more spacing
          const cols = Math.ceil(Math.sqrt(impl.blocks.length))
          const col = index % cols
          const row = Math.floor(index / cols)
          newPosition = { x: 100 + col * 250, y: 100 + row * 150 }
        } else {
          // Keep relative positions but offset to start from (100, 100) with scaling
          // Scale up positions if they're too compressed
          const scaleX = Math.max(1, 150 / Math.max(1, (impl.blocks.reduce((max, b) => Math.max(max, b.position.x), 0) - minX) / impl.blocks.length))
          const scaleY = Math.max(1, 100 / Math.max(1, (impl.blocks.reduce((max, b) => Math.max(max, b.position.y), 0) - minY) / impl.blocks.length))
          newPosition = {
            x: 100 + (child.position.x - minX) * Math.min(scaleX, 2),
            y: 100 + (child.position.y - minY) * Math.min(scaleY, 2),
          }
        }

        return {
          ...child,
          id: newChildId,
          position: newPosition,
          inputPorts: newInputPorts,
          outputPorts: newOutputPorts,
        }
      })

      // Deep copy connections with updated block and port IDs
      const childConnections: Connection[] = impl.connections.map((conn) => ({
        id: `${blockId}__${nanoid()}`,
        sourceBlockId: idMap.get(conn.sourceBlockId) || conn.sourceBlockId,
        sourcePortId: portIdMap.get(conn.sourcePortId) || conn.sourcePortId,
        targetBlockId: idMap.get(conn.targetBlockId) || conn.targetBlockId,
        targetPortId: portIdMap.get(conn.targetPortId) || conn.targetPortId,
      }))

      // Override block type to 'subsystem' since that's what the backend expects
      newBlock.type = 'subsystem'
      newBlock.children = children
      newBlock.childConnections = childConnections
      newBlock.isExpanded = false
    }

    // Add block at the current path level
    if (currentPath.length === 0) {
      // At root level - add directly to model.blocks
      set({
        model: { ...model, blocks: [...model.blocks, newBlock] },
        isDirty: true,
      })
    } else {
      // Inside a subsystem - need to add to the parent subsystem's children
      const addBlockToSubsystem = (blocks: BlockInstance[], path: SubsystemPathItem[]): BlockInstance[] => {
        if (path.length === 0) return blocks

        const [current, ...rest] = path

        return blocks.map(block => {
          if (block.id === current.id && block.type === 'subsystem' && block.children) {
            if (rest.length === 0) {
              // This is the target subsystem - add the block to its children
              return {
                ...block,
                children: [...block.children, newBlock],
              }
            } else {
              // Recurse deeper
              return {
                ...block,
                children: addBlockToSubsystem(block.children, rest),
              }
            }
          }
          return block
        })
      }

      set({
        model: { ...model, blocks: addBlockToSubsystem(model.blocks, currentPath) },
        isDirty: true,
      })
    }

    return blockId
  },

  removeBlock: (blockId: string) => {
    const { model, currentPath } = get()
    if (!model) return

    if (currentPath.length === 0) {
      // At root level - remove from model.blocks and model.connections
      const connections = model.connections.filter(
        (c) => c.sourceBlockId !== blockId && c.targetBlockId !== blockId
      )

      set({
        model: {
          ...model,
          blocks: model.blocks.filter((b) => b.id !== blockId),
          connections,
        },
        isDirty: true,
        selectedBlockIds: get().selectedBlockIds.filter((id) => id !== blockId),
      })
    } else {
      // Inside a subsystem - need to remove from parent subsystem's children
      const removeBlockFromSubsystem = (blocks: BlockInstance[], path: SubsystemPathItem[]): BlockInstance[] => {
        if (path.length === 0) return blocks

        const [current, ...rest] = path

        return blocks.map(block => {
          if (block.id === current.id && block.type === 'subsystem' && block.children) {
            if (rest.length === 0) {
              // This is the target subsystem - remove block and its connections
              return {
                ...block,
                children: block.children.filter((b) => b.id !== blockId),
                childConnections: (block.childConnections || []).filter(
                  (c) => c.sourceBlockId !== blockId && c.targetBlockId !== blockId
                ),
              }
            } else {
              // Recurse deeper
              return {
                ...block,
                children: removeBlockFromSubsystem(block.children, rest),
              }
            }
          }
          return block
        })
      }

      set({
        model: { ...model, blocks: removeBlockFromSubsystem(model.blocks, currentPath) },
        isDirty: true,
        selectedBlockIds: get().selectedBlockIds.filter((id) => id !== blockId),
      })
    }
  },

  updateBlockPosition: (blockId: string, position: { x: number; y: number }) => {
    const { model, currentPath } = get()
    if (!model) return

    set({
      model: {
        ...model,
        blocks: updateBlockInHierarchy(model.blocks, currentPath, blockId, (b) => ({ ...b, position })),
      },
      isDirty: true,
    })
  },

  updateBlockParameters: (blockId: string, parameters: Record<string, unknown>) => {
    const { model, currentPath } = get()
    if (!model) return

    set({
      model: {
        ...model,
        blocks: updateBlockInHierarchy(model.blocks, currentPath, blockId, (b) => {
          const updatedBlock = {
            ...b,
            parameters: { ...b.parameters, ...parameters }
          }

          // Handle dynamic port count updates for certain block types
          if (b.type === 'mux' && 'numInputs' in parameters) {
            const numInputs = Math.max(2, Math.min(32, Number(parameters.numInputs) || 2))
            const newInputPorts = []
            for (let i = 0; i < numInputs; i++) {
              newInputPorts.push({
                id: `${b.id}-in-${i}`,
                name: `in${i + 1}`,
                dataType: 'double' as const,
                dimensions: [1],
              })
            }
            updatedBlock.inputPorts = newInputPorts
            // Update output dimensions to match
            updatedBlock.outputPorts = [{
              id: `${b.id}-out-0`,
              name: 'out',
              dataType: 'double' as const,
              dimensions: [numInputs],
            }]
          }

          if (b.type === 'demux' && 'numOutputs' in parameters) {
            const numOutputs = Math.max(2, Math.min(32, Number(parameters.numOutputs) || 2))
            const newOutputPorts = []
            for (let i = 0; i < numOutputs; i++) {
              newOutputPorts.push({
                id: `${b.id}-out-${i}`,
                name: `out${i + 1}`,
                dataType: 'double' as const,
                dimensions: [1],
              })
            }
            updatedBlock.outputPorts = newOutputPorts
            // Update input dimensions to match
            updatedBlock.inputPorts = [{
              id: `${b.id}-in-0`,
              name: 'in',
              dataType: 'double' as const,
              dimensions: [numOutputs],
            }]
          }

          // Handle Sum block signs parameter (determines number of inputs)
          if (b.type === 'sum' && 'signs' in parameters) {
            const signs = String(parameters.signs || '++')
            const numInputs = signs.length
            const newInputPorts = []
            for (let i = 0; i < numInputs; i++) {
              newInputPorts.push({
                id: `${b.id}-in-${i}`,
                name: `in${i + 1}`,
                dataType: 'double' as const,
                dimensions: [1],
              })
            }
            updatedBlock.inputPorts = newInputPorts
          }

          // Handle Scope numInputs
          if (b.type === 'scope' && 'numInputs' in parameters) {
            const numInputs = Math.max(1, Math.min(16, Number(parameters.numInputs) || 1))
            const newInputPorts = []
            for (let i = 0; i < numInputs; i++) {
              newInputPorts.push({
                id: `${b.id}-in-${i}`,
                name: `in${i + 1}`,
                dataType: 'double' as const,
                dimensions: [1],
              })
            }
            updatedBlock.inputPorts = newInputPorts
          }

          // Handle Reshape outputDimensions
          if (b.type === 'reshape' && 'outputDimensions' in parameters) {
            let dims: number[] = [1]
            const dimStr = String(parameters.outputDimensions || '[1]')
            try {
              const parsed = JSON.parse(dimStr)
              if (Array.isArray(parsed) && parsed.every(n => typeof n === 'number')) {
                dims = parsed
              }
            } catch {
              // If parsing fails, try to extract numbers from the string
              const matches = dimStr.match(/\d+/g)
              if (matches) {
                dims = matches.map(Number)
              }
            }
            updatedBlock.outputPorts = [{
              id: `${b.id}-out-0`,
              name: 'out',
              dataType: 'double' as const,
              dimensions: dims,
            }]
          }

          // Handle Constant block value parameter to update dimensions
          if (b.type === 'constant' && 'value' in parameters) {
            const dims = parseConstantValueDimensions(parameters.value)
            updatedBlock.outputPorts = [{
              id: `${b.id}-out-0`,
              name: 'out',
              dataType: 'double' as const,
              dimensions: dims,
            }]
          }

          return updatedBlock
        }),
      },
      isDirty: true,
    })

    // Clean up orphaned connections (connections to ports that no longer exist)
    const { model: updatedModel, currentPath: path } = get()
    if (updatedModel) {
      // Get the updated block to check its current ports
      const currentBlocks = path.length === 0
        ? updatedModel.blocks
        : findBlockAtPath(updatedModel.blocks, path)?.blocks || []
      const updatedBlock = currentBlocks.find(b => b.id === blockId)

      if (updatedBlock) {
        const validInputPortIds = new Set(updatedBlock.inputPorts.map(p => p.id))
        const validOutputPortIds = new Set(updatedBlock.outputPorts.map(p => p.id))

        // Filter out connections that reference non-existent ports on this block
        const filterConnections = (connections: Connection[]) =>
          connections.filter(c => {
            // Check if this connection involves the updated block
            if (c.targetBlockId === blockId && !validInputPortIds.has(c.targetPortId)) {
              return false // Remove - target port no longer exists
            }
            if (c.sourceBlockId === blockId && !validOutputPortIds.has(c.sourcePortId)) {
              return false // Remove - source port no longer exists
            }
            return true
          })

        if (path.length === 0) {
          // At root level
          const filteredConnections = filterConnections(updatedModel.connections)
          if (filteredConnections.length !== updatedModel.connections.length) {
            set({ model: { ...updatedModel, connections: filteredConnections } })
          }
        } else {
          // Inside a subsystem - need to update connections within the subsystem
          const updateSubsystemConnections = (blocks: BlockInstance[], remainingPath: SubsystemPathItem[]): BlockInstance[] => {
            if (remainingPath.length === 0) return blocks
            const [first, ...rest] = remainingPath
            return blocks.map(b => {
              if (b.id === first.id && b.type === 'subsystem') {
                if (rest.length === 0 && b.childConnections) {
                  // This is the target subsystem
                  const filteredConnections = filterConnections(b.childConnections)
                  return { ...b, childConnections: filteredConnections }
                }
                if (b.children) {
                  return { ...b, children: updateSubsystemConnections(b.children, rest) }
                }
              }
              return b
            })
          }
          set({ model: { ...updatedModel, blocks: updateSubsystemConnections(updatedModel.blocks, path) } })
        }
      }

      // Re-propagate dimensions after parameter changes that might affect signal dimensions
      const { model: finalModel } = get()
      if (finalModel) {
        propagateDimensions(finalModel.blocks, finalModel.connections)
        set({ model: { ...finalModel } })
      }
    }
  },

  renameBlock: (blockId: string, name: string) => {
    const { model, currentPath } = get()
    if (!model) return

    set({
      model: {
        ...model,
        blocks: updateBlockInHierarchy(model.blocks, currentPath, blockId, (b) => ({ ...b, name })),
      },
      isDirty: true,
    })
  },

  addScopeInput: (blockId: string) => {
    const { model, currentPath } = get()
    if (!model) return null

    // Find the block and verify it's a scope
    const currentBlocks = get().getCurrentBlocks()
    const block = currentBlocks.find((b) => b.id === blockId)
    if (!block || block.type !== 'scope') return null

    // Calculate the new port index
    const newPortIndex = block.inputPorts.length
    const newPortId = `${blockId}-in-${newPortIndex}`
    const newNumInputs = newPortIndex + 1

    // Update the block with new port and numInputs parameter
    set({
      model: {
        ...model,
        blocks: updateBlockInHierarchy(model.blocks, currentPath, blockId, (b) => ({
          ...b,
          parameters: { ...b.parameters, numInputs: newNumInputs },
          inputPorts: [
            ...b.inputPorts,
            {
              id: newPortId,
              name: `in${newNumInputs}`,
              dataType: 'double' as const,
              dimensions: [1],
            },
          ],
        })),
      },
      isDirty: true,
    })

    return newPortId
  },

  addConnection: (connection: Omit<Connection, 'id'>) => {
    const { model, currentPath } = get()
    if (!model) return null

    // Get the current level's connections to check for duplicates
    const currentConnections = get().getCurrentConnections()

    // Check if connection already exists
    const exists = currentConnections.some(
      (c) =>
        c.sourceBlockId === connection.sourceBlockId &&
        c.sourcePortId === connection.sourcePortId &&
        c.targetBlockId === connection.targetBlockId &&
        c.targetPortId === connection.targetPortId
    )
    if (exists) return null

    // Check if target port already has a connection
    const targetConnected = currentConnections.some(
      (c) =>
        c.targetBlockId === connection.targetBlockId &&
        c.targetPortId === connection.targetPortId
    )
    if (targetConnected) return null

    const connectionId = nanoid()
    const newConnection: Connection = { ...connection, id: connectionId }

    const updatedModel = addConnectionInHierarchy(model, currentPath, newConnection)

    // Propagate signal dimensions after adding the connection
    // This ensures subsystem output ports reflect the dimensions of connected signals
    propagateDimensions(updatedModel.blocks, updatedModel.connections)

    set({
      model: updatedModel,
      isDirty: true,
    })

    return connectionId
  },

  removeConnection: (connectionId: string) => {
    const { model, currentPath } = get()
    if (!model) return

    set({
      model: removeConnectionInHierarchy(model, currentPath, connectionId),
      isDirty: true,
      selectedConnectionIds: get().selectedConnectionIds.filter((id) => id !== connectionId),
    })
  },

  selectBlocks: (blockIds: string[]) => {
    set({ selectedBlockIds: blockIds, selectedConnectionIds: [] })
  },

  selectConnections: (connectionIds: string[]) => {
    set({ selectedConnectionIds: connectionIds, selectedBlockIds: [] })
  },

  clearSelection: () => {
    set({ selectedBlockIds: [], selectedConnectionIds: [] })
  },

  updateSimulationConfig: (config: Partial<SimulationConfig>) => {
    const { model } = get()
    if (!model) return

    set({
      model: {
        ...model,
        simulationConfig: { ...model.simulationConfig, ...config },
      },
      isDirty: true,
    })
  },

  updateMetadata: (metadata: Partial<ModelMetadata>) => {
    const { model } = get()
    if (!model) return

    set({
      model: {
        ...model,
        metadata: { ...model.metadata, ...metadata },
      },
      isDirty: true,
    })
  },

  spreadBlocks: (factor: number) => {
    const { model, currentPath, selectedBlockIds } = get()
    if (!model) return

    // Get current level blocks
    const currentBlocks = get().getCurrentBlocks()
    if (currentBlocks.length === 0) return

    // Determine which blocks to spread: selected blocks or all blocks
    const blocksToSpread = selectedBlockIds.length > 0
      ? currentBlocks.filter(b => selectedBlockIds.includes(b.id))
      : currentBlocks

    if (blocksToSpread.length < 2) return // Need at least 2 blocks to spread

    // Calculate centroid of the blocks to spread
    const cx = blocksToSpread.reduce((sum, b) => sum + b.position.x, 0) / blocksToSpread.length
    const cy = blocksToSpread.reduce((sum, b) => sum + b.position.y, 0) / blocksToSpread.length

    // Scale positions relative to centroid
    const blockIdsToSpread = new Set(blocksToSpread.map(b => b.id))

    const updatePositions = (blocks: BlockInstance[]): BlockInstance[] => {
      return blocks.map(b => {
        if (blockIdsToSpread.has(b.id)) {
          const newX = cx + (b.position.x - cx) * factor
          const newY = cy + (b.position.y - cy) * factor
          return { ...b, position: { x: newX, y: newY } }
        }
        return b
      })
    }

    if (currentPath.length === 0) {
      // At root level
      set({
        model: { ...model, blocks: updatePositions(model.blocks) },
        isDirty: true,
      })
    } else {
      // Inside a subsystem - need to update blocks within the subsystem
      const updateSubsystemBlocks = (blocks: BlockInstance[], path: SubsystemPathItem[]): BlockInstance[] => {
        if (path.length === 0) return blocks

        const [first, ...rest] = path
        return blocks.map(b => {
          if (b.id === first.id && b.type === 'subsystem' && b.children) {
            if (rest.length === 0) {
              // This is the target subsystem
              return { ...b, children: updatePositions(b.children) }
            } else {
              // Go deeper
              return { ...b, children: updateSubsystemBlocks(b.children, rest) }
            }
          }
          return b
        })
      }

      set({
        model: { ...model, blocks: updateSubsystemBlocks(model.blocks, currentPath) },
        isDirty: true,
      })
    }
  },

  rotateSelectedBlocks: () => {
    const { model, currentPath, selectedBlockIds } = get()
    if (!model || selectedBlockIds.length === 0) return

    // Rotate selected blocks 90 degrees clockwise
    const rotateBlock = (block: BlockInstance): BlockInstance => {
      if (!selectedBlockIds.includes(block.id)) return block
      const currentRotation = block.rotation || 0
      const newRotation = ((currentRotation + 90) % 360) as 0 | 90 | 180 | 270
      return { ...block, rotation: newRotation }
    }

    if (currentPath.length === 0) {
      // At root level
      set({
        model: { ...model, blocks: model.blocks.map(rotateBlock) },
        isDirty: true,
      })
    } else {
      // Inside a subsystem - need to update blocks within the subsystem
      const updateSubsystemBlocks = (blocks: BlockInstance[], path: SubsystemPathItem[]): BlockInstance[] => {
        if (path.length === 0) return blocks

        const [first, ...rest] = path
        return blocks.map(b => {
          if (b.id === first.id && b.type === 'subsystem' && b.children) {
            if (rest.length === 0) {
              // This is the target subsystem
              return { ...b, children: b.children.map(rotateBlock) }
            } else {
              // Go deeper
              return { ...b, children: updateSubsystemBlocks(b.children, rest) }
            }
          }
          return b
        })
      }

      set({
        model: { ...model, blocks: updateSubsystemBlocks(model.blocks, currentPath) },
        isDirty: true,
      })
    }
  },

  // Undo/Redo implementation
  pushHistory: () => {
    const { model, history } = get()
    if (!model) return

    // Deep copy current model state
    const snapshot = JSON.parse(JSON.stringify(model)) as Model

    // Add to history, trim if exceeds max size
    const newHistory = [...history, snapshot].slice(-MAX_HISTORY_SIZE)

    // Clear future when new action is taken (standard undo/redo behavior)
    set({ history: newHistory, future: [] })
  },

  undo: () => {
    const { model, history, future } = get()
    if (history.length === 0 || !model) return

    // Pop the last state from history
    const newHistory = [...history]
    const previousState = newHistory.pop()!

    // Push current state to future for redo
    const currentSnapshot = JSON.parse(JSON.stringify(model)) as Model
    const newFuture = [...future, currentSnapshot]

    set({
      model: previousState,
      history: newHistory,
      future: newFuture,
      isDirty: true,
    })
  },

  redo: () => {
    const { model, history, future } = get()
    if (future.length === 0 || !model) return

    // Pop the last state from future
    const newFuture = [...future]
    const nextState = newFuture.pop()!

    // Push current state to history
    const currentSnapshot = JSON.parse(JSON.stringify(model)) as Model
    const newHistory = [...history, currentSnapshot]

    set({
      model: nextState,
      history: newHistory,
      future: newFuture,
      isDirty: true,
    })
  },

  canUndo: () => get().history.length > 0,
  canRedo: () => get().future.length > 0,

  createSubsystem: (blockIds: string[], name?: string) => {
    const { model } = get()
    if (!model || blockIds.length === 0) return null

    const selectedBlocks = model.blocks.filter((b) => blockIds.includes(b.id))
    if (selectedBlocks.length === 0) return null

    // Calculate center position of selected blocks for subsystem placement
    const avgX = selectedBlocks.reduce((sum, b) => sum + b.position.x, 0) / selectedBlocks.length
    const avgY = selectedBlocks.reduce((sum, b) => sum + b.position.y, 0) / selectedBlocks.length

    // Find all connections
    const internalConnections: Connection[] = []
    const incomingConnections: Connection[] = []
    const outgoingConnections: Connection[] = []

    model.connections.forEach((conn) => {
      const sourceInside = blockIds.includes(conn.sourceBlockId)
      const targetInside = blockIds.includes(conn.targetBlockId)

      if (sourceInside && targetInside) {
        internalConnections.push(conn)
      } else if (!sourceInside && targetInside) {
        incomingConnections.push(conn)
      } else if (sourceInside && !targetInside) {
        outgoingConnections.push(conn)
      }
    })

    // Create Inport blocks for each unique incoming connection target
    const inportMap = new Map<string, { inportId: string; portNumber: number }>()
    const childInports: BlockInstance[] = []
    const newInternalConnections: Connection[] = [...internalConnections]
    let inportNumber = 1

    incomingConnections.forEach((conn) => {
      const key = `${conn.targetBlockId}-${conn.targetPortId}`
      if (!inportMap.has(key)) {
        const inportId = nanoid()
        const targetBlock = selectedBlocks.find((b) => b.id === conn.targetBlockId)
        const targetPort = targetBlock?.inputPorts.find((p) => p.id === conn.targetPortId)

        childInports.push({
          id: inportId,
          type: 'inport',
          name: `In${inportNumber}`,
          position: { x: 50, y: 50 + (inportNumber - 1) * 80 },
          parameters: { portNumber: inportNumber },
          inputPorts: [],
          outputPorts: [{
            id: `${inportId}-out-0`,
            name: 'out',
            dataType: targetPort?.dataType || 'double',
            dimensions: targetPort?.dimensions || [1],
          }],
        })
        inportMap.set(key, { inportId, portNumber: inportNumber })
        inportNumber++
      }

      // Create internal connection from inport to original target
      const inportInfo = inportMap.get(key)!
      newInternalConnections.push({
        id: nanoid(),
        sourceBlockId: inportInfo.inportId,
        sourcePortId: `${inportInfo.inportId}-out-0`,
        targetBlockId: conn.targetBlockId,
        targetPortId: conn.targetPortId,
      })
    })

    // Create Outport blocks for each unique outgoing connection source
    const outportMap = new Map<string, { outportId: string; portNumber: number }>()
    const childOutports: BlockInstance[] = []
    let outportNumber = 1

    outgoingConnections.forEach((conn) => {
      const key = `${conn.sourceBlockId}-${conn.sourcePortId}`
      if (!outportMap.has(key)) {
        const outportId = nanoid()
        const sourceBlock = selectedBlocks.find((b) => b.id === conn.sourceBlockId)
        const sourcePort = sourceBlock?.outputPorts.find((p) => p.id === conn.sourcePortId)

        childOutports.push({
          id: outportId,
          type: 'outport',
          name: `Out${outportNumber}`,
          position: { x: 400, y: 50 + (outportNumber - 1) * 80 },
          parameters: { portNumber: outportNumber },
          inputPorts: [{
            id: `${outportId}-in-0`,
            name: 'in',
            dataType: sourcePort?.dataType || 'double',
            dimensions: sourcePort?.dimensions || [1],
          }],
          outputPorts: [],
        })
        outportMap.set(key, { outportId, portNumber: outportNumber })
        outportNumber++
      }

      // Create internal connection from original source to outport
      const outportInfo = outportMap.get(key)!
      newInternalConnections.push({
        id: nanoid(),
        sourceBlockId: conn.sourceBlockId,
        sourcePortId: conn.sourcePortId,
        targetBlockId: outportInfo.outportId,
        targetPortId: `${outportInfo.outportId}-in-0`,
      })
    })

    // Create the subsystem block
    const subsystemId = nanoid()
    const subsystemName = name || `Subsystem${model.blocks.filter((b) => b.type === 'subsystem').length + 1}`

    // Build input ports from inports
    const subsystemInputPorts = childInports.map((inport, idx) => ({
      id: `${subsystemId}-in-${idx}`,
      name: inport.name,
      dataType: inport.outputPorts[0]?.dataType || 'double' as const,
      dimensions: inport.outputPorts[0]?.dimensions || [1],
    }))

    // Build output ports from outports
    const subsystemOutputPorts = childOutports.map((outport, idx) => ({
      id: `${subsystemId}-out-${idx}`,
      name: outport.name,
      dataType: outport.inputPorts[0]?.dataType || 'double' as const,
      dimensions: outport.inputPorts[0]?.dimensions || [1],
    }))

    const subsystemBlock: BlockInstance = {
      id: subsystemId,
      type: 'subsystem',
      name: subsystemName,
      position: { x: avgX, y: avgY },
      parameters: { description: '' },
      inputPorts: subsystemInputPorts,
      outputPorts: subsystemOutputPorts,
      children: [...childInports, ...selectedBlocks, ...childOutports],
      childConnections: newInternalConnections,
      isExpanded: false,
    }

    // Create new external connections to subsystem
    const newExternalConnections: Connection[] = []

    // Remap incoming connections to subsystem inputs
    incomingConnections.forEach((conn) => {
      const key = `${conn.targetBlockId}-${conn.targetPortId}`
      const inportInfo = inportMap.get(key)
      if (inportInfo) {
        newExternalConnections.push({
          id: nanoid(),
          sourceBlockId: conn.sourceBlockId,
          sourcePortId: conn.sourcePortId,
          targetBlockId: subsystemId,
          targetPortId: `${subsystemId}-in-${inportInfo.portNumber - 1}`,
        })
      }
    })

    // Remap outgoing connections from subsystem outputs
    outgoingConnections.forEach((conn) => {
      const key = `${conn.sourceBlockId}-${conn.sourcePortId}`
      const outportInfo = outportMap.get(key)
      if (outportInfo) {
        newExternalConnections.push({
          id: nanoid(),
          sourceBlockId: subsystemId,
          sourcePortId: `${subsystemId}-out-${outportInfo.portNumber - 1}`,
          targetBlockId: conn.targetBlockId,
          targetPortId: conn.targetPortId,
        })
      }
    })

    // Remove original blocks and their connections, add subsystem
    const remainingBlocks = model.blocks.filter((b) => !blockIds.includes(b.id))
    const remainingConnections = model.connections.filter(
      (c) => !blockIds.includes(c.sourceBlockId) && !blockIds.includes(c.targetBlockId)
    )

    // Propagate signal dimensions within the new subsystem
    // This updates Outport blocks and the subsystem's output ports
    if (subsystemBlock.children && subsystemBlock.childConnections) {
      propagateDimensions([subsystemBlock], [])
    }

    set({
      model: {
        ...model,
        blocks: [...remainingBlocks, subsystemBlock],
        connections: [...remainingConnections, ...newExternalConnections],
      },
      isDirty: true,
      selectedBlockIds: [subsystemId],
    })

    return subsystemId
  },

  toggleSubsystemExpanded: (subsystemId: string) => {
    const { model } = get()
    if (!model) return

    set({
      model: {
        ...model,
        blocks: model.blocks.map((b) =>
          b.id === subsystemId && b.type === 'subsystem'
            ? { ...b, isExpanded: !b.isExpanded }
            : b
        ),
      },
      isDirty: true,
    })
  },

  /**
   * Expand (dissolve) a subsystem, moving its children to the parent level.
   * This is the inverse of createSubsystem.
   * Works at the current navigation level.
   */
  expandSubsystem: (subsystemId: string) => {
    const { model, currentPath } = get()
    if (!model) return

    // Get current level blocks and connections
    const currentBlocks = get().getCurrentBlocks()
    const currentConnections = get().getCurrentConnections()

    // Find the subsystem to expand
    const subsystem = currentBlocks.find(b => b.id === subsystemId && b.type === 'subsystem')
    if (!subsystem || !subsystem.children) return

    // Close any plot windows that were opened for blocks inside this subsystem
    // These windows use flattened IDs like "subsystemId__blockId", so they won't
    // match the blocks after expansion (which will just use "blockId")
    useUIStore.getState().closePlotWindowsWithPrefix(subsystemId)

    // Get the children (excluding Inport/Outport blocks)
    const childBlocks = subsystem.children.filter(b => b.type !== 'inport' && b.type !== 'outport')
    const inportBlocks = subsystem.children.filter(b => b.type === 'inport')
    const outportBlocks = subsystem.children.filter(b => b.type === 'outport')
    const childConnections = subsystem.childConnections || []

    // Calculate position offset - children will be placed relative to subsystem position
    const offsetX = subsystem.position.x - 100 // Offset to spread out children
    const offsetY = subsystem.position.y - 50

    // Create maps for port remapping
    // Map from inport block ID to the connection coming into the subsystem
    const inportToExternalSource = new Map<string, { sourceBlockId: string; sourcePortId: string }>()
    // Map from outport block ID to the connections going out of the subsystem
    const outportToExternalTargets = new Map<string, Array<{ targetBlockId: string; targetPortId: string }>>()

    // Find external connections to this subsystem
    currentConnections.forEach(conn => {
      if (conn.targetBlockId === subsystemId) {
        // Connection coming INTO the subsystem
        // Find which port index this connects to
        const portIndex = subsystem.inputPorts.findIndex(p => p.id === conn.targetPortId)
        if (portIndex >= 0) {
          // Find the corresponding inport block (by port number)
          const inport = inportBlocks.find(b => (b.parameters.portNumber as number) === portIndex + 1)
          if (inport) {
            inportToExternalSource.set(inport.id, {
              sourceBlockId: conn.sourceBlockId,
              sourcePortId: conn.sourcePortId,
            })
          }
        }
      } else if (conn.sourceBlockId === subsystemId) {
        // Connection going OUT of the subsystem
        const portIndex = subsystem.outputPorts.findIndex(p => p.id === conn.sourcePortId)
        if (portIndex >= 0) {
          // Find the corresponding outport block (by port number)
          const outport = outportBlocks.find(b => (b.parameters.portNumber as number) === portIndex + 1)
          if (outport) {
            const existing = outportToExternalTargets.get(outport.id) || []
            existing.push({
              targetBlockId: conn.targetBlockId,
              targetPortId: conn.targetPortId,
            })
            outportToExternalTargets.set(outport.id, existing)
          }
        }
      }
    })

    // Adjust child block positions
    const repositionedChildren = childBlocks.map(child => ({
      ...child,
      position: {
        x: child.position.x + offsetX,
        y: child.position.y + offsetY,
      },
    }))

    // Build new connections:
    // 1. Internal connections between child blocks (not involving inports/outports)
    const newConnections: Connection[] = []

    childConnections.forEach(conn => {
      const sourceIsInport = inportBlocks.some(b => b.id === conn.sourceBlockId)
      const targetIsOutport = outportBlocks.some(b => b.id === conn.targetBlockId)
      const sourceIsChild = childBlocks.some(b => b.id === conn.sourceBlockId)
      const targetIsChild = childBlocks.some(b => b.id === conn.targetBlockId)

      if (sourceIsChild && targetIsChild) {
        // Internal connection between two child blocks - keep as is
        newConnections.push({ ...conn, id: nanoid() })
      } else if (sourceIsInport && targetIsChild) {
        // Connection from inport to child - remap to external source
        const externalSource = inportToExternalSource.get(conn.sourceBlockId)
        if (externalSource) {
          newConnections.push({
            id: nanoid(),
            sourceBlockId: externalSource.sourceBlockId,
            sourcePortId: externalSource.sourcePortId,
            targetBlockId: conn.targetBlockId,
            targetPortId: conn.targetPortId,
          })
        }
      } else if (sourceIsChild && targetIsOutport) {
        // Connection from child to outport - remap to external targets
        const externalTargets = outportToExternalTargets.get(conn.targetBlockId)
        if (externalTargets) {
          externalTargets.forEach(target => {
            newConnections.push({
              id: nanoid(),
              sourceBlockId: conn.sourceBlockId,
              sourcePortId: conn.sourcePortId,
              targetBlockId: target.targetBlockId,
              targetPortId: target.targetPortId,
            })
          })
        }
      }
    })

    // Remove connections that were connected to the subsystem
    const remainingConnections = currentConnections.filter(
      conn => conn.sourceBlockId !== subsystemId && conn.targetBlockId !== subsystemId
    )

    // Update the model based on current path
    if (currentPath.length === 0) {
      // At root level
      const remainingBlocks = model.blocks.filter(b => b.id !== subsystemId)
      set({
        model: {
          ...model,
          blocks: [...remainingBlocks, ...repositionedChildren],
          connections: [...remainingConnections, ...newConnections],
        },
        isDirty: true,
        selectedBlockIds: repositionedChildren.map(b => b.id),
      })
    } else {
      // Inside a subsystem - need to update the parent subsystem's children
      const updateParentSubsystem = (blocks: BlockInstance[], path: SubsystemPathItem[]): BlockInstance[] => {
        if (path.length === 0) {
          // This shouldn't happen, but handle it
          return blocks
        }

        const [current, ...rest] = path

        return blocks.map(block => {
          if (block.id === current.id && block.type === 'subsystem' && block.children) {
            if (rest.length === 0) {
              // This is the parent subsystem - update its children
              const remainingChildren = block.children.filter(b => b.id !== subsystemId)
              const remainingChildConns = (block.childConnections || []).filter(
                conn => conn.sourceBlockId !== subsystemId && conn.targetBlockId !== subsystemId
              )
              return {
                ...block,
                children: [...remainingChildren, ...repositionedChildren],
                childConnections: [...remainingChildConns, ...newConnections],
              }
            } else {
              // Recurse deeper
              return {
                ...block,
                children: updateParentSubsystem(block.children, rest),
              }
            }
          }
          return block
        })
      }

      set({
        model: {
          ...model,
          blocks: updateParentSubsystem(model.blocks, currentPath),
        },
        isDirty: true,
        selectedBlockIds: repositionedChildren.map(b => b.id),
      })
    }
  },

  enterSubsystem: (subsystemId: string) => {
    const { model, currentPath } = get()
    if (!model) return

    // Find the subsystem in the current view
    const currentBlocks = get().getCurrentBlocks()
    const subsystem = currentBlocks.find(b => b.id === subsystemId && b.type === 'subsystem')

    if (subsystem && subsystem.children) {
      set({
        currentPath: [...currentPath, { id: subsystemId, name: subsystem.name }],
        selectedBlockIds: [],
        selectedConnectionIds: [],
      })
    }
  },

  exitSubsystem: () => {
    const { currentPath } = get()
    if (currentPath.length === 0) return

    set({
      currentPath: currentPath.slice(0, -1),
      selectedBlockIds: [],
      selectedConnectionIds: [],
    })
  },

  navigateToPath: (pathIndex: number) => {
    const { currentPath } = get()
    if (pathIndex < 0 || pathIndex >= currentPath.length) {
      // Navigate to root
      set({
        currentPath: [],
        selectedBlockIds: [],
        selectedConnectionIds: [],
      })
    } else {
      set({
        currentPath: currentPath.slice(0, pathIndex + 1),
        selectedBlockIds: [],
        selectedConnectionIds: [],
      })
    }
  },

  getCurrentBlocks: () => {
    const { model, currentPath } = get()
    if (!model) return []

    if (currentPath.length === 0) {
      return model.blocks
    }

    const result = findBlockAtPath(model.blocks, currentPath)
    return result ? result.blocks : []
  },

  getCurrentConnections: () => {
    const { model, currentPath } = get()
    if (!model) return []

    if (currentPath.length === 0) {
      return model.connections
    }

    const result = findBlockAtPath(model.blocks, currentPath)
    return result ? result.connections : []
  },
}))
