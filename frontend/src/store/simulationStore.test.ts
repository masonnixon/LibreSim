import { describe, it, expect, beforeEach } from 'vitest'
import { useSimulationStore } from './simulationStore'
import type { SimulationResults, SignalData } from '../types/simulation'

describe('useSimulationStore', () => {
  // Reset store before each test
  beforeEach(() => {
    useSimulationStore.setState({
      state: {
        status: 'idle',
        currentTime: 0,
        progress: 0,
      },
      results: null,
      wsConnected: false,
    })
  })

  describe('initial state', () => {
    it('has correct initial values', () => {
      const state = useSimulationStore.getState()
      expect(state.state.status).toBe('idle')
      expect(state.state.currentTime).toBe(0)
      expect(state.state.progress).toBe(0)
      expect(state.results).toBeNull()
      expect(state.wsConnected).toBe(false)
    })
  })

  describe('status management', () => {
    it('sets status to running', () => {
      useSimulationStore.getState().setStatus('running')
      expect(useSimulationStore.getState().state.status).toBe('running')
    })

    it('sets status to completed', () => {
      useSimulationStore.getState().setStatus('completed')
      expect(useSimulationStore.getState().state.status).toBe('completed')
    })

    it('sets status to error', () => {
      useSimulationStore.getState().setStatus('error')
      expect(useSimulationStore.getState().state.status).toBe('error')
    })
  })

  describe('progress management', () => {
    it('sets progress and current time', () => {
      useSimulationStore.getState().setProgress(5.5, 0.55)

      const state = useSimulationStore.getState().state
      expect(state.currentTime).toBe(5.5)
      expect(state.progress).toBe(0.55)
    })

    it('updates progress multiple times', () => {
      const { setProgress } = useSimulationStore.getState()

      setProgress(1, 0.1)
      setProgress(5, 0.5)
      setProgress(10, 1.0)

      const state = useSimulationStore.getState().state
      expect(state.currentTime).toBe(10)
      expect(state.progress).toBe(1.0)
    })
  })

  describe('error management', () => {
    it('sets error with message', () => {
      useSimulationStore.getState().setError('Simulation failed')

      const state = useSimulationStore.getState().state
      expect(state.status).toBe('error')
      expect(state.error).toBe('Simulation failed')
    })

    it('clears error', () => {
      useSimulationStore.getState().setError('Some error')
      useSimulationStore.getState().clearError()

      expect(useSimulationStore.getState().state.error).toBeUndefined()
    })
  })

  describe('results management', () => {
    it('sets results', () => {
      const results: SimulationResults = {
        signals: [
          {
            blockId: 'block-1',
            name: 'Scope1',
            portId: 'in-0',
            times: [0, 1, 2],
            values: [0, 1, 2],
          },
        ],
        statistics: {
          totalSteps: 100,
          executionTime: 0.5,
          finalTime: 10,
        },
      }

      useSimulationStore.getState().setResults(results)

      expect(useSimulationStore.getState().results).toEqual(results)
    })

    it('clears results', () => {
      useSimulationStore.getState().setResults({
        signals: [],
        statistics: { totalSteps: 0, executionTime: 0, finalTime: 0 },
      })

      useSimulationStore.getState().clearResults()

      expect(useSimulationStore.getState().results).toBeNull()
    })

    it('adds signal data to empty results', () => {
      const signal: SignalData = {
        blockId: 'block-1',
        name: 'Scope1',
        portId: 'in-0',
        times: [0, 1],
        values: [0, 1],
      }

      useSimulationStore.getState().addSignalData(signal)

      const results = useSimulationStore.getState().results
      expect(results).toBeDefined()
      expect(results!.signals).toHaveLength(1)
      expect(results!.signals[0]).toEqual(signal)
    })

    it('adds signal data to existing results', () => {
      const signal1: SignalData = {
        blockId: 'block-1',
        name: 'Scope1',
        portId: 'in-0',
        times: [0, 1],
        values: [0, 1],
      }
      const signal2: SignalData = {
        blockId: 'block-2',
        name: 'Scope2',
        portId: 'in-0',
        times: [0, 1],
        values: [2, 3],
      }

      useSimulationStore.getState().addSignalData(signal1)
      useSimulationStore.getState().addSignalData(signal2)

      const results = useSimulationStore.getState().results
      expect(results!.signals).toHaveLength(2)
    })

    it('appends data to existing signal', () => {
      const signal: SignalData = {
        blockId: 'block-1',
        name: 'Scope1',
        portId: 'in-0',
        times: [0, 1],
        values: [0, 1],
      }

      useSimulationStore.getState().addSignalData(signal)
      useSimulationStore.getState().appendSignalData('block-1', 'in-0', 2, 2)

      const results = useSimulationStore.getState().results
      expect(results!.signals[0].times).toEqual([0, 1, 2])
      expect(results!.signals[0].values).toEqual([0, 1, 2])
    })

    it('does not append data when results are null', () => {
      useSimulationStore.getState().appendSignalData('block-1', 'in-0', 0, 0)

      // Should not throw and results should remain null
      expect(useSimulationStore.getState().results).toBeNull()
    })

    it('does not append data when signal is not found', () => {
      const signal: SignalData = {
        blockId: 'block-1',
        name: 'Scope1',
        portId: 'in-0',
        times: [0],
        values: [0],
      }

      useSimulationStore.getState().addSignalData(signal)
      useSimulationStore.getState().appendSignalData('block-2', 'in-0', 1, 1)

      // Original signal should be unchanged
      const results = useSimulationStore.getState().results
      expect(results!.signals[0].times).toEqual([0])
      expect(results!.signals[0].values).toEqual([0])
    })
  })

  describe('WebSocket connection', () => {
    it('sets WebSocket connected state', () => {
      useSimulationStore.getState().setWsConnected(true)
      expect(useSimulationStore.getState().wsConnected).toBe(true)

      useSimulationStore.getState().setWsConnected(false)
      expect(useSimulationStore.getState().wsConnected).toBe(false)
    })
  })

  describe('reset', () => {
    it('resets all state to initial values', () => {
      // Set up some state
      useSimulationStore.getState().setStatus('running')
      useSimulationStore.getState().setProgress(5, 0.5)
      useSimulationStore.getState().setResults({
        signals: [],
        statistics: { totalSteps: 100, executionTime: 1, finalTime: 10 },
      })

      // Reset
      useSimulationStore.getState().reset()

      const state = useSimulationStore.getState()
      expect(state.state.status).toBe('idle')
      expect(state.state.currentTime).toBe(0)
      expect(state.state.progress).toBe(0)
      expect(state.results).toBeNull()
    })
  })
})
