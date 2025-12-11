import { create } from 'zustand'
import { nanoid } from '../utils/nanoid'
import type { BlockInstance, Connection, BlockDefinition } from '../types/block'
import type { Model, ModelMetadata } from '../types/model'
import type { SimulationConfig } from '../types/simulation'

interface ModelState {
  // Current model
  model: Model | null
  isDirty: boolean

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

export const useModelStore = create<ModelState>((set, get) => ({
  model: null,
  isDirty: false,
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
    set({ model: newModel, isDirty: false })
  },

  loadModel: (model: Model) => {
    set({ model, isDirty: false, selectedBlockIds: [], selectedConnectionIds: [] })
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
    const { model } = get()
    if (!model) return

    set({
      model: {
        ...model,
        blocks: model.blocks.map((b) =>
          b.id === blockId ? { ...b, position } : b
        ),
      },
      isDirty: true,
    })
  },

  updateBlockParameters: (blockId: string, parameters: Record<string, unknown>) => {
    const { model } = get()
    if (!model) return

    set({
      model: {
        ...model,
        blocks: model.blocks.map((b) =>
          b.id === blockId ? { ...b, parameters: { ...b.parameters, ...parameters } } : b
        ),
      },
      isDirty: true,
    })
  },

  renameBlock: (blockId: string, name: string) => {
    const { model } = get()
    if (!model) return

    set({
      model: {
        ...model,
        blocks: model.blocks.map((b) =>
          b.id === blockId ? { ...b, name } : b
        ),
      },
      isDirty: true,
    })
  },

  addConnection: (connection: Omit<Connection, 'id'>) => {
    const { model } = get()
    if (!model) return null

    // Check if connection already exists
    const exists = model.connections.some(
      (c) =>
        c.sourceBlockId === connection.sourceBlockId &&
        c.sourcePortId === connection.sourcePortId &&
        c.targetBlockId === connection.targetBlockId &&
        c.targetPortId === connection.targetPortId
    )
    if (exists) return null

    // Check if target port already has a connection
    const targetConnected = model.connections.some(
      (c) =>
        c.targetBlockId === connection.targetBlockId &&
        c.targetPortId === connection.targetPortId
    )
    if (targetConnected) return null

    const connectionId = nanoid()
    const newConnection: Connection = { ...connection, id: connectionId }

    set({
      model: { ...model, connections: [...model.connections, newConnection] },
      isDirty: true,
    })

    return connectionId
  },

  removeConnection: (connectionId: string) => {
    const { model } = get()
    if (!model) return

    set({
      model: {
        ...model,
        connections: model.connections.filter((c) => c.id !== connectionId),
      },
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
}))
