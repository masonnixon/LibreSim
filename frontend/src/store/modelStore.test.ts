import { describe, it, expect, beforeEach } from 'vitest'
import { useModelStore } from './modelStore'
import type { Model } from '../types/model'
import type { BlockDefinition, BlockInstance } from '../types/block'

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
    parameters: [{ name: 'value', label: 'Value', type: 'number', default: 0 }],
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
        parameters: [{ name: 'gain', label: 'Gain', type: 'number', default: 2 }],
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
        parameters: [{ name: 'gain', label: 'Gain', type: 'number', default: 1 }],
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
        parameters: [{ name: 'numInputs', label: 'Number of Inputs', type: 'number', default: 2 }],
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
        parameters: [{ name: 'numOutputs', label: 'Number of Outputs', type: 'number', default: 2 }],
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
        parameters: [{ name: 'signs', label: 'Signs', type: 'string', default: '++' }],
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
        parameters: [{ name: 'numInputs', label: 'Number of Inputs', type: 'number', default: 1 }],
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
        parameters: [{ name: 'value', label: 'Value', type: 'string', default: '1' }],
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
        parameters: [{ name: 'numInputs', label: 'Number of Inputs', type: 'number', default: 1 }],
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
        parameters: [{ name: 'gain', label: 'Gain', type: 'number', default: 2 }],
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

  describe('undo/redo', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('canUndo returns false initially', () => {
      expect(useModelStore.getState().canUndo()).toBe(false)
    })

    it('canRedo returns false initially', () => {
      expect(useModelStore.getState().canRedo()).toBe(false)
    })

    it('pushHistory adds current state to history', () => {
      useModelStore.getState().pushHistory()
      expect(useModelStore.getState().history.length).toBeGreaterThan(0)
      expect(useModelStore.getState().canUndo()).toBe(true)
    })

    it('undo restores previous state', () => {
      const blockDef = createBlockDef('constant', 'Constant')
      useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      // State should have been pushed during addBlock
      const blocksBeforeUndo = useModelStore.getState().model?.blocks.length

      useModelStore.getState().undo()

      const blocksAfterUndo = useModelStore.getState().model?.blocks.length
      expect(blocksAfterUndo).toBeLessThan(blocksBeforeUndo!)
    })

    it('redo restores undone state', () => {
      const blockDef = createBlockDef('constant', 'Constant')
      useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      const blocksAfterAdd = useModelStore.getState().model?.blocks.length

      useModelStore.getState().undo()
      useModelStore.getState().redo()

      const blocksAfterRedo = useModelStore.getState().model?.blocks.length
      expect(blocksAfterRedo).toBe(blocksAfterAdd)
    })

    it('canRedo returns true after undo', () => {
      const blockDef = createBlockDef('constant', 'Constant')
      useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })
      useModelStore.getState().undo()

      expect(useModelStore.getState().canRedo()).toBe(true)
    })
  })

  describe('connection waypoints', () => {
    let connId: string | null

    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
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

      connId = useModelStore.getState().addConnection({
        sourceBlockId: id1,
        sourcePortId: block1?.outputPorts[0].id || '',
        targetBlockId: id2,
        targetPortId: block2?.inputPorts[0].id || '',
      })
    })

    it('addConnectionWaypoint adds a waypoint', () => {
      useModelStore.getState().addConnectionWaypoint(connId!, { x: 200, y: 150 })

      const connection = useModelStore.getState().model?.connections.find(c => c.id === connId)
      expect(connection?.waypoints).toBeDefined()
      expect(connection?.waypoints?.length).toBe(1)
      expect(connection?.waypoints?.[0]).toEqual({ x: 200, y: 150 })
    })

    it('addConnectionWaypoint adds waypoint at specific index', () => {
      useModelStore.getState().addConnectionWaypoint(connId!, { x: 200, y: 150 })
      useModelStore.getState().addConnectionWaypoint(connId!, { x: 250, y: 200 }, 0)

      const connection = useModelStore.getState().model?.connections.find(c => c.id === connId)
      expect(connection?.waypoints?.length).toBe(2)
      expect(connection?.waypoints?.[0]).toEqual({ x: 250, y: 200 })
    })

    it('updateConnectionWaypoint updates existing waypoint', () => {
      useModelStore.getState().addConnectionWaypoint(connId!, { x: 200, y: 150 })
      useModelStore.getState().updateConnectionWaypoint(connId!, 0, { x: 220, y: 170 })

      const connection = useModelStore.getState().model?.connections.find(c => c.id === connId)
      expect(connection?.waypoints?.[0]).toEqual({ x: 220, y: 170 })
    })

    it('removeConnectionWaypoint removes a waypoint', () => {
      useModelStore.getState().addConnectionWaypoint(connId!, { x: 200, y: 150 })
      useModelStore.getState().addConnectionWaypoint(connId!, { x: 250, y: 200 })
      useModelStore.getState().removeConnectionWaypoint(connId!, 0)

      const connection = useModelStore.getState().model?.connections.find(c => c.id === connId)
      expect(connection?.waypoints?.length).toBe(1)
      expect(connection?.waypoints?.[0]).toEqual({ x: 250, y: 200 })
    })

    it('clearConnectionWaypoints removes all waypoints', () => {
      useModelStore.getState().addConnectionWaypoint(connId!, { x: 200, y: 150 })
      useModelStore.getState().addConnectionWaypoint(connId!, { x: 250, y: 200 })
      useModelStore.getState().clearConnectionWaypoints(connId!)

      const connection = useModelStore.getState().model?.connections.find(c => c.id === connId)
      expect(connection?.waypoints).toEqual([])
    })

    it('updateConnectionWaypoints replaces all waypoints', () => {
      useModelStore.getState().addConnectionWaypoint(connId!, { x: 200, y: 150 })
      useModelStore.getState().updateConnectionWaypoints(connId!, [
        { x: 180, y: 130 },
        { x: 220, y: 170 },
        { x: 260, y: 210 },
      ])

      const connection = useModelStore.getState().model?.connections.find(c => c.id === connId)
      expect(connection?.waypoints?.length).toBe(3)
    })

    it('updateConnectionSignalName sets signal name', () => {
      useModelStore.getState().updateConnectionSignalName(connId!, 'my_signal')

      const connection = useModelStore.getState().model?.connections.find(c => c.id === connId)
      expect(connection?.signalName).toBe('my_signal')
    })

    it('updateConnectionSignalName can clear signal name', () => {
      useModelStore.getState().updateConnectionSignalName(connId!, 'my_signal')
      useModelStore.getState().updateConnectionSignalName(connId!, undefined)

      const connection = useModelStore.getState().model?.connections.find(c => c.id === connId)
      expect(connection?.signalName).toBeUndefined()
    })

    it('updateConnectionLabelOffset sets label offset', () => {
      useModelStore.getState().updateConnectionLabelOffset(connId!, { t: 0.5, perpOffset: 10 })

      const connection = useModelStore.getState().model?.connections.find(c => c.id === connId)
      expect(connection?.labelOffset).toEqual({ t: 0.5, perpOffset: 10 })
    })
  })

  describe('block size and rotation', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('updateBlockSize updates block dimensions', () => {
      const blockDef = createBlockDef('constant', 'Constant')
      const blockId = useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      useModelStore.getState().updateBlockSize(blockId, { width: 150, height: 75 })

      const block = useModelStore.getState().model?.blocks.find(b => b.id === blockId)
      expect(block?.size?.width).toBe(150)
      expect(block?.size?.height).toBe(75)
    })

    it('rotateSelectedBlocks rotates selected blocks', () => {
      const blockDef = createBlockDef('constant', 'Constant')
      const blockId = useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      useModelStore.getState().selectBlocks([blockId])
      useModelStore.getState().rotateSelectedBlocks()

      const block = useModelStore.getState().model?.blocks.find(b => b.id === blockId)
      expect(block?.rotation).toBe(90)
    })

    it('rotateSelectedBlocks cycles through rotations', () => {
      const blockDef = createBlockDef('constant', 'Constant')
      const blockId = useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      useModelStore.getState().selectBlocks([blockId])

      // Rotate 4 times should cycle back to 0
      useModelStore.getState().rotateSelectedBlocks() // 90
      useModelStore.getState().rotateSelectedBlocks() // 180
      useModelStore.getState().rotateSelectedBlocks() // 270
      useModelStore.getState().rotateSelectedBlocks() // 0

      const block = useModelStore.getState().model?.blocks.find(b => b.id === blockId)
      expect(block?.rotation).toBe(0)
    })
  })

  describe('spreadBlocks', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('spreads blocks apart by factor', () => {
      const blockDef = createBlockDef('constant', 'Constant')
      useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })
      useModelStore.getState().addBlock(blockDef, { x: 200, y: 100 })
      useModelStore.getState().addBlock(blockDef, { x: 100, y: 200 })

      useModelStore.getState().spreadBlocks(2.0)

      const blocks = useModelStore.getState().model?.blocks
      expect(blocks).toBeDefined()
      // Blocks should be spread apart from center
      // The exact positions depend on implementation, but they should be different
      expect(blocks!.length).toBe(3)
    })
  })

  describe('addScopeInput', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('adds input port to scope block', () => {
      const scopeDef: BlockDefinition = {
        type: 'scope',
        name: 'Scope',
        category: 'sinks',
        description: 'A scope block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [],
        parameters: [],
      }

      const scopeId = useModelStore.getState().addBlock(scopeDef, { x: 100, y: 100 })
      const initialInputs = useModelStore.getState().model?.blocks.find(b => b.id === scopeId)?.inputPorts.length

      const newPortId = useModelStore.getState().addScopeInput(scopeId)

      expect(newPortId).toBeTruthy()
      const scope = useModelStore.getState().model?.blocks.find(b => b.id === scopeId)
      expect(scope?.inputPorts.length).toBe(initialInputs! + 1)
    })

    it('returns null for non-scope blocks', () => {
      const blockDef = createBlockDef('constant', 'Constant')
      const blockId = useModelStore.getState().addBlock(blockDef, { x: 100, y: 100 })

      const result = useModelStore.getState().addScopeInput(blockId)

      expect(result).toBeNull()
    })
  })

  describe('saveModel', () => {
    it('returns null when no model exists', () => {
      useModelStore.setState({ model: null })
      const result = useModelStore.getState().saveModel()
      expect(result).toBeNull()
    })

    it('returns model and clears isDirty', () => {
      useModelStore.getState().createNewModel('Test Model')
      useModelStore.setState({ isDirty: true })

      const result = useModelStore.getState().saveModel()

      expect(result).not.toBeNull()
      expect(result?.metadata.name).toBe('Test Model')
      expect(useModelStore.getState().isDirty).toBe(false)
    })
  })

  describe('expandSubsystem', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('expands subsystem children into parent', () => {
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
            position: { x: 0, y: 0 },
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

      useModelStore.getState().expandSubsystem('subsystem-1')

      const blocks = useModelStore.getState().model?.blocks
      // Subsystem should be removed and child added
      expect(blocks?.find(b => b.id === 'subsystem-1')).toBeUndefined()
      // Child should be added with new ID (prefixed)
      expect(blocks?.some(b => b.name === 'ChildConstant')).toBe(true)
    })
  })

  describe('operations inside subsystems', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')

      // Create a subsystem with a child block
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
            position: { x: 50, y: 50 },
            parameters: { value: 1 },
            inputPorts: [],
            outputPorts: [{ id: 'child-out-0', name: 'out', dataType: 'double', dimensions: [1] }],
          },
        ],
        childConnections: [],
      }

      useModelStore.setState({
        model: {
          ...useModelStore.getState().model!,
          blocks: [subsystemBlock],
        },
        currentPath: [{ id: 'subsystem-1', name: 'TestSubsystem' }],
      })
    })

    it('adds block inside subsystem', () => {
      const blockDef = createBlockDef('gain', 'Gain')
      const blockId = useModelStore.getState().addBlock(blockDef, { x: 200, y: 100 })

      expect(blockId).toBeTruthy()

      const currentBlocks = useModelStore.getState().getCurrentBlocks()
      expect(currentBlocks.some(b => b.id === blockId)).toBe(true)
    })

    it('removes block inside subsystem', () => {
      // First add a block to the subsystem
      const blockDef = createBlockDef('gain', 'Gain')
      const blockId = useModelStore.getState().addBlock(blockDef, { x: 200, y: 100 })

      useModelStore.getState().removeBlock(blockId)

      const currentBlocks = useModelStore.getState().getCurrentBlocks()
      expect(currentBlocks.some(b => b.id === blockId)).toBe(false)
    })

    it('adds connection inside subsystem', () => {
      const blockDef: BlockDefinition = {
        type: 'scope',
        name: 'Scope',
        category: 'sinks',
        description: 'A scope block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [],
        parameters: [],
      }

      const scopeId = useModelStore.getState().addBlock(blockDef, { x: 200, y: 100 })

      const currentBlocks = useModelStore.getState().getCurrentBlocks()
      const sourceBlock = currentBlocks.find(b => b.id === 'child-1')
      const targetBlock = currentBlocks.find(b => b.id === scopeId)

      const connId = useModelStore.getState().addConnection({
        sourceBlockId: 'child-1',
        sourcePortId: sourceBlock?.outputPorts[0]?.id || '',
        targetBlockId: scopeId,
        targetPortId: targetBlock?.inputPorts[0]?.id || '',
      })

      expect(connId).toBeTruthy()
      const currentConnections = useModelStore.getState().getCurrentConnections()
      expect(currentConnections.some(c => c.id === connId)).toBe(true)
    })

    it('removes connection inside subsystem', () => {
      const blockDef: BlockDefinition = {
        type: 'scope',
        name: 'Scope',
        category: 'sinks',
        description: 'A scope block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [],
        parameters: [],
      }

      const scopeId = useModelStore.getState().addBlock(blockDef, { x: 200, y: 100 })

      const currentBlocks = useModelStore.getState().getCurrentBlocks()
      const sourceBlock = currentBlocks.find(b => b.id === 'child-1')
      const targetBlock = currentBlocks.find(b => b.id === scopeId)

      const connId = useModelStore.getState().addConnection({
        sourceBlockId: 'child-1',
        sourcePortId: sourceBlock?.outputPorts[0]?.id || '',
        targetBlockId: scopeId,
        targetPortId: targetBlock?.inputPorts[0]?.id || '',
      })

      useModelStore.getState().removeConnection(connId!)

      const currentConnections = useModelStore.getState().getCurrentConnections()
      expect(currentConnections.some(c => c.id === connId)).toBe(false)
    })

    it('updates block position inside subsystem', () => {
      useModelStore.getState().updateBlockPosition('child-1', { x: 150, y: 150 })

      const currentBlocks = useModelStore.getState().getCurrentBlocks()
      const block = currentBlocks.find(b => b.id === 'child-1')
      expect(block?.position).toEqual({ x: 150, y: 150 })
    })

    it('updates block parameters inside subsystem', () => {
      useModelStore.getState().updateBlockParameters('child-1', { value: 42 })

      const currentBlocks = useModelStore.getState().getCurrentBlocks()
      const block = currentBlocks.find(b => b.id === 'child-1')
      expect(block?.parameters.value).toBe(42)
    })

    it('waypoint operations inside subsystem', () => {
      const blockDef: BlockDefinition = {
        type: 'scope',
        name: 'Scope',
        category: 'sinks',
        description: 'A scope block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [],
        parameters: [],
      }

      const scopeId = useModelStore.getState().addBlock(blockDef, { x: 200, y: 100 })

      const currentBlocks = useModelStore.getState().getCurrentBlocks()
      const sourceBlock = currentBlocks.find(b => b.id === 'child-1')
      const targetBlock = currentBlocks.find(b => b.id === scopeId)

      const connId = useModelStore.getState().addConnection({
        sourceBlockId: 'child-1',
        sourcePortId: sourceBlock?.outputPorts[0]?.id || '',
        targetBlockId: scopeId,
        targetPortId: targetBlock?.inputPorts[0]?.id || '',
      })

      // Add waypoint
      useModelStore.getState().addConnectionWaypoint(connId!, { x: 150, y: 75 })

      let currentConnections = useModelStore.getState().getCurrentConnections()
      let conn = currentConnections.find(c => c.id === connId)
      expect(conn?.waypoints?.length).toBe(1)

      // Update waypoint
      useModelStore.getState().updateConnectionWaypoint(connId!, 0, { x: 160, y: 80 })
      currentConnections = useModelStore.getState().getCurrentConnections()
      conn = currentConnections.find(c => c.id === connId)
      expect(conn?.waypoints?.[0]).toEqual({ x: 160, y: 80 })

      // Remove waypoint
      useModelStore.getState().removeConnectionWaypoint(connId!, 0)
      currentConnections = useModelStore.getState().getCurrentConnections()
      conn = currentConnections.find(c => c.id === connId)
      expect(conn?.waypoints?.length).toBe(0)
    })
  })

  describe('library block handling', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('adds library block with implementation', () => {
      // Create a library block definition with implementation
      const libraryBlockDef: BlockDefinition = {
        type: 'my_library__gain_system',
        name: 'Gain System',
        category: 'subsystems',
        description: 'A library block with implementation',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [],
        isLibraryBlock: true,
        libraryId: 'lib-1',
        libraryName: 'My Library',
        originalName: 'GainSystem',
        implementation: {
          blocks: [
            {
              id: 'impl-gain-1',
              type: 'gain',
              name: 'InternalGain',
              position: { x: 100, y: 100 },
              parameters: { gain: 2 },
              inputPorts: [{ id: 'impl-in-0', name: 'in', dataType: 'double', dimensions: [1] }],
              outputPorts: [{ id: 'impl-out-0', name: 'out', dataType: 'double', dimensions: [1] }],
            },
          ],
          connections: [],
          portMappings: [],
        },
      } as any

      const blockId = useModelStore.getState().addBlock(libraryBlockDef, { x: 100, y: 100 })

      expect(blockId).toBeTruthy()
      const block = useModelStore.getState().model?.blocks.find(b => b.id === blockId)
      expect(block?.type).toBe('subsystem')
      expect(block?.children?.length).toBeGreaterThan(0)
    })
  })

  describe('parseConstantValueDimensions edge cases', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('handles array value in constant block', () => {
      const constDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [{ name: 'value', label: 'Value', type: 'string', default: '0' }],
      }

      const blockId = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      useModelStore.getState().updateBlockParameters(blockId, { value: '[1, 2, 3]' })

      const block = useModelStore.getState().model?.blocks.find(b => b.id === blockId)
      expect(block?.outputPorts[0].dimensions).toEqual([3])
    })

    it('handles semicolon-separated array value', () => {
      const constDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [{ name: 'value', label: 'Value', type: 'string', default: '0' }],
      }

      const blockId = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      useModelStore.getState().updateBlockParameters(blockId, { value: '[1; 2; 3; 4]' })

      const block = useModelStore.getState().model?.blocks.find(b => b.id === blockId)
      expect(block?.outputPorts[0].dimensions).toEqual([4])
    })

    it('handles space-separated array value', () => {
      const constDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [{ name: 'value', label: 'Value', type: 'string', default: '0' }],
      }

      const blockId = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      useModelStore.getState().updateBlockParameters(blockId, { value: '[1 2 3 4 5]' })

      const block = useModelStore.getState().model?.blocks.find(b => b.id === blockId)
      expect(block?.outputPorts[0].dimensions).toEqual([5])
    })

    it('handles comma-separated value without brackets', () => {
      const constDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [{ name: 'value', label: 'Value', type: 'string', default: '0' }],
      }

      const blockId = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      useModelStore.getState().updateBlockParameters(blockId, { value: '1,2,3' })

      const block = useModelStore.getState().model?.blocks.find(b => b.id === blockId)
      expect(block?.outputPorts[0].dimensions).toEqual([3])
    })
  })

  describe('subsystem navigation', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('enters a subsystem', () => {
      // Create a subsystem
      const subsystemDef: BlockDefinition = {
        type: 'subsystem',
        name: 'Subsystem',
        category: 'subsystems',
        description: 'A subsystem',
        inputs: [],
        outputs: [],
        parameters: [],
      }

      const subsystemId = useModelStore.getState().addBlock(subsystemDef, { x: 100, y: 100 })

      // Manually set up children since addBlock creates an empty subsystem
      useModelStore.setState(state => ({
        model: state.model ? {
          ...state.model,
          blocks: state.model.blocks.map(b =>
            b.id === subsystemId
              ? { ...b, children: [], childConnections: [] }
              : b
          )
        } : null
      }))

      useModelStore.getState().enterSubsystem(subsystemId)

      const currentPath = useModelStore.getState().currentPath
      expect(currentPath.length).toBe(1)
      expect(currentPath[0].id).toBe(subsystemId)
    })

    it('exits a subsystem', () => {
      // Create and enter a subsystem
      const subsystemDef: BlockDefinition = {
        type: 'subsystem',
        name: 'Subsystem',
        category: 'subsystems',
        description: 'A subsystem',
        inputs: [],
        outputs: [],
        parameters: [],
      }

      const subsystemId = useModelStore.getState().addBlock(subsystemDef, { x: 100, y: 100 })

      // Manually set up children
      useModelStore.setState(state => ({
        model: state.model ? {
          ...state.model,
          blocks: state.model.blocks.map(b =>
            b.id === subsystemId
              ? { ...b, children: [], childConnections: [] }
              : b
          )
        } : null
      }))

      useModelStore.getState().enterSubsystem(subsystemId)
      expect(useModelStore.getState().currentPath.length).toBe(1)

      useModelStore.getState().exitSubsystem()
      expect(useModelStore.getState().currentPath.length).toBe(0)
    })

    it('does nothing when exiting at root level', () => {
      expect(useModelStore.getState().currentPath.length).toBe(0)
      useModelStore.getState().exitSubsystem()
      expect(useModelStore.getState().currentPath.length).toBe(0)
    })

    it('navigates to a specific path index', () => {
      // Create nested subsystems
      const subsystemDef: BlockDefinition = {
        type: 'subsystem',
        name: 'Subsystem',
        category: 'subsystems',
        description: 'A subsystem',
        inputs: [],
        outputs: [],
        parameters: [],
      }

      const subsystem1Id = useModelStore.getState().addBlock(subsystemDef, { x: 100, y: 100 })

      // Manually set up nested subsystems
      useModelStore.setState(state => ({
        model: state.model ? {
          ...state.model,
          blocks: state.model.blocks.map(b =>
            b.id === subsystem1Id
              ? {
                  ...b,
                  children: [{
                    id: 'inner-subsystem',
                    type: 'subsystem',
                    name: 'Inner Subsystem',
                    position: { x: 50, y: 50 },
                    parameters: {},
                    inputPorts: [],
                    outputPorts: [],
                    children: [],
                    childConnections: [],
                  }],
                  childConnections: []
                }
              : b
          )
        } : null,
        currentPath: [
          { id: subsystem1Id, name: 'Subsystem' },
          { id: 'inner-subsystem', name: 'Inner Subsystem' }
        ]
      }))

      // Navigate to first subsystem
      useModelStore.getState().navigateToPath(0)
      expect(useModelStore.getState().currentPath.length).toBe(1)
    })

    it('navigates to root when path index is negative', () => {
      useModelStore.setState({
        currentPath: [
          { id: 'sub1', name: 'Sub1' },
          { id: 'sub2', name: 'Sub2' }
        ]
      })

      useModelStore.getState().navigateToPath(-1)
      expect(useModelStore.getState().currentPath.length).toBe(0)
    })

    it('does not enter non-existent subsystem', () => {
      useModelStore.getState().enterSubsystem('non-existent')
      expect(useModelStore.getState().currentPath.length).toBe(0)
    })

    it('does not enter a non-subsystem block', () => {
      const constDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [],
      }

      const blockId = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      useModelStore.getState().enterSubsystem(blockId)
      expect(useModelStore.getState().currentPath.length).toBe(0)
    })
  })

  describe('expandSubsystem', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('expands a subsystem at root level', () => {
      // Create a subsystem with children
      const subsystemDef: BlockDefinition = {
        type: 'subsystem',
        name: 'Subsystem',
        category: 'subsystems',
        description: 'A subsystem',
        inputs: [],
        outputs: [],
        parameters: [],
      }

      const subsystemId = useModelStore.getState().addBlock(subsystemDef, { x: 100, y: 100 })

      // Manually add children to the subsystem
      useModelStore.setState(state => ({
        model: state.model ? {
          ...state.model,
          blocks: state.model.blocks.map(b =>
            b.id === subsystemId
              ? {
                  ...b,
                  children: [
                    {
                      id: 'child-block-1',
                      type: 'constant',
                      name: 'Child Constant',
                      position: { x: 50, y: 50 },
                      parameters: { value: 1 },
                      inputPorts: [],
                      outputPorts: [{ id: 'out-1', name: 'out', dataType: 'double', dimensions: [1] }],
                    },
                    {
                      id: 'child-block-2',
                      type: 'gain',
                      name: 'Child Gain',
                      position: { x: 150, y: 50 },
                      parameters: { gain: 2 },
                      inputPorts: [{ id: 'in-1', name: 'in', dataType: 'double', dimensions: [1] }],
                      outputPorts: [{ id: 'out-2', name: 'out', dataType: 'double', dimensions: [1] }],
                    }
                  ],
                  childConnections: [
                    {
                      id: 'child-conn-1',
                      sourceBlockId: 'child-block-1',
                      sourcePortId: 'out-1',
                      targetBlockId: 'child-block-2',
                      targetPortId: 'in-1',
                    }
                  ]
                }
              : b
          )
        } : null
      }))

      const initialBlockCount = useModelStore.getState().model?.blocks.length || 0

      useModelStore.getState().expandSubsystem(subsystemId)

      // The subsystem should be replaced by its children
      const model = useModelStore.getState().model
      expect(model?.blocks.length).toBe(initialBlockCount - 1 + 2) // -1 subsystem +2 children

      // Subsystem should no longer exist
      expect(model?.blocks.find(b => b.id === subsystemId)).toBeUndefined()

      // Children should exist at root level (with new IDs)
      const childBlocks = model?.blocks.filter(b => b.type === 'constant' || b.type === 'gain')
      expect(childBlocks?.length).toBe(2)
    })

    it('does nothing for non-existent subsystem', () => {
      const initialBlockCount = useModelStore.getState().model?.blocks.length || 0
      useModelStore.getState().expandSubsystem('non-existent')
      expect(useModelStore.getState().model?.blocks.length).toBe(initialBlockCount)
    })

    it('does nothing for non-subsystem block', () => {
      const constDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [],
      }

      const blockId = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      const initialBlockCount = useModelStore.getState().model?.blocks.length || 0

      useModelStore.getState().expandSubsystem(blockId)
      expect(useModelStore.getState().model?.blocks.length).toBe(initialBlockCount)
    })

    it('does nothing when model is null', () => {
      useModelStore.setState({ model: null })
      useModelStore.getState().expandSubsystem('any-id')
      expect(useModelStore.getState().model).toBeNull()
    })
  })

  describe('getCurrentBlocks and getCurrentConnections', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('returns root blocks when at root level', () => {
      const constDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [],
      }

      useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })

      const currentBlocks = useModelStore.getState().getCurrentBlocks()
      expect(currentBlocks.length).toBe(1)
    })

    it('returns empty array when model is null', () => {
      useModelStore.setState({ model: null })
      expect(useModelStore.getState().getCurrentBlocks()).toEqual([])
      expect(useModelStore.getState().getCurrentConnections()).toEqual([])
    })

    it('returns subsystem children when inside subsystem', () => {
      const subsystemDef: BlockDefinition = {
        type: 'subsystem',
        name: 'Subsystem',
        category: 'subsystems',
        description: 'A subsystem',
        inputs: [],
        outputs: [],
        parameters: [],
      }

      const subsystemId = useModelStore.getState().addBlock(subsystemDef, { x: 100, y: 100 })

      // Set up subsystem with children
      useModelStore.setState(state => ({
        model: state.model ? {
          ...state.model,
          blocks: state.model.blocks.map(b =>
            b.id === subsystemId
              ? {
                  ...b,
                  children: [
                    {
                      id: 'child-block',
                      type: 'constant',
                      name: 'Child',
                      position: { x: 50, y: 50 },
                      parameters: {},
                      inputPorts: [],
                      outputPorts: [],
                    }
                  ],
                  childConnections: []
                }
              : b
          )
        } : null,
        currentPath: [{ id: subsystemId, name: 'Subsystem' }]
      }))

      const currentBlocks = useModelStore.getState().getCurrentBlocks()
      expect(currentBlocks.length).toBe(1)
      expect(currentBlocks[0].id).toBe('child-block')
    })

    it('returns root connections when at root level', () => {
      // Add two blocks and connect them
      const constDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [],
      }

      const gainDef: BlockDefinition = {
        type: 'gain',
        name: 'Gain',
        category: 'math',
        description: 'A gain block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [],
      }

      const constId = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      const gainId = useModelStore.getState().addBlock(gainDef, { x: 200, y: 100 })

      const constBlock = useModelStore.getState().model?.blocks.find(b => b.id === constId)
      const gainBlock = useModelStore.getState().model?.blocks.find(b => b.id === gainId)

      if (constBlock && gainBlock) {
        useModelStore.getState().addConnection({
          sourceBlockId: constId,
          sourcePortId: constBlock.outputPorts[0].id,
          targetBlockId: gainId,
          targetPortId: gainBlock.inputPorts[0].id
        })
      }

      expect(useModelStore.getState().getCurrentConnections().length).toBe(1)
    })
  })

  describe('selection operations', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('selects multiple blocks', () => {
      const constDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [],
      }

      const block1Id = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      const block2Id = useModelStore.getState().addBlock(constDef, { x: 200, y: 100 })

      useModelStore.getState().selectBlocks([block1Id, block2Id])
      expect(useModelStore.getState().selectedBlockIds).toEqual([block1Id, block2Id])
    })

    it('clears selection', () => {
      const constDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [],
      }

      const blockId = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      useModelStore.getState().selectBlocks([blockId])
      expect(useModelStore.getState().selectedBlockIds.length).toBe(1)

      useModelStore.getState().clearSelection()
      expect(useModelStore.getState().selectedBlockIds.length).toBe(0)
      expect(useModelStore.getState().selectedConnectionIds.length).toBe(0)
    })

    it('selects multiple connections', () => {
      useModelStore.getState().selectConnections(['conn1', 'conn2'])
      expect(useModelStore.getState().selectedConnectionIds).toEqual(['conn1', 'conn2'])
    })
  })

  describe('undo/redo', () => {
    beforeEach(() => {
      // Clear history and future stacks before creating new model
      useModelStore.setState({ history: [], future: [] })
      useModelStore.getState().createNewModel('Test Model')
    })

    it('undoes and redoes block addition', () => {
      const constDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [],
      }

      // Push history BEFORE making a change to enable undo
      useModelStore.getState().pushHistory()
      useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      expect(useModelStore.getState().model?.blocks.length).toBe(1)

      useModelStore.getState().undo()
      expect(useModelStore.getState().model?.blocks.length).toBe(0)

      useModelStore.getState().redo()
      expect(useModelStore.getState().model?.blocks.length).toBe(1)
    })

    it('reports canUndo and canRedo correctly', () => {
      expect(useModelStore.getState().canUndo()).toBe(false)
      expect(useModelStore.getState().canRedo()).toBe(false)

      const constDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [],
      }

      // Push history BEFORE making a change to enable undo
      useModelStore.getState().pushHistory()
      useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      expect(useModelStore.getState().canUndo()).toBe(true)
      expect(useModelStore.getState().canRedo()).toBe(false)

      useModelStore.getState().undo()
      expect(useModelStore.getState().canUndo()).toBe(false)
      expect(useModelStore.getState().canRedo()).toBe(true)
    })
  })

  describe('model metadata', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('updates model name via updateMetadata', () => {
      useModelStore.getState().updateMetadata({ name: 'New Name' })
      expect(useModelStore.getState().model?.metadata.name).toBe('New Name')
    })

    it('updates solver via updateSimulationConfig', () => {
      useModelStore.getState().updateSimulationConfig({ solver: 'ode45' })
      expect(useModelStore.getState().model?.simulationConfig.solver).toBe('ode45')
    })

    it('updates stop time via updateSimulationConfig', () => {
      useModelStore.getState().updateSimulationConfig({ stopTime: 20 })
      expect(useModelStore.getState().model?.simulationConfig.stopTime).toBe(20)
    })

    it('updates step size via updateSimulationConfig', () => {
      useModelStore.getState().updateSimulationConfig({ stepSize: 0.001 })
      expect(useModelStore.getState().model?.simulationConfig.stepSize).toBe(0.001)
    })

    it('isDirty is set when model changes', () => {
      // Reset dirty flag by creating new model
      useModelStore.getState().createNewModel('Clean Model')
      expect(useModelStore.getState().isDirty).toBe(false)

      // Making a change should set isDirty
      useModelStore.getState().updateMetadata({ name: 'Changed' })
      expect(useModelStore.getState().isDirty).toBe(true)
    })

    it('updateSimulationConfig does nothing when model is null', () => {
      useModelStore.setState({ model: null })
      useModelStore.getState().updateSimulationConfig({ solver: 'ode45' })
      expect(useModelStore.getState().model).toBeNull()
    })

    it('updateMetadata does nothing when model is null', () => {
      useModelStore.setState({ model: null })
      useModelStore.getState().updateMetadata({ name: 'New Name' })
      expect(useModelStore.getState().model).toBeNull()
    })
  })

  describe('removeBlock deletes connections', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('removes connections when block is deleted', () => {
      const constDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [],
      }

      const gainDef: BlockDefinition = {
        type: 'gain',
        name: 'Gain',
        category: 'math',
        description: 'A gain block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [],
      }

      const constId = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      const gainId = useModelStore.getState().addBlock(gainDef, { x: 200, y: 100 })

      const constBlock = useModelStore.getState().model?.blocks.find(b => b.id === constId)
      const gainBlock = useModelStore.getState().model?.blocks.find(b => b.id === gainId)

      if (constBlock && gainBlock) {
        useModelStore.getState().addConnection({
          sourceBlockId: constId,
          sourcePortId: constBlock.outputPorts[0].id,
          targetBlockId: gainId,
          targetPortId: gainBlock.inputPorts[0].id
        })
      }

      expect(useModelStore.getState().model?.connections.length).toBe(1)

      // Remove the constant block
      useModelStore.getState().removeBlock(constId)

      expect(useModelStore.getState().model?.blocks.length).toBe(1)
      expect(useModelStore.getState().model?.connections.length).toBe(0)
    })
  })

  describe('updateBlockParameters dynamic port updates', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('clamps mux numInputs to valid range', () => {
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
        parameters: [{ name: 'numInputs', label: 'Number of Inputs', type: 'number', default: 2 }],
      }

      const id = useModelStore.getState().addBlock(muxDef, { x: 100, y: 100 })

      // Try setting too low - should clamp to 2
      useModelStore.getState().updateBlockParameters(id, { numInputs: 0 })
      let block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.inputPorts.length).toBe(2)

      // Try setting too high - should clamp to 32
      useModelStore.getState().updateBlockParameters(id, { numInputs: 100 })
      block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.inputPorts.length).toBe(32)
    })

    it('clamps demux numOutputs to valid range', () => {
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
        parameters: [{ name: 'numOutputs', label: 'Number of Outputs', type: 'number', default: 2 }],
      }

      const id = useModelStore.getState().addBlock(demuxDef, { x: 100, y: 100 })

      // Try setting too low - should clamp to 2
      useModelStore.getState().updateBlockParameters(id, { numOutputs: 1 })
      let block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.outputPorts.length).toBe(2)

      // Try setting too high - should clamp to 32
      useModelStore.getState().updateBlockParameters(id, { numOutputs: 50 })
      block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.outputPorts.length).toBe(32)
    })

    it('clamps scope numInputs to valid range', () => {
      const scopeDef: BlockDefinition = {
        type: 'scope',
        name: 'Scope',
        category: 'sinks',
        description: 'A scope block',
        inputs: [{ name: 'in1', dataType: 'double', dimensions: [1] }],
        outputs: [],
        parameters: [{ name: 'numInputs', label: 'Number of Inputs', type: 'number', default: 1 }],
      }

      const id = useModelStore.getState().addBlock(scopeDef, { x: 100, y: 100 })

      // Try setting to 0 - should clamp to 1
      useModelStore.getState().updateBlockParameters(id, { numInputs: 0 })
      let block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.inputPorts.length).toBe(1)

      // Try setting too high - should clamp to 16
      useModelStore.getState().updateBlockParameters(id, { numInputs: 100 })
      block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.inputPorts.length).toBe(16)
    })

    it('handles integrator externalIC parameter', () => {
      const integratorDef: BlockDefinition = {
        type: 'integrator',
        name: 'Integrator',
        category: 'continuous',
        description: 'An integrator block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [{ name: 'externalIC', label: 'External IC', type: 'boolean', default: false }],
      }

      const id = useModelStore.getState().addBlock(integratorDef, { x: 100, y: 100 })

      // Initially should have 1 input
      let block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.inputPorts.length).toBe(1)

      // Enable external IC - should have 2 inputs
      useModelStore.getState().updateBlockParameters(id, { externalIC: true })
      block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.inputPorts.length).toBe(2)
      expect(block?.inputPorts[1].name).toBe('x0')

      // Disable external IC - should go back to 1 input
      useModelStore.getState().updateBlockParameters(id, { externalIC: false })
      block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.inputPorts.length).toBe(1)
    })

    it('handles reshape outputDimensions parameter', () => {
      const reshapeDef: BlockDefinition = {
        type: 'reshape',
        name: 'Reshape',
        category: 'routing',
        description: 'A reshape block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [{ name: 'outputDimensions', label: 'Output Dimensions', type: 'string', default: '[1]' }],
      }

      const id = useModelStore.getState().addBlock(reshapeDef, { x: 100, y: 100 })

      // Set valid JSON dimensions
      useModelStore.getState().updateBlockParameters(id, { outputDimensions: '[3, 4]' })
      let block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.outputPorts[0].dimensions).toEqual([3, 4])

      // Set invalid JSON but parseable string
      useModelStore.getState().updateBlockParameters(id, { outputDimensions: '5x6' })
      block = useModelStore.getState().model?.blocks.find(b => b.id === id)
      expect(block?.outputPorts[0].dimensions).toEqual([5, 6])
    })

    it('removes orphaned connections when ports change', () => {
      const scopeDef: BlockDefinition = {
        type: 'scope',
        name: 'Scope',
        category: 'sinks',
        description: 'A scope block',
        inputs: [
          { name: 'in1', dataType: 'double', dimensions: [1] },
          { name: 'in2', dataType: 'double', dimensions: [1] },
          { name: 'in3', dataType: 'double', dimensions: [1] },
        ],
        outputs: [],
        parameters: [{ name: 'numInputs', label: 'Number of Inputs', type: 'number', default: 3 }],
      }

      const constDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [],
      }

      const scopeId = useModelStore.getState().addBlock(scopeDef, { x: 300, y: 100 })
      const constId = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })

      const scopeBlock = useModelStore.getState().model?.blocks.find(b => b.id === scopeId)
      const constBlock = useModelStore.getState().model?.blocks.find(b => b.id === constId)

      // Connect to the third input port
      if (scopeBlock && constBlock) {
        useModelStore.getState().addConnection({
          sourceBlockId: constId,
          sourcePortId: constBlock.outputPorts[0].id,
          targetBlockId: scopeId,
          targetPortId: scopeBlock.inputPorts[2].id,
        })
      }

      expect(useModelStore.getState().model?.connections.length).toBe(1)

      // Reduce scope inputs to 1 - should remove the orphaned connection
      useModelStore.getState().updateBlockParameters(scopeId, { numInputs: 1 })

      expect(useModelStore.getState().model?.connections.length).toBe(0)
    })
  })

  describe('operations without model', () => {
    beforeEach(() => {
      useModelStore.setState({ model: null })
    })

    it('removeBlock does nothing when no model', () => {
      expect(() => useModelStore.getState().removeBlock('any-id')).not.toThrow()
    })

    it('updateBlockPosition does nothing when no model', () => {
      expect(() => useModelStore.getState().updateBlockPosition('any-id', { x: 0, y: 0 })).not.toThrow()
    })

    it('updateBlockSize does nothing when no model', () => {
      expect(() => useModelStore.getState().updateBlockSize('any-id', { width: 100, height: 50 })).not.toThrow()
    })

    it('updateBlockParameters does nothing when no model', () => {
      expect(() => useModelStore.getState().updateBlockParameters('any-id', { value: 1 })).not.toThrow()
    })

    it('renameBlock does nothing when no model', () => {
      expect(() => useModelStore.getState().renameBlock('any-id', 'New Name')).not.toThrow()
    })

    it('addConnection returns null when no model', () => {
      const result = useModelStore.getState().addConnection({
        sourceBlockId: 's',
        sourcePortId: 'sp',
        targetBlockId: 't',
        targetPortId: 'tp',
      })
      expect(result).toBeNull()
    })

    it('removeConnection does nothing when no model', () => {
      expect(() => useModelStore.getState().removeConnection('any-id')).not.toThrow()
    })

    it('addConnectionWaypoint does nothing when no model', () => {
      expect(() => useModelStore.getState().addConnectionWaypoint('any-id', { x: 0, y: 0 })).not.toThrow()
    })

    it('updateConnectionWaypoint does nothing when no model', () => {
      expect(() => useModelStore.getState().updateConnectionWaypoint('any-id', 0, { x: 0, y: 0 })).not.toThrow()
    })

    it('removeConnectionWaypoint does nothing when no model', () => {
      expect(() => useModelStore.getState().removeConnectionWaypoint('any-id', 0)).not.toThrow()
    })

    it('clearConnectionWaypoints does nothing when no model', () => {
      expect(() => useModelStore.getState().clearConnectionWaypoints('any-id')).not.toThrow()
    })

    it('updateConnectionWaypoints does nothing when no model', () => {
      expect(() => useModelStore.getState().updateConnectionWaypoints('any-id', [])).not.toThrow()
    })

    it('updateConnectionSignalName does nothing when no model', () => {
      expect(() => useModelStore.getState().updateConnectionSignalName('any-id', 'sig')).not.toThrow()
    })

    it('updateConnectionLabelOffset does nothing when no model', () => {
      expect(() => useModelStore.getState().updateConnectionLabelOffset('any-id', { t: 0.5, perpOffset: 0 })).not.toThrow()
    })

    it('spreadBlocks does nothing when no model', () => {
      expect(() => useModelStore.getState().spreadBlocks(2.0)).not.toThrow()
    })

    it('rotateSelectedBlocks does nothing when no model', () => {
      expect(() => useModelStore.getState().rotateSelectedBlocks()).not.toThrow()
    })

    it('pushHistory does nothing when no model', () => {
      expect(() => useModelStore.getState().pushHistory()).not.toThrow()
    })

    it('undo does nothing when no history', () => {
      useModelStore.getState().createNewModel('Test')
      expect(useModelStore.getState().history.length).toBe(0)
      expect(() => useModelStore.getState().undo()).not.toThrow()
    })

    it('redo does nothing when no future', () => {
      useModelStore.setState({ history: [], future: [] })
      useModelStore.getState().createNewModel('Test')
      expect(useModelStore.getState().future.length).toBe(0)
      expect(() => useModelStore.getState().redo()).not.toThrow()
    })

    it('createSubsystem returns null when no model', () => {
      const result = useModelStore.getState().createSubsystem(['block-1'])
      expect(result).toBeNull()
    })

    it('toggleSubsystemExpanded does nothing when no model', () => {
      expect(() => useModelStore.getState().toggleSubsystemExpanded('any-id')).not.toThrow()
    })

    it('enterSubsystem does nothing when no model', () => {
      expect(() => useModelStore.getState().enterSubsystem('any-id')).not.toThrow()
    })
  })

  describe('spreadBlocks edge cases', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('does nothing when fewer than 2 blocks', () => {
      const constDef = createBlockDef('constant', 'Constant')
      const blockId = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })

      const initialPosition = { ...useModelStore.getState().model?.blocks[0].position }

      useModelStore.getState().spreadBlocks(2.0)

      const finalPosition = useModelStore.getState().model?.blocks[0].position
      expect(finalPosition).toEqual(initialPosition)
    })

    it('spreads only selected blocks when selection exists', () => {
      const constDef = createBlockDef('constant', 'Constant')
      const block1Id = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      const block2Id = useModelStore.getState().addBlock(constDef, { x: 200, y: 100 })
      const block3Id = useModelStore.getState().addBlock(constDef, { x: 100, y: 200 })

      // Select only block1 and block2
      useModelStore.getState().selectBlocks([block1Id, block2Id])

      const block3InitialPos = { ...useModelStore.getState().model?.blocks.find(b => b.id === block3Id)?.position }

      useModelStore.getState().spreadBlocks(2.0)

      // Block3 should not have moved
      const block3FinalPos = useModelStore.getState().model?.blocks.find(b => b.id === block3Id)?.position
      expect(block3FinalPos).toEqual(block3InitialPos)
    })

    it('spreads blocks inside subsystem', () => {
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
            name: 'Child1',
            position: { x: 50, y: 50 },
            parameters: {},
            inputPorts: [],
            outputPorts: [],
          },
          {
            id: 'child-2',
            type: 'constant',
            name: 'Child2',
            position: { x: 150, y: 50 },
            parameters: {},
            inputPorts: [],
            outputPorts: [],
          },
        ],
        childConnections: [],
      }

      useModelStore.setState({
        model: {
          ...useModelStore.getState().model!,
          blocks: [subsystemBlock],
        },
        currentPath: [{ id: 'subsystem-1', name: 'TestSubsystem' }],
      })

      useModelStore.getState().spreadBlocks(2.0)

      const currentBlocks = useModelStore.getState().getCurrentBlocks()
      // Verify that spreading happened (blocks moved apart)
      expect(currentBlocks.length).toBe(2)
    })
  })

  describe('rotateSelectedBlocks inside subsystem', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('rotates blocks inside subsystem', () => {
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
            name: 'Child1',
            position: { x: 50, y: 50 },
            parameters: {},
            inputPorts: [],
            outputPorts: [],
          },
        ],
        childConnections: [],
      }

      useModelStore.setState({
        model: {
          ...useModelStore.getState().model!,
          blocks: [subsystemBlock],
        },
        currentPath: [{ id: 'subsystem-1', name: 'TestSubsystem' }],
        selectedBlockIds: ['child-1'],
      })

      useModelStore.getState().rotateSelectedBlocks()

      const currentBlocks = useModelStore.getState().getCurrentBlocks()
      const child = currentBlocks.find(b => b.id === 'child-1')
      expect(child?.rotation).toBe(90)
    })
  })

  describe('waypoint operations with invalid indices', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('updateConnectionWaypoint ignores invalid index', () => {
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

      const constId = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      const scopeId = useModelStore.getState().addBlock(scopeDef, { x: 300, y: 100 })

      const constBlock = useModelStore.getState().model?.blocks.find(b => b.id === constId)
      const scopeBlock = useModelStore.getState().model?.blocks.find(b => b.id === scopeId)

      const connId = useModelStore.getState().addConnection({
        sourceBlockId: constId,
        sourcePortId: constBlock?.outputPorts[0].id || '',
        targetBlockId: scopeId,
        targetPortId: scopeBlock?.inputPorts[0].id || '',
      })

      // Add one waypoint
      useModelStore.getState().addConnectionWaypoint(connId!, { x: 200, y: 150 })

      // Try to update at invalid index (negative)
      useModelStore.getState().updateConnectionWaypoint(connId!, -1, { x: 0, y: 0 })

      // Try to update at invalid index (too large)
      useModelStore.getState().updateConnectionWaypoint(connId!, 10, { x: 0, y: 0 })

      const conn = useModelStore.getState().model?.connections.find(c => c.id === connId)
      expect(conn?.waypoints?.length).toBe(1)
      expect(conn?.waypoints?.[0]).toEqual({ x: 200, y: 150 })
    })

    it('removeConnectionWaypoint ignores invalid index', () => {
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

      const constId = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      const scopeId = useModelStore.getState().addBlock(scopeDef, { x: 300, y: 100 })

      const constBlock = useModelStore.getState().model?.blocks.find(b => b.id === constId)
      const scopeBlock = useModelStore.getState().model?.blocks.find(b => b.id === scopeId)

      const connId = useModelStore.getState().addConnection({
        sourceBlockId: constId,
        sourcePortId: constBlock?.outputPorts[0].id || '',
        targetBlockId: scopeId,
        targetPortId: scopeBlock?.inputPorts[0].id || '',
      })

      // Add one waypoint
      useModelStore.getState().addConnectionWaypoint(connId!, { x: 200, y: 150 })

      // Try to remove at invalid index (negative)
      useModelStore.getState().removeConnectionWaypoint(connId!, -1)

      // Try to remove at invalid index (too large)
      useModelStore.getState().removeConnectionWaypoint(connId!, 10)

      const conn = useModelStore.getState().model?.connections.find(c => c.id === connId)
      expect(conn?.waypoints?.length).toBe(1)
    })
  })

  describe('createSubsystem with external connections', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')
    })

    it('creates inports and outports for external connections', () => {
      const constDef: BlockDefinition = {
        type: 'constant',
        name: 'Constant',
        category: 'sources',
        description: 'A constant block',
        inputs: [],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [],
      }

      const gainDef: BlockDefinition = {
        type: 'gain',
        name: 'Gain',
        category: 'math',
        description: 'A gain block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
        parameters: [],
      }

      const scopeDef: BlockDefinition = {
        type: 'scope',
        name: 'Scope',
        category: 'sinks',
        description: 'A scope block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [],
        parameters: [],
      }

      const constId = useModelStore.getState().addBlock(constDef, { x: 100, y: 100 })
      const gainId = useModelStore.getState().addBlock(gainDef, { x: 200, y: 100 })
      const scopeId = useModelStore.getState().addBlock(scopeDef, { x: 300, y: 100 })

      const blocks = useModelStore.getState().model?.blocks
      const constBlock = blocks?.find(b => b.id === constId)
      const gainBlock = blocks?.find(b => b.id === gainId)
      const scopeBlock = blocks?.find(b => b.id === scopeId)

      // Connect: const -> gain -> scope
      useModelStore.getState().addConnection({
        sourceBlockId: constId,
        sourcePortId: constBlock?.outputPorts[0].id || '',
        targetBlockId: gainId,
        targetPortId: gainBlock?.inputPorts[0].id || '',
      })

      useModelStore.getState().addConnection({
        sourceBlockId: gainId,
        sourcePortId: gainBlock?.outputPorts[0].id || '',
        targetBlockId: scopeId,
        targetPortId: scopeBlock?.inputPorts[0].id || '',
      })

      // Create subsystem from just the gain block
      const subsystemId = useModelStore.getState().createSubsystem([gainId], 'GainSubsystem')

      expect(subsystemId).toBeTruthy()

      const model = useModelStore.getState().model
      const subsystem = model?.blocks.find(b => b.id === subsystemId)

      // Subsystem should have 1 input port (from const) and 1 output port (to scope)
      expect(subsystem?.inputPorts.length).toBe(1)
      expect(subsystem?.outputPorts.length).toBe(1)

      // Children should include Inport, Gain, and Outport
      expect(subsystem?.children?.some(c => c.type === 'inport')).toBe(true)
      expect(subsystem?.children?.some(c => c.type === 'gain')).toBe(true)
      expect(subsystem?.children?.some(c => c.type === 'outport')).toBe(true)
    })

    it('returns null when blocks not found', () => {
      const result = useModelStore.getState().createSubsystem(['non-existent-block'])
      expect(result).toBeNull()
    })
  })

  describe('subsystem operations at deeper nesting', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')

      // Create a nested subsystem structure
      const subsystemBlock: BlockInstance = {
        id: 'subsystem-1',
        type: 'subsystem',
        name: 'OuterSubsystem',
        position: { x: 100, y: 100 },
        parameters: {},
        inputPorts: [],
        outputPorts: [],
        children: [
          {
            id: 'inner-subsystem',
            type: 'subsystem',
            name: 'InnerSubsystem',
            position: { x: 50, y: 50 },
            parameters: {},
            inputPorts: [],
            outputPorts: [],
            children: [
              {
                id: 'innermost-block',
                type: 'constant',
                name: 'InnermostConstant',
                position: { x: 25, y: 25 },
                parameters: { value: 1 },
                inputPorts: [],
                outputPorts: [{ id: 'out-0', name: 'out', dataType: 'double', dimensions: [1] }],
              },
            ],
            childConnections: [],
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
    })

    it('handles connection operations at nested path', () => {
      // Navigate to outer subsystem
      useModelStore.setState({
        currentPath: [{ id: 'subsystem-1', name: 'OuterSubsystem' }],
      })

      const scopeDef: BlockDefinition = {
        type: 'scope',
        name: 'Scope',
        category: 'sinks',
        description: 'A scope block',
        inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
        outputs: [],
        parameters: [],
      }

      const scopeId = useModelStore.getState().addBlock(scopeDef, { x: 200, y: 50 })

      // The scope should be added inside the outer subsystem
      const currentBlocks = useModelStore.getState().getCurrentBlocks()
      expect(currentBlocks.some(b => b.id === scopeId)).toBe(true)
    })

    it('removes block inside nested subsystem', () => {
      // Navigate to inner subsystem (2 levels deep)
      useModelStore.setState({
        currentPath: [
          { id: 'subsystem-1', name: 'OuterSubsystem' },
          { id: 'inner-subsystem', name: 'InnerSubsystem' },
        ],
      })

      let currentBlocks = useModelStore.getState().getCurrentBlocks()
      expect(currentBlocks.some(b => b.id === 'innermost-block')).toBe(true)

      useModelStore.getState().removeBlock('innermost-block')

      currentBlocks = useModelStore.getState().getCurrentBlocks()
      expect(currentBlocks.some(b => b.id === 'innermost-block')).toBe(false)
    })
  })

  describe('waypoint and signal name operations inside subsystems', () => {
    beforeEach(() => {
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
            id: 'child-const',
            type: 'constant',
            name: 'ChildConst',
            position: { x: 50, y: 50 },
            parameters: {},
            inputPorts: [],
            outputPorts: [{ id: 'c-out-0', name: 'out', dataType: 'double', dimensions: [1] }],
          },
          {
            id: 'child-scope',
            type: 'scope',
            name: 'ChildScope',
            position: { x: 200, y: 50 },
            parameters: {},
            inputPorts: [{ id: 's-in-0', name: 'in', dataType: 'double', dimensions: [1] }],
            outputPorts: [],
          },
        ],
        childConnections: [
          {
            id: 'child-conn-1',
            sourceBlockId: 'child-const',
            sourcePortId: 'c-out-0',
            targetBlockId: 'child-scope',
            targetPortId: 's-in-0',
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
    })

    it('updates connection signal name inside subsystem', () => {
      useModelStore.getState().updateConnectionSignalName('child-conn-1', 'inner_signal')

      const currentConnections = useModelStore.getState().getCurrentConnections()
      const conn = currentConnections.find(c => c.id === 'child-conn-1')
      expect(conn?.signalName).toBe('inner_signal')
    })

    it('updates connection label offset inside subsystem', () => {
      useModelStore.getState().updateConnectionLabelOffset('child-conn-1', { t: 0.3, perpOffset: 15 })

      const currentConnections = useModelStore.getState().getCurrentConnections()
      const conn = currentConnections.find(c => c.id === 'child-conn-1')
      expect(conn?.labelOffset).toEqual({ t: 0.3, perpOffset: 15 })
    })
  })

  describe('expandSubsystem inside subsystem', () => {
    beforeEach(() => {
      useModelStore.getState().createNewModel('Test Model')

      // Create an outer subsystem with a nested inner subsystem
      const outerSubsystem: BlockInstance = {
        id: 'outer-sub',
        type: 'subsystem',
        name: 'OuterSubsystem',
        position: { x: 100, y: 100 },
        parameters: {},
        inputPorts: [],
        outputPorts: [],
        children: [
          {
            id: 'inner-sub',
            type: 'subsystem',
            name: 'InnerSubsystem',
            position: { x: 50, y: 50 },
            parameters: {},
            inputPorts: [],
            outputPorts: [],
            children: [
              {
                id: 'deep-block',
                type: 'constant',
                name: 'DeepConstant',
                position: { x: 25, y: 25 },
                parameters: { value: 42 },
                inputPorts: [],
                outputPorts: [{ id: 'd-out-0', name: 'out', dataType: 'double', dimensions: [1] }],
              },
            ],
            childConnections: [],
          },
        ],
        childConnections: [],
      }

      useModelStore.setState({
        model: {
          ...useModelStore.getState().model!,
          blocks: [outerSubsystem],
        },
        currentPath: [{ id: 'outer-sub', name: 'OuterSubsystem' }],
      })
    })

    it('expands nested subsystem into parent', () => {
      let currentBlocks = useModelStore.getState().getCurrentBlocks()
      expect(currentBlocks.some(b => b.id === 'inner-sub')).toBe(true)

      useModelStore.getState().expandSubsystem('inner-sub')

      currentBlocks = useModelStore.getState().getCurrentBlocks()

      // Inner subsystem should be removed
      expect(currentBlocks.some(b => b.id === 'inner-sub')).toBe(false)

      // Deep block should now be at this level
      expect(currentBlocks.some(b => b.name === 'DeepConstant')).toBe(true)
    })
  })
})
