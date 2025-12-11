export type BlockCategory =
  | 'sources'
  | 'sinks'
  | 'continuous'
  | 'discrete'
  | 'math'
  | 'routing'
  | 'subsystems'
  | 'signal_processing'
  | 'nonlinear'
  | 'observers'

export type DataType = 'double' | 'single' | 'int32' | 'boolean' | 'bus'

export interface Port {
  id: string
  name: string
  dataType: DataType
  dimensions: number[]
}

export interface ParameterDefinition {
  name: string
  type: 'number' | 'string' | 'boolean' | 'select' | 'array'
  default: unknown
  label: string
  description?: string
  options?: { value: string; label: string }[]
  min?: number
  max?: number
  step?: number
}

export interface BlockDefinition {
  type: string
  category: BlockCategory
  name: string
  description: string
  inputs: Omit<Port, 'id'>[]
  outputs: Omit<Port, 'id'>[]
  parameters: ParameterDefinition[]
  icon?: string
}

export interface BlockInstance {
  id: string
  type: string
  name: string
  position: { x: number; y: number }
  parameters: Record<string, unknown>
  inputPorts: Port[]
  outputPorts: Port[]
  // For Subsystem blocks only
  children?: BlockInstance[]
  childConnections?: Connection[]
  isExpanded?: boolean
}

export interface Connection {
  id: string
  sourceBlockId: string
  sourcePortId: string
  targetBlockId: string
  targetPortId: string
}
