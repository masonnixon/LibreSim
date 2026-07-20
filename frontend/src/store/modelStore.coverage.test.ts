import { expect, it } from 'vitest'

import { useModelStore } from './modelStore'
import type { BlockDefinition, BlockInstance } from '../types/block'
import type { LibraryBlockDefinition } from '../types/library'
import type { Model } from '../types/model'

const constantDefinition: BlockDefinition = {
  type: 'constant',
  name: 'Constant',
  category: 'sources',
  description: 'Constant',
  inputs: [],
  outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
  parameters: [{ name: 'value', label: 'Value', type: 'string', default: 0 }],
}

it('checks another constant contract', function () {
  useModelStore.getState().createNewModel('Coverage Model')
  const id = useModelStore.getState().addBlock(constantDefinition, { x: 0, y: 0 })
  const cases: Array<[unknown, number[]]> = [
    [null, [1]],
    [[1, 2, 3], [3]],
    ['42', [1]],
    ['not a number', [1]],
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
