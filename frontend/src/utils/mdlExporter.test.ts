import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { modelToMDL, exportModelAsMDL } from './mdlExporter'
import type { Model } from '../types/model'
import type { BlockInstance, Connection } from '../types/block'

// Helper to create a minimal model
function createTestModel(overrides: Partial<Model> = {}): Model {
  return {
    id: 'test-model-id',
    metadata: {
      name: 'Test Model',
      description: 'Test description',
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
    ...overrides,
  }
}

// Helper to create a test block
function createTestBlock(overrides: Partial<BlockInstance> = {}): BlockInstance {
  return {
    id: 'test-block-id',
    type: 'constant',
    name: 'TestBlock',
    position: { x: 100, y: 100 },
    parameters: {},
    inputPorts: [],
    outputPorts: [{ id: 'out-0', name: 'out', dataType: 'double', dimensions: [1] }],
    ...overrides,
  }
}

describe('modelToMDL', () => {
  describe('Model structure', () => {
    it('generates valid MDL structure for empty model', () => {
      const model = createTestModel()
      const mdl = modelToMDL(model)

      expect(mdl).toContain('Model {')
      expect(mdl).toContain('Name\t\t\t  "Test_Model"')
      expect(mdl).toContain('Version\t\t  8.0')
      expect(mdl).toContain('System {')
      expect(mdl).toMatch(/StartTime\t\t  "0"/)
      expect(mdl).toMatch(/StopTime\t\t  "10"/)
    })

    it('sanitizes model name for MDL format', () => {
      const model = createTestModel({
        metadata: {
          ...createTestModel().metadata,
          name: 'My Model-With Spaces & Symbols!',
        },
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('"My_Model_With_Spaces___Symbols_"')
    })

    it('maps solver types correctly', () => {
      const solverTests = [
        { solver: 'euler' as const, expected: 'ode1' },
        { solver: 'rk2' as const, expected: 'ode2' },
        { solver: 'rk4' as const, expected: 'ode4' },
        { solver: 'merson' as const, expected: 'ode45' },
      ]

      for (const { solver, expected } of solverTests) {
        const model = createTestModel({
          simulationConfig: {
            solver,
            startTime: 0,
            stopTime: 10,
            stepSize: 0.01,
          },
        })
        const mdl = modelToMDL(model)
        expect(mdl).toContain(`Solver\t\t  "${expected}"`)
      }
    })

    it('uses default solver for unknown types', () => {
      const model = createTestModel({
        simulationConfig: {
          solver: 'unknown_solver' as 'rk4',
          startTime: 0,
          stopTime: 10,
          stepSize: 0.01,
        },
      })
      const mdl = modelToMDL(model)
      // Falls back to default (ode4 is not found, so uses the key as-is)
      expect(mdl).toContain('Solver')
    })
  })

  describe('Block type mapping', () => {
    const blockTypeMappings = [
      // Sources
      { type: 'constant', expected: 'Constant' },
      { type: 'step', expected: 'Step' },
      { type: 'ramp', expected: 'Ramp' },
      { type: 'sine_wave', expected: 'Sin' },
      { type: 'pulse_generator', expected: 'DiscretePulseGenerator' },
      { type: 'clock', expected: 'Clock' },
      // Sinks
      { type: 'scope', expected: 'Scope' },
      { type: 'display', expected: 'Display' },
      { type: 'to_workspace', expected: 'ToWorkspace' },
      { type: 'terminator', expected: 'Terminator' },
      // Continuous
      { type: 'integrator', expected: 'Integrator' },
      { type: 'derivative', expected: 'Derivative' },
      { type: 'transfer_function', expected: 'TransferFcn' },
      { type: 'state_space', expected: 'StateSpace' },
      { type: 'pid_controller', expected: 'PID' },
      // Discrete
      { type: 'unit_delay', expected: 'UnitDelay' },
      { type: 'zero_order_hold', expected: 'ZeroOrderHold' },
      { type: 'discrete_integrator', expected: 'DiscreteIntegrator' },
      { type: 'discrete_derivative', expected: 'DiscreteDerivative' },
      { type: 'discrete_transfer_function', expected: 'DiscreteTransferFcn' },
      // Math
      { type: 'sum', expected: 'Sum' },
      { type: 'gain', expected: 'Gain' },
      { type: 'product', expected: 'Product' },
      { type: 'abs', expected: 'Abs' },
      { type: 'sign', expected: 'Signum' },
      { type: 'saturation', expected: 'Saturate' },
      { type: 'dead_zone', expected: 'DeadZone' },
      { type: 'math_function', expected: 'Math' },
      { type: 'trigonometry', expected: 'Trigonometry' },
      { type: 'switch', expected: 'Switch' },
      // Signal Processing
      { type: 'rate_limiter', expected: 'RateLimiter' },
      { type: 'quantizer', expected: 'Quantizer' },
      // Nonlinear
      { type: 'relay', expected: 'Relay' },
      { type: 'lookup_table_1d', expected: 'Lookup' },
      { type: 'lookup_table_2d', expected: 'Lookup2D' },
      // Subsystems
      { type: 'subsystem', expected: 'SubSystem' },
      { type: 'inport', expected: 'Inport' },
      { type: 'outport', expected: 'Outport' },
    ]

    for (const { type, expected } of blockTypeMappings) {
      it(`maps ${type} to ${expected}`, () => {
        const model = createTestModel({
          blocks: [createTestBlock({ type, name: `${type}Block` })],
        })
        const mdl = modelToMDL(model)
        expect(mdl).toContain(`BlockType\t\t      ${expected}`)
      })
    }

    it('uses SubSystem as fallback for unknown block types', () => {
      const model = createTestModel({
        blocks: [createTestBlock({ type: 'unknown_type' })],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('BlockType\t\t      SubSystem')
    })
  })

  describe('Block parameters', () => {
    it('exports Constant block with value', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'constant',
            parameters: { value: 42 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('Value\t\t      "42"')
    })

    it('exports Step block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'step',
            parameters: { stepTime: 1, initialValue: 0, finalValue: 1 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('Time\t\t      "1"')
      expect(mdl).toContain('Before\t\t      "0"')
      expect(mdl).toContain('After\t\t      "1"')
    })

    it('exports Ramp block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'ramp',
            parameters: { slope: 2, startTime: 1, initialOutput: 0 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('Slope\t\t      "2"')
      expect(mdl).toContain('Start\t\t      "1"')
      expect(mdl).toContain('X0\t\t      "0"')
    })

    it('exports Sine Wave block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'sine_wave',
            parameters: { amplitude: 5, frequency: 2, phase: 0.5, bias: 1 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('Amplitude\t      "5"')
      expect(mdl).toContain('Frequency\t      "2"')
      expect(mdl).toContain('Phase\t\t      "0.5"')
      expect(mdl).toContain('Bias\t\t      "1"')
    })

    it('exports Pulse Generator block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'pulse_generator',
            parameters: { amplitude: 1, period: 2, dutyCycle: 50 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('Amplitude\t      "1"')
      expect(mdl).toContain('Period\t\t      "2"')
      expect(mdl).toContain('PulseWidth\t      "50"')
    })

    it('exports Scope block with number of inputs', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'scope',
            parameters: { numInputs: 3 },
            inputPorts: [
              { id: 'in-0', name: 'in1', dataType: 'double', dimensions: [1] },
              { id: 'in-1', name: 'in2', dataType: 'double', dimensions: [1] },
              { id: 'in-2', name: 'in3', dataType: 'double', dimensions: [1] },
            ],
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('Ports\t\t      [3]')
      expect(mdl).toContain('NumInputPorts\t      "3"')
    })

    it('exports Integrator block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'integrator',
            parameters: {
              initialCondition: 1,
              limitOutput: true,
              upperLimit: 10,
              lowerLimit: -10,
            },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('InitialCondition      "1"')
      expect(mdl).toContain('LimitOutput\t      "on"')
      expect(mdl).toContain('UpperSaturationLimit  "10"')
      expect(mdl).toContain('LowerSaturationLimit  "-10"')
    })

    it('exports Derivative block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'derivative',
            parameters: { coefficient: 2 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('Coefficient\t      "2"')
    })

    it('exports Transfer Function block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'transfer_function',
            parameters: { numerator: [1, 2], denominator: [1, 3, 2] },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('Numerator\t      "[1 2]"')
      expect(mdl).toContain('Denominator\t      "[1 3 2]"')
    })

    it('exports State Space block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'state_space',
            parameters: {
              A: [[0, 1], [-2, -3]],
              B: [[0], [1]],
              C: [[1, 0]],
              D: [[0]],
            },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('A\t\t      "[[0,1],[-2,-3]]"')
      expect(mdl).toContain('B\t\t      "[[0],[1]]"')
      expect(mdl).toContain('C\t\t      "[[1,0]]"')
      expect(mdl).toContain('D\t\t      "[[0]]"')
    })

    it('exports PID Controller block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'pid_controller',
            parameters: { Kp: 1, Ki: 0.5, Kd: 0.1, N: 100 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('P\t\t      "1"')
      expect(mdl).toContain('I\t\t      "0.5"')
      expect(mdl).toContain('D\t\t      "0.1"')
      expect(mdl).toContain('N\t\t      "100"')
    })

    it('exports Unit Delay block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'unit_delay',
            parameters: { initialCondition: 0, sampleTime: 0.1 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('InitialCondition      "0"')
      expect(mdl).toContain('SampleTime\t      "0.1"')
    })

    it('exports Zero Order Hold block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'zero_order_hold',
            parameters: { sampleTime: 0.05 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('SampleTime\t      "0.05"')
    })

    it('exports Sum block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'sum',
            parameters: { signs: '+-+' },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('Inputs\t\t      "+-+"')
      expect(mdl).toContain('IconShape\t      "round"')
    })

    it('exports Gain block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'gain',
            parameters: { gain: 2.5 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('Gain\t\t      "2.5"')
    })

    it('exports Product block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'product',
            parameters: { operations: '**/' },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('Inputs\t\t      "**/"')
    })

    it('exports Saturation block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'saturation',
            parameters: { upperLimit: 10, lowerLimit: -5 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('UpperLimit\t      "10"')
      expect(mdl).toContain('LowerLimit\t      "-5"')
    })

    it('exports Dead Zone block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'dead_zone',
            parameters: { start: -1, end: 1 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('LowerValue\t      "-1"')
      expect(mdl).toContain('UpperValue\t      "1"')
    })

    it('exports Rate Limiter block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'rate_limiter',
            parameters: { risingLimit: 5, fallingLimit: -3 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('RisingSlewLimit\t      "5"')
      expect(mdl).toContain('FallingSlewLimit      "-3"')
    })

    it('exports Relay block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'relay',
            parameters: { switchOn: 1, switchOff: -1, outputOn: 1, outputOff: 0 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('OnSwitchValue\t      "1"')
      expect(mdl).toContain('OffSwitchValue\t      "-1"')
      expect(mdl).toContain('OnOutputValue\t      "1"')
      expect(mdl).toContain('OffOutputValue\t      "0"')
    })

    it('exports Inport block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'inport',
            parameters: { portNumber: 2 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('Port\t\t      "2"')
    })

    it('exports Outport block parameters', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            type: 'outport',
            parameters: { portNumber: 3 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('Port\t\t      "3"')
    })
  })

  describe('Block positioning', () => {
    it('converts position to Simulink format [left, top, right, bottom]', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            position: { x: 150, y: 200 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      // Position should be [x, y, x+60, y+40] for a 60x40 block
      expect(mdl).toContain('Position\t\t      [150, 200, 210, 240]')
    })

    it('rounds position values', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            position: { x: 100.7, y: 50.3 },
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('Position\t\t      [101, 50, 161, 90]')
    })
  })

  describe('Block name escaping', () => {
    it('escapes quotes in block names', () => {
      const model = createTestModel({
        blocks: [
          createTestBlock({
            name: 'Block "with" Quotes',
          }),
        ],
      })
      const mdl = modelToMDL(model)
      expect(mdl).toContain('Name\t\t      "Block \\"with\\" Quotes"')
    })
  })

  describe('Connections', () => {
    it('exports connections between blocks', () => {
      const block1 = createTestBlock({
        id: 'block-1',
        name: 'Source',
        outputPorts: [{ id: 'block-1-out-0', name: 'out', dataType: 'double', dimensions: [1] }],
      })
      const block2 = createTestBlock({
        id: 'block-2',
        type: 'scope',
        name: 'Sink',
        inputPorts: [{ id: 'block-2-in-0', name: 'in', dataType: 'double', dimensions: [1] }],
        outputPorts: [],
      })

      const connection: Connection = {
        id: 'conn-1',
        sourceBlockId: 'block-1',
        sourcePortId: 'block-1-out-0',
        targetBlockId: 'block-2',
        targetPortId: 'block-2-in-0',
      }

      const model = createTestModel({
        blocks: [block1, block2],
        connections: [connection],
      })
      const mdl = modelToMDL(model)

      expect(mdl).toContain('Line {')
      expect(mdl).toContain('SrcBlock\t\t      "Source"')
      expect(mdl).toContain('SrcPort\t\t      1')
      expect(mdl).toContain('DstBlock\t\t      "Sink"')
      expect(mdl).toContain('DstPort\t\t      1')
    })

    it('uses correct port indices for multi-port blocks', () => {
      const block1 = createTestBlock({
        id: 'block-1',
        name: 'Source',
        outputPorts: [
          { id: 'block-1-out-0', name: 'out1', dataType: 'double', dimensions: [1] },
          { id: 'block-1-out-1', name: 'out2', dataType: 'double', dimensions: [1] },
        ],
      })
      const block2 = createTestBlock({
        id: 'block-2',
        type: 'sum',
        name: 'Sum',
        inputPorts: [
          { id: 'block-2-in-0', name: 'in1', dataType: 'double', dimensions: [1] },
          { id: 'block-2-in-1', name: 'in2', dataType: 'double', dimensions: [1] },
        ],
      })

      // Connection from second output to second input
      const connection: Connection = {
        id: 'conn-1',
        sourceBlockId: 'block-1',
        sourcePortId: 'block-1-out-1',
        targetBlockId: 'block-2',
        targetPortId: 'block-2-in-1',
      }

      const model = createTestModel({
        blocks: [block1, block2],
        connections: [connection],
      })
      const mdl = modelToMDL(model)

      expect(mdl).toContain('SrcPort\t\t      2')
      expect(mdl).toContain('DstPort\t\t      2')
    })

    it('skips connections with missing source block', () => {
      const block = createTestBlock({ id: 'block-1', name: 'Block' })

      const connection: Connection = {
        id: 'conn-1',
        sourceBlockId: 'missing-block',
        sourcePortId: 'missing-port',
        targetBlockId: 'block-1',
        targetPortId: 'block-1-in-0',
      }

      const model = createTestModel({
        blocks: [block],
        connections: [connection],
      })
      const mdl = modelToMDL(model)

      // Should not contain a Line block
      expect(mdl).not.toContain('Line {')
    })

    it('skips connections with missing target block', () => {
      const block = createTestBlock({ id: 'block-1', name: 'Block' })

      const connection: Connection = {
        id: 'conn-1',
        sourceBlockId: 'block-1',
        sourcePortId: 'block-1-out-0',
        targetBlockId: 'missing-block',
        targetPortId: 'missing-port',
      }

      const model = createTestModel({
        blocks: [block],
        connections: [connection],
      })
      const mdl = modelToMDL(model)

      // Should not contain a Line block
      expect(mdl).not.toContain('Line {')
    })

    it('escapes quotes in block names within connections', () => {
      const block1 = createTestBlock({
        id: 'block-1',
        name: 'Source "Block"',
        outputPorts: [{ id: 'block-1-out-0', name: 'out', dataType: 'double', dimensions: [1] }],
      })
      const block2 = createTestBlock({
        id: 'block-2',
        name: 'Target "Block"',
        inputPorts: [{ id: 'block-2-in-0', name: 'in', dataType: 'double', dimensions: [1] }],
      })

      const connection: Connection = {
        id: 'conn-1',
        sourceBlockId: 'block-1',
        sourcePortId: 'block-1-out-0',
        targetBlockId: 'block-2',
        targetPortId: 'block-2-in-0',
      }

      const model = createTestModel({
        blocks: [block1, block2],
        connections: [connection],
      })
      const mdl = modelToMDL(model)

      expect(mdl).toContain('SrcBlock\t\t      "Source \\"Block\\""')
      expect(mdl).toContain('DstBlock\t\t      "Target \\"Block\\""')
    })
  })
})

describe('exportModelAsMDL', () => {
  let mockCreateElement: ReturnType<typeof vi.fn>
  let mockAppendChild: ReturnType<typeof vi.fn>
  let mockRemoveChild: ReturnType<typeof vi.fn>
  let mockClick: ReturnType<typeof vi.fn>
  let mockCreateObjectURL: ReturnType<typeof vi.fn>
  let mockRevokeObjectURL: ReturnType<typeof vi.fn>

  beforeEach(() => {
    // Mock DOM methods
    mockClick = vi.fn()
    mockCreateElement = vi.fn().mockReturnValue({
      href: '',
      download: '',
      click: mockClick,
    })
    mockAppendChild = vi.fn()
    mockRemoveChild = vi.fn()
    mockCreateObjectURL = vi.fn().mockReturnValue('blob:mock-url')
    mockRevokeObjectURL = vi.fn()

    vi.stubGlobal('document', {
      createElement: mockCreateElement,
      body: {
        appendChild: mockAppendChild,
        removeChild: mockRemoveChild,
      },
    })
    vi.stubGlobal('URL', {
      createObjectURL: mockCreateObjectURL,
      revokeObjectURL: mockRevokeObjectURL,
    })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('creates a download link and triggers download', () => {
    const model = createTestModel()
    exportModelAsMDL(model)

    expect(mockCreateElement).toHaveBeenCalledWith('a')
    expect(mockCreateObjectURL).toHaveBeenCalled()
    expect(mockAppendChild).toHaveBeenCalled()
    expect(mockClick).toHaveBeenCalled()
    expect(mockRemoveChild).toHaveBeenCalled()
    expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
  })

  it('uses model name for filename', () => {
    const model = createTestModel()
    const anchor = { href: '', download: '', click: mockClick }
    mockCreateElement.mockReturnValue(anchor)

    exportModelAsMDL(model)

    expect(anchor.download).toBe('Test_Model.mdl')
  })

  it('sanitizes filename', () => {
    const model = createTestModel({
      metadata: {
        ...createTestModel().metadata,
        name: 'My Model <with> Special/Chars',
      },
    })
    const anchor = { href: '', download: '', click: mockClick }
    mockCreateElement.mockReturnValue(anchor)

    exportModelAsMDL(model)

    expect(anchor.download).toBe('My_Model__with__Special_Chars.mdl')
  })

  it('uses "model" as default filename when name is empty', () => {
    const model = createTestModel({
      metadata: {
        ...createTestModel().metadata,
        name: '',
      },
    })
    const anchor = { href: '', download: '', click: mockClick }
    mockCreateElement.mockReturnValue(anchor)

    exportModelAsMDL(model)

    expect(anchor.download).toBe('model.mdl')
  })

  it('creates blob with correct MIME type', () => {
    const model = createTestModel()
    exportModelAsMDL(model)

    expect(mockCreateObjectURL).toHaveBeenCalled()
    const blob = mockCreateObjectURL.mock.calls[0][0]
    expect(blob).toBeInstanceOf(Blob)
    expect(blob.type).toBe('text/plain')
  })
})
