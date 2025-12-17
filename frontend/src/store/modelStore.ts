import { create } from 'zustand'
import { nanoid } from '../utils/nanoid'
import type { BlockInstance, Connection, BlockDefinition } from '../types/block'
import type { Model, ModelMetadata } from '../types/model'
import type { SimulationConfig } from '../types/simulation'
import { isLibraryBlockDefinition } from '../types/library'

// Path item for subsystem navigation
interface SubsystemPathItem {
  id: string
  name: string
}

interface ModelState {
  // Current model
  model: Model | null
  isDirty: boolean

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

  // Connection operations
  addConnection: (connection: Omit<Connection, 'id'>) => string | null
  removeConnection: (connectionId: string) => void

  // Selection operations
  selectBlocks: (blockIds: string[]) => void
  selectConnections: (connectionIds: string[]) => void
  clearSelection: () => void

  // Subsystem operations
  createSubsystem: (blockIds: string[], name?: string) => string | null
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
    const { model } = get()
    if (!model) return ''

    const blockId = nanoid()
    const blockCount = model.blocks.filter((b) => b.type === definition.type).length

    const newBlock: BlockInstance = {
      id: blockId,
      type: definition.type,
      name: `${definition.name}${blockCount > 0 ? blockCount + 1 : ''}`,
      position,
      parameters: definition.parameters.reduce(
        (acc, param) => ({ ...acc, [param.name]: param.default }),
        {}
      ),
      inputPorts: definition.inputs.map((input, idx) => ({
        ...input,
        id: `${blockId}-in-${idx}`,
      })),
      outputPorts: definition.outputs.map((output, idx) => ({
        ...output,
        id: `${blockId}-out-${idx}`,
      })),
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

    set({
      model: { ...model, blocks: [...model.blocks, newBlock] },
      isDirty: true,
    })

    return blockId
  },

  removeBlock: (blockId: string) => {
    const { model } = get()
    if (!model) return

    // Remove block and all its connections
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
        blocks: updateBlockInHierarchy(model.blocks, currentPath, blockId, (b) => ({
          ...b,
          parameters: { ...b.parameters, ...parameters }
        })),
      },
      isDirty: true,
    })
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

    set({
      model: addConnectionInHierarchy(model, currentPath, newConnection),
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
