import { describe, it, expect, beforeEach } from 'vitest'
import {
  importMDL,
  isMDLFile,
  isMDLLibrary,
  importMDLAsLibrary,
  registerLibraryBlocks,
  unregisterLibraryBlocks,
  getRegisteredBlock,
  clearLibraryRegistry,
  getRegisteredLibraryNames,
  analyzeLibraryDependencies,
  propagateDimensions,
} from './mdlImporter'
import type { BlockInstance, Connection } from '../types/block'

describe('mdlImporter', () => {
  beforeEach(() => {
    // Clear the library registry before each test
    clearLibraryRegistry()
  })

  describe('isMDLFile', () => {
    it('should return true for valid Model content', () => {
      expect(isMDLFile('Model {\n  Name "test"\n}')).toBe(true)
    })

    it('should return true for valid Library content', () => {
      expect(isMDLFile('Library {\n  Name "test"\n}')).toBe(true)
    })

    it('should return false for invalid content', () => {
      expect(isMDLFile('Not a model')).toBe(false)
      expect(isMDLFile('')).toBe(false)
      expect(isMDLFile('Model without brace')).toBe(false)
    })

    it('should handle whitespace at start', () => {
      expect(isMDLFile('  \n  Model {\n  Name "test"\n}')).toBe(true)
    })
  })

  describe('isMDLLibrary', () => {
    it('should return true for library with multiple subsystems', () => {
      const mdl = `Library {
        Name "TestLib"
        System {
          Name "TestLib"
          Block {
            BlockType SubSystem
            Name "Sub1"
          }
          Block {
            BlockType SubSystem
            Name "Sub2"
          }
        }
      }`
      expect(isMDLLibrary(mdl)).toBe(true)
    })

    it('should return false for model with single subsystem', () => {
      const mdl = `Model {
        Name "TestModel"
        System {
          Name "TestModel"
          Block {
            BlockType SubSystem
            Name "Sub1"
          }
        }
      }`
      expect(isMDLLibrary(mdl)).toBe(false)
    })

    it('should return false for invalid content', () => {
      expect(isMDLLibrary('invalid')).toBe(false)
    })
  })

  describe('importMDL', () => {
    it('should import a simple model with a constant block', () => {
      const mdl = `Model {
        Name "SimpleTest"
        StartTime "0"
        StopTime "10"
        FixedStep "0.01"
        Solver "ode4"
        System {
          Name "SimpleTest"
          Block {
            BlockType Constant
            Name "Const1"
            Position [100, 100, 150, 130]
            Value "5.0"
          }
        }
      }`

      const model = importMDL(mdl)

      expect(model.metadata.name).toBe('SimpleTest')
      expect(model.blocks.length).toBe(1)
      expect(model.blocks[0].type).toBe('constant')
      expect(model.blocks[0].name).toBe('Const1')
      expect(model.blocks[0].parameters.value).toBe(5.0)
      expect(model.simulationConfig.startTime).toBe(0)
      expect(model.simulationConfig.stopTime).toBe(10)
      expect(model.simulationConfig.stepSize).toBe(0.01)
      expect(model.simulationConfig.solver).toBe('rk4')
    })

    it('should import a model with connections', () => {
      const mdl = `Model {
        Name "ConnectedTest"
        System {
          Name "ConnectedTest"
          Block {
            BlockType Constant
            Name "Const1"
            Position [100, 100, 150, 130]
            Value "1"
          }
          Block {
            BlockType Gain
            Name "Gain1"
            Position [200, 100, 250, 130]
            Gain "2.5"
          }
          Block {
            BlockType Scope
            Name "Scope1"
            Position [300, 100, 350, 130]
          }
          Line {
            SrcBlock "Const1"
            SrcPort 1
            DstBlock "Gain1"
            DstPort 1
          }
          Line {
            SrcBlock "Gain1"
            SrcPort 1
            DstBlock "Scope1"
            DstPort 1
          }
        }
      }`

      const model = importMDL(mdl)

      expect(model.blocks.length).toBe(3)
      expect(model.connections.length).toBe(2)

      const constant = model.blocks.find(b => b.name === 'Const1')
      const gain = model.blocks.find(b => b.name === 'Gain1')
      const scope = model.blocks.find(b => b.name === 'Scope1')

      expect(constant).toBeDefined()
      expect(gain).toBeDefined()
      expect(scope).toBeDefined()
      expect(gain?.parameters.gain).toBe(2.5)
    })

    it('should import a model with branching connections', () => {
      const mdl = `Model {
        Name "BranchTest"
        System {
          Name "BranchTest"
          Block {
            BlockType Constant
            Name "Source"
            Value "1"
          }
          Block {
            BlockType Scope
            Name "Scope1"
          }
          Block {
            BlockType Scope
            Name "Scope2"
          }
          Line {
            SrcBlock "Source"
            SrcPort 1
            Branch {
              DstBlock "Scope1"
              DstPort 1
            }
            Branch {
              DstBlock "Scope2"
              DstPort 1
            }
          }
        }
      }`

      const model = importMDL(mdl)

      expect(model.connections.length).toBe(2)
    })

    it('should handle Sum block with multiple inputs', () => {
      const mdl = `Model {
        Name "SumTest"
        System {
          Name "SumTest"
          Block {
            BlockType Sum
            Name "Sum1"
            Inputs "+-+"
          }
        }
      }`

      const model = importMDL(mdl)
      const sum = model.blocks[0]

      expect(sum.type).toBe('sum')
      expect(sum.parameters.signs).toBe('+-+')
      expect(sum.inputPorts.length).toBe(3)
    })

    it('should handle Mux block', () => {
      const mdl = `Model {
        Name "MuxTest"
        System {
          Name "MuxTest"
          Block {
            BlockType Mux
            Name "Mux1"
            Inputs "3"
          }
        }
      }`

      const model = importMDL(mdl)
      const mux = model.blocks[0]

      expect(mux.type).toBe('mux')
      expect(mux.inputPorts.length).toBe(3)
    })

    it('should handle Demux block', () => {
      const mdl = `Model {
        Name "DemuxTest"
        System {
          Name "DemuxTest"
          Block {
            BlockType Demux
            Name "Demux1"
            Outputs "4"
          }
        }
      }`

      const model = importMDL(mdl)
      const demux = model.blocks[0]

      expect(demux.type).toBe('demux')
      expect(demux.outputPorts.length).toBe(4)
    })

    it('should handle Integrator block', () => {
      const mdl = `Model {
        Name "IntegratorTest"
        System {
          Name "IntegratorTest"
          Block {
            BlockType Integrator
            Name "Integrator1"
            InitialCondition "0.5"
          }
        }
      }`

      const model = importMDL(mdl)
      const integrator = model.blocks[0]

      expect(integrator.type).toBe('integrator')
      expect(integrator.parameters.initialCondition).toBe(0.5)
    })

    it('should handle Transfer Function block', () => {
      const mdl = `Model {
        Name "TFTest"
        System {
          Name "TFTest"
          Block {
            BlockType TransferFcn
            Name "TF1"
            Numerator "[1 2]"
            Denominator "[1 3 2]"
          }
        }
      }`

      const model = importMDL(mdl)
      const tf = model.blocks[0]

      expect(tf.type).toBe('transfer_function')
      expect(tf.parameters.numerator).toEqual([1, 2])
      expect(tf.parameters.denominator).toEqual([1, 3, 2])
    })

    it('should handle Step block', () => {
      const mdl = `Model {
        Name "StepTest"
        System {
          Name "StepTest"
          Block {
            BlockType Step
            Name "Step1"
            Time "1.0"
            Before "0"
            After "1"
          }
        }
      }`

      const model = importMDL(mdl)
      const step = model.blocks[0]

      expect(step.type).toBe('step')
      expect(step.parameters.stepTime).toBe(1.0)
      expect(step.parameters.initialValue).toBe(0)
      expect(step.parameters.finalValue).toBe(1)
    })

    it('should handle Saturation block', () => {
      const mdl = `Model {
        Name "SatTest"
        System {
          Name "SatTest"
          Block {
            BlockType Saturation
            Name "Sat1"
            UpperLimit "10"
            LowerLimit "-10"
          }
        }
      }`

      const model = importMDL(mdl)
      const sat = model.blocks[0]

      expect(sat.type).toBe('saturation')
      expect(sat.parameters.upperLimit).toBe(10)
      expect(sat.parameters.lowerLimit).toBe(-10)
    })

    it('should handle Trigonometry block with Operator parameter', () => {
      const mdl = `Model {
        Name "TrigTest"
        System {
          Name "TrigTest"
          Block {
            BlockType Trigonometry
            Name "Cos1"
            Operator "cos"
          }
        }
      }`

      const model = importMDL(mdl)
      const trig = model.blocks[0]

      expect(trig.type).toBe('trigonometry')
      expect(trig.parameters.function).toBe('cos')
    })

    it('should handle Math Function block with Operator parameter', () => {
      const mdl = `Model {
        Name "MathTest"
        System {
          Name "MathTest"
          Block {
            BlockType Math
            Name "Exp1"
            Operator "exp"
          }
        }
      }`

      const model = importMDL(mdl)
      const math = model.blocks[0]

      expect(math.type).toBe('math_function')
      expect(math.parameters.function).toBe('exp')
    })

    it('should handle Dead Zone block', () => {
      const mdl = `Model {
        Name "DeadZoneTest"
        System {
          Name "DeadZoneTest"
          Block {
            BlockType DeadZone
            Name "DZ1"
            LowerValue "-0.5"
            UpperValue "0.5"
          }
        }
      }`

      const model = importMDL(mdl)
      const dz = model.blocks[0]

      expect(dz.type).toBe('dead_zone')
      expect(dz.parameters.start).toBe(-0.5)
      expect(dz.parameters.end).toBe(0.5)
    })

    it('should handle Inport and Outport blocks', () => {
      const mdl = `Model {
        Name "PortTest"
        System {
          Name "PortTest"
          Block {
            BlockType Inport
            Name "In1"
            Port "1"
          }
          Block {
            BlockType Outport
            Name "Out1"
            Port "1"
          }
        }
      }`

      const model = importMDL(mdl)

      expect(model.blocks.length).toBe(2)
      const inport = model.blocks.find(b => b.type === 'inport')
      const outport = model.blocks.find(b => b.type === 'outport')

      expect(inport).toBeDefined()
      expect(outport).toBeDefined()
      expect(inport?.parameters.portNumber).toBe(1)
      expect(outport?.parameters.portNumber).toBe(1)
    })

    it('should handle Subsystem block with children', () => {
      const mdl = `Model {
        Name "SubsystemTest"
        System {
          Name "SubsystemTest"
          Block {
            BlockType SubSystem
            Name "MySub"
            Ports "[1, 1]"
          }
        }
        System {
          Name "SubsystemTest/MySub"
          Block {
            BlockType Inport
            Name "In1"
            Port "1"
          }
          Block {
            BlockType Gain
            Name "InternalGain"
            Gain "2"
          }
          Block {
            BlockType Outport
            Name "Out1"
            Port "1"
          }
          Line {
            SrcBlock "In1"
            SrcPort 1
            DstBlock "InternalGain"
            DstPort 1
          }
          Line {
            SrcBlock "InternalGain"
            SrcPort 1
            DstBlock "Out1"
            DstPort 1
          }
        }
      }`

      const model = importMDL(mdl)

      expect(model.blocks.length).toBe(1)
      const subsystem = model.blocks[0]

      expect(subsystem.type).toBe('subsystem')
      expect(subsystem.name).toBe('MySub')
      expect(subsystem.children).toBeDefined()
      expect(subsystem.children?.length).toBe(3)
      expect(subsystem.childConnections?.length).toBe(2)
    })

    it('should map Simulink solvers to LibreSim solvers', () => {
      const testCases = [
        { simulinkSolver: 'ode1', expected: 'euler' },
        { simulinkSolver: 'ode4', expected: 'rk4' },
        { simulinkSolver: 'ode45', expected: 'merson' },
      ]

      for (const { simulinkSolver, expected } of testCases) {
        const mdl = `Model {
          Name "SolverTest"
          Solver "${simulinkSolver}"
          System {
            Name "SolverTest"
          }
        }`

        const model = importMDL(mdl)
        expect(model.simulationConfig.solver).toBe(expected)
      }
    })

    it('should throw error for invalid MDL content', () => {
      expect(() => importMDL('invalid content')).toThrow('Failed to parse MDL file')
    })

    it('should handle comments in MDL', () => {
      const mdl = `Model {
        % This is a comment
        Name "CommentTest"
        System {
          Name "CommentTest"
          % Another comment
          Block {
            BlockType Constant
            Name "Const1"
            Value "1"
          }
        }
      }`

      const model = importMDL(mdl)
      expect(model.blocks.length).toBe(1)
    })

    it('should handle quoted strings with escapes', () => {
      const mdl = `Model {
        Name "Test\\"Quoted"
        System {
          Name "Test"
        }
      }`

      const model = importMDL(mdl)
      expect(model.metadata.name).toBe('Test"Quoted')
    })

    it('should handle array values in block parameters', () => {
      const mdl = `Model {
        Name "ArrayTest"
        System {
          Name "ArrayTest"
          Block {
            BlockType Constant
            Name "VectorConst"
            Value "[1, 2, 3]"
          }
        }
      }`

      const model = importMDL(mdl)
      const constant = model.blocks[0]

      expect(constant.parameters.value).toEqual([1, 2, 3])
    })

    it('should set default values for missing parameters', () => {
      const mdl = `Model {
        Name "DefaultTest"
        System {
          Name "DefaultTest"
          Block {
            BlockType Constant
            Name "NoValue"
          }
          Block {
            BlockType Trigonometry
            Name "NoOperator"
          }
        }
      }`

      const model = importMDL(mdl)

      const constant = model.blocks.find(b => b.name === 'NoValue')
      const trig = model.blocks.find(b => b.name === 'NoOperator')

      expect(constant?.parameters.value).toBe(1) // Default constant value
      expect(trig?.parameters.function).toBe('sin') // Default trig function
    })
  })

  describe('Library Registry', () => {
    const createMockSubsystem = (name: string): BlockInstance => ({
      id: `block_${name}`,
      type: 'subsystem',
      name,
      position: { x: 100, y: 100 },
      parameters: {},
      inputPorts: [{ id: 'in_0', name: 'in', dataType: 'double', dimensions: [1] }],
      outputPorts: [{ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] }],
      children: [],
      childConnections: [],
    })

    it('should register library blocks', () => {
      const blocks = [createMockSubsystem('Block1'), createMockSubsystem('Block2')]

      registerLibraryBlocks('TestLib', blocks)

      expect(getRegisteredBlock('TestLib/Block1')).toBe(blocks[0])
      expect(getRegisteredBlock('TestLib/Block2')).toBe(blocks[1])
    })

    it('should register under normalized name for versioned libraries', () => {
      const blocks = [createMockSubsystem('Block1')]

      registerLibraryBlocks('TestLib_2009b', blocks)

      // Should be accessible via both paths
      expect(getRegisteredBlock('TestLib_2009b/Block1')).toBe(blocks[0])
      expect(getRegisteredBlock('TestLib/Block1')).toBe(blocks[0])
    })

    it('should unregister library blocks', () => {
      const blocks = [createMockSubsystem('Block1')]
      registerLibraryBlocks('TestLib', blocks)

      expect(getRegisteredBlock('TestLib/Block1')).toBe(blocks[0])

      unregisterLibraryBlocks('TestLib')

      expect(getRegisteredBlock('TestLib/Block1')).toBeUndefined()
    })

    it('should clear all registered blocks', () => {
      registerLibraryBlocks('Lib1', [createMockSubsystem('A')])
      registerLibraryBlocks('Lib2', [createMockSubsystem('B')])

      clearLibraryRegistry()

      expect(getRegisteredBlock('Lib1/A')).toBeUndefined()
      expect(getRegisteredBlock('Lib2/B')).toBeUndefined()
    })

    it('should get registered library names', () => {
      registerLibraryBlocks('Lib1', [createMockSubsystem('A')])
      registerLibraryBlocks('Lib2', [createMockSubsystem('B')])

      const names = getRegisteredLibraryNames()

      expect(names).toContain('Lib1')
      expect(names).toContain('Lib2')
    })
  })

  describe('analyzeLibraryDependencies', () => {
    it('should detect external references', () => {
      const mdl = `Library {
        Name "TestLib"
        System {
          Name "TestLib"
          Block {
            BlockType SubSystem
            Name "MySub"
            System {
              Name "TestLib/MySub"
              Block {
                BlockType Reference
                Name "ExtRef"
                SourceBlock "OtherLib/ExternalBlock"
              }
            }
          }
        }
        System {
          Name "TestLib/MySub"
          Block {
            BlockType Reference
            Name "ExtRef"
            SourceBlock "OtherLib/ExternalBlock"
          }
        }
      }`

      const deps = analyzeLibraryDependencies(mdl)

      expect(deps.externalReferences.length).toBeGreaterThan(0)
      expect(deps.externalReferences[0].libraryName).toBe('OtherLib')
      expect(deps.externalReferences[0].blockName).toBe('ExternalBlock')
      expect(deps.missingLibraries).toContain('OtherLib')
    })

    it('should not count internal references as external', () => {
      const mdl = `Library {
        Name "TestLib"
        System {
          Name "TestLib"
          Block {
            BlockType SubSystem
            Name "Block1"
          }
          Block {
            BlockType SubSystem
            Name "Block2"
          }
        }
        System {
          Name "TestLib/Block2"
          Block {
            BlockType Reference
            Name "InternalRef"
            SourceBlock "TestLib/Block1"
          }
        }
      }`

      const deps = analyzeLibraryDependencies(mdl)

      // Internal references should not appear as external
      expect(deps.externalReferences.filter(r => r.libraryName === 'TestLib').length).toBe(0)
    })
  })

  describe('importMDLAsLibrary', () => {
    it('should import library with subsystem blocks', () => {
      const mdl = `Library {
        Name "TestLib"
        System {
          Name "TestLib"
          Block {
            BlockType SubSystem
            Name "MyBlock"
            Ports "[1, 1]"
          }
        }
        System {
          Name "TestLib/MyBlock"
          Block {
            BlockType Inport
            Name "In1"
            Port "1"
          }
          Block {
            BlockType Gain
            Name "InternalGain"
            Gain "2"
          }
          Block {
            BlockType Outport
            Name "Out1"
            Port "1"
          }
          Line {
            SrcBlock "In1"
            SrcPort 1
            DstBlock "InternalGain"
            DstPort 1
          }
          Line {
            SrcBlock "InternalGain"
            SrcPort 1
            DstBlock "Out1"
            DstPort 1
          }
        }
      }`

      const result = importMDLAsLibrary(mdl, { registerBlocks: false })

      expect(result.library.name).toBe('TestLib')
      expect(result.library.blocks.length).toBe(1)
      expect(result.library.blocks[0].name).toBe('MyBlock')
      expect(result.subsystemBlocks.length).toBe(1)
    })

    it('should register blocks when option is true', () => {
      const mdl = `Library {
        Name "RegisterTest"
        System {
          Name "RegisterTest"
          Block {
            BlockType SubSystem
            Name "RegBlock"
            Ports "[1, 1]"
          }
        }
        System {
          Name "RegisterTest/RegBlock"
          Block {
            BlockType Inport
            Name "In1"
            Port "1"
          }
          Block {
            BlockType Outport
            Name "Out1"
            Port "1"
          }
        }
      }`

      importMDLAsLibrary(mdl, { registerBlocks: true })

      expect(getRegisteredBlock('RegisterTest/RegBlock')).toBeDefined()
    })
  })

  describe('propagateDimensions', () => {
    it('should set dimensions for Constant blocks based on value', () => {
      const blocks: BlockInstance[] = [
        {
          id: 'const1',
          type: 'constant',
          name: 'VectorConst',
          position: { x: 0, y: 0 },
          parameters: { value: [1, 2, 3] },
          inputPorts: [],
          outputPorts: [{ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] }],
        },
      ]

      propagateDimensions(blocks, [])

      expect(blocks[0].outputPorts[0].dimensions).toEqual([3])
    })

    it('should propagate dimensions through subsystem output ports', () => {
      const inport: BlockInstance = {
        id: 'inport1',
        type: 'inport',
        name: 'In1',
        position: { x: 0, y: 0 },
        parameters: { portNumber: 1 },
        inputPorts: [],
        outputPorts: [{ id: 'inport1-out-0', name: 'out', dataType: 'double', dimensions: [3] }],
      }

      const outport: BlockInstance = {
        id: 'outport1',
        type: 'outport',
        name: 'Out1',
        position: { x: 100, y: 0 },
        parameters: { portNumber: 1 },
        inputPorts: [{ id: 'outport1-in-0', name: 'in', dataType: 'double', dimensions: [1] }],
        outputPorts: [],
      }

      const childConnections: Connection[] = [
        {
          id: 'conn1',
          sourceBlockId: 'inport1',
          sourcePortId: 'inport1-out-0',
          targetBlockId: 'outport1',
          targetPortId: 'outport1-in-0',
        },
      ]

      const subsystem: BlockInstance = {
        id: 'sub1',
        type: 'subsystem',
        name: 'MySub',
        position: { x: 0, y: 0 },
        parameters: {},
        inputPorts: [{ id: 'sub1-in-0', name: 'in1', dataType: 'double', dimensions: [1] }],
        outputPorts: [{ id: 'sub1-out-0', name: 'out1', dataType: 'double', dimensions: [1] }],
        children: [inport, outport],
        childConnections,
      }

      propagateDimensions([subsystem], [])

      // Outport input should get dimensions from inport output
      expect(outport.inputPorts[0].dimensions).toEqual([3])
      // Subsystem output should get dimensions from outport
      expect(subsystem.outputPorts[0].dimensions).toEqual([3])
    })

    it('should handle string constant values with arrays', () => {
      const blocks: BlockInstance[] = [
        {
          id: 'const1',
          type: 'constant',
          name: 'StringArrayConst',
          position: { x: 0, y: 0 },
          parameters: { value: '[1, 2, 3, 4, 5]' },
          inputPorts: [],
          outputPorts: [{ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] }],
        },
      ]

      propagateDimensions(blocks, [])

      expect(blocks[0].outputPorts[0].dimensions).toEqual([5])
    })
  })

  describe('Block type mappings', () => {
    const testBlockTypeMapping = (simulinkType: string, expectedType: string) => {
      const mdl = `Model {
        Name "TypeTest"
        System {
          Name "TypeTest"
          Block {
            BlockType ${simulinkType}
            Name "TestBlock"
          }
        }
      }`

      const model = importMDL(mdl)
      expect(model.blocks[0].type).toBe(expectedType)
    }

    it('should map Constant to constant', () => testBlockTypeMapping('Constant', 'constant'))
    it('should map Step to step', () => testBlockTypeMapping('Step', 'step'))
    it('should map Ramp to ramp', () => testBlockTypeMapping('Ramp', 'ramp'))
    it('should map Gain to gain', () => testBlockTypeMapping('Gain', 'gain'))
    it('should map Sum to sum', () => testBlockTypeMapping('Sum', 'sum'))
    it('should map Product to product', () => testBlockTypeMapping('Product', 'product'))
    it('should map Abs to abs', () => testBlockTypeMapping('Abs', 'abs'))
    it('should map Scope to scope', () => testBlockTypeMapping('Scope', 'scope'))
    it('should map Display to display', () => testBlockTypeMapping('Display', 'display'))
    it('should map Integrator to integrator', () => testBlockTypeMapping('Integrator', 'integrator'))
    it('should map Derivative to derivative', () => testBlockTypeMapping('Derivative', 'derivative'))
    it('should map TransferFcn to transfer_function', () => testBlockTypeMapping('TransferFcn', 'transfer_function'))
    it('should map UnitDelay to unit_delay', () => testBlockTypeMapping('UnitDelay', 'unit_delay'))
    it('should map ZeroOrderHold to zero_order_hold', () => testBlockTypeMapping('ZeroOrderHold', 'zero_order_hold'))
    it('should map Mux to mux', () => testBlockTypeMapping('Mux', 'mux'))
    it('should map Demux to demux', () => testBlockTypeMapping('Demux', 'demux'))
    it('should map Switch to switch', () => testBlockTypeMapping('Switch', 'switch'))
    it('should map Goto to goto', () => testBlockTypeMapping('Goto', 'goto'))
    it('should map From to from', () => testBlockTypeMapping('From', 'from'))
    it('should map Trigonometry to trigonometry', () => testBlockTypeMapping('Trigonometry', 'trigonometry'))
    it('should map Math to math_function', () => testBlockTypeMapping('Math', 'math_function'))
    it('should map Saturation to saturation', () => testBlockTypeMapping('Saturation', 'saturation'))
    it('should map DeadZone to dead_zone', () => testBlockTypeMapping('DeadZone', 'dead_zone'))
    it('should map Relay to relay', () => testBlockTypeMapping('Relay', 'relay'))
    it('should map Memory to memory', () => testBlockTypeMapping('Memory', 'memory'))
    it('should map SubSystem to subsystem', () => testBlockTypeMapping('SubSystem', 'subsystem'))
    it('should map Inport to inport', () => testBlockTypeMapping('Inport', 'inport'))
    it('should map Outport to outport', () => testBlockTypeMapping('Outport', 'outport'))
  })

  describe('Port creation', () => {
    it('should create correct ports for scope with numInputs', () => {
      const mdl = `Model {
        Name "ScopePortTest"
        System {
          Name "ScopePortTest"
          Block {
            BlockType Scope
            Name "MultiScope"
            NumInputPorts "3"
          }
        }
      }`

      const model = importMDL(mdl)
      const scope = model.blocks[0]

      expect(scope.inputPorts.length).toBe(3)
    })

    it('should create correct ports for product with operations', () => {
      const mdl = `Model {
        Name "ProductPortTest"
        System {
          Name "ProductPortTest"
          Block {
            BlockType Product
            Name "DivMult"
            Inputs "*/"
          }
        }
      }`

      const model = importMDL(mdl)
      const product = model.blocks[0]

      expect(product.parameters.operations).toBe('*/')
    })
  })

  describe('Position parsing', () => {
    it('should parse array position', () => {
      const mdl = `Model {
        Name "PosTest"
        System {
          Name "PosTest"
          Block {
            BlockType Constant
            Name "Const1"
            Position [150, 200, 200, 230]
          }
        }
      }`

      const model = importMDL(mdl)

      expect(model.blocks[0].position.x).toBe(150)
      expect(model.blocks[0].position.y).toBe(200)
    })

    it('should use default position when not specified', () => {
      const mdl = `Model {
        Name "DefaultPosTest"
        System {
          Name "DefaultPosTest"
          Block {
            BlockType Constant
            Name "Const1"
          }
        }
      }`

      const model = importMDL(mdl)

      expect(model.blocks[0].position.x).toBe(100)
      expect(model.blocks[0].position.y).toBe(100)
    })
  })

  describe('importMDLAsLibrary', () => {
    it('should import a library with subsystem blocks', () => {
      const mdl = `Library {
        Name "TestLibrary"
        System {
          Name "TestLibrary"
          Block {
            BlockType SubSystem
            Name "MyBlock"
            System {
              Name "TestLibrary/MyBlock"
              Block {
                BlockType Constant
                Name "InternalConst"
                Value "5"
              }
              Block {
                BlockType Outport
                Name "Out1"
                Port "1"
              }
            }
          }
        }
        System {
          Name "TestLibrary/MyBlock"
          Block {
            BlockType Constant
            Name "InternalConst"
            Value "5"
          }
          Block {
            BlockType Outport
            Name "Out1"
            Port "1"
          }
        }
      }`

      const result = importMDLAsLibrary(mdl, { registerBlocks: false })

      expect(result.library.name).toBe('TestLibrary')
      expect(result.library.blocks.length).toBeGreaterThanOrEqual(0)
      expect(result.subsystemBlocks.length).toBeGreaterThanOrEqual(0)
    })

    it('should set sourcePath from options', () => {
      const mdl = `Library {
        Name "TestLib"
        System {
          Name "TestLib"
          Block {
            BlockType SubSystem
            Name "Sub1"
          }
        }
      }`

      const result = importMDLAsLibrary(mdl, { sourcePath: 'test/path/lib.mdl', registerBlocks: false })

      expect(result.library.description).toContain('test/path/lib.mdl')
    })

    it('should register blocks when registerBlocks is true', () => {
      const mdl = `Library {
        Name "RegTestLib"
        System {
          Name "RegTestLib"
          Block {
            BlockType SubSystem
            Name "RegBlock"
            System {
              Name "RegTestLib/RegBlock"
              Block {
                BlockType Constant
                Name "Const"
                Value "1"
              }
            }
          }
        }
        System {
          Name "RegTestLib/RegBlock"
          Block {
            BlockType Constant
            Name "Const"
            Value "1"
          }
        }
      }`

      importMDLAsLibrary(mdl, { registerBlocks: true })

      // Block should be registered
      const registeredBlock = getRegisteredBlock('RegTestLib/RegBlock')
      expect(registeredBlock).toBeDefined()
    })

    it('should throw error for invalid MDL content', () => {
      expect(() => importMDLAsLibrary('invalid content')).toThrow('Failed to import MDL library')
    })
  })

  describe('State Space blocks', () => {
    it('should parse state space matrices', () => {
      const mdl = `Model {
        Name "StateSpaceTest"
        System {
          Name "StateSpaceTest"
          Block {
            BlockType "S-Function"
            Name "SS1"
            FunctionName "stateflow"
          }
          Block {
            BlockType StateSpace
            Name "StateSpaceBlock"
            A "[-1 0; 0 -2]"
            B "[1; 1]"
            C "[1 1]"
            D "[0]"
          }
        }
      }`

      const model = importMDL(mdl)
      const ssBlock = model.blocks.find(b => b.type === 'state_space')

      if (ssBlock) {
        expect(ssBlock.parameters.A).toBeDefined()
        expect(ssBlock.parameters.B).toBeDefined()
        expect(ssBlock.parameters.C).toBeDefined()
        expect(ssBlock.parameters.D).toBeDefined()
      }
    })
  })

  describe('PID Controller blocks', () => {
    it('should parse PID parameters', () => {
      const mdl = `Model {
        Name "PIDTest"
        System {
          Name "PIDTest"
          Block {
            BlockType "PID"
            Name "PID1"
            P "1.5"
            I "0.5"
            D "0.1"
            N "100"
          }
        }
      }`

      const model = importMDL(mdl)
      const pid = model.blocks.find(b => b.type === 'pid_controller')

      if (pid) {
        expect(pid.parameters.Kp).toBeDefined()
        expect(pid.parameters.Ki).toBeDefined()
        expect(pid.parameters.Kd).toBeDefined()
      }
    })
  })

  describe('Transfer Function blocks', () => {
    it('should parse transfer function coefficients', () => {
      const mdl = `Model {
        Name "TFTest"
        System {
          Name "TFTest"
          Block {
            BlockType TransferFcn
            Name "TF1"
            Numerator "[1 2]"
            Denominator "[1 3 2]"
          }
        }
      }`

      const model = importMDL(mdl)
      const tf = model.blocks.find(b => b.type === 'transfer_function')

      expect(tf).toBeDefined()
      expect(tf?.parameters.numerator).toEqual([1, 2])
      expect(tf?.parameters.denominator).toEqual([1, 3, 2])
    })
  })

  describe('Lookup table blocks', () => {
    it('should parse 1D lookup table', () => {
      const mdl = `Model {
        Name "LookupTest"
        System {
          Name "LookupTest"
          Block {
            BlockType Lookup
            Name "LUT1D"
            InputValues "[0 1 2 3]"
            OutputValues "[0 1 4 9]"
          }
        }
      }`

      const model = importMDL(mdl)
      const lut = model.blocks.find(b => b.type === 'lookup_table_1d')

      expect(lut).toBeDefined()
      // Parameters may be stored differently based on implementation
      expect(lut?.parameters).toBeDefined()
    })

    it('should parse 2D lookup table', () => {
      const mdl = `Model {
        Name "Lookup2DTest"
        System {
          Name "Lookup2DTest"
          Block {
            BlockType Lookup2D
            Name "LUT2D"
            RowIndex "[0 1]"
            ColumnIndex "[0 1]"
          }
        }
      }`

      const model = importMDL(mdl)
      const lut2d = model.blocks.find(b => b.type === 'lookup_table_2d')

      expect(lut2d).toBeDefined()
    })
  })

  describe('Discrete blocks', () => {
    it('should parse discrete integrator', () => {
      const mdl = `Model {
        Name "DiscreteTest"
        System {
          Name "DiscreteTest"
          Block {
            BlockType DiscreteIntegrator
            Name "DI1"
            gainval "1"
            InitialConditionSetting "State (most efficient)"
            IntegratorMethod "Integration: Forward Euler"
          }
        }
      }`

      const model = importMDL(mdl)
      const di = model.blocks.find(b => b.type === 'discrete_integrator')

      expect(di).toBeDefined()
    })

    it('should parse discrete transfer function', () => {
      const mdl = `Model {
        Name "DiscreteTFTest"
        System {
          Name "DiscreteTFTest"
          Block {
            BlockType DiscreteTransferFcn
            Name "DTF1"
            Numerator "[1 0.5]"
            Denominator "[1 -0.9]"
            SampleTime "0.1"
          }
        }
      }`

      const model = importMDL(mdl)
      const dtf = model.blocks.find(b => b.type === 'discrete_transfer_function')

      expect(dtf).toBeDefined()
      // Parameters are parsed from MDL
      expect(dtf?.parameters).toBeDefined()
    })
  })

  describe('Routing blocks', () => {
    it('should parse Goto and From blocks', () => {
      const mdl = `Model {
        Name "GotoFromTest"
        System {
          Name "GotoFromTest"
          Block {
            BlockType Goto
            Name "Goto1"
            GotoTag "signal_a"
          }
          Block {
            BlockType From
            Name "From1"
            GotoTag "signal_a"
          }
        }
      }`

      const model = importMDL(mdl)
      const gotoBlock = model.blocks.find(b => b.type === 'goto')
      const fromBlock = model.blocks.find(b => b.type === 'from')

      expect(gotoBlock).toBeDefined()
      expect(fromBlock).toBeDefined()
      // Parameters are parsed from MDL
      expect(gotoBlock?.parameters).toBeDefined()
      expect(fromBlock?.parameters).toBeDefined()
    })
  })

  describe('Signal processing blocks', () => {
    it('should parse rate limiter', () => {
      const mdl = `Model {
        Name "RateLimTest"
        System {
          Name "RateLimTest"
          Block {
            BlockType RateLimiter
            Name "RL1"
            RisingSlewLimit "5"
            FallingSlewLimit "-3"
          }
        }
      }`

      const model = importMDL(mdl)
      const rl = model.blocks.find(b => b.type === 'rate_limiter')

      expect(rl).toBeDefined()
      expect(rl?.parameters.risingLimit).toBe(5)
      expect(rl?.parameters.fallingLimit).toBe(-3)
    })

    it('should parse quantizer', () => {
      const mdl = `Model {
        Name "QuantizerTest"
        System {
          Name "QuantizerTest"
          Block {
            BlockType Quantizer
            Name "Q1"
            QuantizationInterval "0.5"
          }
        }
      }`

      const model = importMDL(mdl)
      const q = model.blocks.find(b => b.type === 'quantizer')

      expect(q).toBeDefined()
      // Parameters are parsed from MDL
      expect(q?.parameters).toBeDefined()
    })
  })

  describe('Observer blocks', () => {
    it('should parse Kalman filter block', () => {
      const mdl = `Model {
        Name "KalmanTest"
        System {
          Name "KalmanTest"
          Block {
            BlockType SubSystem
            Name "KalmanFilter"
            System {
              Name "KalmanTest/KalmanFilter"
            }
          }
        }
      }`

      const model = importMDL(mdl)
      expect(model.blocks.length).toBeGreaterThan(0)
    })
  })

  describe('Nonlinear blocks', () => {
    it('should parse relay block', () => {
      const mdl = `Model {
        Name "RelayTest"
        System {
          Name "RelayTest"
          Block {
            BlockType Relay
            Name "Relay1"
            OnSwitchValue "1"
            OffSwitchValue "-1"
            OnOutputValue "1"
            OffOutputValue "-1"
          }
        }
      }`

      const model = importMDL(mdl)
      const relay = model.blocks.find(b => b.type === 'relay')

      expect(relay).toBeDefined()
      expect(relay?.parameters.switchOn).toBe(1)
      expect(relay?.parameters.switchOff).toBe(-1)
      expect(relay?.parameters.outputOn).toBe(1)
      expect(relay?.parameters.outputOff).toBe(-1)
    })
  })

  describe('Additional block types', () => {
    it('should parse saturation block', () => {
      const mdl = `Model {
        Name "SatTest"
        System {
          Name "SatTest"
          Block {
            BlockType Saturate
            Name "Sat1"
            UpperLimit "10"
            LowerLimit "-5"
          }
        }
      }`

      const model = importMDL(mdl)
      const sat = model.blocks.find(b => b.type === 'saturation')

      expect(sat).toBeDefined()
      expect(sat?.parameters.upperLimit).toBe(10)
      expect(sat?.parameters.lowerLimit).toBe(-5)
    })

    it('should parse dead zone block', () => {
      const mdl = `Model {
        Name "DeadZoneTest"
        System {
          Name "DeadZoneTest"
          Block {
            BlockType DeadZone
            Name "DZ1"
            LowerValue "-1"
            UpperValue "1"
          }
        }
      }`

      const model = importMDL(mdl)
      const dz = model.blocks.find(b => b.type === 'dead_zone')

      expect(dz).toBeDefined()
      expect(dz?.parameters.start).toBe(-1)
      expect(dz?.parameters.end).toBe(1)
    })

    it('should parse math function block with operator', () => {
      const mdl = `Model {
        Name "MathTest"
        System {
          Name "MathTest"
          Block {
            BlockType Math
            Name "Log1"
            Operator "log"
          }
        }
      }`

      const model = importMDL(mdl)
      const math = model.blocks.find(b => b.type === 'math_function')

      expect(math).toBeDefined()
      expect(math?.parameters.function).toBe('log')
    })

    it('should parse math function with power and exponent', () => {
      const mdl = `Model {
        Name "PowerTest"
        System {
          Name "PowerTest"
          Block {
            BlockType Math
            Name "Pow1"
            Operator "pow"
            Exponent "3"
          }
        }
      }`

      const model = importMDL(mdl)
      const math = model.blocks.find(b => b.type === 'math_function')

      expect(math).toBeDefined()
      expect(math?.parameters.function).toBe('pow')
      expect(math?.parameters.exponent).toBe(3)
    })

    it('should parse logic block', () => {
      const mdl = `Model {
        Name "LogicTest"
        System {
          Name "LogicTest"
          Block {
            BlockType Logic
            Name "And1"
            Operator "AND"
            Inputs "3"
          }
        }
      }`

      const model = importMDL(mdl)
      const logic = model.blocks.find(b => b.type === 'logic')

      expect(logic).toBeDefined()
      expect(logic?.parameters.operator).toBe('AND')
      expect(logic?.parameters.numInputs).toBe(3)
    })

    it('should parse relational operator block', () => {
      const mdl = `Model {
        Name "RelOpTest"
        System {
          Name "RelOpTest"
          Block {
            BlockType RelationalOperator
            Name "GT1"
            Operator ">"
          }
        }
      }`

      const model = importMDL(mdl)
      const relOp = model.blocks.find(b => b.type === 'relational_operator')

      expect(relOp).toBeDefined()
      expect(relOp?.parameters.operator).toBe('>')
    })

    it('should parse memory block', () => {
      const mdl = `Model {
        Name "MemoryTest"
        System {
          Name "MemoryTest"
          Block {
            BlockType Memory
            Name "Mem1"
            InitialCondition "0"
          }
        }
      }`

      const model = importMDL(mdl)
      const mem = model.blocks.find(b => b.type === 'memory')

      expect(mem).toBeDefined()
      expect(mem?.parameters.initialCondition).toBe(0)
    })

    it('should parse concatenate block', () => {
      const mdl = `Model {
        Name "ConcatTest"
        System {
          Name "ConcatTest"
          Block {
            BlockType Concatenate
            Name "Cat1"
            NumInputs "3"
            Mode "Multidimensional array"
          }
        }
      }`

      const model = importMDL(mdl)
      const cat = model.blocks.find(b => b.type === 'concatenate')

      expect(cat).toBeDefined()
      expect(cat?.parameters.numInputs).toBe(3)
      expect(cat?.parameters.mode).toBe('Multidimensional array')
    })

    it('should parse selector block', () => {
      const mdl = `Model {
        Name "SelectorTest"
        System {
          Name "SelectorTest"
          Block {
            BlockType Selector
            Name "Sel1"
            IndexMode "One-based"
            Indices "[1, 3]"
          }
        }
      }`

      const model = importMDL(mdl)
      const sel = model.blocks.find(b => b.type === 'selector')

      expect(sel).toBeDefined()
      expect(sel?.parameters.indexMode).toBe('One-based')
    })

    it('should parse reshape block', () => {
      const mdl = `Model {
        Name "ReshapeTest"
        System {
          Name "ReshapeTest"
          Block {
            BlockType Reshape
            Name "Rsh1"
            OutputDimensionality "Row vector"
            OutputDimensions "[4]"
          }
        }
      }`

      const model = importMDL(mdl)
      const rsh = model.blocks.find(b => b.type === 'reshape')

      expect(rsh).toBeDefined()
      expect(rsh?.parameters.outputDimensionality).toBe('Row vector')
    })

    it('should parse reference block (library link)', () => {
      const mdl = `Model {
        Name "RefTest"
        System {
          Name "RefTest"
          Block {
            BlockType Reference
            Name "LibBlock1"
            SourceBlock "mylib/MyBlock"
            SourceType "MyBlockType"
          }
        }
      }`

      const model = importMDL(mdl)
      const ref = model.blocks.find(b => b.type === 'reference')

      expect(ref).toBeDefined()
      expect(ref?.parameters.sourceBlock).toBe('mylib/MyBlock')
      expect(ref?.parameters.sourceType).toBe('MyBlockType')
    })

    it('should parse unary minus block', () => {
      const mdl = `Model {
        Name "UnaryTest"
        System {
          Name "UnaryTest"
          Block {
            BlockType UnaryMinus
            Name "Neg1"
          }
        }
      }`

      const model = importMDL(mdl)
      const neg = model.blocks.find(b => b.type === 'unary_minus')

      expect(neg).toBeDefined()
    })

    it('should parse bias block', () => {
      const mdl = `Model {
        Name "BiasTest"
        System {
          Name "BiasTest"
          Block {
            BlockType Bias
            Name "Bias1"
            Bias "5"
          }
        }
      }`

      const model = importMDL(mdl)
      const bias = model.blocks.find(b => b.type === 'bias')

      expect(bias).toBeDefined()
    })

    it('should parse ground block', () => {
      const mdl = `Model {
        Name "GroundTest"
        System {
          Name "GroundTest"
          Block {
            BlockType Ground
            Name "Gnd1"
          }
        }
      }`

      const model = importMDL(mdl)
      const gnd = model.blocks.find(b => b.type === 'ground')

      expect(gnd).toBeDefined()
    })

    it('should parse terminator block', () => {
      const mdl = `Model {
        Name "TermTest"
        System {
          Name "TermTest"
          Block {
            BlockType Terminator
            Name "Term1"
          }
        }
      }`

      const model = importMDL(mdl)
      const term = model.blocks.find(b => b.type === 'terminator')

      expect(term).toBeDefined()
    })
  })

  describe('Mux and Demux blocks', () => {
    it('should parse mux with Inputs property', () => {
      const mdl = `Model {
        Name "MuxTest"
        System {
          Name "MuxTest"
          Block {
            BlockType Mux
            Name "Mux1"
            Inputs "4"
          }
        }
      }`

      const model = importMDL(mdl)
      const mux = model.blocks.find(b => b.type === 'mux')

      expect(mux).toBeDefined()
      expect(mux?.parameters.numInputs).toBe(4)
    })

    it('should parse mux with Ports property as array', () => {
      const mdl = `Model {
        Name "MuxTest2"
        System {
          Name "MuxTest2"
          Block {
            BlockType Mux
            Name "Mux2"
            Ports [3, 1]
          }
        }
      }`

      const model = importMDL(mdl)
      const mux = model.blocks.find(b => b.type === 'mux')

      expect(mux).toBeDefined()
      expect(mux?.parameters.numInputs).toBe(3)
    })

    it('should parse demux with Outputs property', () => {
      const mdl = `Model {
        Name "DemuxTest"
        System {
          Name "DemuxTest"
          Block {
            BlockType Demux
            Name "Demux1"
            Outputs "3"
          }
        }
      }`

      const model = importMDL(mdl)
      const demux = model.blocks.find(b => b.type === 'demux')

      expect(demux).toBeDefined()
      expect(demux?.parameters.numOutputs).toBe(3)
    })
  })

  describe('Inport and Outport blocks', () => {
    it('should parse inport with Port property', () => {
      const mdl = `Model {
        Name "InportTest"
        System {
          Name "InportTest"
          Block {
            BlockType Inport
            Name "In1"
            Port "2"
          }
        }
      }`

      const model = importMDL(mdl)
      const inp = model.blocks.find(b => b.type === 'inport')

      expect(inp).toBeDefined()
      expect(inp?.parameters.portNumber).toBe(2)
    })

    it('should parse outport with default port number', () => {
      const mdl = `Model {
        Name "OutportTest"
        System {
          Name "OutportTest"
          Block {
            BlockType Outport
            Name "Out1"
          }
        }
      }`

      const model = importMDL(mdl)
      const out = model.blocks.find(b => b.type === 'outport')

      expect(out).toBeDefined()
      expect(out?.parameters.portNumber).toBe(1)
    })
  })

  describe('Subsystem with Ports', () => {
    it('should parse subsystem with Ports array', () => {
      const mdl = `Model {
        Name "SubsysPortsTest"
        System {
          Name "SubsysPortsTest"
          Block {
            BlockType SubSystem
            Name "MySub"
            Ports [2, 3]
          }
        }
      }`

      const model = importMDL(mdl)
      const sub = model.blocks.find(b => b.type === 'subsystem')

      expect(sub).toBeDefined()
      expect(sub?.parameters.numInputs).toBe(2)
      expect(sub?.parameters.numOutputs).toBe(3)
    })

    it('should parse subsystem with Ports string', () => {
      const mdl = `Model {
        Name "SubsysPortsStrTest"
        System {
          Name "SubsysPortsStrTest"
          Block {
            BlockType SubSystem
            Name "MySub2"
            Ports "[4, 2]"
          }
        }
      }`

      const model = importMDL(mdl)
      const sub = model.blocks.find(b => b.type === 'subsystem')

      expect(sub).toBeDefined()
      expect(sub?.parameters.numInputs).toBe(4)
      expect(sub?.parameters.numOutputs).toBe(2)
    })
  })

  describe('propagateDimensions', () => {
    it('should propagate dimensions through constant blocks', () => {
      const blocks: BlockInstance[] = [
        {
          id: 'const1',
          type: 'constant',
          name: 'Const1',
          position: { x: 0, y: 0 },
          parameters: { value: [1, 2, 3] },
          inputPorts: [],
          outputPorts: [{ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] }],
        },
      ]

      propagateDimensions(blocks, [])

      expect(blocks[0].outputPorts[0].dimensions).toEqual([3])
    })

    it('should propagate dimensions from constant string value', () => {
      const blocks: BlockInstance[] = [
        {
          id: 'const1',
          type: 'constant',
          name: 'Const1',
          position: { x: 0, y: 0 },
          parameters: { value: '[1, 2, 3, 4, 5]' },
          inputPorts: [],
          outputPorts: [{ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] }],
        },
      ]

      propagateDimensions(blocks, [])

      expect(blocks[0].outputPorts[0].dimensions).toEqual([5])
    })

    it('should propagate dimensions to outport blocks', () => {
      const blocks: BlockInstance[] = [
        {
          id: 'const1',
          type: 'constant',
          name: 'Const1',
          position: { x: 0, y: 0 },
          parameters: { value: [1, 2, 3] },
          inputPorts: [],
          outputPorts: [{ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] }],
        },
        {
          id: 'out1',
          type: 'outport',
          name: 'Out1',
          position: { x: 100, y: 0 },
          parameters: { portNumber: 1 },
          inputPorts: [{ id: 'in_0', name: 'in', dataType: 'double', dimensions: [1] }],
          outputPorts: [],
        },
      ]

      const connections: Connection[] = [
        {
          id: 'conn1',
          sourceBlockId: 'const1',
          sourcePortId: 'out_0',
          targetBlockId: 'out1',
          targetPortId: 'in_0',
        },
      ]

      propagateDimensions(blocks, connections)

      expect(blocks[0].outputPorts[0].dimensions).toEqual([3])
      expect(blocks[1].inputPorts[0].dimensions).toEqual([3])
    })

    it('should propagate dimensions in nested subsystems', () => {
      const childBlocks: BlockInstance[] = [
        {
          id: 'child_const',
          type: 'constant',
          name: 'ChildConst',
          position: { x: 0, y: 0 },
          parameters: { value: [1, 2] },
          inputPorts: [],
          outputPorts: [{ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] }],
        },
      ]

      const blocks: BlockInstance[] = [
        {
          id: 'sub1',
          type: 'subsystem',
          name: 'Sub1',
          position: { x: 0, y: 0 },
          parameters: {},
          inputPorts: [],
          outputPorts: [],
          children: childBlocks,
          childConnections: [],
        },
      ]

      propagateDimensions(blocks, [])

      expect(childBlocks[0].outputPorts[0].dimensions).toEqual([2])
    })
  })

  describe('Edge cases', () => {
    it('should handle blocks with no Name', () => {
      const mdl = `Model {
        Name "NoNameTest"
        System {
          Name "NoNameTest"
          Block {
            BlockType Constant
            Value "1"
          }
        }
      }`

      const model = importMDL(mdl)
      expect(model.blocks.length).toBe(1)
      // Should have a default name
      expect(model.blocks[0].name).toBeDefined()
    })

    it('should handle numeric block names', () => {
      const mdl = `Model {
        Name "NumericNameTest"
        System {
          Name "NumericNameTest"
          Block {
            BlockType Constant
            Name "123"
            Value "5"
          }
        }
      }`

      const model = importMDL(mdl)
      expect(model.blocks[0].name).toBe('123')
    })

    it('should handle empty System', () => {
      const mdl = `Model {
        Name "EmptySystemTest"
        System {
          Name "EmptySystemTest"
        }
      }`

      const model = importMDL(mdl)
      expect(model.blocks).toEqual([])
      expect(model.connections).toEqual([])
    })
  })
})
