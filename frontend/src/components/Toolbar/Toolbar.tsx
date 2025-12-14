import { useRef, useCallback, ChangeEvent, useState, useEffect } from 'react'
import { useModelStore } from '../../store/modelStore'
import { useSimulationStore } from '../../store/simulationStore'
import { useUIStore } from '../../store/uiStore'
import { api } from '../../api/client'
import { toast } from '../Toast/Toast'
import { exampleList, getExample } from '../../data/examples'
import type { Model } from '../../types/model'

const STORAGE_KEY = 'libresim_last_model'

export function Toolbar() {
  const { model, isDirty, createNewModel, saveModel, loadModel } = useModelStore()
  const { state: simState, setStatus, setProgress, setResults, setError, clearResults } = useSimulationStore()
  const {
    toggleProperties,
    toggleSimulation,
    showProperties,
    showSimulation,
    setShowSimulation,
    sidebarCollapsed,
    toggleSidebar,
  } = useUIStore()

  const pollingRef = useRef<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const importInputRef = useRef<HTMLInputElement>(null)
  const [showExamplesMenu, setShowExamplesMenu] = useState(false)
  const [showMobileMenu, setShowMobileMenu] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  // Check for mobile screen size
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Load last model from localStorage on startup
  useEffect(() => {
    const savedModel = localStorage.getItem(STORAGE_KEY)
    if (savedModel) {
      try {
        const modelData = JSON.parse(savedModel) as Model
        if (modelData.blocks && modelData.connections) {
          loadModel(modelData)
          toast.info('Model Restored', 'Your last session model has been loaded.')
        }
      } catch (e) {
        console.error('Failed to load saved model:', e)
      }
    } else {
      // Create a new blank model if none was saved
      createNewModel('Untitled')
    }
  }, [])

  // Save model to localStorage whenever it changes
  useEffect(() => {
    if (model) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(model))
    }
  }, [model])

  // Close menus when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setShowExamplesMenu(false)
      setShowMobileMenu(false)
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

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
      toast.success('New Model', `Created new model "${name}"`)
    }
    setShowMobileMenu(false)
  }

  const handleOpen = () => {
    fileInputRef.current?.click()
    setShowMobileMenu(false)
  }

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      const text = await file.text()
      const modelData = JSON.parse(text) as Model

      if (!modelData.blocks || !modelData.connections) {
        throw new Error('Invalid model file: missing blocks or connections')
      }

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
      toast.success('Model Opened', `Loaded "${modelData.metadata.name}"`)
    } catch (error) {
      console.error('Failed to load model:', error)
      toast.warning('Load Failed', `${error instanceof Error ? error.message : 'Unknown error'}`)
    }

    event.target.value = ''
  }

  const handleImport = () => {
    importInputRef.current?.click()
    setShowMobileMenu(false)
  }

  const handleImportChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      const text = await file.text()

      if (file.name.endsWith('.json')) {
        const modelData = JSON.parse(text) as Model
        if (!modelData.id) {
          modelData.id = crypto.randomUUID?.() || Date.now().toString()
        }
        loadModel(modelData)
        toast.success('Import Complete', `Imported "${file.name}"`)
      } else if (file.name.endsWith('.mdl')) {
        toast.warning('MDL Import', 'Simulink MDL import is coming soon. Please use JSON format for now.')
      } else {
        toast.warning('Unsupported Format', 'Please use .json or .mdl files.')
      }
    } catch (error) {
      console.error('Failed to import model:', error)
      toast.warning('Import Failed', `${error instanceof Error ? error.message : 'Unknown error'}`)
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

    toast.success('Model Exported', `Saved as "${model.metadata.name || 'model'}.json" to your Downloads folder`)
    setShowMobileMenu(false)
  }

  const handleSave = async () => {
    const savedModel = saveModel()
    if (savedModel) {
      try {
        await api.saveModel(savedModel)
        toast.success(
          'Model Saved',
          'Changes saved to browser storage. Use Export to download as a file.'
        )
      } catch (error) {
        console.error('Failed to save model:', error)
        toast.info(
          'Saved Locally',
          'Model saved to browser storage. Use Export to download as a file.'
        )
      }
    }
    setShowMobileMenu(false)
  }

  const handleLoadExample = (exampleId: string) => {
    const example = getExample(exampleId)
    if (example) {
      loadModel(example)
      toast.success('Example Loaded', `Loaded "${example.metadata.name}"`)
    } else {
      toast.warning('Example Not Found', 'This example is not available yet.')
    }
    setShowExamplesMenu(false)
    setShowMobileMenu(false)
  }

  const handleRun = async () => {
    if (!model) return

    try {
      clearResults()
      setStatus('running')
      setShowSimulation(true)

      await api.startSimulation(model, model.simulationConfig)

      pollingRef.current = window.setInterval(async () => {
        try {
          const status = await api.getSimulationStatus()
          setProgress(status.currentTime || 0, status.progress || 0)

          if (status.status === 'completed') {
            stopPolling()
            setStatus('completed')
            const results = await api.getSimulationResults()
            setResults(results)
          } else if (status.status === 'error') {
            stopPolling()
            setError('Simulation failed')
          } else if (status.status === 'idle') {
            stopPolling()
            setStatus('idle')
          }
        } catch (err) {
          console.error('Failed to get simulation status:', err)
        }
      }, 100)
    } catch (error: unknown) {
      console.error('Failed to start simulation:', error)
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
    setShowMobileMenu(false)
  }

  const handleStop = async () => {
    try {
      stopPolling()
      await api.stopSimulation()
      setStatus('idle')
    } catch (error) {
      console.error('Failed to stop simulation:', error)
    }
    setShowMobileMenu(false)
  }

  const isRunning = simState.status === 'running'

  // Mobile hamburger menu
  const MobileMenu = () => (
    <div className="dropdown-menu right-0 left-auto" onClick={(e) => e.stopPropagation()}>
      <div className="dropdown-item" onClick={handleNew}>New Model</div>
      <div className="dropdown-item" onClick={handleOpen}>Open</div>
      <div className="dropdown-item" onClick={handleSave}>Save</div>
      <div className="dropdown-item" onClick={handleExport}>Export</div>
      <div className="dropdown-item" onClick={handleImport}>Import</div>
      <div className="border-t border-editor-border my-1" />
      <div className="dropdown-item font-medium text-gray-400 text-xs">Examples</div>
      {exampleList.slice(0, 5).map((ex) => (
        <div key={ex.id} className="dropdown-item text-sm" onClick={() => handleLoadExample(ex.id)}>
          {ex.name}
        </div>
      ))}
      <div className="border-t border-editor-border my-1" />
      <div className="dropdown-item" onClick={() => { toggleSidebar(); setShowMobileMenu(false) }}>
        {sidebarCollapsed ? 'Show Blocks' : 'Hide Blocks'}
      </div>
      <div className="dropdown-item" onClick={() => { toggleProperties(); setShowMobileMenu(false) }}>
        {showProperties ? 'Hide Properties' : 'Show Properties'}
      </div>
      <div className="dropdown-item" onClick={() => { toggleSimulation(); setShowMobileMenu(false) }}>
        {showSimulation ? 'Hide Scope' : 'Show Scope'}
      </div>
    </div>
  )

  return (
    <div className="h-12 bg-editor-surface border-b border-editor-border flex items-center px-2 md:px-4 gap-1 md:gap-2">
      {/* Logo/Title */}
      <div className="flex items-center gap-2 pr-2 md:pr-4 border-r border-editor-border">
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

      {/* Desktop Menu */}
      {!isMobile && (
        <>
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

          {/* Examples Menu */}
          <div className="relative pr-2 border-r border-editor-border">
            <button
              onClick={(e) => {
                e.stopPropagation()
                setShowExamplesMenu(!showExamplesMenu)
              }}
              className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors flex items-center gap-1"
              title="Load Example Models"
            >
              Examples
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {showExamplesMenu && (
              <div className="dropdown-menu" onClick={(e) => e.stopPropagation()}>
                <div className="px-3 py-2 text-xs text-gray-400 font-medium border-b border-editor-border">
                  Basic
                </div>
                {exampleList
                  .filter((ex) => ex.category === 'basic')
                  .map((ex) => (
                    <div
                      key={ex.id}
                      className="dropdown-item"
                      onClick={() => handleLoadExample(ex.id)}
                    >
                      <div className="text-sm">{ex.name}</div>
                      <div className="text-xs text-gray-500">{ex.description}</div>
                    </div>
                  ))}
                <div className="px-3 py-2 text-xs text-gray-400 font-medium border-b border-t border-editor-border">
                  Control Systems
                </div>
                {exampleList
                  .filter((ex) => ex.category === 'control')
                  .map((ex) => (
                    <div
                      key={ex.id}
                      className="dropdown-item"
                      onClick={() => handleLoadExample(ex.id)}
                    >
                      <div className="text-sm">{ex.name}</div>
                      <div className="text-xs text-gray-500">{ex.description}</div>
                    </div>
                  ))}
                <div className="px-3 py-2 text-xs text-gray-400 font-medium border-b border-t border-editor-border">
                  Signal Processing
                </div>
                {exampleList
                  .filter((ex) => ex.category === 'signal')
                  .map((ex) => (
                    <div
                      key={ex.id}
                      className="dropdown-item"
                      onClick={() => handleLoadExample(ex.id)}
                    >
                      <div className="text-sm">{ex.name}</div>
                      <div className="text-xs text-gray-500">{ex.description}</div>
                    </div>
                  ))}
              </div>
            )}
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
        </>
      )}

      {/* Mobile Menu */}
      {isMobile && (
        <>
          {/* Mobile Run/Stop Buttons */}
          <div className="flex items-center gap-1 flex-1">
            <button
              onClick={handleRun}
              disabled={!model || isRunning}
              className="p-2 text-sm bg-green-600 hover:bg-green-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Run Simulation"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
              </svg>
            </button>
            <button
              onClick={handleStop}
              disabled={!isRunning}
              className="p-2 text-sm bg-red-600 hover:bg-red-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Stop Simulation"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5.75 3A1.75 1.75 0 004 4.75v10.5c0 .966.784 1.75 1.75 1.75h8.5A1.75 1.75 0 0016 15.25V4.75A1.75 1.75 0 0014.25 3h-8.5z" />
              </svg>
            </button>

            {/* Status indicator */}
            {isRunning && (
              <span className="text-xs text-gray-400 ml-2">
                {Math.round(simState.progress * 100)}%
              </span>
            )}
          </div>

          {/* Hamburger Menu Button */}
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation()
                setShowMobileMenu(!showMobileMenu)
              }}
              className="p-2 hover:bg-editor-border rounded transition-colors"
              title="Menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            {showMobileMenu && <MobileMenu />}
          </div>
        </>
      )}
    </div>
  )
}
