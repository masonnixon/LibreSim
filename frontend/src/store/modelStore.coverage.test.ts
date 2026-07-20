import { expect, it } from 'vitest'

import { useModelStore } from './modelStore'
import type { BlockDefinition, BlockInstance, Connection } from '../types/block'
import type { LibraryBlockDefinition } from '../types/library'
import type { Model } from '../types/model'

const caseFn = it

const constantDefinition: BlockDefinition = {
  type: 'constant',
  name: 'Constant',
  category: 'sources',
  description: 'Constant',
  inputs: [],
  outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
  parameters: [{ name: 'value', label: 'Value', type: 'string', default: 0 }],
}

function coveragePort(id: string) {
  return { id, name: id, dataType: 'double' as const, dimensions: [1] }
}

function coverageBlock(id: string, type: string = 'gain'): BlockInstance {
  return {
    id,
    type,
    name: id,
    position: { x: 0, y: 0 },
    parameters: {},
    inputPorts: [coveragePort(`${id}-in-0`)],
    outputPorts: [coveragePort(`${id}-out-0`)],
  }
}

function coverageModel(blocks: BlockInstance[], connections: Connection[] = []): Model {
  return {
    id: 'coverage-model',
    metadata: { name: 'Coverage', description: '', author: '', createdAt: '', modifiedAt: '', version: '1' },
    blocks,
    connections,
    simulationConfig: { solver: 'rk4', startTime: 0, stopTime: 1, stepSize: 0.1 },
  }
}

function setDeepFixture() {
  const source = coverageBlock('deep-source', 'constant')
  source.inputPorts = []
  source.parameters = { value: 1 }
  const transform = coverageBlock('deep-transform', 'demux')
  transform.parameters = { numOutputs: 3 }
  transform.outputPorts = [
    coveragePort('deep-transform-out-0'),
    coveragePort('deep-transform-out-1'),
    coveragePort('deep-transform-out-2'),
  ]
  const sink = coverageBlock('deep-sink', 'scope')
  sink.inputPorts = [
    coveragePort('deep-sink-in-0'),
    coveragePort('deep-sink-in-1'),
    coveragePort('deep-sink-in-2'),
  ]
  sink.outputPorts = []
  const untouched = coverageBlock('deep-untouched')
  untouched.position = { x: 100, y: 100 }
  const middle = coverageBlock('middle', 'subsystem')
  middle.children = [source, transform, sink, untouched]
  middle.childConnections = [
    { id: 'source-transform', sourceBlockId: source.id, sourcePortId: source.outputPorts[0].id, targetBlockId: transform.id, targetPortId: transform.inputPorts[0].id },
    { id: 'transform-sink', sourceBlockId: transform.id, sourcePortId: transform.outputPorts[2].id, targetBlockId: sink.id, targetPortId: sink.inputPorts[2].id },
    { id: 'unrelated', sourceBlockId: source.id, sourcePortId: source.outputPorts[0].id, targetBlockId: sink.id, targetPortId: sink.inputPorts[0].id },
  ]
  const outerSibling = coverageBlock('outer-sibling')
  const outer = coverageBlock('outer', 'subsystem')
  outer.children = [outerSibling, middle]
  outer.childConnections = []
  const rootSibling = coverageBlock('root-sibling')
  useModelStore.setState({
    model: coverageModel([rootSibling, outer]),
    currentPath: [{ id: outer.id, name: outer.name }, { id: middle.id, name: middle.name }],
    selectedBlockIds: [],
    selectedConnectionIds: [],
    isDirty: false,
  })
  return { source, transform, sink, untouched, middle, outer }
}

function currentMiddle(): BlockInstance {
  const outer = useModelStore.getState().model?.blocks.find(block => block.id === 'outer')
  const middle = outer?.children?.find(block => block.id === 'middle')
  if (!middle) throw new Error('deep fixture is missing its middle subsystem')
  return middle
}

it('checks another constant contract', function () {
  useModelStore.getState().createNewModel('Coverage Model')
  const id = useModelStore.getState().addBlock(constantDefinition, { x: 0, y: 0 })
  const cases: Array<[unknown, number[]]> = [
    [null, [1]],
    [[1, 2, 3], [3]],
    ['42', [1]],
    ['not a number', [1]],
    ['[]', [1]],
    ['[1, nope]', [1]],
    ['one,two', [1]],
  ]
  for (const [value, dimensions] of cases) {
    useModelStore.getState().updateBlockParameters(id, { value })
    const block = useModelStore.getState().model?.blocks.find(item => item.id === id)
    expect(block?.outputPorts[0].dimensions).toEqual(dimensions)
  }
})

it('extracts reshape dimensions from a descriptive default', function () {
  useModelStore.getState().createNewModel('Coverage Model')
  const definition: BlockDefinition = {
    type: 'reshape',
    name: 'Reshape',
    category: 'routing',
    description: 'Reshape',
    inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
    outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
    parameters: [{
      name: 'outputDimensions',
      label: 'Dimensions',
      type: 'string',
      default: 'rows 2 by columns 3',
    }],
  }
  const id = useModelStore.getState().addBlock(definition, { x: 0, y: 0 })
  const block = useModelStore.getState().model?.blocks.find(item => item.id === id)
  expect(block?.outputPorts[0].dimensions).toEqual([2, 3])
})

it('copies a connected multi-block library implementation', function () {
  const first: BlockInstance = {
    id: 'first',
    type: 'constant',
    name: 'First',
    position: { x: 10, y: 10 },
    parameters: { value: 1 },
    inputPorts: [],
    outputPorts: [{ id: 'first-out', name: 'out', dataType: 'double', dimensions: [1] }],
  }
  const second: BlockInstance = {
    id: 'second',
    type: 'gain',
    name: 'Second',
    position: { x: 10, y: 10 },
    parameters: { gain: 2 },
    inputPorts: [{ id: 'second-in', name: 'in', dataType: 'double', dimensions: [1] }],
    outputPorts: [{ id: 'second-out', name: 'out', dataType: 'double', dimensions: [1] }],
  }
  const definition: LibraryBlockDefinition = {
    type: 'coverage__pair',
    name: 'Pair',
    category: 'subsystems',
    description: 'Pair',
    inputs: [],
    outputs: [],
    parameters: [],
    isLibraryBlock: true,
    libraryId: 'coverage',
    libraryName: 'Coverage',
    originalName: 'Pair',
    implementation: {
      blocks: [first, second],
      connections: [{
        id: 'wire',
        sourceBlockId: first.id,
        sourcePortId: first.outputPorts[0].id,
        targetBlockId: second.id,
        targetPortId: second.inputPorts[0].id,
      }],
      portMappings: [],
    },
  }
  useModelStore.getState().createNewModel('Coverage Model')
  const id = useModelStore.getState().addBlock(definition, { x: 0, y: 0 })
  const block = useModelStore.getState().model?.blocks.find(item => item.id === id)
  expect(block?.type).toBe('subsystem')
  expect(block?.children?.map(child => child.position)).toEqual([
    { x: 100, y: 100 },
    { x: 350, y: 100 },
  ])
  expect(block?.childConnections).toHaveLength(1)
  expect(block?.childConnections?.[0].sourceBlockId).toBe(block?.children?.[0].id)
  expect(block?.childConnections?.[0].targetBlockId).toBe(block?.children?.[1].id)
})

it('expands a root subsystem and remaps its complete connection interface', function () {
  function makePort(id: string) {
    return { id, name: id, dataType: 'double' as const, dimensions: [1] }
  }
  function makeNode(id: string): BlockInstance {
    return { id, type: 'gain', name: id, position: { x: 10, y: 20 }, parameters: {}, inputPorts: [], outputPorts: [] }
  }
  const source = makeNode('source')
  source.type = 'constant'
  source.outputPorts = [makePort('source-out')]
  const targetA = makeNode('target-a')
  targetA.type = 'scope'
  targetA.inputPorts = [makePort('target-a-in')]
  const targetB = makeNode('target-b')
  targetB.type = 'scope'
  targetB.inputPorts = [makePort('target-b-in')]
  const inport = makeNode('inport')
  inport.type = 'inport'
  inport.parameters = { portNumber: 1 }
  inport.outputPorts = [makePort('inport-out')]
  const first = makeNode('first')
  first.inputPorts = [makePort('first-in')]
  first.outputPorts = [makePort('first-out')]
  const second = makeNode('second')
  second.inputPorts = [makePort('second-in')]
  second.outputPorts = [makePort('second-out')]
  const outport = makeNode('outport')
  outport.type = 'outport'
  outport.parameters = { portNumber: 1 }
  outport.inputPorts = [makePort('outport-in')]
  const subsystem = makeNode('subsystem')
  subsystem.type = 'subsystem'
  subsystem.position = { x: 300, y: 200 }
  subsystem.inputPorts = [makePort('subsystem-in')]
  subsystem.outputPorts = [makePort('subsystem-out')]
  subsystem.children = [inport, first, second, outport]
  subsystem.childConnections = [
    { id: 'from-inport', sourceBlockId: 'inport', sourcePortId: 'inport-out', targetBlockId: 'first', targetPortId: 'first-in' },
    { id: 'internal', sourceBlockId: 'first', sourcePortId: 'first-out', targetBlockId: 'second', targetPortId: 'second-in' },
    { id: 'to-outport', sourceBlockId: 'second', sourcePortId: 'second-out', targetBlockId: 'outport', targetPortId: 'outport-in' },
  ]
  const model: Model = {
    id: 'model',
    metadata: { name: 'Expand', description: '', author: '', createdAt: '', modifiedAt: '', version: '1' },
    blocks: [source, subsystem, targetA, targetB],
    connections: [
      { id: 'incoming', sourceBlockId: 'source', sourcePortId: 'source-out', targetBlockId: 'subsystem', targetPortId: 'subsystem-in' },
      { id: 'out-a', sourceBlockId: 'subsystem', sourcePortId: 'subsystem-out', targetBlockId: 'target-a', targetPortId: 'target-a-in' },
      { id: 'out-b', sourceBlockId: 'subsystem', sourcePortId: 'subsystem-out', targetBlockId: 'target-b', targetPortId: 'target-b-in' },
      { id: 'unrelated', sourceBlockId: 'source', sourcePortId: 'source-out', targetBlockId: 'target-a', targetPortId: 'target-a-in' },
    ],
    simulationConfig: { solver: 'rk4', startTime: 0, stopTime: 1, stepSize: 0.1 },
  }
  useModelStore.setState({ model, currentPath: [], selectedBlockIds: [], selectedConnectionIds: [] })
  useModelStore.getState().expandSubsystem('subsystem')
  const expanded = useModelStore.getState().model
  expect(expanded?.blocks.map(item => item.id)).toEqual(['source', 'target-a', 'target-b', 'first', 'second'])
  expect(expanded?.connections).toHaveLength(5)
  expect(expanded?.connections).toEqual(expect.arrayContaining([
    expect.objectContaining({ sourceBlockId: 'source', targetBlockId: 'first' }),
    expect.objectContaining({ sourceBlockId: 'first', targetBlockId: 'second' }),
    expect.objectContaining({ sourceBlockId: 'second', targetBlockId: 'target-a' }),
    expect.objectContaining({ sourceBlockId: 'second', targetBlockId: 'target-b' }),
  ]))
  expect(useModelStore.getState().selectedBlockIds).toEqual(['first', 'second'])
})

it('performs block and connection operations through a two-level subsystem path', function () {
  const fixture = setDeepFixture()
  const addedId = useModelStore.getState().addBlock(constantDefinition, { x: 9, y: 8 })
  useModelStore.getState().updateBlockPosition(fixture.source.id, { x: 20, y: 30 })
  useModelStore.getState().updateBlockSize(fixture.source.id, { width: 70, height: 40 })
  useModelStore.getState().renameBlock(fixture.source.id, 'Renamed Source')

  let middle = currentMiddle()
  expect(middle.children?.find(block => block.id === addedId)?.position).toEqual({ x: 9, y: 8 })
  expect(middle.children?.find(block => block.id === fixture.source.id)).toMatchObject({
    name: 'Renamed Source',
    position: { x: 20, y: 30 },
    size: { width: 70, height: 40 },
  })

  const connectionId = useModelStore.getState().addConnection({
    sourceBlockId: fixture.source.id,
    sourcePortId: fixture.source.outputPorts[0].id,
    targetBlockId: fixture.untouched.id,
    targetPortId: fixture.untouched.inputPorts[0].id,
  })
  expect(connectionId).toBeTruthy()
  useModelStore.getState().addConnectionWaypoint(connectionId!, { x: 1, y: 2 })
  useModelStore.getState().updateConnectionWaypoint(connectionId!, 0, { x: 3, y: 4 })
  useModelStore.getState().updateConnectionWaypoints(connectionId!, [{ x: 5, y: 6 }, { x: 7, y: 8 }])
  useModelStore.getState().updateConnectionSignalName(connectionId!, 'deep signal')
  useModelStore.getState().updateConnectionLabelOffset(connectionId!, { t: 0.25, perpOffset: 6 })
  useModelStore.getState().clearConnectionWaypoints(connectionId!)

  middle = currentMiddle()
  expect(middle.childConnections?.find(connection => connection.id === connectionId)).toMatchObject({
    waypoints: [],
    signalName: 'deep signal',
    labelOffset: { t: 0.25, perpOffset: 6 },
  })
  useModelStore.getState().selectConnections([connectionId!])
  useModelStore.getState().removeConnection(connectionId!)
  expect(useModelStore.getState().selectedConnectionIds).toEqual([])

  useModelStore.getState().updateBlockParameters(fixture.transform.id, { numOutputs: 2 })
  expect(currentMiddle().childConnections?.some(connection => connection.id === 'transform-sink')).toBe(false)
  useModelStore.getState().selectBlocks([fixture.transform.id, fixture.source.id])
  useModelStore.getState().removeBlock(fixture.transform.id)
  middle = currentMiddle()
  expect(middle.children?.some(block => block.id === fixture.transform.id)).toBe(false)
  expect(middle.childConnections?.map(connection => connection.id)).toEqual(['unrelated'])
  expect(useModelStore.getState().selectedBlockIds).toEqual([fixture.source.id])
})

it('spreads and rotates selected blocks at depth and handles invalid navigation state', function () {
  const fixture = setDeepFixture()
  useModelStore.getState().updateBlockPosition(fixture.source.id, { x: 0, y: 0 })
  useModelStore.getState().updateBlockPosition(fixture.transform.id, { x: 10, y: 0 })
  useModelStore.getState().selectBlocks([fixture.source.id, fixture.transform.id])
  useModelStore.getState().spreadBlocks(2)

  let middle = currentMiddle()
  expect(middle.children?.find(block => block.id === fixture.source.id)?.position).toEqual({ x: -5, y: 0 })
  expect(middle.children?.find(block => block.id === fixture.transform.id)?.position).toEqual({ x: 15, y: 0 })
  expect(middle.children?.find(block => block.id === fixture.untouched.id)?.position).toEqual({ x: 100, y: 100 })

  useModelStore.getState().selectBlocks([fixture.source.id])
  useModelStore.getState().rotateSelectedBlocks()
  middle = currentMiddle()
  expect(middle.children?.find(block => block.id === fixture.source.id)?.rotation).toBe(90)
  expect(middle.children?.find(block => block.id === fixture.transform.id)?.rotation).toBeUndefined()

  useModelStore.setState({ currentPath: [{ id: 'missing', name: 'Missing' }] })
  expect(useModelStore.getState().getCurrentBlocks()).toEqual([])
  expect(useModelStore.getState().getCurrentConnections()).toEqual([])

  useModelStore.getState().createNewModel('Empty')
  useModelStore.getState().spreadBlocks(2)
  expect(useModelStore.getState().model?.blocks).toEqual([])
})

it('creates a default-named subsystem and expands a nested subsystem in place', function () {
  useModelStore.getState().createNewModel('Named Subsystem')
  const rootId = useModelStore.getState().addBlock(constantDefinition, { x: 0, y: 0 })
  const subsystemId = useModelStore.getState().createSubsystem([rootId])
  expect(useModelStore.getState().model?.blocks.find(block => block.id === subsystemId)?.name).toBe('Subsystem1')

  const fixture = setDeepFixture()
  const child = coverageBlock('expanded-child')
  const inner = coverageBlock('inner', 'subsystem')
  inner.children = [child]
  inner.childConnections = []
  fixture.middle.children?.push(inner)
  fixture.middle.childConnections?.push({
    id: 'source-inner',
    sourceBlockId: fixture.source.id,
    sourcePortId: fixture.source.outputPorts[0].id,
    targetBlockId: inner.id,
    targetPortId: inner.inputPorts[0].id,
  })

  useModelStore.getState().expandSubsystem(inner.id)

  const middle = currentMiddle()
  expect(middle.children?.some(block => block.id === inner.id)).toBe(false)
  expect(middle.children?.some(block => block.id === child.id)).toBe(true)
  expect(middle.childConnections?.some(connection => connection.id === 'source-inner')).toBe(false)
  expect(middle.childConnections?.some(connection => connection.id === 'unrelated')).toBe(true)
  expect(useModelStore.getState().selectedBlockIds).toEqual([child.id])
})

caseFn('removing a block prunes only connection selections deleted with it', function () {
  const source = coverageBlock('selection-source', 'constant')
  source.inputPorts = []
  const victim = coverageBlock('selection-victim')
  const sink = coverageBlock('selection-sink', 'scope')
  sink.outputPorts = []
  const doomed: Connection = {
    id: 'selection-doomed',
    sourceBlockId: source.id,
    sourcePortId: source.outputPorts[0].id,
    targetBlockId: victim.id,
    targetPortId: victim.inputPorts[0].id,
  }
  const retained: Connection = {
    id: 'selection-retained',
    sourceBlockId: source.id,
    sourcePortId: source.outputPorts[0].id,
    targetBlockId: sink.id,
    targetPortId: sink.inputPorts[0].id,
  }
  useModelStore.setState({
    model: coverageModel([source, victim, sink], [doomed, retained]),
    currentPath: [],
    selectedBlockIds: [victim.id],
    selectedConnectionIds: [doomed.id, retained.id],
  })

  useModelStore.getState().removeBlock(victim.id)

  expect(useModelStore.getState().model?.connections.map(connection => connection.id)).toEqual([retained.id])
  expect(useModelStore.getState().selectedConnectionIds).toEqual([retained.id])
})

caseFn('orphan pruning and nested block removal discard stale connection selections', function () {
  const fixture = setDeepFixture()
  useModelStore.setState({ selectedConnectionIds: ['transform-sink', 'unrelated'] })

  useModelStore.getState().updateBlockParameters(fixture.transform.id, { numOutputs: 2 })

  expect(currentMiddle().childConnections?.map(connection => connection.id)).toEqual([
    'source-transform',
    'unrelated',
  ])
  expect(useModelStore.getState().selectedConnectionIds).toEqual(['unrelated'])

  useModelStore.setState({ selectedConnectionIds: ['source-transform', 'unrelated'] })
  useModelStore.getState().removeBlock(fixture.transform.id)

  expect(currentMiddle().childConnections?.map(connection => connection.id)).toEqual(['unrelated'])
  expect(useModelStore.getState().selectedConnectionIds).toEqual(['unrelated'])
})

caseFn('createSubsystem groups blocks at the active nested path', function () {
  const fixture = setDeepFixture()

  const subsystemId = useModelStore.getState().createSubsystem(
    [fixture.source.id, fixture.transform.id],
    'NestedPair'
  )

  expect(subsystemId).toBeTruthy()
  const middle = currentMiddle()
  const nested = middle.children?.find(block => block.id === subsystemId)
  expect(nested).toMatchObject({ type: 'subsystem', name: 'NestedPair' })
  expect(nested?.children?.map(block => block.id)).toEqual(expect.arrayContaining([
    fixture.source.id,
    fixture.transform.id,
  ]))
  expect(middle.children?.some(block => block.id === fixture.source.id)).toBe(false)
  expect(middle.children?.some(block => block.id === fixture.transform.id)).toBe(false)
  expect(useModelStore.getState().currentPath.map(item => item.id)).toEqual(['outer', 'middle'])
  expect(useModelStore.getState().selectedBlockIds).toEqual([subsystemId])
  expect(useModelStore.getState().selectedConnectionIds).toEqual([])
})

caseFn('expanding a subsystem clears connection selections invalidated by rewiring', function () {
  const fixture = setDeepFixture()
  const child = coverageBlock('selection-expanded-child')
  const inner = coverageBlock('selection-inner', 'subsystem')
  inner.children = [child]
  inner.childConnections = []
  fixture.middle.children?.push(inner)
  fixture.middle.childConnections?.push({
    id: 'selection-inner-edge',
    sourceBlockId: fixture.source.id,
    sourcePortId: fixture.source.outputPorts[0].id,
    targetBlockId: inner.id,
    targetPortId: inner.inputPorts[0].id,
  })
  useModelStore.setState({ selectedConnectionIds: ['selection-inner-edge', 'unrelated'] })

  useModelStore.getState().expandSubsystem(inner.id)

  expect(useModelStore.getState().selectedConnectionIds).toEqual([])
  expect(currentMiddle().children?.some(block => block.id === child.id)).toBe(true)
})

caseFn('preserves malformed library connection identifiers that cannot be remapped', function () {
  const definition: LibraryBlockDefinition = {
    type: 'coverage__malformed',
    name: 'Malformed Library Block',
    category: 'subsystems',
    description: 'Malformed connection fixture',
    inputs: [],
    outputs: [],
    parameters: [],
    isLibraryBlock: true,
    libraryId: 'coverage',
    libraryName: 'Coverage',
    originalName: 'Malformed',
    implementation: {
      blocks: [coverageBlock('known-child')],
      connections: [{
        id: 'malformed-wire',
        sourceBlockId: 'missing-source',
        sourcePortId: 'missing-source-port',
        targetBlockId: 'missing-target',
        targetPortId: 'missing-target-port',
      }],
      portMappings: [],
    },
  }
  useModelStore.getState().createNewModel('Malformed Library')

  const blockId = useModelStore.getState().addBlock(definition, { x: 0, y: 0 })
  const connection = useModelStore.getState().model?.blocks
    .find(function (block) { return block.id === blockId })
    ?.childConnections?.[0]

  expect(connection).toMatchObject({
    sourceBlockId: 'missing-source',
    sourcePortId: 'missing-source-port',
    targetBlockId: 'missing-target',
    targetPortId: 'missing-target-port',
  })
})

caseFn('falls back to scalar reshape dimensions for malformed defaults', function () {
  useModelStore.getState().createNewModel('Malformed Reshapes')
  const defaults = ['["bad"]', 'invalid']

  for (const defaultValue of defaults) {
    const definition: BlockDefinition = {
      type: 'reshape',
      name: 'Reshape',
      category: 'routing',
      description: 'Malformed reshape',
      inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
      outputs: [{ name: 'out', dataType: 'double', dimensions: [9] }],
      parameters: [{
        name: 'outputDimensions',
        label: 'Dimensions',
        type: 'string',
        default: defaultValue,
      }],
    }
    const blockId = useModelStore.getState().addBlock(definition, { x: 0, y: 0 })
    const block = useModelStore.getState().model?.blocks.find(function (item) {
      return item.id === blockId
    })
    expect(block?.outputPorts[0].dimensions).toEqual([1])
  }
})

caseFn('treats omitted subsystem connection arrays as empty', function () {
  function resetFixture() {
    const source = coverageBlock('optional-source', 'constant')
    source.inputPorts = []
    const target = coverageBlock('optional-target')
    const subsystem = coverageBlock('optional-subsystem', 'subsystem')
    subsystem.children = [source, target]
    delete subsystem.childConnections
    useModelStore.setState({
      model: coverageModel([subsystem]),
      currentPath: [{ id: subsystem.id, name: subsystem.name }],
      selectedBlockIds: [],
      selectedConnectionIds: [],
    })
    return { source, target }
  }

  let fixture = resetFixture()
  expect(useModelStore.getState().getCurrentConnections()).toEqual([])
  const connectionId = useModelStore.getState().addConnection({
    sourceBlockId: fixture.source.id,
    sourcePortId: fixture.source.outputPorts[0].id,
    targetBlockId: fixture.target.id,
    targetPortId: fixture.target.inputPorts[0].id,
  })
  expect(useModelStore.getState().getCurrentConnections()).toHaveLength(1)
  expect(connectionId).toBeTruthy()

  resetFixture()
  useModelStore.getState().removeConnection('missing')
  expect(useModelStore.getState().getCurrentConnections()).toEqual([])

  resetFixture()
  useModelStore.getState().addConnectionWaypoint('missing', { x: 1, y: 2 })
  expect(useModelStore.getState().getCurrentConnections()).toEqual([])

  resetFixture()
  useModelStore.getState().updateConnectionSignalName('missing', 'signal')
  expect(useModelStore.getState().getCurrentConnections()).toEqual([])

  resetFixture()
  useModelStore.getState().updateConnectionLabelOffset('missing', { t: 0.5, perpOffset: 1 })
  expect(useModelStore.getState().getCurrentConnections()).toEqual([])

  fixture = resetFixture()
  useModelStore.getState().updateBlockParameters(fixture.target.id, { gain: 2 })
  expect(useModelStore.getState().getCurrentConnections()).toEqual([])

  fixture = resetFixture()
  useModelStore.getState().removeBlock(fixture.target.id)
  expect(useModelStore.getState().getCurrentBlocks().map(function (block) { return block.id })).toEqual([
    fixture.source.id,
  ])
})

caseFn('applies dynamic parameter fallbacks without corrupting ports', function () {
  const demux = coverageBlock('fallback-demux', 'demux')
  const sum = coverageBlock('fallback-sum', 'sum')
  const reshape = coverageBlock('fallback-reshape', 'reshape')
  useModelStore.setState({
    model: coverageModel([demux, sum, reshape]),
    currentPath: [],
    selectedBlockIds: [],
    selectedConnectionIds: [],
  })

  useModelStore.getState().updateBlockParameters(demux.id, { numOutputs: 'bad' })
  useModelStore.getState().updateBlockParameters(sum.id, { signs: '' })
  useModelStore.getState().updateBlockParameters(reshape.id, { outputDimensions: null })
  useModelStore.getState().updateBlockParameters(reshape.id, { outputDimensions: '["bad"]' })
  useModelStore.getState().updateBlockParameters(reshape.id, { outputDimensions: 'invalid' })
  useModelStore.getState().updateBlockParameters('missing-block', { value: 1 })

  let model = useModelStore.getState().model
  expect(model?.blocks.find(function (block) { return block.id === demux.id })?.outputPorts).toHaveLength(2)
  expect(model?.blocks.find(function (block) { return block.id === sum.id })?.inputPorts).toHaveLength(2)
  expect(model?.blocks.find(function (block) { return block.id === reshape.id })?.outputPorts[0].dimensions).toEqual([1])

  useModelStore.setState({ currentPath: [{ id: 'missing-path', name: 'Missing' }] })
  useModelStore.getState().updateBlockParameters(demux.id, { numOutputs: 3 })
  model = useModelStore.getState().model
  expect(model?.blocks.find(function (block) { return block.id === demux.id })?.outputPorts).toHaveLength(2)
})

caseFn('groups repeated malformed subsystem interfaces with safe scalar ports', function () {
  const externalA = coverageBlock('external-a')
  const externalB = coverageBlock('external-b')
  const selectedSource = coverageBlock('selected-source')
  const selectedTarget = coverageBlock('selected-target')
  const connections: Connection[] = [
    { id: 'incoming-a', sourceBlockId: externalA.id, sourcePortId: externalA.outputPorts[0].id, targetBlockId: selectedTarget.id, targetPortId: 'missing-target-port' },
    { id: 'incoming-b', sourceBlockId: externalB.id, sourcePortId: externalB.outputPorts[0].id, targetBlockId: selectedTarget.id, targetPortId: 'missing-target-port' },
    { id: 'outgoing-a', sourceBlockId: selectedSource.id, sourcePortId: 'missing-source-port', targetBlockId: externalA.id, targetPortId: externalA.inputPorts[0].id },
    { id: 'outgoing-b', sourceBlockId: selectedSource.id, sourcePortId: 'missing-source-port', targetBlockId: externalB.id, targetPortId: externalB.inputPorts[0].id },
    { id: 'outside', sourceBlockId: externalA.id, sourcePortId: externalA.outputPorts[0].id, targetBlockId: externalB.id, targetPortId: externalB.inputPorts[0].id },
  ]
  useModelStore.setState({
    model: coverageModel([externalA, externalB, selectedSource, selectedTarget], connections),
    currentPath: [],
    selectedBlockIds: [],
    selectedConnectionIds: [],
  })

  const subsystemId = useModelStore.getState().createSubsystem(
    [selectedSource.id, selectedTarget.id],
    'Malformed Interface',
  )
  const subsystem = useModelStore.getState().model?.blocks.find(function (block) {
    return block.id === subsystemId
  })

  expect(subsystem?.inputPorts).toEqual([
    expect.objectContaining({ dataType: 'double', dimensions: [1] }),
  ])
  expect(subsystem?.outputPorts).toEqual([
    expect.objectContaining({ dataType: 'double', dimensions: [1] }),
  ])
  expect(useModelStore.getState().model?.connections).toHaveLength(5)
})

caseFn('dissolves malformed subsystem interfaces without dangling connections', function () {
  const source = coverageBlock('malformed-expand-source')
  const target = coverageBlock('malformed-expand-target')
  const child = coverageBlock('malformed-expand-child')
  const inport = coverageBlock('malformed-expand-inport', 'inport')
  inport.parameters = { portNumber: 1 }
  inport.inputPorts = []
  const outport = coverageBlock('malformed-expand-outport', 'outport')
  outport.parameters = { portNumber: 1 }
  outport.outputPorts = []
  const subsystem = coverageBlock('malformed-expand', 'subsystem')
  subsystem.inputPorts = [coveragePort('subsystem-in-1'), coveragePort('subsystem-in-2')]
  subsystem.outputPorts = [coveragePort('subsystem-out-1'), coveragePort('subsystem-out-2')]
  subsystem.children = [inport, child, outport]
  subsystem.childConnections = [
    { id: 'unmapped-in', sourceBlockId: inport.id, sourcePortId: inport.outputPorts[0].id, targetBlockId: child.id, targetPortId: child.inputPorts[0].id },
    { id: 'unmapped-out', sourceBlockId: child.id, sourcePortId: child.outputPorts[0].id, targetBlockId: outport.id, targetPortId: outport.inputPorts[0].id },
    { id: 'interface-only', sourceBlockId: inport.id, sourcePortId: inport.outputPorts[0].id, targetBlockId: outport.id, targetPortId: outport.inputPorts[0].id },
    { id: 'unsupported', sourceBlockId: child.id, sourcePortId: child.outputPorts[0].id, targetBlockId: 'missing-child', targetPortId: 'missing-input' },
  ]
  const externalConnections: Connection[] = [
    { id: 'bad-in-port', sourceBlockId: source.id, sourcePortId: source.outputPorts[0].id, targetBlockId: subsystem.id, targetPortId: 'unknown-input' },
    { id: 'missing-inport', sourceBlockId: source.id, sourcePortId: source.outputPorts[0].id, targetBlockId: subsystem.id, targetPortId: subsystem.inputPorts[1].id },
    { id: 'bad-out-port', sourceBlockId: subsystem.id, sourcePortId: 'unknown-output', targetBlockId: target.id, targetPortId: target.inputPorts[0].id },
    { id: 'missing-outport', sourceBlockId: subsystem.id, sourcePortId: subsystem.outputPorts[1].id, targetBlockId: target.id, targetPortId: target.inputPorts[0].id },
  ]
  useModelStore.setState({
    model: coverageModel([source, subsystem, target], externalConnections),
    currentPath: [],
    selectedBlockIds: [],
    selectedConnectionIds: externalConnections.map(function (connection) { return connection.id }),
  })

  useModelStore.getState().expandSubsystem(subsystem.id)

  const model = useModelStore.getState().model
  expect(model?.blocks.some(function (block) { return block.id === subsystem.id })).toBe(false)
  expect(model?.connections.some(function (connection) {
    return connection.sourceBlockId === subsystem.id || connection.targetBlockId === subsystem.id
  })).toBe(false)
  expect(useModelStore.getState().selectedConnectionIds).toEqual([])

  const emptySubsystem = coverageBlock('empty-connections-subsystem', 'subsystem')
  emptySubsystem.children = [coverageBlock('empty-connections-child')]
  delete emptySubsystem.childConnections
  useModelStore.setState({ model: coverageModel([emptySubsystem]), currentPath: [] })
  useModelStore.getState().expandSubsystem(emptySubsystem.id)
  expect(useModelStore.getState().model?.blocks.map(function (block) { return block.id })).toEqual([
    'empty-connections-child',
  ])

  useModelStore.getState().toggleSubsystemExpanded('missing-subsystem')
  expect(useModelStore.getState().model?.blocks).toHaveLength(1)
})

caseFn('expands inside a parent with an omitted connection array', function () {
  const child = coverageBlock('nested-empty-child')
  const inner = coverageBlock('nested-empty-inner', 'subsystem')
  inner.children = [child]
  inner.childConnections = []
  const outer = coverageBlock('nested-empty-outer', 'subsystem')
  outer.children = [inner]
  delete outer.childConnections
  useModelStore.setState({
    model: coverageModel([outer]),
    currentPath: [{ id: outer.id, name: outer.name }],
    selectedBlockIds: [],
    selectedConnectionIds: [],
  })

  useModelStore.getState().expandSubsystem(inner.id)

  expect(useModelStore.getState().getCurrentBlocks().map(function (block) { return block.id })).toEqual([
    child.id,
  ])
  expect(useModelStore.getState().getCurrentConnections()).toEqual([])
})
