import { expect, it, vi } from 'vitest'
import { blockRegistry } from '../blocks'

import {
  analyzeLibraryDependencies,
  clearLibraryRegistry,
  importMDL,
  importMDLAsLibrary,
  importMDLAsLibraryLegacy,
  isMDLLibrary,
  propagateDimensions,
  registerLibraryBlocks,
  unregisterLibraryBlocks,
  getRegisteredBlock,
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
          Value "escaped\\"value"
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
  expect(parameters('ReshapeSize')?.outputDimensions).toEqual([2, 3])
  expect(parameters('ReshapeDimensions')?.outputDimensions).toEqual([4, 5])
  expect(parameters('ReshapeShort')?.outputDimensions).toEqual([6, 7])
  expect(parameters('ReshapeDefault')).toMatchObject({
    outputDimensions: '[1]',
    outputDimensionality: '1-D array',
  })
  expect(parameters('ProductDefault')?.operations).toBe('**')
  expect(parameters('ProductInvalid')?.operations).toBe('***')
})

it('preserves the inherit marker for reshape modes without explicit dimensions', function () {
  // Regression: the default output size used to mask dimension inheritance entirely.
  const model = importMDL(`Model {
    Name "InheritedReshape"
    System {
      Name "InheritedReshape"
      Block {
        BlockType Reshape
        Name "ColumnVector"
        OutputDimensionality "Column vector (2-D)"
      }
    }
  }`)

  expect(model.blocks[0].outputPorts[0].dimensions).toEqual([-1])
})

it('preserves structured constant values and reshape dimensions', function () {
  const model = importMDL(`Model {
    Name "MatrixReshape"
    System {
      Name "MatrixReshape"
      Block { BlockType Constant Name "Vector" Value [1, 2, 3] }
      Block { BlockType Reshape Name "Matrix" OutputDimensions [2, 3] }
    }
  }`)

  expect(model.blocks[0].parameters.value).toEqual([1, 2, 3])
  expect(model.blocks[0].outputPorts[0].dimensions).toEqual([3])
  expect(model.blocks[1].outputPorts[0].dimensions).toEqual([6])
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
        }, {
          id: 'nested-unmapped-source',
          sourceBlockId: 'unmapped-source',
          sourcePortId: 'unmapped-source-port',
          targetBlockId: 'nested-child',
          targetPortId: 'nested-child-out',
        }],
      },
    ],
    childConnections: [{
      id: 'external-connection',
      sourceBlockId: 'external-child',
      sourcePortId: 'external-child-out',
      targetBlockId: 'unmapped-target',
      targetPortId: 'unmapped-port',
    }, {
      id: 'external-unmapped-source',
      sourceBlockId: 'unmapped-source',
      sourcePortId: 'unmapped-source-port',
      targetBlockId: 'external-child',
      targetPortId: 'external-child-in',
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

it('tracks absent local references and resolves an explicitly empty external block', function () {
  const external: BlockInstance = {
    id: 'empty-external',
    type: 'subsystem',
    name: 'Reusable',
    position: { x: 0, y: 0 },
    parameters: {},
    inputPorts: [],
    outputPorts: [],
    children: [],
  }
  clearLibraryRegistry()
  registerLibraryBlocks('EmptyExternal', [external])
  try {
    const result = importMDLAsLibrary(`Library {
      Name "Current"
      System {
        Name "Current"
        Block {
          BlockType SubSystem
          Name "Container"
          System {
            Block { BlockType Constant Name "Value" Value 1 }
            Block { BlockType Reference Name "LocalAbsent" SourceBlock "LocalAbsent" }
            Block { BlockType Reference Name "ExternalEmpty" SourceBlock "EmptyExternal/Reusable" }
          }
        }
      }
    }`, { registerBlocks: false })
    const children = result.subsystemBlocks[0].children || []

    expect(result.unresolvedReferences).toEqual(['LocalAbsent'])
    expect(children.find(block => block.name === 'ExternalEmpty')).toMatchObject({
      type: 'subsystem',
      children: undefined,
      childConnections: undefined,
    })
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
    expect(byName('ReshapeInherit')?.outputPorts[0].dimensions).toEqual([-1])
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
  const badSink: BlockInstance = {
    id: 'bad-sink', type: 'outport', name: 'BadSink', position: { x: 0, y: 0 }, parameters: {},
    inputPorts: [{ id: 'bad-sink-in', name: 'in', dataType: 'double', dimensions: [1] }],
    outputPorts: [],
  }
  const connections: Connection[] = [
    { id: 'cycle', sourceBlockId: 'gain', sourcePortId: 'gain-out', targetBlockId: 'gain', targetPortId: 'gain-in' },
    { id: 'observe', sourceBlockId: 'gain', sourcePortId: 'gain-out', targetBlockId: 'sink', targetPortId: 'sink-in' },
    { id: 'bad-port', sourceBlockId: 'gain', sourcePortId: 'missing-output', targetBlockId: 'bad-sink', targetPortId: 'bad-sink-in' },
  ]
  propagateDimensions([gain, sink, badSink], connections)
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

it('covers omitted optional parameters and malformed dynamic port counts', function () {
  const model = importMDL(`Model {
    Name "SparseParameters"
    System {
      Name "SparseParameters"
      Block { BlockType "Sine Wave" Name "Sine" }
      Block { BlockType DiscretePulseGenerator Name "Pulse" }
      Block { BlockType Integrator Name "Limited" LimitOutput on }
      Block { BlockType TransferFcn Name "ScalarTransfer" Numerator "5" Denominator "6" }
      Block { BlockType StateSpace Name "StateSpace" }
      Block { BlockType PID Name "PID" }
      Block { BlockType RateLimiter Name "Rate" }
      Block { BlockType Logic Name "Logic" }
      Block { BlockType Concatenate Name "Concat" }
      Block { BlockType Mux Name "MuxBadArray" Ports [bad] }
      Block { BlockType Mux Name "MuxZeroText" Ports "[0]" }
      Block { BlockType Mux Name "MuxInvalidText" Ports "invalid" }
      Block { BlockType Mux Name "MuxEmptyArray" Ports [] }
      Block { BlockType Demux Name "DemuxBadArray" Ports [1, bad] }
      Block { BlockType Demux Name "DemuxZeroText" Ports "[1, 0]" }
      Block { BlockType Demux Name "DemuxInvalidText" Ports "invalid" }
      Block { BlockType Demux Name "DemuxEmptyArray" Ports [] }
      Block { BlockType Scope Name "ScopeBad" NumInputPorts "bad" }
    }
  }`)
  const byName = (name: string) => model.blocks.find(block => block.name === name)

  expect(byName('Sine')?.parameters).toEqual({})
  expect(byName('Pulse')?.parameters).toEqual({})
  expect(byName('Limited')?.parameters).toEqual({ limitOutput: true })
  expect(byName('ScalarTransfer')?.parameters).toEqual({ numerator: [5], denominator: [6] })
  expect(byName('StateSpace')?.parameters).toEqual({})
  expect(byName('PID')?.parameters).toEqual({})
  expect(byName('Rate')?.parameters).toEqual({})
  expect(byName('Logic')?.parameters).toEqual({})
  expect(byName('Concat')?.parameters).toEqual({})
  expect(byName('MuxBadArray')?.inputPorts).toHaveLength(2)
  expect(byName('MuxZeroText')?.inputPorts).toHaveLength(2)
  expect(byName('MuxInvalidText')?.parameters.numInputs).toBeUndefined()
  expect(byName('MuxEmptyArray')?.parameters.numInputs).toBeUndefined()
  expect(byName('DemuxBadArray')?.outputPorts).toHaveLength(2)
  expect(byName('DemuxZeroText')?.outputPorts).toHaveLength(2)
  expect(byName('DemuxInvalidText')?.parameters.numOutputs).toBeUndefined()
  expect(byName('DemuxEmptyArray')?.parameters.numOutputs).toBeUndefined()
  expect(byName('ScopeBad')?.inputPorts).toHaveLength(1)
})

it('covers fallback port defaults and malformed reshape dimensions', function () {
  const registryLookup = vi.spyOn(blockRegistry, 'get').mockReturnValue(undefined)
  try {
    const model = importMDL(`Model {
      Name "FallbackDefaults"
      System {
        Name "FallbackDefaults"
        Block { BlockType Mux Name "MuxBad" Inputs "bad" }
        Block { BlockType Demux Name "DemuxBad" Outputs "bad" }
        Block { BlockType Logic Name "LogicBad" Inputs "bad" }
        Block { BlockType Concatenate Name "ConcatBad" NumInputs "bad" }
        Block { BlockType Reshape Name "ArrayPrefix" OutputDimensions [3x] }
        Block { BlockType Reshape Name "ArrayInvalid" OutputDimensions [bad] }
        Block { BlockType Reshape Name "JsonObject" OutputDimensions "{}" }
        Block { BlockType Reshape Name "NoDigits" OutputDimensions "no dimensions" }
      }
    }`)
    const byName = (name: string) => model.blocks.find(block => block.name === name)

    expect(byName('MuxBad')?.inputPorts).toHaveLength(4)
    expect(byName('DemuxBad')?.outputPorts).toHaveLength(4)
    expect(byName('LogicBad')?.inputPorts).toHaveLength(2)
    expect(byName('ConcatBad')?.inputPorts).toHaveLength(2)
    expect(byName('ArrayPrefix')?.outputPorts[0].dimensions).toEqual([3])
    expect(byName('ArrayInvalid')?.outputPorts[0].dimensions).toEqual([1])
    expect(byName('JsonObject')?.outputPorts[0].dimensions).toEqual([1])
    expect(byName('NoDigits')?.outputPorts[0].dimensions).toEqual([1])
  } finally {
    registryLookup.mockRestore()
  }
})

it('covers deep parser logging arms and unnamed library defaults', function () {
  const dollar = String.fromCharCode(36)
  const model = importMDL(`Library {
    System {
      Block { BlockType Constant Name "MixedPosition" Position [1 nope] Value 1 }
      Block { BlockType Constant Name "BadPosition" Position "nonsense" Value 2 }
    }
    Block { BlockType Constant Name "Direct" Value 3 }
    BlockDiagram {
      System { Name "Secondary" }
      Block { BlockType Constant Name "Merged" Value 4 }
    }
    BlockDiagram { }
    Outer {
      Inner {
        Deeper {
          ${dollar}Scalar 1
          ${dollar}Object { Value 2 }
          Simulink.SolverCC { Value 3 }
          BlockDiagram { }
          Ordinary { Value 4 }
          Empty
        }
      }
    }
  }`)

  expect(model.metadata.name).toBe('Imported Library')
  expect(model.blocks.map(block => block.name)).toEqual(['MixedPosition', 'BadPosition'])
  expect(model.blocks[0].position).toEqual({ x: 1, y: 100 })
  expect(model.blocks[1].position).toEqual({ x: 100, y: 100 })
})

it('preserves unrelated registry entries', function () {
  clearLibraryRegistry()
  const first = {
    id: 'one', type: 'subsystem', name: 'One', position: { x: 0, y: 0 },
    parameters: {}, inputPorts: [], outputPorts: [],
  } as BlockInstance
  const second = { ...first, id: 'two', name: 'Two' }
  registerLibraryBlocks('First_2009b', [first])
  registerLibraryBlocks('Second', [second])
  unregisterLibraryBlocks('First_2009b')
  expect(getRegisteredBlock('First/One')).toBeUndefined()
  expect(getRegisteredBlock('Second/Two')?.name).toBe('Two')
  clearLibraryRegistry()
})

it('keeps disconnected dimension graphs stable', function () {
  const block = {
    id: 'constant', type: 'constant', name: 'Constant', position: { x: 0, y: 0 },
    parameters: { value: '[]' }, inputPorts: [],
    outputPorts: [{ id: 'constant-out', name: 'out', dataType: 'double', dimensions: [9] }],
  } as BlockInstance
  propagateDimensions([block], [])
  expect(block.outputPorts[0].dimensions).toEqual([1])
})

it('handles zero and malformed subsystem ports plus destination-free branches', function () {
  const model = importMDL(`Model {
    Name "SystemFallbacks"
    Solver "unknown-solver"
    StartTime "bad"
    StopTime "bad"
    FixedStep 0
    System {
      Name "SystemFallbacks"
      Block { BlockType Constant Name "Source" Value 1 }
      Block { BlockType Gain Name "Target" Gain 2 }
      Block { BlockType SubSystem Name "ZeroArray" Ports [0, 0] }
      Block { BlockType SubSystem Name "ZeroText" Ports "[0, 0]" }
      Block { BlockType SubSystem Name "InvalidText" Ports "bad" }
      Block { BlockType Reference Name "NumericPorts" Ports 7 }
      Line {
        SrcBlock "Source"
        SrcPort "bad"
        Branch {
          Branch { DstBlock "Target" DstPort "bad" }
        }
      }
    }
    System { Name "SystemFallbacks/ZeroArray" }
  }`)
  const byName = (name: string) => model.blocks.find(block => block.name === name)

  expect(byName('ZeroArray')?.parameters).toMatchObject({ numInputs: 0, numOutputs: 0 })
  expect(byName('ZeroText')?.parameters).toMatchObject({ numInputs: 0, numOutputs: 0 })
  expect(byName('InvalidText')?.inputPorts).toHaveLength(0)
  expect(byName('NumericPorts')?.inputPorts).toHaveLength(1)
  expect(model.connections).toHaveLength(1)
  expect(model.simulationConfig).toMatchObject({ solver: 'rk4', startTime: 0, stopTime: 10, stepSize: 0.01 })
})

it('handles alternate reshape modes and invalid registered dynamic counts', function () {
  const model = importMDL(`Model {
    Name "DynamicDefaults"
    FixedStep "bad"
    System {
      Name "DynamicDefaults"
      Block { BlockType Reshape Name "Row" OutputDimensionality "Row vector" }
      Block { BlockType Reshape Name "OneD" OutputDimensionality "1-D array" }
      Block { BlockType Mux Name "MuxBad" Inputs "bad" }
      Block { BlockType Demux Name "DemuxBad" Outputs "bad" }
    }
  }`)
  const byName = function (name: string) {
    return model.blocks.find(function (block) { return block.name === name })
  }

  expect(byName('Row')?.outputPorts[0].dimensions).toEqual([1])
  expect(byName('OneD')?.outputPorts[0].dimensions).toEqual([-1])
  expect(byName('MuxBad')?.inputPorts).toHaveLength(2)
  expect(byName('DemuxBad')?.outputPorts).toHaveLength(2)
  expect(model.simulationConfig.stepSize).toBe(0.01)
})

it('recognizes alternate subsystem spelling and scans empty nested systems', function () {
  const library = `Library {
    Name "Alternate"
    System {
      Name "Alternate"
      Block { BlockType Subsystem Name "First" System { Name "Empty" } }
      Block { BlockType Subsystem Name "Second" }
    }
  }`

  expect(isMDLLibrary(library)).toBe(true)
  expect(analyzeLibraryDependencies(library)).toEqual({
    externalReferences: [],
    missingLibraries: [],
    availableLibraries: [],
  })
})

it('keeps malformed and cyclic dimension graphs stable', function () {
  function port(id: string, dimensions: number[] = [1]) {
    return { id, name: id, dataType: 'double' as const, dimensions }
  }
  function block(id: string, type: string): BlockInstance {
    return {
      id, type, name: id, position: { x: 0, y: 0 }, parameters: {},
      inputPorts: [], outputPorts: [port(`${id}-out`)],
    }
  }
  function propagateFrom(source: BlockInstance, extraConnections: Connection[] = []) {
    const sink = block(`${source.id}-sink`, 'outport')
    sink.inputPorts = [port(`${sink.id}-in`)]
    sink.outputPorts = []
    const connection: Connection = {
      id: `${source.id}-wire`,
      sourceBlockId: source.id,
      sourcePortId: source.outputPorts[0].id,
      targetBlockId: sink.id,
      targetPortId: sink.inputPorts[0].id,
    }
    propagateDimensions([source, sink], [...extraConnections, connection])
    return sink.inputPorts[0].dimensions
  }

  const noOutport = block('no-outport', 'subsystem')
  noOutport.children = []
  expect(propagateFrom(noOutport)).toEqual([1])

  const outportWithoutInput = block('outport-without-input-parent', 'subsystem')
  const emptyOutport = block('empty-outport', 'outport')
  emptyOutport.outputPorts = []
  outportWithoutInput.children = [emptyOutport]
  expect(propagateFrom(outportWithoutInput)).toEqual([1])

  const disconnected = block('disconnected-parent', 'subsystem')
  const disconnectedOutport = block('disconnected-outport', 'outport')
  disconnectedOutport.inputPorts = [port('disconnected-in')]
  disconnectedOutport.outputPorts = []
  disconnected.children = [disconnectedOutport]
  expect(propagateFrom(disconnected)).toEqual([1])

  const missingChild = block('missing-child-parent', 'subsystem')
  const missingChildOutport = block('missing-child-outport', 'outport')
  missingChildOutport.parameters = { portNumber: 1 }
  missingChildOutport.inputPorts = [port('missing-child-in')]
  missingChildOutport.outputPorts = []
  missingChild.children = [missingChildOutport]
  missingChild.childConnections = [{
    id: 'missing-child-wire',
    sourceBlockId: 'absent-child',
    sourcePortId: 'absent-output',
    targetBlockId: missingChildOutport.id,
    targetPortId: missingChildOutport.inputPorts[0].id,
  }]
  expect(propagateFrom(missingChild)).toEqual([1])

  const missingPort = block('missing-port-parent', 'subsystem')
  const existingChild = block('existing-child', 'gain')
  const missingPortOutport = block('missing-port-outport', 'outport')
  missingPortOutport.parameters = { portNumber: 1 }
  missingPortOutport.inputPorts = [port('missing-port-in')]
  missingPortOutport.outputPorts = []
  missingPort.children = [existingChild, missingPortOutport]
  missingPort.childConnections = [{
    id: 'missing-port-wire',
    sourceBlockId: existingChild.id,
    sourcePortId: 'absent-child-port',
    targetBlockId: missingPortOutport.id,
    targetPortId: missingPortOutport.inputPorts[0].id,
  }]
  expect(propagateFrom(missingPort)).toEqual([1])

  const cyclic = block('cyclic-parent', 'subsystem')
  const gain = block('cyclic-gain', 'gain')
  gain.inputPorts = [port('cyclic-gain-in')]
  const cyclicOutport = block('cyclic-outport', 'outport')
  cyclicOutport.parameters = { portNumber: 1 }
  cyclicOutport.inputPorts = [port('cyclic-outport-in')]
  cyclicOutport.outputPorts = []
  cyclic.children = [gain, cyclicOutport]
  cyclic.childConnections = [
    { id: 'cycle', sourceBlockId: gain.id, sourcePortId: gain.outputPorts[0].id, targetBlockId: gain.id, targetPortId: gain.inputPorts[0].id },
    { id: 'cycle-output', sourceBlockId: gain.id, sourcePortId: gain.outputPorts[0].id, targetBlockId: cyclicOutport.id, targetPortId: cyclicOutport.inputPorts[0].id },
  ]
  expect(propagateFrom(cyclic)).toEqual([1])

  const bareGain = block('bare-gain', 'gain')
  bareGain.inputPorts = [port('bare-gain-in')]
  expect(propagateFrom(bareGain)).toEqual([1])

  const missingSourceGain = block('missing-source-gain', 'gain')
  missingSourceGain.inputPorts = [port('missing-source-gain-in')]
  expect(propagateFrom(missingSourceGain, [{
    id: 'missing-source',
    sourceBlockId: 'absent-root',
    sourcePortId: 'absent-root-out',
    targetBlockId: missingSourceGain.id,
    targetPortId: missingSourceGain.inputPorts[0].id,
  }])).toEqual([1])

  const missingInherited = block('missing-inherited', 'reshape')
  missingInherited.inputPorts = [port('missing-inherited-in')]
  missingInherited.outputPorts[0].dimensions = [-1]
  propagateDimensions([missingInherited], [{
    id: 'missing-inherit-wire',
    sourceBlockId: 'absent-inherit-source',
    sourcePortId: 'absent-inherit-output',
    targetBlockId: missingInherited.id,
    targetPortId: missingInherited.inputPorts[0].id,
  }])
  expect(missingInherited.outputPorts[0].dimensions).toEqual([-1])

  const missingOutport = block('missing-root-outport', 'outport')
  missingOutport.inputPorts = [port('missing-root-outport-in')]
  missingOutport.outputPorts = []
  propagateDimensions([missingOutport], [{
    id: 'missing-root-output-wire',
    sourceBlockId: 'absent-output-source',
    sourcePortId: 'absent-output-port',
    targetBlockId: missingOutport.id,
    targetPortId: missingOutport.inputPorts[0].id,
  }])
  expect(missingOutport.inputPorts[0].dimensions).toEqual([1])

  const inherited = block('inherited', 'reshape')
  inherited.inputPorts = [port('inherited-in')]
  inherited.outputPorts[0].dimensions = [-1]
  const inheritedSource = block('inherited-source', 'gain')
  inheritedSource.outputPorts[0].dimensions = [-1]
  propagateDimensions([inheritedSource, inherited], [{
    id: 'inherit-wire',
    sourceBlockId: inheritedSource.id,
    sourcePortId: inheritedSource.outputPorts[0].id,
    targetBlockId: inherited.id,
    targetPortId: inherited.inputPorts[0].id,
  }])
  expect(inherited.outputPorts[0].dimensions).toEqual([-1])

  const malformedSubsystem = block('malformed-subsystem', 'subsystem')
  const unnumberedOutport = block('unnumbered-outport', 'outport')
  unnumberedOutport.inputPorts = []
  unnumberedOutport.outputPorts = []
  malformedSubsystem.children = [unnumberedOutport]
  malformedSubsystem.outputPorts = []
  propagateDimensions([malformedSubsystem], [])
  expect(malformedSubsystem.outputPorts).toEqual([])
})
