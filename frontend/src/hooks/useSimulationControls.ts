import { useCallback, useRef } from 'react'
import { api } from '../api/client'
import { useSimulationStore } from '../store/simulationStore'
import type { Model } from '../types/model'
import { toast } from '../components/Toast/Toast'

export interface UseSimulationControlsOptions {
  model: Model | null
  onInteractionEnd: () => void
}

export function getSimulationErrorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === 'object') {
    const apiError = error as { response?: { data?: { detail?: string } }; message?: string }
    if (apiError.response?.data?.detail) return apiError.response.data.detail
    if (apiError.message) return apiError.message
  }
  return fallback
}

export function useSimulationControls({
  model,
  onInteractionEnd,
}: UseSimulationControlsOptions) {
  const {
    state: simState,
    setStatus,
    setProgress,
    setResults,
    setError,
    clearResults,
    stepModeActive,
    stepHistorySize,
    setStepModeActive,
    setStepHistorySize,
  } = useSimulationStore()
  const pollingRef = useRef<number | null>(null)

  const stopPolling = useCallback(function () {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  const startPolling = useCallback(function () {
    pollingRef.current = window.setInterval(async function () {
      try {
        const status = await api.getSimulationStatus()
        setProgress(status.currentTime || 0, status.progress || 0)

        if (status.status === 'completed') {
          stopPolling()
          setStatus('completed')
          setResults(await api.getSimulationResults())
        } else if (status.status === 'error') {
          stopPolling()
          const errorMessage = status.error || 'Simulation failed'
          setError(errorMessage)
          toast.warning('Simulation Error', errorMessage)
        } else if (status.status === 'idle') {
          stopPolling()
          setStatus('idle')
        }
      } catch (error) {
        console.error('Failed to get simulation status:', error)
      }
    }, 100)
  }, [setError, setProgress, setResults, setStatus, stopPolling])

  async function handleRun() {
    if (!model) return

    try {
      clearResults()
      setStatus('running')
      await api.startSimulation(model, model.simulationConfig)
      startPolling()
    } catch (error) {
      console.error('Failed to start simulation:', error)
      setError(getSimulationErrorMessage(error, 'Failed to start simulation'))
    }
    onInteractionEnd()
  }

  async function handleStop() {
    try {
      stopPolling()
      await api.stopSimulation()
      setStatus('idle')
      setStepModeActive(false)
    } catch (error) {
      console.error('Failed to stop simulation:', error)
    }
    onInteractionEnd()
  }

  async function handleReset() {
    try {
      stopPolling()
      const result = await api.resetSimulation()
      if (result.success) {
        clearResults()
        setStatus('idle')
        setStepModeActive(false)
        setStepHistorySize(0)
        setProgress(0, 0)
        toast.info('Reset', 'Simulation reset to initial state')
      }
    } catch (error) {
      console.error('Failed to reset simulation:', error)
      clearResults()
      setStatus('idle')
      setStepModeActive(false)
      setStepHistorySize(0)
      setProgress(0, 0)
    }
    onInteractionEnd()
  }

  async function handlePause() {
    try {
      await api.pauseSimulation()
      setStatus('paused')
      try {
        setResults(await api.getSimulationResults())
      } catch (error) {
        console.error('Failed to fetch paused results:', error)
      }
    } catch (error) {
      console.error('Failed to pause simulation:', error)
    }
    onInteractionEnd()
  }

  async function handleResume() {
    if (stepModeActive) {
      try {
        await api.continueFromStepMode()
        setStepModeActive(false)
        setStatus('running')
        startPolling()
      } catch (error) {
        console.error('Failed to resume from step mode:', error)
        setStepModeActive(true)
        setStatus('paused')
      }
    } else {
      try {
        await api.resumeSimulation()
        setStatus('running')
      } catch (error) {
        console.error('Failed to resume simulation:', error)
      }
    }
    onInteractionEnd()
  }

  async function handleInitStepMode() {
    if (!model) return

    try {
      clearResults()
      setStatus('compiling')
      const result = await api.initStepMode(model, model.simulationConfig)
      if (result.success) {
        setStepModeActive(true)
        setStepHistorySize(1)
        setStatus('paused')
        setProgress(result.currentTime, 0)
        toast.success('Step Mode', 'Simulation ready. Use step buttons to advance.')
      }
    } catch (error) {
      console.error('Failed to initialize step mode:', error)
      setStatus('error')
      setStepModeActive(false)
      setError(getSimulationErrorMessage(error, 'Failed to initialize step mode'))
    }
  }

  async function handleStepForward() {
    if (!stepModeActive) {
      if (simState.status === 'paused') {
        try {
          stopPolling()
          const result = await api.enterStepMode()
          if (result.success) {
            setStepModeActive(true)
            setProgress(result.currentTime, result.progress)
            setStepHistorySize(result.historySize)
            toast.info('Step Mode', `Entered step mode at t=${result.currentTime.toFixed(3)}s`)
          }
        } catch (error) {
          console.error('Failed to enter step mode:', error)
          return
        }
      } else {
        await handleInitStepMode()
        return
      }
    }

    try {
      const result = await api.stepForward(1)
      if (result.success) {
        setProgress(result.currentTime, result.progress)
        setStepHistorySize(result.historySize)
        try {
          setResults(await api.getSimulationResults())
        } catch (error) {
          console.error('Failed to fetch step results:', error)
        }
        if (result.completed) {
          setStatus('completed')
          toast.info('Step Mode', 'Simulation completed.')
        }
      }
    } catch (error) {
      console.error('Failed to step forward:', error)
    }
  }

  async function handleStepBackward() {
    if (!stepModeActive) return

    try {
      const result = await api.stepBackward(1)
      if (result.success) {
        setProgress(result.currentTime, result.progress)
        setStepHistorySize(result.historySize)
        try {
          setResults(await api.getSimulationResults())
        } catch (error) {
          console.error('Failed to fetch step results:', error)
        }
      } else {
        toast.info('Step Mode', 'Cannot step backward - at beginning.')
      }
    } catch (error) {
      console.error('Failed to step backward:', error)
    }
  }

  return {
    simState,
    clearResults,
    stepModeActive,
    stepHistorySize,
    isRunning: simState.status === 'running',
    isPaused: simState.status === 'paused',
    isCompleted: simState.status === 'completed',
    handleRun,
    handleStop,
    handleReset,
    handlePause,
    handleResume,
    handleStepForward,
    handleStepBackward,
  }
}
