import { useRef, useCallback, ChangeEvent, useState, useEffect } from 'react'
import { useModelStore } from '../../store/modelStore'
import { useSimulationStore } from '../../store/simulationStore'
import { useUIStore } from '../../store/uiStore'
import { useLibraryStore } from '../../store/libraryStore'
import { api } from '../../api/client'
import { toast } from '../Toast/Toast'
import { exampleList, getExample } from '../../data/examples'
import { exportModelAsMDL } from '../../utils/mdlExporter'
import { importMDL, isMDLFile, importMDLAsLibrary } from '../../utils/mdlImporter'
import { blockRegistry } from '../../blocks'
import type { Model } from '../../types/model'
import type { BlockInstance } from '../../types/block'

/**
 * Recursively find all scope block IDs in the model, including inside subsystems.
 * Returns flattened IDs that match backend naming convention.
 */
function findAllScopeBlockIds(blocks: BlockInstance[], parentPath: string = ''): string[] {
  const result: string[] = []
  for (const block of blocks) {
    const flattenedId = parentPath ? `${parentPath}__${block.id}` : block.id
    if (block.type === 'scope' || block.type === 'xy_graph') {
      result.push(flattenedId)
    }
    if (block.type === 'subsystem' && block.children) {
      result.push(...findAllScopeBlockIds(block.children, flattenedId))
    }
  }
  return result
}

const STORAGE_KEY = 'libresim_last_model'

export function Toolbar() {
  const { model, isDirty, createNewModel, saveModel, loadModel } = useModelStore()
  const { state: simState, setStatus, setProgress, setResults, setError, clearResults } = useSimulationStore()
  const {
    toggleProperties,
    showProperties,
    sidebarCollapsed,
    toggleSidebar,
    plotWindows,
    closeAllPlotWindows,
    openPlotWindow,
  } = useUIStore()
  const importLibrary = useLibraryStore((state) => state.importLibrary)

  const pollingRef = useRef<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const importInputRef = useRef<HTMLInputElement>(null)
  const libraryInputRef = useRef<HTMLInputElement>(null)
  const [showExamplesMenu, setShowExamplesMenu] = useState(false)
  const [showExportMenu, setShowExportMenu] = useState(false)
  const [showImportMenu, setShowImportMenu] = useState(false)
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
          closeAllPlotWindows()
          clearResults()
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
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Intentionally run only on mount; store functions are stable
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
      setShowExportMenu(false)
      setShowImportMenu(false)
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
      closeAllPlotWindows()
      clearResults()
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

      closeAllPlotWindows()
      clearResults()
      loadModel(modelData)
      toast.success('Model Opened', `Loaded "${modelData.metadata.name}"`)
    } catch (error) {
      console.error('Failed to load model:', error)
      toast.warning('Load Failed', `${error instanceof Error ? error.message : 'Unknown error'}`)
    }

    event.target.value = ''
  }

  const handleImportModel = () => {
    importInputRef.current?.click()
    setShowImportMenu(false)
    setShowMobileMenu(false)
  }

  const handleImportLibrary = () => {
    libraryInputRef.current?.click()
    setShowImportMenu(false)
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
        closeAllPlotWindows()
        clearResults()
        loadModel(modelData)
        toast.success('Import Complete', `Imported "${file.name}"`)
      } else if (file.name.endsWith('.mdl') || isMDLFile(text)) {
        // Import Simulink MDL file
        const modelData = importMDL(text)
        // Use filename as model name if not set
        if (!modelData.metadata.name || modelData.metadata.name === 'Imported Model') {
          modelData.metadata.name = file.name.replace(/\.mdl$/i, '')
        }
        closeAllPlotWindows()
        clearResults()
        loadModel(modelData)
        toast.success('MDL Import Complete', `Imported "${modelData.metadata.name}" from Simulink format (${modelData.blocks.length} blocks, ${modelData.connections.length} connections)`)
      } else {
        toast.warning('Unsupported Format', 'Please use .json or .mdl files.')
      }
    } catch (error) {
      console.error('Failed to import model:', error)
      toast.warning('Import Failed', `${error instanceof Error ? error.message : 'Unknown error'}`)
    }

    event.target.value = ''
  }

  const handleLibraryImportChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      const text = await file.text()

      if (!isMDLFile(text)) {
        toast.warning('Invalid Format', 'Library import only supports Simulink MDL files.')
        return
      }

      // Parse as library (with new return type that includes dependency info)
      console.group(`[Library Import] Importing: ${file.name}`)
      const importResult = importMDLAsLibrary(text, { sourcePath: file.name, registerBlocks: true })
      const { library: libraryData, unresolvedReferences, dependencies } = importResult

      if (libraryData.blocks.length === 0) {
        console.warn('No subsystem blocks found')
        console.groupEnd()
        toast.warning('No Library Blocks', 'No subsystem blocks found in this MDL file. Import it as a model instead.')
        return
      }

      // Warn about missing dependencies
      if (dependencies.missingLibraries.length > 0) {
        const missingMsg = `This library requires: ${dependencies.missingLibraries.join(', ')}. Import those libraries first for full functionality.`
        console.warn(`Missing Dependencies: ${missingMsg}`)
        toast.warning('Missing Dependencies', missingMsg)
      }

      // Log external references for debugging
      if (dependencies.externalReferences.length > 0) {
        console.log(`External references found: ${dependencies.externalReferences.length}`)
        dependencies.externalReferences.forEach(ref => {
          const status = ref.isResolvable ? '✓' : '✗'
          console.log(`  ${status} ${ref.path}`)
        })
      }

      // Import into library store
      const result = importLibrary(libraryData, { replaceExisting: true })

      if (result.success && result.library) {
        // Register blocks with the block registry
        blockRegistry.registerLibraryBlocks(result.library.blocks)

        // Build success message
        let successMsg = `Imported "${result.library.name}" with ${result.library.blocks.length} reusable blocks`
        if (unresolvedReferences.length > 0) {
          successMsg += ` (${unresolvedReferences.length} unresolved references)`
          console.warn(`Unresolved references: ${unresolvedReferences.join(', ')}`)
        }

        console.log(`Success: ${successMsg}`)
        toast.success('Library Imported', successMsg)

        if (result.warnings.length > 0) {
          result.warnings.forEach((warn) => {
            console.warn(`Warning: ${warn}`)
            toast.info('Note', warn)
          })
        }

        // Show info about resolved cross-library references
        if (dependencies.availableLibraries.length > 0) {
          const depsMsg = `Used blocks from: ${dependencies.availableLibraries.join(', ')}`
          console.log(`Dependencies Resolved: ${depsMsg}`)
          toast.info('Dependencies Resolved', depsMsg)
        }
      } else {
        const errorMsg = result.errors.join(', ')
        console.error(`Failed: ${errorMsg}`)
        toast.warning('Import Failed', errorMsg)
      }
      console.groupEnd()
    } catch (error) {
      console.error('Failed to import library:', error)
      toast.warning('Library Import Failed', `${error instanceof Error ? error.message : 'Unknown error'}`)
    }

    event.target.value = ''
  }

  const handleExportJSON = () => {
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

    toast.success('JSON Exported', `Saved as "${model.metadata.name || 'model'}.json" to your Downloads folder`)
    setShowExportMenu(false)
    setShowMobileMenu(false)
  }

  const handleExportMDL = () => {
    if (!model) return

    try {
      exportModelAsMDL(model)
      toast.success('MDL Exported', `Saved as "${model.metadata.name || 'model'}.mdl" (Simulink format) to your Downloads folder`)
    } catch (error) {
      console.error('Failed to export MDL:', error)
      toast.warning('Export Failed', `${error instanceof Error ? error.message : 'Unknown error'}`)
    }
    setShowExportMenu(false)
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
      closeAllPlotWindows()
      clearResults()
      loadModel(example)
      toast.success('Example Loaded', `Loaded "${example.metadata.name}"`)
    } else {
      toast.warning('Example Not Found', 'This example is not available yet.')
    }
    setShowExamplesMenu(false)
    setShowMobileMenu(false)
  }

  // Track scope blocks for reopening windows (including inside subsystems)
  const scopeBlockIds = model?.blocks ? findAllScopeBlockIds(model.blocks) : []

  const hasOpenPlotWindows = Object.keys(plotWindows).length > 0

  const handleTogglePlotWindows = () => {
    if (hasOpenPlotWindows) {
      closeAllPlotWindows()
    } else {
      // Reopen windows for all scope blocks
      scopeBlockIds.forEach((id, index) => {
        openPlotWindow(id, { x: 20 + index * 40, y: 100 + index * 40 })
      })
    }
  }

  const handleRun = async () => {
    if (!model) return

    try {
      clearResults()
      setStatus('running')

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
            const errorMsg = status.error || 'Simulation failed'
            setError(errorMsg)
            toast.warning('Simulation Error', errorMsg)
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
      <div className="dropdown-item" onClick={handleExportJSON}>Export JSON</div>
      <div className="dropdown-item" onClick={handleExportMDL}>Export MDL (Simulink)</div>
      <div className="dropdown-item" onClick={handleImportModel}>Import Model</div>
      <div className="dropdown-item text-cyan-400" onClick={handleImportLibrary}>Import Library</div>
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
      <div className="dropdown-item" onClick={() => { handleTogglePlotWindows(); setShowMobileMenu(false) }}>
        {hasOpenPlotWindows ? 'Hide Scopes' : 'Show Scopes'}
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
      <input
        ref={libraryInputRef}
        type="file"
        accept=".mdl"
        onChange={handleLibraryImportChange}
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
            <div className="relative">
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setShowExportMenu(!showExportMenu)
                }}
                disabled={!model}
                className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                title="Export Model"
              >
                Export
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {showExportMenu && (
                <div className="dropdown-menu" onClick={(e) => e.stopPropagation()}>
                  <div
                    className="dropdown-item"
                    onClick={handleExportJSON}
                  >
                    <div className="text-sm">Export as JSON</div>
                    <div className="text-xs text-gray-500">LibreSim native format</div>
                  </div>
                  <div
                    className="dropdown-item"
                    onClick={handleExportMDL}
                  >
                    <div className="text-sm">Export as MDL</div>
                    <div className="text-xs text-gray-500">Simulink compatible</div>
                  </div>
                </div>
              )}
            </div>
            <div className="relative">
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setShowImportMenu(!showImportMenu)
                }}
                className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors flex items-center gap-1"
                title="Import Model or Library"
              >
                Import
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {showImportMenu && (
                <div className="dropdown-menu" onClick={(e) => e.stopPropagation()}>
                  <div
                    className="dropdown-item"
                    onClick={handleImportModel}
                  >
                    <div className="text-sm">Import Model</div>
                    <div className="text-xs text-gray-500">JSON or Simulink MDL file</div>
                  </div>
                  <div
                    className="dropdown-item"
                    onClick={handleImportLibrary}
                  >
                    <div className="text-sm">Import Library</div>
                    <div className="text-xs text-cyan-400">Reusable MDL subsystems</div>
                  </div>
                </div>
              )}
            </div>
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
                <div className="px-3 py-2 text-xs text-gray-400 font-medium border-b border-t border-editor-border">
                  Advanced
                </div>
                {exampleList
                  .filter((ex) => ex.category === 'advanced')
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
              {simState.status === 'error' && simState.error && (
                <span className="text-red-400 max-w-xs truncate" title={simState.error}>
                  : {simState.error}
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
              onClick={handleTogglePlotWindows}
              className={`px-3 py-1.5 text-sm rounded transition-colors ${
                hasOpenPlotWindows ? 'bg-blue-600' : 'hover:bg-editor-border'
              }`}
              title={hasOpenPlotWindows ? 'Close All Plot Windows' : 'Open Plot Windows'}
            >
              Scopes {hasOpenPlotWindows ? `(${Object.keys(plotWindows).length})` : ''}
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
