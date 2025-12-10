import { useRef, useCallback } from 'react'
import { useModelStore } from '../../store/modelStore'
import { useSimulationStore } from '../../store/simulationStore'
import { useUIStore } from '../../store/uiStore'
import { api } from '../../api/client'

export function Toolbar() {
  const { model, isDirty, createNewModel, saveModel } = useModelStore()
  const { state: simState, setStatus, setProgress, setResults, setError, clearResults } = useSimulationStore()
  const {
    toggleProperties,
    toggleSimulation,
    showProperties,
    showSimulation,
    openImportModal,
    setShowSimulation,
  } = useUIStore()

  const pollingRef = useRef<number | null>(null)

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  const handleNew = () => {
    const name = prompt('Enter model name:', 'Untitled')
    if (name) {
      createNewModel(name)
    }
  }

  const handleSave = async () => {
    const savedModel = saveModel()
    if (savedModel) {
      try {
        await api.saveModel(savedModel)
      } catch (error) {
        console.error('Failed to save model:', error)
      }
    }
  }

  const handleRun = async () => {
    if (!model) return

    try {
      // Clear previous results and set status to running
      clearResults()
      setStatus('running')

      // Open the Scope panel
      setShowSimulation(true)

      // Start the simulation with the full model
      await api.startSimulation(model, model.simulationConfig)

      // Poll for status and results
      pollingRef.current = window.setInterval(async () => {
        try {
          const status = await api.getSimulationStatus()
          setProgress(status.currentTime || 0, status.progress || 0)

          if (status.status === 'completed') {
            stopPolling()
            setStatus('completed')

            // Fetch final results
            const results = await api.getSimulationResults()
            setResults(results)
          } else if (status.status === 'error') {
            stopPolling()
            setError('Simulation failed')
          } else if (status.status === 'idle') {
            // Simulation was stopped
            stopPolling()
            setStatus('idle')
          }
        } catch (err) {
          console.error('Failed to get simulation status:', err)
        }
      }, 100) // Poll every 100ms
    } catch (error: unknown) {
      console.error('Failed to start simulation:', error)
      // Extract error detail from axios response
      let errorMessage = 'Failed to start simulation'
      if (error && typeof error === 'object') {
        const axiosError = error as { response?: { data?: { detail?: string } }; message?: string }
        if (axiosError.response?.data?.detail) {
          errorMessage = axiosError.response.data.detail
        } else if (axiosError.message) {
          errorMessage = axiosError.message
        }
      }
      setError(errorMessage)
    }
  }

  const handleStop = async () => {
    try {
      stopPolling()
      await api.stopSimulation()
      setStatus('idle')
    } catch (error) {
      console.error('Failed to stop simulation:', error)
    }
  }

  const isRunning = simState.status === 'running'

  return (
    <div className="h-12 bg-editor-surface border-b border-editor-border flex items-center px-4 gap-2">
      {/* Logo/Title */}
      <div className="flex items-center gap-2 pr-4 border-r border-editor-border">
        <span className="font-bold text-lg text-blue-400">LibreSim</span>
      </div>

      {/* File Operations */}
      <div className="flex items-center gap-1 pr-2 border-r border-editor-border">
        <button
          onClick={handleNew}
          className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors"
          title="New Model"
        >
          New
        </button>
        <button
          onClick={() => {}}
          className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors"
          title="Open Model"
        >
          Open
        </button>
        <button
          onClick={handleSave}
          disabled={!model || !isDirty}
          className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Save Model"
        >
          Save{isDirty ? '*' : ''}
        </button>
        <button
          onClick={openImportModal}
          className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors"
          title="Import Simulink MDL"
        >
          Import
        </button>
      </div>

      {/* Simulation Controls */}
      <div className="flex items-center gap-1 pr-2 border-r border-editor-border">
        <button
          onClick={handleRun}
          disabled={!model || isRunning}
          className="px-3 py-1.5 text-sm bg-green-600 hover:bg-green-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
          title="Run Simulation"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
          </svg>
          Run
        </button>
        <button
          onClick={handleStop}
          disabled={!isRunning}
          className="px-3 py-1.5 text-sm bg-red-600 hover:bg-red-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
          title="Stop Simulation"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M5.75 3A1.75 1.75 0 004 4.75v10.5c0 .966.784 1.75 1.75 1.75h8.5A1.75 1.75 0 0016 15.25V4.75A1.75 1.75 0 0014.25 3h-8.5z" />
          </svg>
          Stop
        </button>
      </div>

      {/* Simulation Status */}
      {model && (
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <span
            className={`w-2 h-2 rounded-full ${
              simState.status === 'running'
                ? 'bg-green-500 animate-pulse'
                : simState.status === 'error'
                ? 'bg-red-500'
                : 'bg-gray-500'
            }`}
          />
          <span className="capitalize">{simState.status}</span>
          {isRunning && (
            <span>
              | t = {simState.currentTime.toFixed(3)}s ({Math.round(simState.progress * 100)}%)
            </span>
          )}
        </div>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* View Toggles */}
      <div className="flex items-center gap-1">
        <button
          onClick={toggleProperties}
          className={`px-3 py-1.5 text-sm rounded transition-colors ${
            showProperties ? 'bg-blue-600' : 'hover:bg-editor-border'
          }`}
          title="Toggle Properties Panel"
        >
          Properties
        </button>
        <button
          onClick={toggleSimulation}
          className={`px-3 py-1.5 text-sm rounded transition-colors ${
            showSimulation ? 'bg-blue-600' : 'hover:bg-editor-border'
          }`}
          title="Toggle Simulation Panel"
        >
          Scope
        </button>
      </div>
    </div>
  )
}
