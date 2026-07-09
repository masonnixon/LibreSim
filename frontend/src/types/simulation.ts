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
  maxResultPoints?: number
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
  // 3D Scope specific fields
  x?: number[]
  y?: number[]
  z?: number[]
  is3D?: boolean
}

export type AnalysisType = 'bode' | 'nyquist' | 'pzmap' | 'stepinfo'

export interface AnalysisData {
  analysisType: AnalysisType
  name?: string  // Block name for display
  // Bode-specific
  frequencies?: number[]
  magnitude_db?: number[]
  phase_deg?: number[]
  gain_margin?: number | null
  phase_margin?: number | null
  gain_crossover_freq?: number | null
  phase_crossover_freq?: number | null
  // Nyquist-specific
  real?: number[]
  imag?: number[]
  encirclements?: number
  // Pole-Zero specific
  poles?: [number, number][]
  zeros?: [number, number][]
  is_stable?: boolean
  dominant_pole?: [number, number] | null
  // Step response specific
  times?: number[]
  response?: number[]
  rise_time?: number | null
  settling_time?: number | null
  overshoot_percent?: number | null
  peak_time?: number | null
  peak_value?: number | null
  steady_state_value?: number | null
}

export interface SimulationResults {
  signals: SignalData[]
  analyses?: Record<string, AnalysisData>  // Analysis block data keyed by block ID
  statistics: {
    totalSteps: number
    executionTime: number
    finalTime: number
    decimationFactors?: Record<string, number>
  }
}
