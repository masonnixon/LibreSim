import type { Model, ModelMetadata } from '../types/model'
import type { BlockInstance, Connection, Port } from '../types/block'
import { blockRegistry } from '../blocks'

// Counter for generating unique IDs when crypto.randomUUID is not available
let idCounter = 0

/**
 * Generate a unique ID for blocks and connections
 */
function generateUniqueId(prefix: string = ''): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  // Fallback: use timestamp + counter to ensure uniqueness
  idCounter++
  return `${prefix}${Date.now()}_${idCounter}_${Math.random().toString(36).substr(2, 9)}`
}

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

  // Math Operations
  'Sum': 'sum',
  'Gain': 'gain',
  'Product': 'product',
  'DotProduct': 'dot_product',
  'Abs': 'abs',
  'Signum': 'sign',
  'Saturate': 'saturation',
  'Saturation': 'saturation',
  'DeadZone': 'dead_zone',
  'Math': 'math_function',
  'Sqrt': 'sqrt',
  'Trigonometry': 'trigonometry',
  'Switch': 'switch',
  'MinMax': 'minmax',
  'Bias': 'bias',
  'UnaryMinus': 'unary_minus',
  'Fcn': 'fcn',

  // Signal routing
  'Mux': 'mux',
  'Demux': 'demux',
  'Selector': 'selector',
  'Reshape': 'reshape',
  'BusCreator': 'bus_creator',
  'BusSelector': 'bus_selector',
  'Merge': 'merge',
  'Goto': 'goto',
  'From': 'from',
  'DataTypeConversion': 'data_type_conversion',

  // Signal Processing
  'RateLimiter': 'rate_limiter',
  'Quantizer': 'quantizer',

  // Nonlinear
  'Relay': 'relay',
  'Lookup': 'lookup_table_1d',
  'Lookup_n-D': 'lookup_table_nd',
  'Lookup2D': 'lookup_table_2d',
  'Backlash': 'backlash',

  // Subsystems and ports
  'SubSystem': 'subsystem',
  'Subsystem': 'subsystem',
  'Inport': 'inport',
  'Outport': 'outport',
  'EnablePort': 'enable_port',
  'TriggerPort': 'trigger_port',
  'ActionPort': 'action_port',

  // References (library blocks)
  'Reference': 'reference',

  // Logic and comparison
  'Logic': 'logic',
  'RelationalOperator': 'relational_operator',
  'Compare To Constant': 'compare_to_constant',
  'Compare To Zero': 'compare_to_zero',

  // Memory/state
  'Memory': 'memory',
  'DataStoreMemory': 'data_store_memory',
  'DataStoreRead': 'data_store_read',
  'DataStoreWrite': 'data_store_write',

  // Matrix operations
  'Concatenate': 'concatenate',
  'Assignment': 'assignment',
  'Permute Dimensions': 'permute_dimensions',
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

    // Skip comments (% to end of line)
    if (content[i] === '%') {
      while (i < len && content[i] !== '\n') {
        i++
      }
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

    // Handle square bracket arrays as a single token [1, 2, 3]
    if (content[i] === '[') {
      let arr = '['
      i++
      let depth = 1
      while (i < len && depth > 0) {
        if (content[i] === '[') depth++
        else if (content[i] === ']') depth--
        arr += content[i]
        i++
      }
      tokens.push(arr)
      continue
    }

    // Handle identifiers and numbers
    let token = ''
    while (i < len && !/[\s{}"[\]]/.test(content[i])) {
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

  function parseObject(depth: number = 0): Record<string, unknown> {
    const obj: Record<string, unknown> = {}
    const debugPrefix = '  '.repeat(depth)

    while (pos < tokens.length && tokens[pos] !== '}') {
      const key = tokens[pos]
      pos++

      if (tokens[pos] === '{') {
        pos++ // skip {

        // Check if this is an array of objects (like Block, Line, System, Branch, Port, Annotation, Array, Object)
        // Also handle special Simulink config objects that should be skipped
        const arrayElements = ['Block', 'Line', 'System', 'Branch', 'Port', 'Annotation', 'Array', 'Object']
        if (arrayElements.includes(key)) {
          const arrayKey = key.toLowerCase() + 's' // blocks, lines, systems, branchs, ports, annotations, arrays, objects
          if (!obj[arrayKey]) {
            obj[arrayKey] = []
          }
          const parsed = parseObject(depth + 1)
          if (key === 'Block' && depth <= 2) {
            console.log(`${debugPrefix}[MDL Parse] Adding Block: "${parsed.Name}" (type: ${parsed.BlockType})`)
          } else if (depth <= 2) {
            console.log(`${debugPrefix}[MDL Parse] Adding ${key} to ${arrayKey} array`)
          }
          ;(obj[arrayKey] as unknown[]).push(parsed)
        } else if (key.startsWith('$')) {
          // Skip special properties (e.g., $ObjectID, $BackupClass)
          if (depth <= 2) console.log(`${debugPrefix}[MDL Parse] SKIPPING $ property: "${key}"`)
          parseObject(depth + 1) // Parse but discard
        } else if (key.includes('.') && (key.includes('CC') || key.includes('ConfigSet') || key.includes('AUTOSARPro'))) {
          // Skip Simulink configuration objects that end in CC (e.g., Simulink.SolverCC, Simulink.DataIOCC)
          // or are ConfigSet objects - these are configuration, not block data
          if (depth <= 2) console.log(`${debugPrefix}[MDL Parse] SKIPPING config object: "${key}"`)
          parseObject(depth + 1) // Parse but discard
        } else if (key === 'Simulink.BlockDiagram' || key === 'BlockDiagram') {
          // Simulink.BlockDiagram contains the main diagram data - extract its contents
          if (depth <= 2) console.log(`${debugPrefix}[MDL Parse] Parsing BlockDiagram: "${key}"`)
          const bdContent = parseObject(depth + 1)
          // Merge BlockDiagram contents into current object
          if (bdContent.systems) {
            if (!obj.systems) obj.systems = []
            ;(obj.systems as unknown[]).push(...(bdContent.systems as unknown[]))
          }
          if (bdContent.blocks) {
            if (!obj.blocks) obj.blocks = []
            ;(obj.blocks as unknown[]).push(...(bdContent.blocks as unknown[]))
          }
        } else {
          if (depth <= 2) console.log(`${debugPrefix}[MDL Parse] Parsing nested object: "${key}"`)
          obj[key] = parseObject(depth + 1)
        }
        pos++ // skip }
      } else if (tokens[pos] !== '{' && tokens[pos] !== '}') {
        // Skip special properties starting with $ (e.g., $ObjectID, $BackupClass)
        if (!key.startsWith('$')) {
          obj[key] = parseValue(tokens[pos])
        }
        pos++
      } else if (tokens[pos] === '}') {
        // Unexpected closing brace without a value - this key has no value
        // This can happen with empty objects or special syntax
        if (depth <= 2) console.log(`${debugPrefix}[MDL Parse] Key "${key}" has no value (closing brace)`)
      }
    }

    return obj
  }

  // Find Model { or Library { (libraries are block collections that can also be imported)
  let fileType: 'Model' | 'Library' | null = null
  while (pos < tokens.length) {
    if (tokens[pos] === 'Model' || tokens[pos] === 'Library') {
      fileType = tokens[pos] as 'Model' | 'Library'
      break
    }
    pos++
  }

  if (!fileType) {
    throw new Error('Invalid MDL format: Model or Library block not found')
  }

  pos++ // skip 'Model' or 'Library'

  if (tokens[pos] === '{') {
    pos++ // skip {
    const modelObj = parseObject()

    console.log('[MDL Parse] Top-level keys:', Object.keys(modelObj))

    // Extract system information
    const systems = (modelObj.systems as Record<string, unknown>[]) || []
    console.log('[MDL Parse] Number of systems found:', systems.length)

    const mainSystem = systems[0] || {}
    console.log('[MDL Parse] Main system keys:', Object.keys(mainSystem))

    // Log all systems' block counts
    systems.forEach((sys, i) => {
      const sysBlocks = (sys.blocks as ParsedBlock[]) || []
      console.log(`[MDL Parse] System ${i} name: "${sys.Name}", blocks: ${sysBlocks.length}`)
    })

    // For libraries, collect all top-level subsystem blocks as the main content
    // Check both mainSystem and modelObj for blocks (different MDL versions structure differently)
    let blocks = (mainSystem.blocks as ParsedBlock[]) || []
    let lines = (mainSystem.lines as ParsedLine[]) || []

    // Also check if blocks are directly in the model object (some formats)
    if (blocks.length === 0 && modelObj.blocks) {
      blocks = modelObj.blocks as ParsedBlock[]
      console.log('[MDL Parse] Using blocks from model object instead of system')
    }

    console.log('[MDL Parse] Blocks found in main system:', blocks.length)
    if (blocks.length > 0) {
      console.log('[MDL Parse] Block details:')
      blocks.forEach((b, i) => {
        console.log(`  [${i}] Name: "${b.Name}", Type: "${b.BlockType}"`)
      })
    }
    console.log('[MDL Parse] Lines found in main system:', lines.length)

    // Debug: Check if there are Arrays that might contain blocks
    if (modelObj.arrays) {
      console.log('[MDL Parse] Found arrays:', (modelObj.arrays as unknown[]).length)
    }

    // Debug: Check for blocks directly in model object (some formats)
    if (modelObj.blocks) {
      console.log('[MDL Parse] Found blocks directly in model:', (modelObj.blocks as unknown[]).length)
    }

    return {
      Name: modelObj.Name as string || (fileType === 'Library' ? 'Imported Library' : 'Imported Model'),
      StartTime: modelObj.StartTime as string,
      StopTime: modelObj.StopTime as string,
      Solver: modelObj.Solver as string,
      FixedStep: modelObj.FixedStep as string,
      system: {
        Name: mainSystem.Name as string || 'Main',
        blocks,
        lines,
      }
    }
  }

  throw new Error('Invalid MDL format: Could not parse file structure')
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

    case 'mux':
      if (block.Inputs !== undefined) params.numInputs = parseValue(String(block.Inputs))
      break

    case 'demux':
      if (block.Outputs !== undefined) params.numOutputs = parseValue(String(block.Outputs))
      break

    case 'math_function':
      if (block.Operator !== undefined) params.operator = String(block.Operator)
      break

    case 'reshape':
      if (block.OutputDimensionality !== undefined) params.outputDimensionality = String(block.OutputDimensionality)
      if (block.OutputDimensions !== undefined) params.outputDimensions = String(block.OutputDimensions)
      break

    case 'selector':
      if (block.IndexMode !== undefined) params.indexMode = String(block.IndexMode)
      if (block.Indices !== undefined) params.indices = parseValue(String(block.Indices))
      break

    case 'logic':
      if (block.Operator !== undefined) params.operator = String(block.Operator)
      if (block.Inputs !== undefined) params.numInputs = parseValue(String(block.Inputs))
      break

    case 'relational_operator':
      if (block.Operator !== undefined) params.operator = String(block.Operator)
      break

    case 'reference':
      // Library reference blocks - capture the source block path
      if (block.SourceBlock !== undefined) params.sourceBlock = String(block.SourceBlock)
      if (block.SourceType !== undefined) params.sourceType = String(block.SourceType)
      break

    case 'memory':
      if (block.InitialCondition !== undefined) params.initialCondition = parseValue(String(block.InitialCondition))
      break

    case 'concatenate':
      if (block.NumInputs !== undefined) params.numInputs = parseValue(String(block.NumInputs))
      if (block.Mode !== undefined) params.mode = String(block.Mode)
      break

    case 'unary_minus':
      // No special parameters needed
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

  // Handle blocks not in registry but with known port configurations
  const inputPorts: Port[] = []
  const outputPorts: Port[] = []

  switch (blockType) {
    case 'mux': {
      const numInputs = typeof params.numInputs === 'number' ? params.numInputs : parseInt(String(params.numInputs)) || 4
      for (let i = 0; i < numInputs; i++) {
        inputPorts.push({
          id: `in_${i}`,
          name: `in${i + 1}`,
          dataType: 'double',
          dimensions: [1],
        })
      }
      outputPorts.push({ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] })
      break
    }

    case 'demux': {
      const numOutputs = typeof params.numOutputs === 'number' ? params.numOutputs : parseInt(String(params.numOutputs)) || 4
      inputPorts.push({ id: 'in_0', name: 'in', dataType: 'double', dimensions: [1] })
      for (let i = 0; i < numOutputs; i++) {
        outputPorts.push({
          id: `out_${i}`,
          name: `out${i + 1}`,
          dataType: 'double',
          dimensions: [1],
        })
      }
      break
    }

    case 'dot_product':
      inputPorts.push({ id: 'in_0', name: 'in1', dataType: 'double', dimensions: [1] })
      inputPorts.push({ id: 'in_1', name: 'in2', dataType: 'double', dimensions: [1] })
      outputPorts.push({ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] })
      break

    case 'reshape':
    case 'math_function':
    case 'sqrt':
    case 'unary_minus':
    case 'data_type_conversion':
    case 'memory':
      inputPorts.push({ id: 'in_0', name: 'in', dataType: 'double', dimensions: [1] })
      outputPorts.push({ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] })
      break

    case 'selector':
      inputPorts.push({ id: 'in_0', name: 'in', dataType: 'double', dimensions: [1] })
      outputPorts.push({ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] })
      break

    case 'logic': {
      const numInputs = typeof params.numInputs === 'number' ? params.numInputs : parseInt(String(params.numInputs)) || 2
      for (let i = 0; i < numInputs; i++) {
        inputPorts.push({
          id: `in_${i}`,
          name: `in${i + 1}`,
          dataType: 'double',
          dimensions: [1],
        })
      }
      outputPorts.push({ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] })
      break
    }

    case 'relational_operator':
      inputPorts.push({ id: 'in_0', name: 'in1', dataType: 'double', dimensions: [1] })
      inputPorts.push({ id: 'in_1', name: 'in2', dataType: 'double', dimensions: [1] })
      outputPorts.push({ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] })
      break

    case 'concatenate': {
      const numInputs = typeof params.numInputs === 'number' ? params.numInputs : parseInt(String(params.numInputs)) || 2
      for (let i = 0; i < numInputs; i++) {
        inputPorts.push({
          id: `in_${i}`,
          name: `in${i + 1}`,
          dataType: 'double',
          dimensions: [1],
        })
      }
      outputPorts.push({ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] })
      break
    }

    case 'inport':
      // Inport has no inputs, only an output
      outputPorts.push({ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] })
      break

    case 'outport':
      // Outport has no outputs, only an input
      inputPorts.push({ id: 'in_0', name: 'in', dataType: 'double', dimensions: [1] })
      break

    case 'reference':
    case 'subsystem': {
      // For references and subsystems, use numInputs/numOutputs from Ports parameter
      const numInputs = typeof params.numInputs === 'number' ? params.numInputs : parseInt(String(params.numInputs)) || 1
      const numOutputs = typeof params.numOutputs === 'number' ? params.numOutputs : parseInt(String(params.numOutputs)) || 1
      for (let i = 0; i < numInputs; i++) {
        inputPorts.push({
          id: `in_${i}`,
          name: `in${i + 1}`,
          dataType: 'double',
          dimensions: [1],
        })
      }
      for (let i = 0; i < numOutputs; i++) {
        outputPorts.push({
          id: `out_${i}`,
          name: `out${i + 1}`,
          dataType: 'double',
          dimensions: [1],
        })
      }
      break
    }

    default:
      // Default: 1 input, 1 output
      inputPorts.push({ id: 'in_0', name: 'in', dataType: 'double', dimensions: [1] })
      outputPorts.push({ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] })
  }

  return { inputPorts, outputPorts }
}

/**
 * Recursively convert a parsed system (blocks and lines) to LibreSim format
 */
function convertSystem(
  parsedBlocks: ParsedBlock[],
  parsedLines: ParsedLine[],
  idPrefix: string = ''
): { blocks: BlockInstance[]; connections: Connection[] } {
  const blockMap = new Map<string, BlockInstance>()
  const blocks: BlockInstance[] = []
  const connections: Connection[] = []
  let blockCounter = 0
  let connCounter = 0

  // Convert blocks
  for (const parsedBlock of parsedBlocks) {
    const simulinkType = parsedBlock.BlockType
    const libreSimType = SIMULINK_TO_LIBRESIM[simulinkType]
    if (!libreSimType) {
      console.warn(`[MDL Import] Unknown Simulink block type: "${simulinkType}" - defaulting to subsystem`)
    }
    const finalType = libreSimType || 'subsystem'
    const blockName = parsedBlock.Name || `Block_${blockCounter}`

    const position = parsePosition(parsedBlock.Position)
    const parameters = convertBlockParameters(parsedBlock, finalType)

    // Handle Ports parameter for subsystems and references
    // Ports format in MDL: [numInputs, numOutputs] or [numInputs]
    if ((finalType === 'subsystem' || finalType === 'reference') && parsedBlock.Ports !== undefined) {
      const ports = parsedBlock.Ports
      if (Array.isArray(ports)) {
        parameters.numInputs = ports[0] || 0
        parameters.numOutputs = ports[1] || 0
      } else if (typeof ports === 'string') {
        const match = ports.match(/\[?\s*(\d+)\s*,?\s*(\d*)\s*\]?/)
        if (match) {
          parameters.numInputs = parseInt(match[1]) || 0
          parameters.numOutputs = parseInt(match[2]) || 0
        }
      }
    }

    const { inputPorts, outputPorts } = createPorts(finalType, parameters)

    const blockId = generateUniqueId(`${idPrefix}block_`)
    const block: BlockInstance = {
      id: blockId,
      type: finalType,
      name: blockName,
      position,
      parameters,
      inputPorts,
      outputPorts,
    }

    // Check for nested System inside this block (for subsystems)
    const nestedSystems = parsedBlock.systems as Record<string, unknown>[] | undefined
    if (nestedSystems && nestedSystems.length > 0 && finalType === 'subsystem') {
      const nestedSystem = nestedSystems[0]
      const nestedBlocks = (nestedSystem.blocks as ParsedBlock[]) || []
      const nestedLines = (nestedSystem.lines as ParsedLine[]) || []

      if (nestedBlocks.length > 0) {
        // Recursively convert nested system
        const { blocks: childBlocks, connections: childConns } = convertSystem(
          nestedBlocks,
          nestedLines,
          `${blockId}_`
        )
        block.children = childBlocks
        block.childConnections = childConns

        // Update port counts based on actual Inport/Outport blocks found
        const inportCount = childBlocks.filter(b => b.type === 'inport').length
        const outportCount = childBlocks.filter(b => b.type === 'outport').length
        if (inportCount > 0 || outportCount > 0) {
          // Regenerate ports based on actual inport/outport blocks
          block.inputPorts = []
          block.outputPorts = []
          for (let i = 0; i < inportCount; i++) {
            block.inputPorts.push({
              id: `in_${i}`,
              name: `in${i + 1}`,
              dataType: 'double',
              dimensions: [1],
            })
          }
          for (let i = 0; i < outportCount; i++) {
            block.outputPorts.push({
              id: `out_${i}`,
              name: `out${i + 1}`,
              dataType: 'double',
              dimensions: [1],
            })
          }
        }
      }
    }

    blocks.push(block)
    blockMap.set(blockName, block)
  }

  // Helper function to create a connection
  function createConnection(
    srcBlockName: string,
    srcPortNum: number,
    dstBlockName: string,
    dstPortNum: number
  ) {
    const srcBlock = blockMap.get(srcBlockName)
    const dstBlock = blockMap.get(dstBlockName)

    if (!srcBlock) {
      console.warn(`[MDL Import] Connection source block not found: "${srcBlockName}"`)
      return
    }
    if (!dstBlock) {
      console.warn(`[MDL Import] Connection destination block not found: "${dstBlockName}"`)
      return
    }

    const srcPort = srcBlock.outputPorts[srcPortNum] || srcBlock.outputPorts[0]
    const dstPort = dstBlock.inputPorts[dstPortNum] || dstBlock.inputPorts[0]

    if (!srcPort) {
      console.warn(`[MDL Import] Source port ${srcPortNum} not found on block "${srcBlockName}" (type: ${srcBlock.type}, has ${srcBlock.outputPorts.length} output ports)`)
      return
    }
    if (!dstPort) {
      console.warn(`[MDL Import] Destination port ${dstPortNum} not found on block "${dstBlockName}" (type: ${dstBlock.type}, has ${dstBlock.inputPorts.length} input ports)`)
      return
    }

    connections.push({
      id: generateUniqueId(`${idPrefix}conn_`),
      sourceBlockId: srcBlock.id,
      sourcePortId: srcPort.id,
      targetBlockId: dstBlock.id,
      targetPortId: dstPort.id,
    })
  }

  // Helper to process branches recursively
  function processBranches(
    branches: Array<Record<string, unknown>> | undefined,
    srcBlockName: string,
    srcPortNum: number
  ) {
    if (!branches) return

    for (const branch of branches) {
      const dstBlockName = branch.DstBlock as string
      const dstPort = branch.DstPort as number | string

      if (dstBlockName) {
        const dstPortNum = typeof dstPort === 'number' ? dstPort - 1 : parseInt(String(dstPort)) - 1 || 0
        createConnection(srcBlockName, srcPortNum, dstBlockName, dstPortNum)
      }

      // Handle nested branches (branching from a branch)
      const nestedBranches = branch.branchs as Array<Record<string, unknown>> | undefined
      if (nestedBranches) {
        processBranches(nestedBranches, srcBlockName, srcPortNum)
      }
    }
  }

  // Convert connections (lines)
  for (const line of parsedLines) {
    const srcBlockName = line.SrcBlock
    const srcPort = line.SrcPort
    const srcPortNum = typeof srcPort === 'number' ? srcPort - 1 : parseInt(String(srcPort)) - 1 || 0

    // Check if this line has branches (one source to multiple destinations)
    const branches = (line as Record<string, unknown>).branchs as Array<Record<string, unknown>> | undefined

    if (branches && branches.length > 0) {
      // Process all branches from this source
      processBranches(branches, srcBlockName, srcPortNum)
    } else if (line.DstBlock) {
      // Direct connection (no branching)
      const dstPortNum = typeof line.DstPort === 'number' ? line.DstPort - 1 : parseInt(String(line.DstPort)) - 1 || 0
      createConnection(srcBlockName, srcPortNum, line.DstBlock, dstPortNum)
    }
  }

  return { blocks, connections }
}

/**
 * Convert parsed MDL to LibreSim Model
 */
function convertToModel(parsed: ParsedModel): Model {
  const { blocks, connections } = convertSystem(
    parsed.system.blocks,
    parsed.system.lines
  )

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
    id: generateUniqueId('model_'),
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
    console.log('[MDL Import] Parsed model name:', parsed.Name)
    console.log('[MDL Import] Parsed system blocks count:', parsed.system.blocks.length)
    console.log('[MDL Import] Block names:', parsed.system.blocks.map(b => b.Name))
    console.log('[MDL Import] Block types:', parsed.system.blocks.map(b => b.BlockType))
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
  // Check for Model { or Library { at the start (with possible whitespace/comments)
  const trimmed = content.trim()
  return (trimmed.startsWith('Model') || trimmed.startsWith('Library')) && trimmed.includes('{')
}
