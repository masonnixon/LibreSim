import { create } from 'zustand'
import type {
  SimulationState,
  SimulationResults,
  SignalData,
  SimulationStatus,
} from '../types/simulation'

interface SimulationStoreState {
  // Simulation state
  state: SimulationState
  results: SimulationResults | null

  // WebSocket connection
  wsConnected: boolean

  // Actions
  setStatus: (status: SimulationStatus) => void
  setProgress: (currentTime: number, progress: number) => void
  setError: (error: string) => void
  clearError: () => void

  // Results management
  addSignalData: (signal: SignalData) => void
  appendSignalData: (blockId: string, portId: string, time: number, value: number) => void
  setResults: (results: SimulationResults) => void
  clearResults: () => void

  // Connection state
  setWsConnected: (connected: boolean) => void

  // Reset
  reset: () => void
}

const initialState: SimulationState = {
  status: 'idle',
  currentTime: 0,
  progress: 0,
}

export const useSimulationStore = create<SimulationStoreState>((set, get) => ({
  state: { ...initialState },
  results: null,
  wsConnected: false,

  setStatus: (status: SimulationStatus) => {
    set((state) => ({
      state: { ...state.state, status },
    }))
  },

  setProgress: (currentTime: number, progress: number) => {
    set((state) => ({
      state: { ...state.state, currentTime, progress },
    }))
  },

  setError: (error: string) => {
    set((state) => ({
      state: { ...state.state, status: 'error', error },
    }))
  },

  clearError: () => {
    set((state) => ({
      state: { ...state.state, error: undefined },
    }))
  },

  addSignalData: (signal: SignalData) => {
    const { results } = get()
    if (results) {
      set({
        results: {
          ...results,
          signals: [...results.signals, signal],
        },
      })
    } else {
      set({
        results: {
          signals: [signal],
          statistics: { totalSteps: 0, executionTime: 0, finalTime: 0 },
        },
      })
    }
  },

  appendSignalData: (blockId: string, portId: string, time: number, value: number) => {
    const { results } = get()
    if (!results) return

    const signalIndex = results.signals.findIndex(
      (s) => s.blockId === blockId && s.portId === portId
    )

    if (signalIndex >= 0) {
      const updatedSignals = [...results.signals]
      const signal = updatedSignals[signalIndex]
      // Only append to single-input signals (number[] type)
      const currentValues = signal.values
      if (Array.isArray(currentValues) && (currentValues.length === 0 || typeof currentValues[0] === 'number')) {
        updatedSignals[signalIndex] = {
          ...signal,
          times: [...signal.times, time],
          values: [...(currentValues as number[]), value],
        }
        set({ results: { ...results, signals: updatedSignals } })
      }
    }
  },

  setResults: (results: SimulationResults) => {
    set({ results })
  },

  clearResults: () => {
    set({ results: null })
  },

  setWsConnected: (connected: boolean) => {
    set({ wsConnected: connected })
  },

  reset: () => {
    set({
      state: { ...initialState },
      results: null,
    })
  },
}))
