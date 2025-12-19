export type SolverType = 'euler' | 'rk4' | 'merson'

export interface SimulationConfig {
  solver: SolverType
  startTime: number
  stopTime: number
  stepSize: number
  maxStep?: number
  minStep?: number
  relativeTolerance?: number
  absoluteTolerance?: number
}

export type SimulationStatus =
  | 'idle'
  | 'compiling'
  | 'running'
  | 'paused'
  | 'completed'
  | 'error'

export interface SimulationState {
  status: SimulationStatus
  currentTime: number
  progress: number
  error?: string
}

export interface SignalData {
  blockId: string
  portId: string
  name: string
  times: number[]
  values: number[] | number[][]  // Single array for single-input, array of arrays for multi-input
  inputNames?: string[]  // Names for each input trace (for legend)
  numInputs?: number  // Number of inputs (1 for single-input scopes)
}

export interface SimulationResults {
  signals: SignalData[]
  statistics: {
    totalSteps: number
    executionTime: number
    finalTime: number
  }
}
