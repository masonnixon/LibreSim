import type { Model } from '../types/model'
import type { BlockInstance, Connection } from '../types/block'

// Map LibreSim block types to Simulink BlockTypes
const BLOCK_TYPE_MAP: Record<string, string> = {
  // Sources
  constant: 'Constant',
  step: 'Step',
  ramp: 'Ramp',
  sine_wave: 'Sin',
  pulse_generator: 'DiscretePulseGenerator',
  clock: 'Clock',

  // Sinks
  scope: 'Scope',
  display: 'Display',
  to_workspace: 'ToWorkspace',
  terminator: 'Terminator',

  // Continuous
  integrator: 'Integrator',
  derivative: 'Derivative',
  transfer_function: 'TransferFcn',
  state_space: 'StateSpace',
  pid_controller: 'PID',

  // Discrete
  unit_delay: 'UnitDelay',
  zero_order_hold: 'ZeroOrderHold',
  discrete_integrator: 'DiscreteIntegrator',
  discrete_derivative: 'DiscreteDerivative',
  discrete_transfer_function: 'DiscreteTransferFcn',

  // Math
  sum: 'Sum',
  gain: 'Gain',
  product: 'Product',
  abs: 'Abs',
  sign: 'Signum',
  saturation: 'Saturate',
  dead_zone: 'DeadZone',
  math_function: 'Math',
  trigonometry: 'Trigonometry',
  switch: 'Switch',

  // Signal Processing
  rate_limiter: 'RateLimiter',
  quantizer: 'Quantizer',

  // Nonlinear
  relay: 'Relay',
  lookup_table_1d: 'Lookup',
  lookup_table_2d: 'Lookup2D',

  // Subsystems
  subsystem: 'SubSystem',
  inport: 'Inport',
  outport: 'Outport',
}

// Map solver types
const SOLVER_MAP: Record<string, string> = {
  euler: 'ode1',
  rk2: 'ode2',
  rk4: 'ode4',
  merson: 'ode45',
}

function escapeString(str: string): string {
  return str.replace(/"/g, '\\"')
}

function formatArray(arr: number[]): string {
  return `[${arr.join(' ')}]`
}

function getBlockParameters(block: BlockInstance): string[] {
  const params: string[] = []
  const p = block.parameters

  switch (block.type) {
    case 'constant':
      if (p.value !== undefined) params.push(`Value\t\t      "${p.value}"`)
      break

    case 'step':
      if (p.stepTime !== undefined) params.push(`Time\t\t      "${p.stepTime}"`)
      if (p.initialValue !== undefined) params.push(`Before\t\t      "${p.initialValue}"`)
      if (p.finalValue !== undefined) params.push(`After\t\t      "${p.finalValue}"`)
      break

    case 'ramp':
      if (p.slope !== undefined) params.push(`Slope\t\t      "${p.slope}"`)
      if (p.startTime !== undefined) params.push(`Start\t\t      "${p.startTime}"`)
      if (p.initialOutput !== undefined) params.push(`X0\t\t      "${p.initialOutput}"`)
      break

    case 'sine_wave':
      if (p.amplitude !== undefined) params.push(`Amplitude\t      "${p.amplitude}"`)
      if (p.frequency !== undefined) params.push(`Frequency\t      "${p.frequency}"`)
      if (p.phase !== undefined) params.push(`Phase\t\t      "${p.phase}"`)
      if (p.bias !== undefined) params.push(`Bias\t\t      "${p.bias}"`)
      break

    case 'pulse_generator':
      if (p.amplitude !== undefined) params.push(`Amplitude\t      "${p.amplitude}"`)
      if (p.period !== undefined) params.push(`Period\t\t      "${p.period}"`)
      if (p.dutyCycle !== undefined) params.push(`PulseWidth\t      "${p.dutyCycle}"`)
      break

    case 'scope':
      const numInputs = block.inputPorts?.length || p.numInputs || 1
      params.push(`Ports\t\t      [${numInputs}]`)
      params.push(`NumInputPorts\t      "${numInputs}"`)
      break

    case 'integrator':
      if (p.initialCondition !== undefined) params.push(`InitialCondition      "${p.initialCondition}"`)
      if (p.limitOutput) {
        params.push(`LimitOutput\t      "on"`)
        if (p.upperLimit !== undefined) params.push(`UpperSaturationLimit  "${p.upperLimit}"`)
        if (p.lowerLimit !== undefined) params.push(`LowerSaturationLimit  "${p.lowerLimit}"`)
      }
      break

    case 'derivative':
      if (p.coefficient !== undefined) params.push(`Coefficient\t      "${p.coefficient}"`)
      break

    case 'transfer_function':
      if (p.numerator) params.push(`Numerator\t      "${formatArray(p.numerator as number[])}"`)
      if (p.denominator) params.push(`Denominator\t      "${formatArray(p.denominator as number[])}"`)
      break

    case 'state_space':
      if (p.A) params.push(`A\t\t      "${JSON.stringify(p.A)}"`)
      if (p.B) params.push(`B\t\t      "${JSON.stringify(p.B)}"`)
      if (p.C) params.push(`C\t\t      "${JSON.stringify(p.C)}"`)
      if (p.D) params.push(`D\t\t      "${JSON.stringify(p.D)}"`)
      break

    case 'pid_controller':
      if (p.Kp !== undefined) params.push(`P\t\t      "${p.Kp}"`)
      if (p.Ki !== undefined) params.push(`I\t\t      "${p.Ki}"`)
      if (p.Kd !== undefined) params.push(`D\t\t      "${p.Kd}"`)
      if (p.N !== undefined) params.push(`N\t\t      "${p.N}"`)
      break

    case 'unit_delay':
      if (p.initialCondition !== undefined) params.push(`InitialCondition      "${p.initialCondition}"`)
      if (p.sampleTime !== undefined) params.push(`SampleTime\t      "${p.sampleTime}"`)
      break

    case 'zero_order_hold':
      if (p.sampleTime !== undefined) params.push(`SampleTime\t      "${p.sampleTime}"`)
      break

    case 'sum':
      if (p.signs) params.push(`Inputs\t\t      "${p.signs}"`)
      params.push(`IconShape\t      "round"`)
      break

    case 'gain':
      if (p.gain !== undefined) params.push(`Gain\t\t      "${p.gain}"`)
      break

    case 'product':
      if (p.operations) params.push(`Inputs\t\t      "${p.operations}"`)
      break

    case 'saturation':
      if (p.upperLimit !== undefined) params.push(`UpperLimit\t      "${p.upperLimit}"`)
      if (p.lowerLimit !== undefined) params.push(`LowerLimit\t      "${p.lowerLimit}"`)
      break

    case 'dead_zone':
      if (p.start !== undefined) params.push(`LowerValue\t      "${p.start}"`)
      if (p.end !== undefined) params.push(`UpperValue\t      "${p.end}"`)
      break

    case 'rate_limiter':
      if (p.risingLimit !== undefined) params.push(`RisingSlewLimit\t      "${p.risingLimit}"`)
      if (p.fallingLimit !== undefined) params.push(`FallingSlewLimit      "${p.fallingLimit}"`)
      break

    case 'relay':
      if (p.switchOn !== undefined) params.push(`OnSwitchValue\t      "${p.switchOn}"`)
      if (p.switchOff !== undefined) params.push(`OffSwitchValue\t      "${p.switchOff}"`)
      if (p.outputOn !== undefined) params.push(`OnOutputValue\t      "${p.outputOn}"`)
      if (p.outputOff !== undefined) params.push(`OffOutputValue\t      "${p.outputOff}"`)
      break

    case 'inport':
      if (p.portNumber !== undefined) params.push(`Port\t\t      "${p.portNumber}"`)
      break

    case 'outport':
      if (p.portNumber !== undefined) params.push(`Port\t\t      "${p.portNumber}"`)
      break
  }

  return params
}

function blockToMDL(block: BlockInstance, indent: string = '    '): string {
  const blockType = BLOCK_TYPE_MAP[block.type] || 'SubSystem'
  const pos = block.position
  // Simulink uses [left, top, right, bottom] format
  const width = 60
  const height = 40
  const position = `[${Math.round(pos.x)}, ${Math.round(pos.y)}, ${Math.round(pos.x + width)}, ${Math.round(pos.y + height)}]`

  const lines: string[] = [
    `${indent}Block {`,
    `${indent}  BlockType\t\t      ${blockType}`,
    `${indent}  Name\t\t      "${escapeString(block.name)}"`,
    `${indent}  Position\t\t      ${position}`,
  ]

  // Add block-specific parameters
  const params = getBlockParameters(block)
  for (const param of params) {
    lines.push(`${indent}  ${param}`)
  }

  lines.push(`${indent}}`)
  return lines.join('\n')
}

function connectionToMDL(
  connection: Connection,
  blocks: BlockInstance[],
  indent: string = '    '
): string {
  const sourceBlock = blocks.find(b => b.id === connection.sourceBlockId)
  const targetBlock = blocks.find(b => b.id === connection.targetBlockId)

  if (!sourceBlock || !targetBlock) return ''

  // Determine port numbers (1-indexed in Simulink)
  const srcPortIndex = sourceBlock.outputPorts?.findIndex(p => p.id === connection.sourcePortId) ?? 0
  const dstPortIndex = targetBlock.inputPorts?.findIndex(p => p.id === connection.targetPortId) ?? 0

  const lines: string[] = [
    `${indent}Line {`,
    `${indent}  SrcBlock\t\t      "${escapeString(sourceBlock.name)}"`,
    `${indent}  SrcPort\t\t      ${srcPortIndex + 1}`,
    `${indent}  DstBlock\t\t      "${escapeString(targetBlock.name)}"`,
    `${indent}  DstPort\t\t      ${dstPortIndex + 1}`,
    `${indent}}`,
  ]

  return lines.join('\n')
}

export function modelToMDL(model: Model): string {
  const config = model.simulationConfig
  const solver = SOLVER_MAP[config.solver] || 'ode4'
  const modelName = model.metadata.name.replace(/[^a-zA-Z0-9_]/g, '_') || 'untitled'

  const lines: string[] = [
    'Model {',
    `  Name\t\t\t  "${modelName}"`,
    '  Version\t\t  8.0',
    '  SavedCharacterEncoding  "UTF-8"',
    `  StartTime\t\t  "${config.startTime}"`,
    `  StopTime\t\t  "${config.stopTime}"`,
    '  SolverType\t\t  "Fixed-step"',
    `  Solver\t\t  "${solver}"`,
    `  FixedStep\t\t  "${config.stepSize}"`,
    '',
    '  System {',
    `    Name\t\t    "${modelName}"`,
    '    Location\t\t    [100, 100, 900, 600]',
    '    Open\t\t    on',
    '',
  ]

  // Add blocks
  for (const block of model.blocks) {
    lines.push(blockToMDL(block))
  }

  // Add connections
  for (const connection of model.connections) {
    const lineStr = connectionToMDL(connection, model.blocks)
    if (lineStr) {
      lines.push(lineStr)
    }
  }

  lines.push('  }')
  lines.push('}')

  return lines.join('\n')
}

export function exportModelAsMDL(model: Model): void {
  const mdlContent = modelToMDL(model)
  const blob = new Blob([mdlContent], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)

  const a = document.createElement('a')
  a.href = url
  a.download = `${model.metadata.name.replace(/[^a-zA-Z0-9_-]/g, '_') || 'model'}.mdl`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
