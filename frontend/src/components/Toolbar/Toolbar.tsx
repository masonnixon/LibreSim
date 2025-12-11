import { useRef, useCallback, ChangeEvent } from 'react'
import { useModelStore } from '../../store/modelStore'
import { useSimulationStore } from '../../store/simulationStore'
import { useUIStore } from '../../store/uiStore'
import { api } from '../../api/client'
import type { Model } from '../../types/model'

export function Toolbar() {
  const { model, isDirty, createNewModel, saveModel, loadModel } = useModelStore()
  const { state: simState, setStatus, setProgress, setResults, setError, clearResults } = useSimulationStore()
  const {
    toggleProperties,
    toggleSimulation,
    showProperties,
    showSimulation,
    setShowSimulation,
  } = useUIStore()

  const pollingRef = useRef<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const importInputRef = useRef<HTMLInputElement>(null)

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

  const handleOpen = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      const text = await file.text()
      const modelData = JSON.parse(text) as Model

      // Validate basic model structure
      if (!modelData.blocks || !modelData.connections) {
        throw new Error('Invalid model file: missing blocks or connections')
      }

      // Ensure required fields exist
      if (!modelData.id) {
        modelData.id = crypto.randomUUID?.() || Date.now().toString()
      }
      if (!modelData.metadata) {
        modelData.metadata = {
          name: file.name.replace(/\.(json|mdl)$/i, ''),
          description: '',
          author: '',
          createdAt: new Date().toISOString(),
          modifiedAt: new Date().toISOString(),
          version: '1.0.0',
        }
      }
      if (!modelData.simulationConfig) {
        modelData.simulationConfig = {
          solver: 'rk4',
          startTime: 0,
          stopTime: 10,
          stepSize: 0.01,
        }
      }

      loadModel(modelData)
    } catch (error) {
      console.error('Failed to load model:', error)
      alert(`Failed to load model: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }

    // Reset the input so the same file can be selected again
    event.target.value = ''
  }

  const handleImport = () => {
    importInputRef.current?.click()
  }

  const handleImportChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      const text = await file.text()

      // Check if it's a JSON file (LibreSim format)
      if (file.name.endsWith('.json')) {
        const modelData = JSON.parse(text) as Model
        if (!modelData.id) {
          modelData.id = crypto.randomUUID?.() || Date.now().toString()
        }
        loadModel(modelData)
      }
      // Check if it's an MDL file (Simulink format)
      else if (file.name.endsWith('.mdl')) {
        // For now, show a message that MDL import is coming
        // In the future, this would parse the MDL format
        alert('Simulink MDL import is a work in progress. For now, please use LibreSim JSON format.')
      }
      else {
        alert('Unsupported file format. Please use .json or .mdl files.')
      }
    } catch (error) {
      console.error('Failed to import model:', error)
      alert(`Failed to import: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }

    event.target.value = ''
  }

  const handleExport = () => {
    if (!model) return

    const dataStr = JSON.stringify(model, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)

    const a = document.createElement('a')
    a.href = url
    a.download = `${model.metadata.name || 'model'}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
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

      {/* Hidden file inputs */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleFileChange}
        className="hidden"
      />
      <input
        ref={importInputRef}
        type="file"
        accept=".json,.mdl"
        onChange={handleImportChange}
        className="hidden"
      />

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
          onClick={handleOpen}
          className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors"
          title="Open Model (JSON)"
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
          onClick={handleExport}
          disabled={!model}
          className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Export Model as JSON"
        >
          Export
        </button>
        <button
          onClick={handleImport}
          className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors"
          title="Import Simulink MDL or JSON"
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
