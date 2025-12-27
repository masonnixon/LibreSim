import type { Model, ModelMetadata } from '../types/model'
import type { BlockInstance, Connection, Port } from '../types/block'
import type {
  Library,
  LibraryBlockDefinition,
  LibraryBlockImplementation,
  LibraryPortMapping,
} from '../types/library'
import { blockRegistry } from '../blocks'

/**
 * Global registry of library blocks for cross-library reference resolution.
 * Maps "libraryName/blockName" paths to their BlockInstance implementations.
 */
const globalLibraryRegistry = new Map<string, BlockInstance>()

/**
 * Register a library's blocks in the global registry for cross-library reference resolution.
 * Call this after importing a library so its blocks can be referenced by other libraries.
 *
 * Blocks are registered under both the full library name (e.g., "quaternionLib_2009b/Quaternion")
 * and the normalized name without version suffix (e.g., "quaternionLib/Quaternion").
 *
 * @param libraryName - The name of the library (e.g., "quaternionLib_2009b")
 * @param blocks - Array of subsystem BlockInstance objects from the library
 */
export function registerLibraryBlocks(libraryName: string, blocks: BlockInstance[]): void {
  // Normalize the library name by removing version suffix (e.g., "_2009b" -> "")
  const normalizedName = libraryName.replace(/_\d+[a-z]*$/i, '')
  const hasVersionSuffix = normalizedName !== libraryName

  console.log(`[MDL Registry] Registering ${blocks.length} blocks from library "${libraryName}"${hasVersionSuffix ? ` (also as "${normalizedName}")` : ''}`)

  blocks.forEach(block => {
    // Register under the full name
    const fullPath = `${libraryName}/${block.name}`
    globalLibraryRegistry.set(fullPath, block)

    // Also register under the normalized name if different
    if (hasVersionSuffix) {
      const normalizedPath = `${normalizedName}/${block.name}`
      globalLibraryRegistry.set(normalizedPath, block)
      console.log(`[MDL Registry]   Registered: ${fullPath} (and ${normalizedPath})`)
    } else {
      console.log(`[MDL Registry]   Registered: ${fullPath}`)
    }
  })
}

/**
 * Unregister all blocks from a library.
 *
 * @param libraryName - The name of the library to unregister
 */
export function unregisterLibraryBlocks(libraryName: string): void {
  // Also remove normalized name entries
  const normalizedName = libraryName.replace(/_\d+[a-z]*$/i, '')
  const prefixes = [libraryName, normalizedName].filter((v, i, a) => a.indexOf(v) === i).map(n => `${n}/`)

  const keysToDelete: string[] = []
  globalLibraryRegistry.forEach((_, key) => {
    if (prefixes.some(p => key.startsWith(p))) {
      keysToDelete.push(key)
    }
  })
  keysToDelete.forEach(key => globalLibraryRegistry.delete(key))
  console.log(`[MDL Registry] Unregistered ${keysToDelete.length} blocks from library "${libraryName}"`)
}

/**
 * Get a block from the global registry by its path.
 *
 * @param path - The path to the block (e.g., "quaternionLib/Quaternion")
 * @returns The BlockInstance if found, undefined otherwise
 */
export function getRegisteredBlock(path: string): BlockInstance | undefined {
  return globalLibraryRegistry.get(path)
}

/**
 * Clear all registered library blocks.
 */
export function clearLibraryRegistry(): void {
  globalLibraryRegistry.clear()
  console.log('[MDL Registry] Cleared all registered blocks')
}

/**
 * Get all registered library names.
 */
export function getRegisteredLibraryNames(): string[] {
  const names = new Set<string>()
  globalLibraryRegistry.forEach((_, key) => {
    const parts = key.split('/')
    if (parts.length > 0) {
      names.add(parts[0])
    }
  })
  return Array.from(names)
}

/**
 * Interface for dependency analysis results
 */
export interface LibraryDependencies {
  /** External library references found in this library */
  externalReferences: Array<{
    /** The full path of the reference (e.g., "quaternionLib/Quaternion") */
    path: string
    /** The library name (first part of path) */
    libraryName: string
    /** The block name (last part of path) */
    blockName: string
    /** Whether this reference is currently resolvable */
    isResolvable: boolean
  }>
  /** List of unique library names that are required but not available */
  missingLibraries: string[]
  /** List of unique library names that are required and available */
  availableLibraries: string[]
}

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
  // Allow additional properties like branchs
  [key: string]: unknown
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
  // Map of system path names to their content (for nested subsystems)
  systemMap?: Map<string, ParsedSystem>
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

    // Build a map of system names to their content for looking up subsystem internals
    const systemMap = new Map<string, ParsedSystem>()
    systems.forEach((sys, i) => {
      const sysBlocks = (sys.blocks as ParsedBlock[]) || []
      const sysLines = (sys.lines as ParsedLine[]) || []
      const sysName = sys.Name as string || ''
      console.log(`[MDL Parse] System ${i} name: "${sysName}", blocks: ${sysBlocks.length}`)
      if (sysName) {
        systemMap.set(sysName, {
          Name: sysName,
          blocks: sysBlocks,
          lines: sysLines,
        })
      }
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
      },
      systemMap,
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
      // MDL uses various property names for constant value
      if (block.Value !== undefined) params.value = parseValue(String(block.Value))
      else if (block.ConstantValue !== undefined) params.value = parseValue(String(block.ConstantValue))
      else if (block.Constant !== undefined) params.value = parseValue(String(block.Constant))
      // Default to 1 if no value specified (MDL default)
      if (params.value === undefined) {
        console.log('[MDL Import] Constant block properties (no value found):', Object.keys(block))
        params.value = 1 // Default constant value
      }
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
      // MDL uses various property names for port number
      if (block.Port !== undefined) params.portNumber = parseValue(String(block.Port))
      else if (block.PortNumber !== undefined) params.portNumber = parseValue(String(block.PortNumber))
      else if (block.PortNum !== undefined) params.portNumber = parseValue(String(block.PortNum))
      else if (block.Number !== undefined) params.portNumber = parseValue(String(block.Number))
      // Default to 1 if no port number specified
      if (params.portNumber === undefined) {
        console.log(`[MDL Import] ${libreSimType} block "${block.Name}" properties (no port found):`, Object.keys(block))
        params.portNumber = 1 // Default port number
      }
      break

    case 'mux':
      // MDL uses various property names for input count
      if (block.Inputs !== undefined) params.numInputs = parseValue(String(block.Inputs))
      else if (block.NumberOfInputs !== undefined) params.numInputs = parseValue(String(block.NumberOfInputs))
      else if (block.NumInputs !== undefined) params.numInputs = parseValue(String(block.NumInputs))
      // Also check Ports property - Ports [numInputs] for Mux
      if (params.numInputs === undefined && block.Ports !== undefined) {
        const ports = block.Ports
        if (Array.isArray(ports) && ports[0]) {
          params.numInputs = typeof ports[0] === 'number' ? ports[0] : parseInt(String(ports[0])) || 2
        } else if (typeof ports === 'string') {
          const match = ports.match(/\[?\s*(\d+)/)
          if (match) params.numInputs = parseInt(match[1]) || 2
        } else if (typeof ports === 'number') {
          params.numInputs = ports
        }
      }
      break

    case 'demux':
      // MDL uses various property names for output count
      if (block.Outputs !== undefined) params.numOutputs = parseValue(String(block.Outputs))
      else if (block.NumberOfOutputs !== undefined) params.numOutputs = parseValue(String(block.NumberOfOutputs))
      else if (block.NumOutputs !== undefined) params.numOutputs = parseValue(String(block.NumOutputs))
      // Also check Ports property - Ports [numInputs, numOutputs] for Demux
      if (params.numOutputs === undefined && block.Ports !== undefined) {
        const ports = block.Ports
        if (Array.isArray(ports) && ports[1]) {
          params.numOutputs = typeof ports[1] === 'number' ? ports[1] : parseInt(String(ports[1])) || 2
        } else if (typeof ports === 'string') {
          const match = ports.match(/\[?\s*\d+\s*,\s*(\d+)/)
          if (match) params.numOutputs = parseInt(match[1]) || 2
        }
      }
      break

    case 'math_function':
      // MDL Math Function block uses 'Operator' property, LibreSim uses 'function' parameter
      if (block.Operator !== undefined) params.function = String(block.Operator).toLowerCase()
      else if (block.Function !== undefined) params.function = String(block.Function).toLowerCase()
      else if (block.MathFunction !== undefined) params.function = String(block.MathFunction).toLowerCase()
      // Handle exponent parameter for power functions
      if (block.Exponent !== undefined) params.exponent = parseValue(String(block.Exponent))
      else if (block.Power !== undefined) params.exponent = parseValue(String(block.Power))
      // Default to exp function if not specified
      if (params.function === undefined) {
        console.log('[MDL Import] math_function block properties (no function found):', Object.keys(block))
        params.function = 'exp' // Default function
      }
      // Default exponent for power function
      if (params.exponent === undefined && params.function === 'pow') {
        params.exponent = 2
      }
      break

    case 'trigonometry':
      // MDL Trigonometry block uses 'Operator' property, LibreSim uses 'function' parameter
      if (block.Operator !== undefined) params.function = String(block.Operator).toLowerCase()
      else if (block.Function !== undefined) params.function = String(block.Function).toLowerCase()
      // Default to sin function if not specified
      if (params.function === undefined) {
        console.log('[MDL Import] trigonometry block properties (no function found):', Object.keys(block))
        params.function = 'sin' // Default function
      }
      break

    case 'reshape':
      // Handle various property names for reshape parameters
      if (block.OutputDimensionality !== undefined) params.outputDimensionality = String(block.OutputDimensionality)
      else if (block.OutputDimensions !== undefined) params.outputDimensionality = String(block.OutputDimensions)
      // Try multiple property names for output dimensions
      if (block.OutputDimensions !== undefined) params.outputDimensions = parseValue(String(block.OutputDimensions))
      else if (block.OutputSize !== undefined) params.outputDimensions = parseValue(String(block.OutputSize))
      else if (block.Dimensions !== undefined) params.outputDimensions = parseValue(String(block.Dimensions))
      else if (block.Size !== undefined) params.outputDimensions = parseValue(String(block.Size))
      // Provide defaults if not found
      if (params.outputDimensions === undefined) {
        console.log('[MDL Import] reshape block properties (no dimensions found):', Object.keys(block))
        params.outputDimensions = '[1]' // Default output dimensions
      }
      if (params.outputDimensionality === undefined) {
        params.outputDimensionality = '1-D array' // Default dimensionality
      }
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

    // Handle mux with dynamic number of inputs
    if (blockType === 'mux' && params.numInputs) {
      const numInputs = typeof params.numInputs === 'number' ? params.numInputs : parseInt(String(params.numInputs)) || 2
      inputPorts.length = 0
      for (let i = 0; i < numInputs; i++) {
        inputPorts.push({
          id: `in_${i}`,
          name: `in${i + 1}`,
          dataType: 'double',
          dimensions: [1],
        })
      }
      // Update output dimensions to match
      outputPorts.length = 0
      outputPorts.push({
        id: 'out_0',
        name: 'out',
        dataType: 'double',
        dimensions: [numInputs],
      })
    }

    // Handle demux with dynamic number of outputs
    if (blockType === 'demux' && params.numOutputs) {
      const numOutputs = typeof params.numOutputs === 'number' ? params.numOutputs : parseInt(String(params.numOutputs)) || 2
      outputPorts.length = 0
      for (let i = 0; i < numOutputs; i++) {
        outputPorts.push({
          id: `out_${i}`,
          name: `out${i + 1}`,
          dataType: 'double',
          dimensions: [1],
        })
      }
      // Update input dimensions to match
      inputPorts.length = 0
      inputPorts.push({
        id: 'in_0',
        name: 'in',
        dataType: 'double',
        dimensions: [numOutputs],
      })
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

    case 'reshape': {
      inputPorts.push({ id: 'in_0', name: 'in', dataType: 'double', dimensions: [1] })
      // Parse output dimensions from parameters
      // For "Column vector (2-D)" or "1-D array" mode without explicit dimensions,
      // the output dimension should match input (handled by dimension propagation)
      let reshapeDims: number[] = [1]
      const dimMode = String(params.outputDimensionality || '').toLowerCase()

      if (params.outputDimensions) {
        // outputDimensions might already be an array from parseValue, or a string
        if (Array.isArray(params.outputDimensions)) {
          reshapeDims = params.outputDimensions.map((n: unknown) => typeof n === 'number' ? n : parseInt(String(n)) || 1)
        } else {
          const dimStr = String(params.outputDimensions)
          try {
            const parsed = JSON.parse(dimStr)
            if (Array.isArray(parsed) && parsed.every((n: unknown) => typeof n === 'number')) {
              reshapeDims = parsed
            }
          } catch {
            const matches = dimStr.match(/\d+/g)
            if (matches) {
              reshapeDims = matches.map(Number)
            }
          }
        }
      } else if (dimMode.includes('column vector') || dimMode.includes('1-d array')) {
        // For column vector or 1-D array mode without explicit dimensions,
        // use -1 as a marker to indicate "same as input" (dimension propagation will fix it)
        reshapeDims = [-1]
      }

      // Calculate total dimension for vector representation
      // -1 means "inherit from input", which dimension propagation will handle
      const totalDim = reshapeDims[0] === -1 ? -1 : reshapeDims.reduce((a, b) => a * b, 1)
      outputPorts.push({ id: 'out_0', name: 'out', dataType: 'double', dimensions: totalDim === -1 ? [-1] : [totalDim] })
      break
    }

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
 * Get the output dimensions of a block by tracing through connections.
 * This handles subsystems by looking at their Outport blocks.
 * For blocks that pass through signals (like Gain), it traces back to the source.
 */
function getBlockOutputDimensions(
  block: BlockInstance,
  portId: string,
  blockMap: Map<string, BlockInstance>,
  connectionsByTarget: Map<string, Connection>,
  visited: Set<string> = new Set()
): number[] | null {
  // Prevent infinite loops
  const visitKey = `${block.id}:${portId}`
  if (visited.has(visitKey)) {
    return null
  }
  visited.add(visitKey)

  const port = block.outputPorts.find(p => p.id === portId)
  if (!port) return null

  // If this block already has non-default dimensions, use them
  if (port.dimensions && !(port.dimensions.length === 1 && port.dimensions[0] === 1)) {
    return port.dimensions
  }

  // For subsystems, look at the corresponding Outport block inside
  if (block.type === 'subsystem' && block.children) {
    const portIndex = block.outputPorts.findIndex(p => p.id === portId)
    if (portIndex >= 0) {
      // Find the Outport block with matching port number
      const outportBlock = block.children.find(
        b => b.type === 'outport' && ((b.parameters.portNumber as number) || 1) === portIndex + 1
      )
      if (outportBlock && outportBlock.inputPorts.length > 0) {
        // Trace back what's connected to this Outport
        const outportInputPort = outportBlock.inputPorts[0]

        // Build connection map for subsystem's internal connections
        const childConnectionsByTarget = new Map<string, Connection>()
        const childBlockMap = new Map<string, BlockInstance>()
        block.children.forEach(b => childBlockMap.set(b.id, b))
        ;(block.childConnections || []).forEach(conn => {
          childConnectionsByTarget.set(`${conn.targetBlockId}:${conn.targetPortId}`, conn)
        })

        const connKey = `${outportBlock.id}:${outportInputPort.id}`
        const conn = childConnectionsByTarget.get(connKey)
        if (conn) {
          const sourceBlock = childBlockMap.get(conn.sourceBlockId)
          if (sourceBlock) {
            const dims = getBlockOutputDimensions(
              sourceBlock,
              conn.sourcePortId,
              childBlockMap,
              childConnectionsByTarget,
              new Set(visited)
            )
            if (dims) return dims
          }
        }
      }
    }
  }

  // For pass-through blocks (blocks that preserve input dimensions on output),
  // trace back to the source if this block has a single input
  const passThroughTypes = [
    'gain', 'abs', 'sign', 'sqrt', 'unary_minus', 'bias',
    'saturation', 'dead_zone', 'rate_limiter', 'quantizer',
    'relay', 'memory', 'unit_delay', 'integrator', 'derivative',
    'trigonometry', 'math_function', 'data_type_conversion',
    'reshape' // Reshape often preserves total element count, passes through dimensions
  ]

  if (passThroughTypes.includes(block.type) && block.inputPorts.length > 0) {
    // Look for what's connected to the first input
    const inputPort = block.inputPorts[0]
    const connKey = `${block.id}:${inputPort.id}`
    const conn = connectionsByTarget.get(connKey)
    if (conn) {
      const sourceBlock = blockMap.get(conn.sourceBlockId)
      if (sourceBlock) {
        const dims = getBlockOutputDimensions(
          sourceBlock,
          conn.sourcePortId,
          blockMap,
          connectionsByTarget,
          visited
        )
        if (dims) return dims
      }
    }
  }

  return port.dimensions || [1]
}

/**
 * Parse a Constant block value to determine its dimensions.
 * Supports: numbers, arrays like [1,2,3], comma-separated values like 1,2,3
 */
function parseConstantValueDimensions(value: unknown): number[] {
  if (value === null || value === undefined) {
    return [1]
  }

  // Already an array
  if (Array.isArray(value)) {
    return [value.length]
  }

  // String value - parse to determine dimensions
  if (typeof value === 'string') {
    const trimmed = value.trim()

    // Try as simple number first
    if (!isNaN(Number(trimmed)) && trimmed !== '') {
      return [1]
    }

    // Array literal: [1, 2, 3] or [1 2 3]
    if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
      const inner = trimmed.slice(1, -1).trim()
      if (inner) {
        let parts: string[]
        if (inner.includes(',')) {
          parts = inner.split(',').map(p => p.trim()).filter(p => p !== '')
        } else if (inner.includes(';')) {
          parts = inner.split(';').map(p => p.trim()).filter(p => p !== '')
        } else {
          parts = inner.split(/\s+/).filter(p => p !== '')
        }
        if (parts.length > 0 && parts.every(p => !isNaN(Number(p)))) {
          return [parts.length]
        }
      }
    }

    // Comma-separated values without brackets: 1,2,3
    if (trimmed.includes(',')) {
      const parts = trimmed.split(',').map(p => p.trim()).filter(p => p !== '')
      if (parts.length > 1 && parts.every(p => !isNaN(Number(p)))) {
        return [parts.length]
      }
    }
  }

  // Default to scalar
  return [1]
}

/**
 * Propagate signal dimensions through a system.
 * This traces connections to determine output dimensions for blocks like Outports.
 * Exported for use in modelStore when subsystems are created dynamically.
 */
export function propagateDimensions(blocks: BlockInstance[], connections: Connection[]): void {
  // First, recursively propagate dimensions in all nested subsystems (bottom-up)
  blocks.forEach(block => {
    if (block.type === 'subsystem' && block.children && block.childConnections) {
      propagateDimensions(block.children, block.childConnections)
    }
  })

  // Set dimensions for Constant blocks based on their value parameter
  blocks.forEach(block => {
    if (block.type === 'constant' && block.outputPorts.length > 0) {
      const dims = parseConstantValueDimensions(block.parameters.value)
      block.outputPorts[0].dimensions = dims
    }
  })

  // Build maps for this level
  const blockMap = new Map<string, BlockInstance>()
  blocks.forEach(b => blockMap.set(b.id, b))

  const connectionsByTarget = new Map<string, Connection>()
  connections.forEach(conn => {
    const key = `${conn.targetBlockId}:${conn.targetPortId}`
    connectionsByTarget.set(key, conn)
  })

  // Multiple passes to propagate dimensions through the graph
  // This handles chains of blocks where dimensions flow through
  const maxPasses = 10
  for (let pass = 0; pass < maxPasses; pass++) {
    let changed = false

    // For each block, try to determine its output dimensions from its inputs
    blocks.forEach(block => {
      // Update Reshape blocks that have -1 dimensions (inherit from input)
      if (block.type === 'reshape' && block.outputPorts.length > 0) {
        const outputPort = block.outputPorts[0]
        if (outputPort.dimensions && outputPort.dimensions[0] === -1 && block.inputPorts.length > 0) {
          // Get dimensions from input source
          const inputPort = block.inputPorts[0]
          const connKey = `${block.id}:${inputPort.id}`
          const conn = connectionsByTarget.get(connKey)
          if (conn) {
            const sourceBlock = blockMap.get(conn.sourceBlockId)
            if (sourceBlock) {
              const dims = getBlockOutputDimensions(
                sourceBlock,
                conn.sourcePortId,
                blockMap,
                connectionsByTarget
              )
              if (dims && dims[0] !== -1) {
                outputPort.dimensions = [...dims]
                changed = true
              }
            }
          }
        }
      }

      // Update Outport blocks based on what's connected to them
      if (block.type === 'outport' && block.inputPorts.length > 0) {
        const inputPort = block.inputPorts[0]
        const connKey = `${block.id}:${inputPort.id}`
        const conn = connectionsByTarget.get(connKey)

        if (conn) {
          const sourceBlock = blockMap.get(conn.sourceBlockId)
          if (sourceBlock) {
            const dims = getBlockOutputDimensions(
              sourceBlock,
              conn.sourcePortId,
              blockMap,
              connectionsByTarget
            )
            if (dims && JSON.stringify(dims) !== JSON.stringify(inputPort.dimensions)) {
              inputPort.dimensions = [...dims]
              changed = true
            }
          }
        }
      }

      // Update subsystem output ports based on their Outport blocks
      if (block.type === 'subsystem' && block.children) {
        const outportBlocks = block.children.filter(b => b.type === 'outport')
        outportBlocks.forEach(outport => {
          const portNumber = (outport.parameters.portNumber as number) || 1
          const outputPortIndex = portNumber - 1
          if (block.outputPorts[outputPortIndex] && outport.inputPorts[0]) {
            const newDims = outport.inputPorts[0].dimensions || [1]
            const currentDims = block.outputPorts[outputPortIndex].dimensions || [1]
            if (JSON.stringify(newDims) !== JSON.stringify(currentDims)) {
              block.outputPorts[outputPortIndex].dimensions = [...newDims]
              changed = true
            }
          }
        })
      }
    })

    // If nothing changed, we've reached a fixed point
    if (!changed) break
  }
}

/**
 * Recursively convert a parsed system (blocks and lines) to LibreSim format
 *
 * @param parsedBlocks - Array of parsed block objects
 * @param parsedLines - Array of parsed line (connection) objects
 * @param idPrefix - Prefix for generating unique IDs
 * @param systemMap - Map of system path names to their content (for nested subsystems)
 * @param currentPath - Current system path for looking up nested systems
 */
function convertSystem(
  parsedBlocks: ParsedBlock[],
  parsedLines: ParsedLine[],
  idPrefix: string = '',
  systemMap: Map<string, ParsedSystem> = new Map(),
  currentPath: string = ''
): { blocks: BlockInstance[]; connections: Connection[] } {
  const blockMap = new Map<string, BlockInstance>()
  const blocks: BlockInstance[] = []
  const connections: Connection[] = []
  let blockCounter = 0

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

    // Generate block ID first, so we can use it in port IDs
    const blockId = generateUniqueId(`${idPrefix}block_`)

    // Create ports with block ID included in port IDs for proper mapping later
    const { inputPorts: basePorts, outputPorts: baseOutputPorts } = createPorts(finalType, parameters)

    // Update port IDs to include block ID prefix for proper connection mapping
    const inputPorts = basePorts.map((port, idx) => ({
      ...port,
      id: `${blockId}-in-${idx}`,
    }))
    const outputPorts = baseOutputPorts.map((port, idx) => ({
      ...port,
      id: `${blockId}-out-${idx}`,
    }))

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
    // MDL files store all systems as siblings at the top level, linked by path names
    // e.g., "Model/Subsystem1/NestedSub" is a sibling of "Model/Subsystem1" in the systemMap
    if (finalType === 'subsystem') {
      // Build the path for this subsystem's content
      const subsystemPath = currentPath ? `${currentPath}/${blockName}` : blockName
      console.log(`[MDL Import] Looking for subsystem content at path: "${subsystemPath}"`)

      // First check the systemMap for the subsystem's content
      const nestedSystem = systemMap.get(subsystemPath)

      // Also check for nested systems in the block itself (older MDL format or inline subsystems)
      const inlineNestedSystems = parsedBlock.systems as Record<string, unknown>[] | undefined

      if (nestedSystem) {
        console.log(`[MDL Import] Found subsystem "${blockName}" in systemMap with ${nestedSystem.blocks.length} blocks`)
        const nestedBlocks = nestedSystem.blocks || []
        const nestedLines = nestedSystem.lines || []

        if (nestedBlocks.length > 0) {
          // Recursively convert nested system, passing the systemMap and new path
          console.log(`[MDL Import] Converting ${nestedBlocks.length} child blocks for "${blockName}"`)
          const { blocks: childBlocks, connections: childConns } = convertSystem(
            nestedBlocks,
            nestedLines,
            `${blockId}_`,
            systemMap,
            subsystemPath
          )
          block.children = childBlocks
          block.childConnections = childConns
          console.log(`[MDL Import] Subsystem "${blockName}" now has ${childBlocks.length} children`)

          // Update port counts based on actual Inport/Outport blocks found
          const inportCount = childBlocks.filter(b => b.type === 'inport').length
          const outportCount = childBlocks.filter(b => b.type === 'outport').length
          if (inportCount > 0 || outportCount > 0) {
            block.inputPorts = []
            block.outputPorts = []
            for (let i = 0; i < inportCount; i++) {
              block.inputPorts.push({
                id: `${blockId}-in-${i}`,
                name: `in${i + 1}`,
                dataType: 'double',
                dimensions: [1],
              })
            }
            for (let i = 0; i < outportCount; i++) {
              block.outputPorts.push({
                id: `${blockId}-out-${i}`,
                name: `out${i + 1}`,
                dataType: 'double',
                dimensions: [1],
              })
            }
          }
        }
      } else if (inlineNestedSystems && inlineNestedSystems.length > 0) {
        // Fallback: check for inline nested systems (older MDL format)
        console.log(`[MDL Import] Subsystem "${blockName}" has inline systems: ${inlineNestedSystems.length}`)
        const inlineSystem = inlineNestedSystems[0]
        const nestedBlocks = (inlineSystem.blocks as ParsedBlock[]) || []
        const nestedLines = (inlineSystem.lines as ParsedLine[]) || []

        if (nestedBlocks.length > 0) {
          console.log(`[MDL Import] Converting ${nestedBlocks.length} inline child blocks for "${blockName}"`)
          const { blocks: childBlocks, connections: childConns } = convertSystem(
            nestedBlocks,
            nestedLines,
            `${blockId}_`,
            systemMap,
            subsystemPath
          )
          block.children = childBlocks
          block.childConnections = childConns
          console.log(`[MDL Import] Subsystem "${blockName}" now has ${childBlocks.length} children`)

          const inportCount = childBlocks.filter(b => b.type === 'inport').length
          const outportCount = childBlocks.filter(b => b.type === 'outport').length
          if (inportCount > 0 || outportCount > 0) {
            block.inputPorts = []
            block.outputPorts = []
            for (let i = 0; i < inportCount; i++) {
              block.inputPorts.push({
                id: `${blockId}-in-${i}`,
                name: `in${i + 1}`,
                dataType: 'double',
                dimensions: [1],
              })
            }
            for (let i = 0; i < outportCount; i++) {
              block.outputPorts.push({
                id: `${blockId}-out-${i}`,
                name: `out${i + 1}`,
                dataType: 'double',
                dimensions: [1],
              })
            }
          }
        }
      } else {
        console.log(`[MDL Import] No content found for subsystem "${blockName}" (path: "${subsystemPath}")`)
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
    const branches = line.branchs as Array<Record<string, unknown>> | undefined

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
  // Get the main system name for path construction
  const mainSystemName = parsed.system.Name || ''

  const { blocks, connections } = convertSystem(
    parsed.system.blocks,
    parsed.system.lines,
    '',
    parsed.systemMap || new Map(),
    mainSystemName
  )

  // Propagate signal dimensions through the system
  // This ensures subsystem output ports have correct dimensions based on their internal connections
  propagateDimensions(blocks, connections)

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

/**
 * Convert a subsystem BlockInstance to a LibraryBlockDefinition
 */
function subsystemToLibraryBlock(
  block: BlockInstance,
  libraryId: string,
  libraryName: string
): LibraryBlockDefinition {
  // Extract port information from child blocks
  const inports = (block.children || []).filter(b => b.type === 'inport')
  const outports = (block.children || []).filter(b => b.type === 'outport')

  // Sort by port number
  inports.sort((a, b) => {
    const portA = (a.parameters.portNumber as number) || 1
    const portB = (b.parameters.portNumber as number) || 1
    return portA - portB
  })
  outports.sort((a, b) => {
    const portA = (a.parameters.portNumber as number) || 1
    const portB = (b.parameters.portNumber as number) || 1
    return portA - portB
  })

  // Create port mappings
  const portMappings: LibraryPortMapping[] = [
    ...inports.map((inport, index) => ({
      externalPort: {
        name: inport.name || `in${index + 1}`,
        dataType: 'double' as const,
        dimensions: [1],
      },
      internalBlockId: inport.id,
      portNumber: (inport.parameters.portNumber as number) || index + 1,
      direction: 'input' as const,
    })),
    ...outports.map((outport, index) => ({
      externalPort: {
        name: outport.name || `out${index + 1}`,
        dataType: 'double' as const,
        dimensions: [1],
      },
      internalBlockId: outport.id,
      portNumber: (outport.parameters.portNumber as number) || index + 1,
      direction: 'output' as const,
    })),
  ]

  // Build the implementation
  const implementation: LibraryBlockImplementation = {
    blocks: block.children || [],
    connections: block.childConnections || [],
    portMappings,
  }

  // Create input/output definitions for the block interface
  const inputs = inports.map((inport, index) => ({
    name: inport.name || `in${index + 1}`,
    dataType: 'double' as const,
    dimensions: [1],
  }))

  const outputs = outports.map((outport, index) => ({
    name: outport.name || `out${index + 1}`,
    dataType: 'double' as const,
    dimensions: [1],
  }))

  // Generate a unique type name for this library block
  const typeSlug = block.name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '')

  return {
    type: typeSlug,
    category: 'subsystems',
    name: block.name,
    description: `Library block from ${libraryName}`,
    inputs,
    outputs,
    parameters: [],
    icon: '⊡',
    // Library-specific fields
    isLibraryBlock: true,
    libraryId,
    libraryName,
    originalName: block.name,
    implementation,
  }
}

/**
 * Helper function to deep copy a block with new IDs.
 * Used when resolving references to copy the implementation.
 */
function deepCopyBlockWithNewIds(
  sourceBlock: BlockInstance,
  newId: string
): { block: BlockInstance; idMap: Map<string, string>; portIdMap: Map<string, string> } {
  const idMap = new Map<string, string>()
  const portIdMap = new Map<string, string>()

  // Recursively copy children with new IDs
  function copyChildren(children: BlockInstance[] | undefined, parentId: string): BlockInstance[] {
    if (!children) return []

    return children.map(c => {
      const newChildId = `${parentId}__${generateUniqueId('ref_')}`
      idMap.set(c.id, newChildId)

      const newInputPorts = c.inputPorts.map((p, idx) => {
        const newPortId = `${newChildId}-in-${idx}`
        portIdMap.set(p.id, newPortId)
        return { ...p, id: newPortId }
      })

      const newOutputPorts = c.outputPorts.map((p, idx) => {
        const newPortId = `${newChildId}-out-${idx}`
        portIdMap.set(p.id, newPortId)
        return { ...p, id: newPortId }
      })

      // Recursively copy nested children
      const nestedChildren = copyChildren(c.children, newChildId)
      const nestedConnections = (c.childConnections || []).map(conn => ({
        id: `${newChildId}__${generateUniqueId('conn_')}`,
        sourceBlockId: idMap.get(conn.sourceBlockId) || conn.sourceBlockId,
        sourcePortId: portIdMap.get(conn.sourcePortId) || conn.sourcePortId,
        targetBlockId: idMap.get(conn.targetBlockId) || conn.targetBlockId,
        targetPortId: portIdMap.get(conn.targetPortId) || conn.targetPortId,
      }))

      return {
        ...c,
        id: newChildId,
        inputPorts: newInputPorts,
        outputPorts: newOutputPorts,
        children: nestedChildren.length > 0 ? nestedChildren : undefined,
        childConnections: nestedConnections.length > 0 ? nestedConnections : undefined,
      }
    })
  }

  const newChildren = copyChildren(sourceBlock.children, newId)
  const newConnections = (sourceBlock.childConnections || []).map(conn => ({
    id: `${newId}__${generateUniqueId('conn_')}`,
    sourceBlockId: idMap.get(conn.sourceBlockId) || conn.sourceBlockId,
    sourcePortId: portIdMap.get(conn.sourcePortId) || conn.sourcePortId,
    targetBlockId: idMap.get(conn.targetBlockId) || conn.targetBlockId,
    targetPortId: portIdMap.get(conn.targetPortId) || conn.targetPortId,
  }))

  const block: BlockInstance = {
    ...sourceBlock,
    id: newId,
    children: newChildren.length > 0 ? newChildren : undefined,
    childConnections: newConnections.length > 0 ? newConnections : undefined,
    inputPorts: sourceBlock.inputPorts.map((p, idx) => ({ ...p, id: `${newId}-in-${idx}` })),
    outputPorts: sourceBlock.outputPorts.map((p, idx) => ({ ...p, id: `${newId}-out-${idx}` })),
  }

  return { block, idMap, portIdMap }
}

/**
 * Resolve reference blocks within a library by copying the implementation
 * from the referenced subsystem block.
 *
 * This function checks both the local subsystemMap (same library) and the
 * global library registry (cross-library references).
 *
 * @param blocks - Blocks to process
 * @param subsystemMap - Map of block names to blocks within the current library
 * @param libraryName - Name of the current library being imported
 * @param unresolvedRefs - Set to collect unresolved reference paths (optional)
 */
function resolveReferenceBlocks(
  blocks: BlockInstance[],
  subsystemMap: Map<string, BlockInstance>,
  libraryName: string,
  unresolvedRefs: Set<string> = new Set()
): void {
  for (const block of blocks) {
    // Check children for reference blocks
    if (block.children) {
      for (let i = 0; i < block.children.length; i++) {
        const child = block.children[i]
        if (child.type === 'reference' && child.parameters.sourceBlock) {
          // Parse the source block path (e.g., "quaternionLib/Quaternion" or just "Quaternion")
          const sourcePath = String(child.parameters.sourceBlock)
          const parts = sourcePath.split('/')
          const sourceLibraryName = parts.length > 1 ? parts[0] : libraryName
          const targetName = parts[parts.length - 1] // Get the last part (block name)

          console.log(`[MDL Library Import] Resolving reference: ${child.name} -> ${sourcePath}`)

          // Try to find the referenced block
          let referencedBlock: BlockInstance | undefined

          // First, check if it's a local reference (same library)
          if (parts.length === 1 || sourceLibraryName === libraryName) {
            referencedBlock = subsystemMap.get(targetName)
            if (referencedBlock) {
              console.log(`[MDL Library Import] Found local reference: ${targetName}`)
            }
          }

          // If not found locally, check the global registry
          if (!referencedBlock) {
            // Try the full path first
            referencedBlock = globalLibraryRegistry.get(sourcePath)
            if (!referencedBlock && parts.length > 1) {
              // Try normalized path (library name might have different casing or suffix like _2009b)
              // Try common variations
              const variations = [
                sourcePath,
                `${sourceLibraryName}/${targetName}`,
                // Handle version suffixes like quaternionLib_2009b -> quaternionLib
                `${sourceLibraryName.replace(/_\d+[a-z]*$/i, '')}/${targetName}`,
              ]

              for (const variation of variations) {
                referencedBlock = globalLibraryRegistry.get(variation)
                if (referencedBlock) {
                  console.log(`[MDL Library Import] Found external reference via: ${variation}`)
                  break
                }
              }
            }
          }

          if (referencedBlock && referencedBlock.children) {
            console.log(`[MDL Library Import] Resolved reference: ${targetName} with ${referencedBlock.children.length} children`)

            // Deep copy the referenced block with new IDs
            const { block: copiedBlock } = deepCopyBlockWithNewIds(referencedBlock, child.id)

            // Convert reference to subsystem with copied implementation
            const resolvedBlock: BlockInstance = {
              ...child,
              type: 'subsystem',
              children: copiedBlock.children,
              childConnections: copiedBlock.childConnections,
              inputPorts: copiedBlock.inputPorts,
              outputPorts: copiedBlock.outputPorts,
            }
            block.children[i] = resolvedBlock

            // Recursively resolve any references within the newly resolved block
            if (resolvedBlock.children) {
              resolveReferenceBlocks([resolvedBlock], subsystemMap, libraryName, unresolvedRefs)
            }
          } else {
            // Track unresolved reference
            unresolvedRefs.add(sourcePath)
            console.warn(`[MDL Library Import] Could not resolve reference to: ${sourcePath}`)
          }
        }
      }

      // Recursively resolve references in nested subsystems
      resolveReferenceBlocks(block.children, subsystemMap, libraryName, unresolvedRefs)
    }
  }
}

/**
 * Analyze a library's MDL content to detect external dependencies.
 * This can be called before import to check what dependencies are needed.
 *
 * @param content - The MDL file content
 * @returns Dependencies analysis result
 */
export function analyzeLibraryDependencies(content: string): LibraryDependencies {
  const externalReferences: LibraryDependencies['externalReferences'] = []
  const seenPaths = new Set<string>()

  try {
    const parsed = parseMDL(content)
    const libraryName = parsed.Name

    // Scan all blocks for Reference blocks with SourceBlock property
    function scanBlocks(blocks: ParsedBlock[]) {
      for (const block of blocks) {
        if (block.BlockType === 'Reference' && block.SourceBlock) {
          const sourcePath = String(block.SourceBlock).replace(/\n/g, '')
          const parts = sourcePath.split('/')
          const sourceLibraryName = parts.length > 1 ? parts[0] : libraryName

          // Only track external references (different library)
          if (sourceLibraryName !== libraryName && !seenPaths.has(sourcePath)) {
            seenPaths.add(sourcePath)
            const blockName = parts[parts.length - 1]
            const isResolvable = globalLibraryRegistry.has(sourcePath) ||
              globalLibraryRegistry.has(`${sourceLibraryName.replace(/_\d+[a-z]*$/i, '')}/${blockName}`)

            externalReferences.push({
              path: sourcePath,
              libraryName: sourceLibraryName,
              blockName,
              isResolvable,
            })
          }
        }

        // Check nested systems
        if (block.systems) {
          for (const sys of block.systems as Record<string, unknown>[]) {
            if (sys.blocks) {
              scanBlocks(sys.blocks as ParsedBlock[])
            }
          }
        }
      }
    }

    scanBlocks(parsed.system.blocks)

    // Also scan systems in the systemMap
    if (parsed.systemMap) {
      parsed.systemMap.forEach(system => {
        scanBlocks(system.blocks)
      })
    }
  } catch (error) {
    console.error('[MDL Dependency Analysis] Error:', error)
  }

  // Compute missing and available libraries
  const libraryNames = new Set(externalReferences.map(ref => ref.libraryName))
  const missingLibraries: string[] = []
  const availableLibraries: string[] = []

  libraryNames.forEach(name => {
    // Check if this library has any blocks registered
    const hasBlocks = Array.from(globalLibraryRegistry.keys()).some(key =>
      key.startsWith(`${name}/`) || key.startsWith(`${name.replace(/_\d+[a-z]*$/i, '')}/`)
    )
    if (hasBlocks) {
      availableLibraries.push(name)
    } else {
      missingLibraries.push(name)
    }
  })

  return {
    externalReferences,
    missingLibraries,
    availableLibraries,
  }
}

/**
 * Options for importing an MDL library
 */
export interface ImportMDLLibraryOptions {
  /** Source file path for display */
  sourcePath?: string
  /** Whether to register the library's blocks in the global registry after import */
  registerBlocks?: boolean
}

/**
 * Result of importing an MDL library
 */
export interface ImportMDLLibraryResult {
  /** The imported library data */
  library: Omit<Library, 'id' | 'importedAt'>
  /** Subsystem blocks from this library (for registration) */
  subsystemBlocks: BlockInstance[]
  /** List of unresolved reference paths */
  unresolvedReferences: string[]
  /** Dependency analysis */
  dependencies: LibraryDependencies
}

/**
 * Import an MDL file as a library of reusable blocks.
 * This extracts all top-level subsystem blocks as library block definitions.
 *
 * @param content - The MDL file content
 * @param options - Import options
 * @returns Import result with library data and dependency info
 */
export function importMDLAsLibrary(
  content: string,
  options: ImportMDLLibraryOptions = {}
): ImportMDLLibraryResult {
  const { sourcePath, registerBlocks = true } = options

  try {
    const parsed = parseMDL(content)
    const libraryName = parsed.Name || 'Imported Library'

    console.log('[MDL Library Import] Parsed library name:', libraryName)
    console.log('[MDL Library Import] Total blocks in system:', parsed.system.blocks.length)

    // Analyze dependencies first
    const dependencies = analyzeLibraryDependencies(content)
    if (dependencies.missingLibraries.length > 0) {
      console.warn('[MDL Library Import] Missing dependencies:', dependencies.missingLibraries)
    }
    if (dependencies.availableLibraries.length > 0) {
      console.log('[MDL Library Import] Available dependencies:', dependencies.availableLibraries)
    }

    // Get the main system name for path construction
    const mainSystemName = parsed.system.Name || ''

    // Convert all blocks first (to get subsystems with their children)
    const { blocks } = convertSystem(
      parsed.system.blocks,
      parsed.system.lines,
      '',
      parsed.systemMap || new Map(),
      mainSystemName
    )

    // Filter to only subsystem blocks that have children (these are the reusable library blocks)
    const subsystemBlocks = blocks.filter(
      block => block.type === 'subsystem' && block.children && block.children.length > 0
    )

    console.log('[MDL Library Import] Found subsystem blocks:', subsystemBlocks.length)
    subsystemBlocks.forEach(block => {
      console.log(`  - ${block.name}: ${block.children?.length || 0} children`)
    })

    // Build a map of subsystem names to their blocks for reference resolution
    const subsystemMap = new Map<string, BlockInstance>()
    subsystemBlocks.forEach(block => {
      subsystemMap.set(block.name, block)
    })

    // Track unresolved references
    const unresolvedRefs = new Set<string>()

    // Resolve any reference blocks within subsystems
    resolveReferenceBlocks(subsystemBlocks, subsystemMap, libraryName, unresolvedRefs)

    // Register blocks in global registry if requested
    if (registerBlocks) {
      registerLibraryBlocks(libraryName, subsystemBlocks)
    }

    // Temporary library ID for processing (will be replaced by store)
    const tempLibraryId = generateUniqueId('lib_')

    // Convert each subsystem to a LibraryBlockDefinition
    const libraryBlocks: LibraryBlockDefinition[] = subsystemBlocks.map(block =>
      subsystemToLibraryBlock(block, tempLibraryId, libraryName)
    )

    const library: Omit<Library, 'id' | 'importedAt'> = {
      name: libraryName,
      description: `Imported from ${sourcePath || 'MDL file'}`,
      version: '1.0.0',
      sourcePath,
      sourceFormat: 'mdl',
      blocks: libraryBlocks,
    }

    return {
      library,
      subsystemBlocks,
      unresolvedReferences: Array.from(unresolvedRefs),
      dependencies,
    }
  } catch (error) {
    console.error('MDL library import error:', error)
    throw new Error(`Failed to import MDL library: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

/**
 * Legacy function signature for backward compatibility.
 * @deprecated Use importMDLAsLibrary with options object instead.
 */
export function importMDLAsLibraryLegacy(
  content: string,
  sourcePath?: string
): Omit<Library, 'id' | 'importedAt'> {
  const result = importMDLAsLibrary(content, { sourcePath, registerBlocks: true })
  return result.library
}

/**
 * Check if an MDL file contains library content (multiple subsystem blocks)
 */
export function isMDLLibrary(content: string): boolean {
  try {
    const parsed = parseMDL(content)
    // A library typically has multiple top-level subsystem blocks
    const subsystemCount = parsed.system.blocks.filter(
      b => b.BlockType === 'SubSystem' || b.BlockType === 'Subsystem'
    ).length
    return subsystemCount > 1
  } catch {
    return false
  }
}
