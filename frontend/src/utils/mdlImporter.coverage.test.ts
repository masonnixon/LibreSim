import { expect, it, vi } from 'vitest'
import { blockRegistry } from '../blocks'

import {
  analyzeLibraryDependencies,
  clearLibraryRegistry,
  importMDL,
  importMDLAsLibrary,
  importMDLAsLibraryLegacy,
  propagateDimensions,
  registerLibraryBlocks,
} from './mdlImporter'
import type { BlockInstance, Connection } from '../types/block'

it('parses wrapper objects, ignored configuration, and nested arrays', function () {
  const mdl = `Model {
    Name "Wrapped"
    $ObjectID { Value 10 }
    Simulink.SolverCC { Ignored true }
    Array { Name "diagnostic" }
    Simulink.BlockDiagram {
      Block {
        BlockType Constant
        Name "Direct"
        Value []
      }
      System {
        Name "Wrapped"
        Block {
          BlockType Constant
          Name "Nested"
          Position [[10 20] [30 40]]
          Value "escaped\\\"value"
        }
      }
    }
  }`

  const model = importMDL(mdl)

  expect(model.metadata.name).toBe('Wrapped')
  expect(model.blocks.map(block => block.name)).toEqual(['Nested'])
  expect(model.blocks[0].position).toEqual({ x: 100, y: 20 })
  expect(model.blocks[0].parameters.value).toBe('escaped"value')
})

it('normalizes legacy parameter aliases and defaults', function () {
  const mdl = `Model {
    Name "Aliases"
    System {
      Name "Aliases"
      Block { BlockType Inport Name "PortNumber" PortNumber 2 }
      Block { BlockType Outport Name "PortNum" PortNum 3 }
      Block { BlockType Inport Name "Number" Number 4 }
      Block { BlockType Mux Name "MuxNumber" NumberOfInputs 3 }
      Block { BlockType Mux Name "MuxShort" NumInputs 4 }
      Block { BlockType Mux Name "MuxPorts" Ports 5 }
      Block { BlockType Demux Name "DemuxNumber" NumberOfOutputs 3 }
      Block { BlockType Demux Name "DemuxShort" NumOutputs 4 }
      Block { BlockType Demux Name "DemuxPorts" Ports [1, 5] }
      Block { BlockType Math Name "MathFunction" Function "log" }
      Block { BlockType Math Name "MathAlias" MathFunction "sqrt" }
      Block { BlockType Math Name "MathPower" Operator "pow" Power 7 }
      Block { BlockType Math Name "MathDefault" }
      Block { BlockType Trigonometry Name "TrigFunction" Function "cos" }
      Block { BlockType Trigonometry Name "TrigDefault" }
      Block { BlockType Reshape Name "ReshapeSize" OutputSize [2, 3] }
      Block { BlockType Reshape Name "ReshapeDimensions" Dimensions [4, 5] }
      Block { BlockType Reshape Name "ReshapeShort" Size [6, 7] }
      Block { BlockType Reshape Name "ReshapeDefault" }
      Block { BlockType Product Name "ProductDefault" Inputs "" }
      Block { BlockType Product Name "ProductInvalid" Inputs "abc" }
    }
  }`
  const model = importMDL(mdl)
  const parameters = (name: string) => model.blocks.find(block => block.name === name)?.parameters
  expect(model.blocks).toHaveLength(21)
  expect(parameters('PortNumber')?.portNumber).toBe(2)
  expect(parameters('PortNum')?.portNumber).toBe(3)
  expect(parameters('Number')?.portNumber).toBe(4)
  expect(parameters('MuxNumber')?.numInputs).toBe(3)
  expect(parameters('MuxShort')?.numInputs).toBe(4)
  expect(parameters('MuxPorts')?.numInputs).toBe(5)
  expect(parameters('DemuxNumber')?.numOutputs).toBe(3)
  expect(parameters('DemuxShort')?.numOutputs).toBe(4)
  expect(parameters('DemuxPorts')?.numOutputs).toBe(5)
  expect(parameters('MathFunction')?.function).toBe('log')
  expect(parameters('MathAlias')?.function).toBe('sqrt')
  expect(parameters('MathPower')?.exponent).toBe(7)
  expect(parameters('MathDefault')?.function).toBe('exp')
  expect(parameters('TrigFunction')?.function).toBe('cos')
  expect(parameters('TrigDefault')?.function).toBe('sin')
  expect(parameters('ReshapeSize')?.outputDimensions).toBe(2)
  expect(parameters('ReshapeDimensions')?.outputDimensions).toBe(4)
  expect(parameters('ReshapeShort')?.outputDimensions).toBe(6)
  expect(parameters('ReshapeDefault')).toMatchObject({
    outputDimensions: '[1]',
    outputDimensionality: '1-D array',
  })
  expect(parameters('ProductDefault')?.operations).toBe('**')
  expect(parameters('ProductInvalid')?.operations).toBe('***')
})

it('converts inline subsystem contents and derives its interface', function () {
  const mdl = `Model {
    Name "Inline"
    System {
      Name "Inline"
      Block {
        BlockType SubSystem
        Name "InlineSub"
        Ports "[9, 9]"
        System {
          Name "Inline/InlineSub"
          Block { BlockType Inport Name "In1" Port "1" }
          Block { BlockType Constant Name "Value" Value "4" }
          Block { BlockType Outport Name "Out1" Port "1" }
          Line { SrcBlock "Value" SrcPort "1" DstBlock "Out1" DstPort "1" }
        }
      }
    }
  }`

  const subsystem = importMDL(mdl).blocks[0]

  expect(subsystem.type).toBe('subsystem')
  expect(subsystem.children?.map(block => block.name)).toEqual(['In1', 'Value', 'Out1'])
  expect(subsystem.childConnections).toHaveLength(1)
  expect(subsystem.inputPorts).toHaveLength(1)
  expect(subsystem.outputPorts).toHaveLength(1)
})

it('skips malformed connections while recursively importing valid branches', function () {
  const mdl = `Model {
    Name "Connections"
    System {
      Name "Connections"
      Block { BlockType Constant Name "Source" Value "1" }
      Block { BlockType Gain Name "Target" Gain "2" }
      Block { BlockType Terminator Name "NoOutput" }
      Block { BlockType Constant Name "NoInput" Value "2" }
      Line { SrcBlock "Missing" SrcPort 1 DstBlock "Target" DstPort 1 }
      Line { SrcBlock "Source" SrcPort 1 DstBlock "Missing" DstPort 1 }
      Line { SrcBlock "NoOutput" SrcPort 1 DstBlock "Target" DstPort 1 }
      Line { SrcBlock "Source" SrcPort 1 DstBlock "NoInput" DstPort 1 }
      Line {
        SrcBlock "Source"
        SrcPort "99"
        Branch {
          DstBlock "Target"
          DstPort "99"
          Branch { DstBlock "Target" DstPort 1 }
        }
      }
      Line { SrcBlock "Source" SrcPort 1 }
    }
  }`

  const model = importMDL(mdl)

  expect(model.connections).toHaveLength(2)
  expect(new Set(model.connections.map(connection => connection.sourcePortId)).size).toBe(1)
  expect(new Set(model.connections.map(connection => connection.targetPortId)).size).toBe(1)
})

it('resolves local and normalized cross-library references with independent IDs', function () {
  const external: BlockInstance = {
    id: 'external',
    type: 'subsystem',
    name: 'Reusable',
    position: { x: 0, y: 0 },
    parameters: {},
    inputPorts: [{ id: 'external-in', name: 'in1', dataType: 'double', dimensions: [1] }],
    outputPorts: [{ id: 'external-out', name: 'out1', dataType: 'double', dimensions: [1] }],
    children: [
      {
        id: 'external-child',
        type: 'gain',
        name: 'Gain',
        position: { x: 10, y: 10 },
        parameters: { gain: 2 },
        inputPorts: [{ id: 'external-child-in', name: 'in1', dataType: 'double', dimensions: [1] }],
        outputPorts: [{ id: 'external-child-out', name: 'out1', dataType: 'double', dimensions: [1] }],
        children: [{
          id: 'nested-child',
          type: 'constant',
          name: 'Nested',
          position: { x: 0, y: 0 },
          parameters: { value: 1 },
          inputPorts: [],
          outputPorts: [{ id: 'nested-child-out', name: 'out1', dataType: 'double', dimensions: [1] }],
        }],
        childConnections: [{
          id: 'nested-connection',
          sourceBlockId: 'nested-child',
          sourcePortId: 'nested-child-out',
          targetBlockId: 'unmapped-target',
          targetPortId: 'unmapped-port',
        }],
      },
    ],
    childConnections: [{
      id: 'external-connection',
      sourceBlockId: 'external-child',
      sourcePortId: 'external-child-out',
      targetBlockId: 'unmapped-target',
      targetPortId: 'unmapped-port',
    }],
  }
  const mdl = `Library {
    Name "CurrentLib"
    System {
      Name "CurrentLib"
      Block {
        BlockType SubSystem
        Name "LocalTarget"
        System { Block { BlockType Constant Name "LocalValue" Value "1" } }
      }
      Block {
        BlockType SubSystem
        Name "Container"
        System {
          Block { BlockType Reference Name "Local" SourceBlock "LocalTarget" }
          Block { BlockType Reference Name "External" SourceBlock "External_2010a/Reusable" }
          Block { BlockType Reference Name "Missing" SourceBlock "MissingLib/Nope" }
        }
      }
    }
  }`

  clearLibraryRegistry()
  registerLibraryBlocks('External_2009b', [external])
  try {
    const result = importMDLAsLibrary(mdl, { sourcePath: 'current.mdl', registerBlocks: false })
    const container = result.subsystemBlocks.find(block => block.name === 'Container')
    const local = container?.children?.find(block => block.name === 'Local')
    const resolved = container?.children?.find(block => block.name === 'External')

    expect(local?.type).toBe('subsystem')
    expect(local?.children?.[0].name).toBe('LocalValue')
    expect(resolved?.type).toBe('subsystem')
    expect(resolved?.children?.[0].id).not.toBe('external-child')
    expect(resolved?.children?.[0].children?.[0].id).not.toBe('nested-child')
    expect(resolved?.childConnections?.[0].sourceBlockId).toBe(resolved?.children?.[0].id)
    expect(result.unresolvedReferences).toEqual(['MissingLib/Nope'])
    expect(result.dependencies.availableLibraries).toEqual(['External_2010a'])
    expect(result.dependencies.missingLibraries).toEqual(['MissingLib'])
    expect(result.library.sourcePath).toBe('current.mdl')
  } finally {
    clearLibraryRegistry()
  }
})

it('returns safe dependency results for invalid content and supports the legacy wrapper', function () {
  expect(analyzeLibraryDependencies('not an mdl file')).toEqual({
    externalReferences: [],
    missingLibraries: [],
    availableLibraries: [],
  })

  const mdl = `Library {
    Name "Legacy"
    System {
      Name "Legacy"
      Block {
        BlockType SubSystem
        Name "Reusable"
        System { Block { BlockType Constant Name "Value" Value "1" } }
      }
    }
  }`
  const library = importMDLAsLibraryLegacy(mdl, 'legacy.mdl')

  expect(library.name).toBe('Legacy')
  expect(library.sourcePath).toBe('legacy.mdl')
  clearLibraryRegistry()
})

it('constructs fallback ports when a block definition is unavailable', function () {
  const mdl = `Model {
    Name "Fallbacks"
    System {
      Name "Fallbacks"
      Block { BlockType Mux Name "Mux" Inputs "3" }
      Block { BlockType Demux Name "Demux" Outputs "3" }
      Block { BlockType DotProduct Name "Dot" }
      Block { BlockType Reshape Name "ReshapeArray" OutputDimensions "[2, 3]" }
      Block { BlockType Reshape Name "ReshapeText" OutputSize "rows 4 by 5" }
      Block { BlockType Reshape Name "ReshapeInherit" OutputDimensionality "Column vector (2-D)" }
      Block { BlockType Math Name "Math" }
      Block { BlockType Sqrt Name "Sqrt" }
      Block { BlockType UnaryMinus Name "Minus" }
      Block { BlockType DataTypeConversion Name "Convert" }
      Block { BlockType Memory Name "Memory" }
      Block { BlockType Selector Name "Selector" }
      Block { BlockType Logic Name "Logic" Inputs "3" }
      Block { BlockType RelationalOperator Name "Relation" }
      Block { BlockType Concatenate Name "Concat" NumInputs "3" }
      Block { BlockType Inport Name "In" }
      Block { BlockType Outport Name "Out" }
      Block { BlockType Reference Name "Reference" Ports "[2, 3]" }
      Block { BlockType SubSystem Name "Subsystem" Ports "[2, 3]" }
      Block { BlockType Constant Name "Default" Value "1" }
    }
  }`
  const registryLookup = vi.spyOn(blockRegistry, 'get').mockReturnValue(undefined)
  try {
    const model = importMDL(mdl)
    const byName = (name: string) => model.blocks.find(block => block.name === name)
    expect(byName('Mux')?.inputPorts).toHaveLength(3)
    expect(byName('Demux')?.outputPorts).toHaveLength(3)
    expect(byName('Dot')?.inputPorts).toHaveLength(2)
    expect(byName('ReshapeArray')?.outputPorts[0].dimensions).toEqual([6])
    expect(byName('ReshapeText')?.outputPorts[0].dimensions).toEqual([20])
    expect(byName('ReshapeInherit')?.outputPorts[0].dimensions).toEqual([1])
    expect(byName('Logic')?.inputPorts).toHaveLength(3)
    expect(byName('Concat')?.inputPorts).toHaveLength(3)
    expect(byName('In')?.inputPorts).toHaveLength(0)
    expect(byName('Out')?.outputPorts).toHaveLength(0)
    expect(byName('Reference')?.inputPorts).toHaveLength(2)
    expect(byName('Subsystem')?.outputPorts).toHaveLength(3)
    expect(byName('Default')?.inputPorts).toHaveLength(1)
  } finally {
    registryLookup.mockRestore()
  }
})

it('propagates dimension edge cases and terminates cyclic traces', function () {
  function constant(id: string, value: unknown): BlockInstance {
    return {
      id,
      type: 'constant',
      name: id,
      position: { x: 0, y: 0 },
      parameters: { value },
      inputPorts: [],
      outputPorts: [{ id: `${id}-out`, name: 'out', dataType: 'double', dimensions: [1] }],
    }
  }
  const constants = [
    constant('null', null),
    constant('number-text', '42'),
    constant('semicolon', '[1; 2; 3]'),
    constant('spaces', '[1 2 3 4]'),
    constant('commas', '1, 2, 3, 4, 5'),
    constant('invalid', '[one, two]'),
  ]
  propagateDimensions(constants, [])
  expect(constants[0].outputPorts[0].dimensions).toEqual([1])
  expect(constants[1].outputPorts[0].dimensions).toEqual([1])
  expect(constants[2].outputPorts[0].dimensions).toEqual([3])
  expect(constants[3].outputPorts[0].dimensions).toEqual([4])
  expect(constants[4].outputPorts[0].dimensions).toEqual([5])
  expect(constants[5].outputPorts[0].dimensions).toEqual([1])
  const gain: BlockInstance = {
    id: 'gain', type: 'gain', name: 'Gain', position: { x: 0, y: 0 }, parameters: {},
    inputPorts: [{ id: 'gain-in', name: 'in', dataType: 'double', dimensions: [1] }],
    outputPorts: [{ id: 'gain-out', name: 'out', dataType: 'double', dimensions: [1] }],
  }
  const sink: BlockInstance = {
    id: 'sink', type: 'outport', name: 'Sink', position: { x: 0, y: 0 }, parameters: {},
    inputPorts: [{ id: 'sink-in', name: 'in', dataType: 'double', dimensions: [1] }],
    outputPorts: [],
  }
  const connections: Connection[] = [
    { id: 'cycle', sourceBlockId: 'gain', sourcePortId: 'gain-out', targetBlockId: 'gain', targetPortId: 'gain-in' },
    { id: 'observe', sourceBlockId: 'gain', sourcePortId: 'gain-out', targetBlockId: 'sink', targetPortId: 'sink-in' },
  ]
  propagateDimensions([gain, sink], connections)
  expect(sink.inputPorts[0].dimensions).toEqual([1])
  const childSource = constant('child-source', [1, 2, 3])
  childSource.outputPorts[0].dimensions = [3]
  const childOut: BlockInstance = {
    id: 'child-out', type: 'outport', name: 'ChildOut', position: { x: 0, y: 0 }, parameters: { portNumber: 1 },
    inputPorts: [{ id: 'child-out-in', name: 'in', dataType: 'double', dimensions: [1] }], outputPorts: [],
  }
  const subsystem: BlockInstance = {
    id: 'dimension-subsystem', type: 'subsystem', name: 'DimensionSubsystem', position: { x: 0, y: 0 }, parameters: {},
    inputPorts: [], outputPorts: [{ id: 'dimension-subsystem-out', name: 'out', dataType: 'double', dimensions: [1] }],
    children: [childSource, childOut],
  }
  const childWire: Connection = {
    id: 'child-wire', sourceBlockId: 'child-source', sourcePortId: 'child-source-out',
    targetBlockId: 'child-out', targetPortId: 'child-out-in',
  }
  let childConnectionReads = 0
  Object.defineProperty(subsystem, 'childConnections', {
    configurable: true,
    get: function getChildConnections() {
      childConnectionReads++
      return childConnectionReads === 1 ? undefined : [childWire]
    },
  })
  const subsystemSink: BlockInstance = {
    id: 'subsystem-sink', type: 'outport', name: 'SubsystemSink', position: { x: 0, y: 0 }, parameters: {},
    inputPorts: [{ id: 'subsystem-sink-in', name: 'in', dataType: 'double', dimensions: [1] }], outputPorts: [],
  }
  propagateDimensions([subsystem, subsystemSink], [{
    id: 'subsystem-wire', sourceBlockId: subsystem.id, sourcePortId: subsystem.outputPorts[0].id,
    targetBlockId: subsystemSink.id, targetPortId: subsystemSink.inputPorts[0].id,
  }])
  expect(subsystemSink.inputPorts[0].dimensions).toEqual([3])
  const reshapeSource = constant('reshape-source', [1, 2, 3, 4])
  const reshape: BlockInstance = {
    id: 'reshape', type: 'reshape', name: 'Reshape', position: { x: 0, y: 0 }, parameters: {},
    inputPorts: [{ id: 'reshape-in', name: 'in', dataType: 'double', dimensions: [1] }],
    outputPorts: [{ id: 'reshape-out', name: 'out', dataType: 'double', dimensions: [-1] }],
  }
  propagateDimensions([reshapeSource, reshape], [{
    id: 'reshape-wire', sourceBlockId: reshapeSource.id, sourcePortId: reshapeSource.outputPorts[0].id,
    targetBlockId: reshape.id, targetPortId: reshape.inputPorts[0].id,
  }])
  expect(reshape.outputPorts[0].dimensions).toEqual([4])
})

it('covers parser fallbacks, legacy aliases, and UUID-free IDs', function () {
  const originalCrypto = globalThis.crypto
  vi.stubGlobal('crypto', undefined)
  try {
    const model = importMDL(`Model {
      Name "Direct"
      Custom { Value 1 }
      Block { BlockType Constant Name "FromConstantValue" ConstantValue "2" }
      Block { BlockType Constant Name "FromConstant" Constant "3" }
      Block { BlockType Mux Name "MuxString" Ports "[3]" }
      Block { BlockType Demux Name "DemuxString" Ports "[1, 3]" }
      Block { BlockType Math Name "PowerDefault" Operator "pow" }
    }`)
    expect(model.id).toMatch(/^model_/)
    expect(model.blocks).toHaveLength(5)
    expect(model.blocks[0].parameters.value).toBe(2)
    expect(model.blocks[1].parameters.value).toBe(3)
    expect(model.blocks[2].inputPorts).toHaveLength(3)
    expect(model.blocks[3].outputPorts).toHaveLength(3)
    expect(model.blocks[4].parameters.exponent).toBe(2)
  } finally {
    vi.stubGlobal('crypto', originalCrypto)
  }
  expect(importMDL('Model { Empty }').blocks).toEqual([])
  expect(function invalidStructure() { importMDL('Model') }).toThrow('Could not parse file structure')
})

it('sorts imported library interface ports by their declared numbers', function () {
  const result = importMDLAsLibrary(`Library {
    Name "Sorted"
    System {
      Name "Sorted"
      Block {
        BlockType SubSystem
        Name "Reusable"
        System {
          Block { BlockType Inport Name "In2" Port 2 }
          Block { BlockType Inport Name "In1" Port 1 }
          Block { BlockType Outport Name "Out2" Port 2 }
          Block { BlockType Outport Name "Out1" Port 1 }
        }
      }
    }
  }`, { registerBlocks: false })

  expect(result.library.blocks[0].inputs.map(port => port.name)).toEqual(['In1', 'In2'])
  expect(result.library.blocks[0].outputs.map(port => port.name)).toEqual(['Out1', 'Out2'])
})
