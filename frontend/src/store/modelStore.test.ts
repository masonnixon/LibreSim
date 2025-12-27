import { describe, it, expect, beforeEach } from 'vitest'
import { useModelStore } from './modelStore'
import type { Model } from '../types/model'
import type { BlockInstance, Connection, BlockDefinition } from '../types/block'

// Helper to create a test model
function createTestModel(): Model {
  return {
    id: 'test-model-id',
    metadata: {
      name: 'Test Model',
      description: 'A test model',
      author: 'Test Author',
      createdAt: '2024-01-01T00:00:00.000Z',
      modifiedAt: '2024-01-01T00:00:00.000Z',
      version: '1.0.0',
    },
    blocks: [],
    connections: [],
    simulationConfig: {
      solver: 'rk4',
      startTime: 0,
      stopTime: 10,
      stepSize: 0.01,
    },
  }
}

// Helper to create a test block definition
function createBlockDef(type: string, name: string): BlockDefinition {
  return {
    type,
    name,
    category: 'sources',
    description: `A ${name} block`,
    inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
    outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
    parameters: [{ name: 'value', type: 'number', default: 0 }],
  }
}

describe('useModelStore', () => {
  // Reset store before each test
  beforeEach(() => {
    useModelStore.setState({
      model: null,
      isDirty: false,
      currentPath: [],
      selectedBlockIds: [],
      selectedConnectionIds: [],
    })
  })

  describe('createNewModel', () => {
    it('creates a new empty model', () => {
      useModelStore.getState().createNewModel('New Model')

      const model = useModelStore.getState().model
      expect(model).not.toBeNull()
      expect(model?.metadata.name).toBe('New Model')
      expect(model?.blocks).toEqual([])
      expect(model?.connections).toEqual([])
    })

    it('sets isDirty to false for new model', () => {
      useModelStore.getState().createNewModel('New Model')
      expect(useModelStore.getState().isDirty).toBe(false)
    })

    it('resets current path to root', () => {
      useModelStore.getState().createNewModel('New Model')
      expect(useModelStore.getState().currentPath).toEqual([])
    })

    it('sets default simulation config', () => {
      useModelStore.getState().createNewModel('New Model')

      const config = useModelStore.getState().model?.simulationConfig
      expect(config?.solver).toBe('rk4')
      expect(config?.startTime).toBe(0)
      expect(config?.stopTime).toBe(10)
      expect(config?.stepSize).toBe(0.01)
    })
  })

  describe('loadModel', () => {
    it('loads an existing model', () => {
      const model = createTestModel()
      model.metadata.name = 'Loaded Model'

      useModelStore.getState().loadModel(model)

      expect(useModelStore.getState().model?.metadata.name).toBe('Loaded Model')
    })

    it('sets isDirty to false', () => {
      useModelStore.getState().loadModel(createTestModel())
      expect(useModelStore.getState().isDirty).toBe(false)
    })

    it('clears selection', () => {
      useModelStore.setState({ selectedBlockIds: ['block-1'], selectedConnectionIds: ['conn-1'] })

      useModelStore.getState().loadModel(createTestModel())

      expect(useModelStore.getState().selectedBlockIds).toEqual([])
      expect(useModelStore.getState().selectedConnectionIds).toEqual([])
    })

    it('resets path to root', () => {
      useModelStore.setState({ currentPath: [{ id: 'sub-1', name: 'Subsystem' }] })

      useModelStore.getState().loadModel(createTestModel())

      expect(useModelStore.getState().currentPath).toEqual([])
    })
  })

  describe('saveModel', () => {
    it('returns null when no model loaded', () => {
      const result = useModelStore.getState().saveModel()
      expect(result).toBeNull()
    })

    it('returns the model and sets isDirty to false', () => {
      useModelStore.getState().createNewModel('Test Model')
      useModelStore.setState({ isDirty: true })

      const result = useModelStore.getState().saveModel()

      expect(result).not.toBeNull()
      expect(useModelStore.getState().isDirty).toBe(false)
    })

    it('updates modifiedAt timestamp', () => {
      useModelStore.getState().createNewModel('Test Model')

      const result = useModelStore.getState().saveModel()

      // The timestamp should be a valid ISO date
      expect(result?.metadata.modifiedAt).toBeDefined()
      expect(new Date(result!.metadata.modifiedAt).toISOString()).toBe(result!.metadata.modifiedAt)
    })
  })

  describe('addBlock', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('adds a block to the model', () => {
      const blockDef = createBlockDef('constant', 'Constant')
      useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      const blocks = useModelStore.getState().model?.blocks
      expect(blocks).toHaveLength(1)
      expect(blocks?.[0].type).toBe('constant')
    })

    it('returns the block ID', () => {
      const blockDef = createBlockDef('constant', 'Constant')
      const id = useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      expect(id).toBeTruthy()
      expect(typeof id).toBe('string')
    })

    it('sets block position', () => {
      const blockDef = createBlockDef('constant', 'Constant')
      useModelStore.getState().addBlock(blockDef, { x: 200, y: 300 })

      const block = useModelStore.getState().model?.blocks[0]
      expect(block?.position).toEqual({ x: 200, y: 300 })
    })

    it('generates unique names for multiple blocks of same type', () => {
      const blockDef = createBlockDef('constant', 'Constant')

      useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })
      useModelStore.getState().addBlock(blockDef, { x: 200, y: 100 })
      useModelStore.getState().addBlock(blockDef, { x: 300, y: 100 })

      const blocks = useModelStore.getState().model?.blocks
      expect(blocks?.[0].name).toBe('Constant')
      expect(blocks?.[1].name).toBe('Constant2')
      expect(blocks?.[2].name).toBe('Constant3')
    })

    it('initializes parameters with defaults', () => {
      const blockDef: BlockDefinition = {
        type: 'gain',
        name: 'Gain',
        category: 'math',
        description: 'A gain block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [{ name: 'gain', type: 'number', default: 2 }],
      }

      useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      const block = useModelStore.getState().model?.blocks[0]
      expect(block?.parameters.gain).toBe(2)
    })

    it('sets isDirty to true', () => {
      const blockDef = createBlockDef('constant', 'Constant')
      useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      expect(useModelStore.getState().isDirty).toBe(true)
    })

    it('returns empty string when no model loaded', () => {
      useModelStore.setState({ model: null })
      const blockDef = createBlockDef('constant', 'Constant')
      const id = useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      expect(id).toBe('')
    })
  })

  describe('removeBlock', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('removes a block from the model', () => {
      const blockDef = createBlockDef('constant', 'Constant')
      const id = useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      useModelStore.getState().removeBlock(id)

      expect(useModelStore.getState().model?.blocks).toHaveLength(0)
    })

    it('removes associated connections', () => {
      const blockDef1 = createBlockDef('constant', 'Constant')
      const blockDef2 = createBlockDef('scope', 'Scope')

      const id1 = useModelStore.getState().addBlock(blockDef1, { x: 100, y: 100 })
      const id2 = useModelStore.getState().addBlock(blockDef2, { x: 300, y: 100 })

      // Get the port IDs
      const blocks = useModelStore.getState().model?.blocks
      const block1 = blocks?.find(b => b.id === id1)
      const block2 = blocks?.find(b => b.id === id2)

      // Add a connection
      useModelStore.getState().addConnection({
        sourceBlockId: id1,
        sourcePortId: block1?.outputPorts[0].id || '',
        targetBlockId: id2,
        targetPortId: block2?.inputPorts[0].id || '',
      })

      // Remove the source block
      useModelStore.getState().removeBlock(id1)

      expect(useModelStore.getState().model?.connections).toHaveLength(0)
    })

    it('clears block from selection', () => {
      const blockDef = createBlockDef('constant', 'Constant')
      const id = useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      useModelStore.getState().selectBlocks([id])
      useModelStore.getState().removeBlock(id)

      expect(useModelStore.getState().selectedBlockIds).not.toContain(id)
    })
  })

  describe('updateBlockPosition', () => {
    it('updates block position', () => {
      useModelStore.getState().createNewModel('Test Model')
      const blockDef = createBlockDef('constant', 'Constant')
      const id = useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      useModelStore.getState().updateBlockPosition(id, { x: 500, y: 600 })

      const block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.position).toEqual({ x: 500, y: 600 })
    })
  })

  describe('updateBlockParameters', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('updates block parameters', () => {
      const blockDef: BlockDefinition = {
        type: 'gain',
        name: 'Gain',
        category: 'math',
        description: 'A gain block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [{ name: 'gain', type: 'number', default: 1 }],
      }

      const id = useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })
      useModelStore.getState().updateBlockParameters(id, { gain: 5 })

      const block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.parameters.gain).toBe(5)
    })

    it('updates mux block input ports when numInputs changes', () => {
      const muxDef: BlockDefinition = {
        type: 'mux',
        name: 'Mux',
        category: 'routing',
        description: 'A mux block',
        inputs: [
          { name: 'in1', dataType: 'double', dimensions: [1] },
          { name: 'in2', dataType: 'double', dimensions: [1] },
        ],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [2] }],
        parameters: [{ name: 'numInputs', type: 'number', default: 2 }],
      }

      const id = useModelStore.getState().addBlock(muxDef, { x: 100, y: 100 })
      useModelStore.getState().updateBlockParameters(id, { numInputs: 4 })

      const block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.inputPorts).toHaveLength(4)
      expect(block?.outputPorts[0].dimensions).toEqual([4])
    })

    it('updates demux block output ports when numOutputs changes', () => {
      const demuxDef: BlockDefinition = {
        type: 'demux',
        name: 'Demux',
        category: 'routing',
        description: 'A demux block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [2] }],
        outputs: [
          { name: 'out1', dataType: 'double', dimensions: [1] },
          { name: 'out2', dataType: 'double', dimensions: [1] },
        ],
        parameters: [{ name: 'numOutputs', type: 'number', default: 2 }],
      }

      const id = useModelStore.getState().addBlock(demuxDef, { x: 100, y: 100 })
      useModelStore.getState().updateBlockParameters(id, { numOutputs: 4 })

      const block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.outputPorts).toHaveLength(4)
      expect(block?.inputPorts[0].dimensions).toEqual([4])
    })

    it('updates sum block input ports when signs changes', () => {
      const sumDef: BlockDefinition = {
        type: 'sum',
        name: 'Sum',
        category: 'math',
        description: 'A sum block',
        inputs: [
          { name: 'in1', dataType: 'double', dimensions: [1] },
          { name: 'in2', dataType: 'double', dimensions: [1] },
        ],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [{ name: 'signs', type: 'string', default: '++' }],
      }

      const id = useModelStore.getState().addBlock(sumDef, { x: 100, y: 100 })
      useModelStore.getState().updateBlockParameters(id, { signs: '+-+-' })

      const block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.inputPorts).toHaveLength(4)
    })

    it('updates scope block input ports when numInputs changes', () => {
      const scopeDef: BlockDefinition = {
        type: 'scope',
        name: 'Scope',
        category: 'sinks',
        description: 'A scope block',
        inputs: [{ name: 'in1', dataType: 'double', dimensions: [1] }],
        outputs: [],
        parameters: [{ name: 'numInputs', type: 'number', default: 1 }],
      }

      const id = useModelStore.getState().addBlock(scopeDef, { x: 100, y: 100 })
      useModelStore.getState().updateBlockParameters(id, { numInputs: 3 })

      const block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.inputPorts).toHaveLength(3)
    })

    it('updates constant block output dimensions for vector values', () => {
      const constantDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [{ name: 'value', type: 'string', default: '1' }],
      }

      const id = useModelStore.getState().addBlock(constantDef, { x: 100, y: 100 })
      useModelStore.getState().updateBlockParameters(id, { value: '[1, 2, 3]' })

      const block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.outputPorts[0].dimensions).toEqual([3])
    })
  })

  describe('renameBlock', () => {
    it('renames a block', () => {
      useModelStore.getState().createNewModel('Test Model')
      const blockDef = createBlockDef('constant', 'Constant')
      const id = useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      useModelStore.getState().renameBlock(id, 'My Constant')

      const block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.name).toBe('My Constant')
    })
  })

  describe('addScopeInput', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('adds an input port to a scope block', () => {
      const scopeDef: BlockDefinition = {
        type: 'scope',
        name: 'Scope',
        category: 'sinks',
        description: 'A scope block',
        inputs: [{ name: 'in1', dataType: 'double', dimensions: [1] }],
        outputs: [],
        parameters: [{ name: 'numInputs', type: 'number', default: 1 }],
      }

      const id = useModelStore.getState().addBlock(scopeDef, { x: 100, y: 100 })
      const newPortId = useModelStore.getState().addScopeInput(id)

      expect(newPortId).toBeTruthy()

      const block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.inputPorts).toHaveLength(2)
      expect(block?.parameters.numInputs).toBe(2)
    })

    it('returns null for non-scope blocks', () => {
      const constantDef = createBlockDef('constant', 'Constant')
      const id = useModelStore.getState().addBlock(constantDef, { x: 100, y: 100 })

      const result = useModelStore.getState().addScopeInput(id)

      expect(result).toBeNull()
    })

    it('returns null when no model loaded', () => {
      useModelStore.setState({ model: null })
      const result = useModelStore.getState().addScopeInput('some-id')
      expect(result).toBeNull()
    })
  })

  describe('connections', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('adds a connection between blocks', () => {
      const constDef = createBlockDef('constant', 'Constant')
      const scopeDef: BlockDefinition = {
        type: 'scope',
        name: 'Scope',
        category: 'sinks',
        description: 'A scope block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [],
        parameters: [],
      }

      const id1 = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      const id2 = useModelStore.getState().addBlock(scopeDef, { x: 300, y: 100 })

      const blocks = useModelStore.getState().model?.blocks
      const block1 = blocks?.find(b => b.id === id1)
      const block2 = blocks?.find(b => b.id === id2)

      const connId = useModelStore.getState().addConnection({
        sourceBlockId: id1,
        sourcePortId: block1?.outputPorts[0].id || '',
        targetBlockId: id2,
        targetPortId: block2?.inputPorts[0].id || '',
      })

      expect(connId).toBeTruthy()
      expect(useModelStore.getState().model?.connections).toHaveLength(1)
    })

    it('prevents duplicate connections', () => {
      const constDef = createBlockDef('constant', 'Constant')
      const scopeDef: BlockDefinition = {
        type: 'scope',
        name: 'Scope',
        category: 'sinks',
        description: 'A scope block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [],
        parameters: [],
      }

      const id1 = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      const id2 = useModelStore.getState().addBlock(scopeDef, { x: 300, y: 100 })

      const blocks = useModelStore.getState().model?.blocks
      const block1 = blocks?.find(b => b.id === id1)
      const block2 = blocks?.find(b => b.id === id2)

      const connection = {
        sourceBlockId: id1,
        sourcePortId: block1?.outputPorts[0].id || '',
        targetBlockId: id2,
        targetPortId: block2?.inputPorts[0].id || '',
      }

      useModelStore.getState().addConnection(connection)
      const secondResult = useModelStore.getState().addConnection(connection)

      expect(secondResult).toBeNull()
      expect(useModelStore.getState().model?.connections).toHaveLength(1)
    })

    it('prevents connecting to already connected input port', () => {
      const constDef = createBlockDef('constant', 'Constant')
      const scopeDef: BlockDefinition = {
        type: 'scope',
        name: 'Scope',
        category: 'sinks',
        description: 'A scope block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [],
        parameters: [],
      }

      const id1 = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      const id2 = useModelStore.getState().addBlock(constDef, { x: 100, y: 200 })
      const id3 = useModelStore.getState().addBlock(scopeDef, { x: 300, y: 100 })

      const blocks = useModelStore.getState().model?.blocks
      const block1 = blocks?.find(b => b.id === id1)
      const block2 = blocks?.find(b => b.id === id2)
      const block3 = blocks?.find(b => b.id === id3)

      // First connection
      useModelStore.getState().addConnection({
        sourceBlockId: id1,
        sourcePortId: block1?.outputPorts[0].id || '',
        targetBlockId: id3,
        targetPortId: block3?.inputPorts[0].id || '',
      })

      // Second connection to same target port should fail
      const result = useModelStore.getState().addConnection({
        sourceBlockId: id2,
        sourcePortId: block2?.outputPorts[0].id || '',
        targetBlockId: id3,
        targetPortId: block3?.inputPorts[0].id || '',
      })

      expect(result).toBeNull()
    })

    it('removes a connection', () => {
      const constDef = createBlockDef('constant', 'Constant')
      const scopeDef: BlockDefinition = {
        type: 'scope',
        name: 'Scope',
        category: 'sinks',
        description: 'A scope block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [],
        parameters: [],
      }

      const id1 = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      const id2 = useModelStore.getState().addBlock(scopeDef, { x: 300, y: 100 })

      const blocks = useModelStore.getState().model?.blocks
      const block1 = blocks?.find(b => b.id === id1)
      const block2 = blocks?.find(b => b.id === id2)

      const connId = useModelStore.getState().addConnection({
        sourceBlockId: id1,
        sourcePortId: block1?.outputPorts[0].id || '',
        targetBlockId: id2,
        targetPortId: block2?.inputPorts[0].id || '',
      })

      useModelStore.getState().removeConnection(connId!)

      expect(useModelStore.getState().model?.connections).toHaveLength(0)
    })
  })

  describe('selection', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('selects blocks', () => {
      const blockDef = createBlockDef('constant', 'Constant')
      const id1 = useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })
      const id2 = useModelStore.getState().addBlock(blockDef, { x: 200, y: 100 })

      useModelStore.getState().selectBlocks([id1, id2])

      expect(useModelStore.getState().selectedBlockIds).toEqual([id1, id2])
      expect(useModelStore.getState().selectedConnectionIds).toEqual([])
    })

    it('selects connections', () => {
      useModelStore.getState().selectConnections(['conn-1', 'conn-2'])

      expect(useModelStore.getState().selectedConnectionIds).toEqual(['conn-1', 'conn-2'])
      expect(useModelStore.getState().selectedBlockIds).toEqual([])
    })

    it('clears selection', () => {
      useModelStore.setState({
        selectedBlockIds: ['block-1'],
        selectedConnectionIds: ['conn-1'],
      })

      useModelStore.getState().clearSelection()

      expect(useModelStore.getState().selectedBlockIds).toEqual([])
      expect(useModelStore.getState().selectedConnectionIds).toEqual([])
    })
  })

  describe('simulation config', () => {
    it('updates simulation config', () => {
      useModelStore.getState().createNewModel('Test Model')

      useModelStore.getState().updateSimulationConfig({
        solver: 'euler',
        stopTime: 20,
      })

      const config = useModelStore.getState().model?.simulationConfig
      expect(config?.solver).toBe('euler')
      expect(config?.stopTime).toBe(20)
      expect(config?.stepSize).toBe(0.01) // Unchanged
    })
  })

  describe('metadata', () => {
    it('updates metadata', () => {
      useModelStore.getState().createNewModel('Test Model')

      useModelStore.getState().updateMetadata({
        description: 'Updated description',
        author: 'New Author',
      })

      const metadata = useModelStore.getState().model?.metadata
      expect(metadata?.description).toBe('Updated description')
      expect(metadata?.author).toBe('New Author')
      expect(metadata?.name).toBe('Test Model') // Unchanged
    })
  })

  describe('subsystem operations', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('creates a subsystem from selected blocks', () => {
      const constDef = createBlockDef('constant', 'Constant')
      const gainDef: BlockDefinition = {
        type: 'gain',
        name: 'Gain',
        category: 'math',
        description: 'A gain block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [{ name: 'gain', type: 'number', default: 2 }],
      }

      const id1 = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      const id2 = useModelStore.getState().addBlock(gainDef, { x: 300, y: 100 })

      // Connect them
      const blocks = useModelStore.getState().model?.blocks
      const block1 = blocks?.find(b => b.id === id1)
      const block2 = blocks?.find(b => b.id === id2)

      useModelStore.getState().addConnection({
        sourceBlockId: id1,
        sourcePortId: block1?.outputPorts[0].id || '',
        targetBlockId: id2,
        targetPortId: block2?.inputPorts[0].id || '',
      })

      // Create subsystem
      const subsystemId = useModelStore.getState().createSubsystem([id1, id2], 'MySubsystem')

      expect(subsystemId).toBeTruthy()

      const model = useModelStore.getState().model
      const subsystem = model?.blocks.find(b => b.id === subsystemId)

      expect(subsystem).toBeDefined()
      expect(subsystem?.type).toBe('subsystem')
      expect(subsystem?.name).toBe('MySubsystem')
      expect(subsystem?.children).toBeDefined()
    })

    it('returns null when creating subsystem with empty block list', () => {
      const result = useModelStore.getState().createSubsystem([])
      expect(result).toBeNull()
    })

    it('enters a subsystem', () => {
      // Create a subsystem block manually
      const subsystemBlock: BlockInstance = {
        id: 'subsystem-1',
        type: 'subsystem',
        name: 'TestSubsystem',
        position: { x: 100, y: 100 },
        parameters: {},
        inputPorts: [],
        outputPorts: [],
        children: [
          {
            id: 'child-1',
            type: 'constant',
            name: 'ChildConstant',
            position: { x: 100, y: 100 },
            parameters: { value: 1 },
            inputPorts: [],
            outputPorts: [{ id: 'out-0', name: 'out', dataType: 'double', dimensions: [1] }],
          },
        ],
        childConnections: [],
      }

      useModelStore.setState({
        model: {
          ...useModelStore.getState().model!,
          blocks: [subsystemBlock],
        },
      })

      useModelStore.getState().enterSubsystem('subsystem-1')

      expect(useModelStore.getState().currentPath).toEqual([
        { id: 'subsystem-1', name: 'TestSubsystem' },
      ])
    })

    it('exits a subsystem', () => {
      useModelStore.setState({
        currentPath: [
          { id: 'subsystem-1', name: 'Subsystem1' },
          { id: 'subsystem-2', name: 'Subsystem2' },
        ],
      })

      useModelStore.getState().exitSubsystem()

      expect(useModelStore.getState().currentPath).toEqual([
        { id: 'subsystem-1', name: 'Subsystem1' },
      ])
    })

    it('navigates to a specific path index', () => {
      useModelStore.setState({
        currentPath: [
          { id: 'sub-1', name: 'Sub1' },
          { id: 'sub-2', name: 'Sub2' },
          { id: 'sub-3', name: 'Sub3' },
        ],
      })

      useModelStore.getState().navigateToPath(0)

      expect(useModelStore.getState().currentPath).toEqual([
        { id: 'sub-1', name: 'Sub1' },
      ])
    })

    it('navigates to root when path index is negative', () => {
      useModelStore.setState({
        currentPath: [{ id: 'sub-1', name: 'Sub1' }],
      })

      useModelStore.getState().navigateToPath(-1)

      expect(useModelStore.getState().currentPath).toEqual([])
    })

    it('toggles subsystem expanded state', () => {
      const subsystemBlock: BlockInstance = {
        id: 'subsystem-1',
        type: 'subsystem',
        name: 'TestSubsystem',
        position: { x: 100, y: 100 },
        parameters: {},
        inputPorts: [],
        outputPorts: [],
        children: [],
        childConnections: [],
        isExpanded: false,
      }

      useModelStore.setState({
        model: {
          ...useModelStore.getState().model!,
          blocks: [subsystemBlock],
        },
      })

      useModelStore.getState().toggleSubsystemExpanded('subsystem-1')

      const block = useModelStore.getState().model?.blocks.find(b => b.id === 'subsystem-1')
      expect(block?.isExpanded).toBe(true)

      useModelStore.getState().toggleSubsystemExpanded('subsystem-1')

      const block2 = useModelStore.getState().model?.blocks.find(b => b.id === 'subsystem-1')
      expect(block2?.isExpanded).toBe(false)
    })
  })

  describe('getCurrentBlocks and getCurrentConnections', () => {
    it('returns root level blocks when at root', () => {
      useModelStore.getState().createNewModel('Test Model')
      const blockDef = createBlockDef('constant', 'Constant')
      useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      const currentBlocks = useModelStore.getState().getCurrentBlocks()
      expect(currentBlocks).toHaveLength(1)
    })

    it('returns empty array when no model', () => {
      useModelStore.setState({ model: null })
      expect(useModelStore.getState().getCurrentBlocks()).toEqual([])
      expect(useModelStore.getState().getCurrentConnections()).toEqual([])
    })

    it('returns subsystem children when inside a subsystem', () => {
      useModelStore.getState().createNewModel('Test Model')

      const subsystemBlock: BlockInstance = {
        id: 'subsystem-1',
        type: 'subsystem',
        name: 'TestSubsystem',
        position: { x: 100, y: 100 },
        parameters: {},
        inputPorts: [],
        outputPorts: [],
        children: [
          {
            id: 'child-1',
            type: 'constant',
            name: 'ChildConstant',
            position: { x: 100, y: 100 },
            parameters: {},
            inputPorts: [],
            outputPorts: [],
          },
        ],
        childConnections: [
          {
            id: 'child-conn-1',
            sourceBlockId: 'child-1',
            sourcePortId: 'out-0',
            targetBlockId: 'child-2',
            targetPortId: 'in-0',
          },
        ],
      }

      useModelStore.setState({
        model: {
          ...useModelStore.getState().model!,
          blocks: [subsystemBlock],
        },
        currentPath: [{ id: 'subsystem-1', name: 'TestSubsystem' }],
      })

      const currentBlocks = useModelStore.getState().getCurrentBlocks()
      expect(currentBlocks).toHaveLength(1)
      expect(currentBlocks[0].id).toBe('child-1')

      const currentConnections = useModelStore.getState().getCurrentConnections()
      expect(currentConnections).toHaveLength(1)
    })
  })
})
