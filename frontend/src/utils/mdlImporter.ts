import type { Model, ModelMetadata } from '../types/model'
import type { BlockInstance, Connection, Port } from '../types/block'
import { blockRegistry } from '../blocks'

// Reverse mapping from Simulink BlockTypes to LibreSim types
const SIMULINK_TO_LIBRESIM: Record<string, string> = {
  // Sources
  'Constant': 'constant',
  'Step': 'step',
  'Ramp': 'ramp',
  'Sin': 'sine_wave',
  'Sine Wave': 'sine_wave',
  'DiscretePulseGenerator': 'pulse_generator',
  'Clock': 'clock',
  'FromWorkspace': 'from_workspace',
  'Ground': 'ground',

  // Sinks
  'Scope': 'scope',
  'Display': 'display',
  'ToWorkspace': 'to_workspace',
  'Terminator': 'terminator',
  'XYGraph': 'xy_graph',

  // Continuous
  'Integrator': 'integrator',
  'Derivative': 'derivative',
  'TransferFcn': 'transfer_function',
  'StateSpace': 'state_space',
  'PID': 'pid_controller',
  'PID Controller': 'pid_controller',

  // Discrete
  'UnitDelay': 'unit_delay',
  'ZeroOrderHold': 'zero_order_hold',
  'DiscreteIntegrator': 'discrete_integrator',
  'DiscreteDerivative': 'discrete_derivative',
  'DiscreteTransferFcn': 'discrete_transfer_function',

  // Math
  'Sum': 'sum',
  'Gain': 'gain',
  'Product': 'product',
  'Abs': 'abs',
  'Signum': 'sign',
  'Saturate': 'saturation',
  'Saturation': 'saturation',
  'DeadZone': 'dead_zone',
  'Math': 'math_function',
  'Trigonometry': 'trigonometry',
  'Switch': 'switch',
  'MinMax': 'minmax',
  'Bias': 'bias',

  // Signal routing
  'Mux': 'mux',
  'Demux': 'demux',
  'BusCreator': 'bus_creator',
  'BusSelector': 'bus_selector',
  'Merge': 'merge',
  'Goto': 'goto',
  'From': 'from',

  // Signal Processing
  'RateLimiter': 'rate_limiter',
  'Quantizer': 'quantizer',

  // Nonlinear
  'Relay': 'relay',
  'Lookup': 'lookup_table_1d',
  'Lookup2D': 'lookup_table_2d',
  'Backlash': 'backlash',

  // Subsystems
  'SubSystem': 'subsystem',
  'Subsystem': 'subsystem',
  'Inport': 'inport',
  'Outport': 'outport',
}

// Map solver types from Simulink to LibreSim
const SOLVER_TO_LIBRESIM: Record<string, 'euler' | 'rk4' | 'merson'> = {
  'ode1': 'euler',
  'ode2': 'rk4',
  'ode3': 'rk4',
  'ode4': 'rk4',
  'ode45': 'merson',
  'ode23': 'merson',
  'ode113': 'merson',
  'ode15s': 'merson',
  'ode23s': 'merson',
  'ode23t': 'merson',
  'ode23tb': 'merson',
  'VariableStepAuto': 'rk4',
  'FixedStepAuto': 'rk4',
}

interface ParsedBlock {
  BlockType: string
  Name: string
  Position?: number[]
  [key: string]: unknown
}

interface ParsedLine {
  SrcBlock: string
  SrcPort: number | string
  DstBlock: string
  DstPort: number | string
  Points?: number[][]
}

interface ParsedSystem {
  Name: string
  blocks: ParsedBlock[]
  lines: ParsedLine[]
  subsystems?: ParsedSystem[]
}

interface ParsedModel {
  Name: string
  StartTime?: string
  StopTime?: string
  Solver?: string
  FixedStep?: string
  system: ParsedSystem
}

/**
 * Tokenize MDL content into meaningful tokens
 */
function tokenize(content: string): string[] {
  const tokens: string[] = []
  let i = 0
  const len = content.length

  while (i < len) {
    // Skip whitespace
    if (/\s/.test(content[i])) {
      i++
      continue
    }

    // Handle braces
    if (content[i] === '{' || content[i] === '}') {
      tokens.push(content[i])
      i++
      continue
    }

    // Handle quoted strings
    if (content[i] === '"') {
      let str = '"'
      i++
      while (i < len && content[i] !== '"') {
        if (content[i] === '\\' && i + 1 < len) {
          str += content[i] + content[i + 1]
          i += 2
        } else {
          str += content[i]
          i++
        }
      }
      str += '"'
      i++
      tokens.push(str)
      continue
    }

    // Handle identifiers and numbers
    let token = ''
    while (i < len && !/[\s{}"]/.test(content[i])) {
      token += content[i]
      i++
    }
    if (token) {
      tokens.push(token)
    }
  }

  return tokens
}

/**
 * Parse a value (could be string, number, array, etc.)
 */
function parseValue(value: string): unknown {
  // Remove quotes if present
  if (value.startsWith('"') && value.endsWith('"')) {
    return value.slice(1, -1).replace(/\\"/g, '"')
  }

  // Try parsing as number
  const num = parseFloat(value)
  if (!isNaN(num) && isFinite(num)) {
    return num
  }

  // Check for array format [1 2 3] or [1, 2, 3]
  if (value.startsWith('[') && value.endsWith(']')) {
    const inner = value.slice(1, -1).trim()
    if (!inner) return []
    const parts = inner.split(/[\s,;]+/).filter(Boolean)
    return parts.map(p => {
      const n = parseFloat(p)
      return isNaN(n) ? p : n
    })
  }

  return value
}

/**
 * Parse MDL content into structured data
 */
function parseMDL(content: string): ParsedModel {
  const tokens = tokenize(content)
  let pos = 0

  function parseObject(): Record<string, unknown> {
    const obj: Record<string, unknown> = {}

    while (pos < tokens.length && tokens[pos] !== '}') {
      const key = tokens[pos]
      pos++

      if (tokens[pos] === '{') {
        pos++ // skip {

        // Check if this is an array of objects (like Block, Line, System)
        if (key === 'Block' || key === 'Line' || key === 'System') {
          const arrayKey = key === 'Block' ? 'blocks' : key === 'Line' ? 'lines' : 'systems'
          if (!obj[arrayKey]) {
            obj[arrayKey] = []
          }
          (obj[arrayKey] as unknown[]).push(parseObject())
        } else {
          obj[key] = parseObject()
        }
        pos++ // skip }
      } else if (tokens[pos] !== '{' && tokens[pos] !== '}') {
        obj[key] = parseValue(tokens[pos])
        pos++
      }
    }

    return obj
  }

  // Find Model {
  while (pos < tokens.length && tokens[pos] !== 'Model') {
    pos++
  }
  pos++ // skip 'Model'

  if (tokens[pos] === '{') {
    pos++ // skip {
    const modelObj = parseObject()

    // Extract system information
    const systems = (modelObj.systems as Record<string, unknown>[]) || []
    const mainSystem = systems[0] || {}

    return {
      Name: modelObj.Name as string || 'Imported Model',
      StartTime: modelObj.StartTime as string,
      StopTime: modelObj.StopTime as string,
      Solver: modelObj.Solver as string,
      FixedStep: modelObj.FixedStep as string,
      system: {
        Name: mainSystem.Name as string || 'Main',
        blocks: (mainSystem.blocks as ParsedBlock[]) || [],
        lines: (mainSystem.lines as ParsedLine[]) || [],
      }
    }
  }

  throw new Error('Invalid MDL format: Model block not found')
}

/**
 * Parse position array from MDL format [left, top, right, bottom]
 */
function parsePosition(pos: unknown): { x: number; y: number } {
  if (Array.isArray(pos) && pos.length >= 2) {
    return {
      x: typeof pos[0] === 'number' ? pos[0] : 100,
      y: typeof pos[1] === 'number' ? pos[1] : 100,
    }
  }
  // Handle string format "[100, 100, 160, 140]"
  if (typeof pos === 'string') {
    const match = pos.match(/\[?\s*(-?\d+)\s*[,\s]\s*(-?\d+)/)
    if (match) {
      return { x: parseInt(match[1]), y: parseInt(match[2]) }
    }
  }
  return { x: 100, y: 100 }
}

/**
 * Convert parsed block parameters to LibreSim format
 */
function convertBlockParameters(block: ParsedBlock, libreSimType: string): Record<string, unknown> {
  const params: Record<string, unknown> = {}

  switch (libreSimType) {
    case 'constant':
      if (block.Value !== undefined) params.value = parseValue(String(block.Value))
      break

    case 'step':
      if (block.Time !== undefined) params.stepTime = parseValue(String(block.Time))
      if (block.Before !== undefined) params.initialValue = parseValue(String(block.Before))
      if (block.After !== undefined) params.finalValue = parseValue(String(block.After))
      break

    case 'ramp':
      if (block.Slope !== undefined) params.slope = parseValue(String(block.Slope))
      if (block.Start !== undefined) params.startTime = parseValue(String(block.Start))
      if (block.X0 !== undefined) params.initialOutput = parseValue(String(block.X0))
      break

    case 'sine_wave':
      if (block.Amplitude !== undefined) params.amplitude = parseValue(String(block.Amplitude))
      if (block.Frequency !== undefined) params.frequency = parseValue(String(block.Frequency))
      if (block.Phase !== undefined) params.phase = parseValue(String(block.Phase))
      if (block.Bias !== undefined) params.bias = parseValue(String(block.Bias))
      break

    case 'pulse_generator':
      if (block.Amplitude !== undefined) params.amplitude = parseValue(String(block.Amplitude))
      if (block.Period !== undefined) params.period = parseValue(String(block.Period))
      if (block.PulseWidth !== undefined) params.dutyCycle = parseValue(String(block.PulseWidth))
      break

    case 'scope':
      if (block.NumInputPorts !== undefined) params.numInputs = parseValue(String(block.NumInputPorts))
      break

    case 'integrator':
      if (block.InitialCondition !== undefined) params.initialCondition = parseValue(String(block.InitialCondition))
      if (block.LimitOutput === 'on') {
        params.limitOutput = true
        if (block.UpperSaturationLimit !== undefined) params.upperLimit = parseValue(String(block.UpperSaturationLimit))
        if (block.LowerSaturationLimit !== undefined) params.lowerLimit = parseValue(String(block.LowerSaturationLimit))
      }
      break

    case 'derivative':
      if (block.Coefficient !== undefined) params.coefficient = parseValue(String(block.Coefficient))
      break

    case 'transfer_function':
      if (block.Numerator !== undefined) {
        const num = parseValue(String(block.Numerator))
        params.numerator = Array.isArray(num) ? num : [num]
      }
      if (block.Denominator !== undefined) {
        const den = parseValue(String(block.Denominator))
        params.denominator = Array.isArray(den) ? den : [den]
      }
      break

    case 'state_space':
      if (block.A !== undefined) params.A = parseValue(String(block.A))
      if (block.B !== undefined) params.B = parseValue(String(block.B))
      if (block.C !== undefined) params.C = parseValue(String(block.C))
      if (block.D !== undefined) params.D = parseValue(String(block.D))
      break

    case 'pid_controller':
      if (block.P !== undefined) params.Kp = parseValue(String(block.P))
      if (block.I !== undefined) params.Ki = parseValue(String(block.I))
      if (block.D !== undefined) params.Kd = parseValue(String(block.D))
      if (block.N !== undefined) params.N = parseValue(String(block.N))
      break

    case 'unit_delay':
      if (block.InitialCondition !== undefined) params.initialCondition = parseValue(String(block.InitialCondition))
      if (block.SampleTime !== undefined) params.sampleTime = parseValue(String(block.SampleTime))
      break

    case 'zero_order_hold':
      if (block.SampleTime !== undefined) params.sampleTime = parseValue(String(block.SampleTime))
      break

    case 'sum':
      if (block.Inputs !== undefined) params.signs = String(block.Inputs)
      break

    case 'gain':
      if (block.Gain !== undefined) params.gain = parseValue(String(block.Gain))
      break

    case 'product':
      if (block.Inputs !== undefined) params.operations = String(block.Inputs)
      break

    case 'saturation':
      if (block.UpperLimit !== undefined) params.upperLimit = parseValue(String(block.UpperLimit))
      if (block.LowerLimit !== undefined) params.lowerLimit = parseValue(String(block.LowerLimit))
      break

    case 'dead_zone':
      if (block.LowerValue !== undefined) params.start = parseValue(String(block.LowerValue))
      if (block.UpperValue !== undefined) params.end = parseValue(String(block.UpperValue))
      break

    case 'rate_limiter':
      if (block.RisingSlewLimit !== undefined) params.risingLimit = parseValue(String(block.RisingSlewLimit))
      if (block.FallingSlewLimit !== undefined) params.fallingLimit = parseValue(String(block.FallingSlewLimit))
      break

    case 'relay':
      if (block.OnSwitchValue !== undefined) params.switchOn = parseValue(String(block.OnSwitchValue))
      if (block.OffSwitchValue !== undefined) params.switchOff = parseValue(String(block.OffSwitchValue))
      if (block.OnOutputValue !== undefined) params.outputOn = parseValue(String(block.OnOutputValue))
      if (block.OffOutputValue !== undefined) params.outputOff = parseValue(String(block.OffOutputValue))
      break

    case 'inport':
    case 'outport':
      if (block.Port !== undefined) params.portNumber = parseValue(String(block.Port))
      break
  }

  return params
}

/**
 * Create ports for a block based on its definition
 */
function createPorts(blockType: string, params: Record<string, unknown>): { inputPorts: Port[]; outputPorts: Port[] } {
  const definition = blockRegistry.get(blockType)

  if (definition) {
    const inputPorts: Port[] = definition.inputs.map((input, i) => ({
      id: `in_${i}`,
      name: input.name,
      dataType: input.dataType,
      dimensions: input.dimensions,
    }))

    const outputPorts: Port[] = definition.outputs.map((output, i) => ({
      id: `out_${i}`,
      name: output.name,
      dataType: output.dataType,
      dimensions: output.dimensions,
    }))

    // Handle dynamic ports for certain blocks
    if (blockType === 'scope' && params.numInputs) {
      const numInputs = typeof params.numInputs === 'number' ? params.numInputs : parseInt(String(params.numInputs)) || 1
      inputPorts.length = 0
      for (let i = 0; i < numInputs; i++) {
        inputPorts.push({
          id: `in_${i}`,
          name: `in${i + 1}`,
          dataType: 'double',
          dimensions: [1],
        })
      }
    }

    if (blockType === 'sum' && params.signs) {
      const signs = String(params.signs)
      const numPorts = signs.replace(/\|/g, '').length
      inputPorts.length = 0
      for (let i = 0; i < numPorts; i++) {
        inputPorts.push({
          id: `in_${i}`,
          name: `in${i + 1}`,
          dataType: 'double',
          dimensions: [1],
        })
      }
    }

    return { inputPorts, outputPorts }
  }

  // Default: 1 input, 1 output
  return {
    inputPorts: [{ id: 'in_0', name: 'in', dataType: 'double', dimensions: [1] }],
    outputPorts: [{ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] }],
  }
}

/**
 * Convert parsed MDL to LibreSim Model
 */
function convertToModel(parsed: ParsedModel): Model {
  const blockMap = new Map<string, BlockInstance>()
  const blocks: BlockInstance[] = []
  const connections: Connection[] = []

  // Convert blocks
  for (const parsedBlock of parsed.system.blocks) {
    const simulinkType = parsedBlock.BlockType
    const libreSimType = SIMULINK_TO_LIBRESIM[simulinkType] || 'subsystem'
    const blockName = parsedBlock.Name || `Block_${blocks.length}`

    const position = parsePosition(parsedBlock.Position)
    const parameters = convertBlockParameters(parsedBlock, libreSimType)
    const { inputPorts, outputPorts } = createPorts(libreSimType, parameters)

    const block: BlockInstance = {
      id: crypto.randomUUID?.() || `block_${Date.now()}_${blocks.length}`,
      type: libreSimType,
      name: blockName,
      position,
      parameters,
      inputPorts,
      outputPorts,
    }

    blocks.push(block)
    blockMap.set(blockName, block)
  }

  // Convert connections (lines)
  for (const line of parsed.system.lines) {
    const srcBlockName = line.SrcBlock
    const dstBlockName = line.DstBlock
    const srcBlock = blockMap.get(srcBlockName)
    const dstBlock = blockMap.get(dstBlockName)

    if (srcBlock && dstBlock) {
      // Port numbers in Simulink are 1-indexed
      const srcPortNum = typeof line.SrcPort === 'number' ? line.SrcPort - 1 : parseInt(String(line.SrcPort)) - 1 || 0
      const dstPortNum = typeof line.DstPort === 'number' ? line.DstPort - 1 : parseInt(String(line.DstPort)) - 1 || 0

      const srcPort = srcBlock.outputPorts[srcPortNum] || srcBlock.outputPorts[0]
      const dstPort = dstBlock.inputPorts[dstPortNum] || dstBlock.inputPorts[0]

      if (srcPort && dstPort) {
        connections.push({
          id: crypto.randomUUID?.() || `conn_${Date.now()}_${connections.length}`,
          sourceBlockId: srcBlock.id,
          sourcePortId: srcPort.id,
          targetBlockId: dstBlock.id,
          targetPortId: dstPort.id,
        })
      }
    }
  }

  // Determine solver
  const solverType = SOLVER_TO_LIBRESIM[parsed.Solver || 'ode4'] || 'rk4'

  // Parse simulation times
  const startTime = parsed.StartTime ? parseFloat(parsed.StartTime) : 0
  const stopTime = parsed.StopTime ? parseFloat(parsed.StopTime) : 10
  const stepSize = parsed.FixedStep ? parseFloat(parsed.FixedStep) : 0.01

  const metadata: ModelMetadata = {
    name: parsed.Name || 'Imported Model',
    description: 'Imported from Simulink MDL file',
    author: '',
    createdAt: new Date().toISOString(),
    modifiedAt: new Date().toISOString(),
    version: '1.0.0',
  }

  return {
    id: crypto.randomUUID?.() || `model_${Date.now()}`,
    metadata,
    blocks,
    connections,
    simulationConfig: {
      solver: solverType,
      startTime: isNaN(startTime) ? 0 : startTime,
      stopTime: isNaN(stopTime) ? 10 : stopTime,
      stepSize: isNaN(stepSize) || stepSize <= 0 ? 0.01 : stepSize,
    },
  }
}

/**
 * Import an MDL file and convert it to a LibreSim Model
 */
export function importMDL(content: string): Model {
  try {
    const parsed = parseMDL(content)
    return convertToModel(parsed)
  } catch (error) {
    console.error('MDL import error:', error)
    throw new Error(`Failed to parse MDL file: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

/**
 * Validate that a string looks like an MDL file
 */
export function isMDLFile(content: string): boolean {
  // Check for Model { at the start (with possible whitespace/comments)
  const trimmed = content.trim()
  return trimmed.startsWith('Model') && trimmed.includes('{')
}
