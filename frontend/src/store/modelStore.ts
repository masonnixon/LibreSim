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
}))
