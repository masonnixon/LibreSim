import { useRef, ChangeEvent, useState, useEffect } from 'react'
import { useModelStore } from '../../store/modelStore'
import { useUIStore } from '../../store/uiStore'
import { useLibraryStore } from '../../store/libraryStore'
import { api } from '../../api/client'
import { toast } from '../Toast/Toast'
import { exampleList, fetchExample } from '../../data/examples'
import { ExamplesModal } from '../Examples/ExamplesModal'
import { CodeGenModal } from '../CodeGen/CodeGenModal'
import { SaveAsModal } from '../SaveAs/SaveAsModal'
import { exportModelAsMDL } from '../../utils/mdlExporter'
import { importMDL, isMDLFile, importMDLAsLibrary } from '../../utils/mdlImporter'
import { blockRegistry } from '../../blocks'
import type { Model } from '../../types/model'
import { findAllScopeBlockIds } from '../../utils/toolbarUtils'
import { useSimulationControls } from '../../hooks/useSimulationControls'

const STORAGE_KEY = 'libresim_last_model'

interface ToolbarProps {
  embed?: boolean
  restoreLastModel?: boolean
}

export function Toolbar({ embed = false, restoreLastModel = true }: ToolbarProps) {
  const { model, isDirty, createNewModel, saveModel, loadModel, undo, redo, canUndo, canRedo } = useModelStore()
  const {
    toggleProperties,
    showProperties,
    sidebarCollapsed,
    toggleSidebar,
    plotWindows,
    closeAllPlotWindows,
    openPlotWindow,
    openSettingsModal,
    openHelpModal,
    showExamplesModal,
    openExamplesModal,
    closeExamplesModal,
    showCodeGenModal,
    openCodeGenModal,
    closeCodeGenModal,
    openSaveAsModal,
  } = useUIStore()
  const importLibrary = useLibraryStore((state) => state.importLibrary)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const importInputRef = useRef<HTMLInputElement>(null)
  const libraryInputRef = useRef<HTMLInputElement>(null)
  const [showExportMenu, setShowExportMenu] = useState(false)
  const [showImportMenu, setShowImportMenu] = useState(false)
  const [showOverflowMenu, setShowOverflowMenu] = useState(false)
  // 'full' (>1024): everything visible
  // 'medium' (768-1024): file ops in menu, sim controls + view toggles visible
  // 'narrow' (<768): only core sim buttons visible, everything else in menu
  const [tier, setTier] = useState<'full' | 'medium' | 'narrow'>(() => {
    const w = window.innerWidth
    return w >= 1440 ? 'full' : w >= 768 ? 'medium' : 'narrow'
  })
  const {
    simState,
    clearResults,
    stepModeActive,
    stepHistorySize,
    isRunning,
    isPaused,
    isCompleted,
    handleRun,
    handleStop,
    handleReset,
    handlePause,
    handleResume,
    handleStepForward,
    handleStepBackward,
  } = useSimulationControls({
    model,
    onInteractionEnd: function () { setShowOverflowMenu(false) },
  })

  // Responsive breakpoint tracking
  useEffect(() => {
    const updateTier = () => {
      const w = window.innerWidth
      setTier(w >= 1440 ? 'full' : w >= 768 ? 'medium' : 'narrow')
    }
    updateTier()
    window.addEventListener('resize', updateTier)
    return () => window.removeEventListener('resize', updateTier)
  }, [])

  // Load last model from localStorage on startup
  useEffect(() => {
    if (!restoreLastModel) return

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
  }, [restoreLastModel])

  // Save model to localStorage whenever it changes
  useEffect(() => {
    if (model && restoreLastModel) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(model))
    }
  }, [model, restoreLastModel])

  // Close menus when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setShowExportMenu(false)
      setShowImportMenu(false)
      setShowOverflowMenu(false)
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])


  const handleNew = () => {
    const name = prompt('Enter model name:', 'Untitled')
    if (name) {
      closeAllPlotWindows()
      clearResults()
      createNewModel(name)
      toast.success('New Model', `Created new model "${name}"`)
    }
    setShowOverflowMenu(false)
  }

  const handleOpen = () => {
    fileInputRef.current?.click()
    setShowOverflowMenu(false)
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
    setShowOverflowMenu(false)
  }

  const handleImportLibrary = () => {
    libraryInputRef.current?.click()
    setShowImportMenu(false)
    setShowOverflowMenu(false)
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
        // Store original filename for tooltip display
        modelData.metadata.sourceFile = file.name
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
    setShowOverflowMenu(false)
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
    setShowOverflowMenu(false)
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
    setShowOverflowMenu(false)
  }

  const handleLoadExample = async (exampleId: string) => {
    closeExamplesModal()
    setShowOverflowMenu(false)

    // Show loading toast
    toast.info('Loading Example', 'Fetching example model...')

    try {
      const example = await fetchExample(exampleId)
      if (example) {
        closeAllPlotWindows()
        clearResults()
        loadModel(example)
        toast.success('Example Loaded', `Loaded "${example.metadata.name}"`)
      } else {
        toast.warning('Example Not Found', 'This example is not available yet.')
      }
    } catch (error) {
      console.error('Failed to load example:', error)
      toast.warning('Load Failed', 'Failed to load the example. Please try again.')
    }
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

  if (embed) {
    return (
      <div className="h-10 bg-editor-surface border-b border-editor-border flex items-center px-3 gap-2">
        <span className="font-bold text-blue-400">LibreSim</span>
        <span className="text-gray-500">|</span>
        <span className="text-gray-300 text-sm truncate min-w-0" title={model?.metadata?.name || 'Untitled'}>
          {model?.metadata?.name || 'Untitled'}
        </span>
        <div className="flex-1" />
        <button
          onClick={handleRun}
          disabled={!model || isRunning}
          className="px-3 py-1 text-sm bg-green-600 hover:bg-green-700 rounded disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Run
        </button>
        <button
          onClick={handleStop}
          disabled={!isRunning && !isPaused && !stepModeActive}
          className="px-3 py-1 text-sm bg-red-600 hover:bg-red-700 rounded disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Stop
        </button>
        <button
          onClick={handleTogglePlotWindows}
          disabled={scopeBlockIds.length === 0}
          className="px-3 py-1 text-sm hover:bg-editor-border rounded disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {hasOpenPlotWindows ? 'Hide Scopes' : 'Scopes'}
        </button>
        <span className="text-xs text-gray-400 capitalize w-16 text-right">{simState.status}</span>
      </div>
    )
  }


  // Overflow menu — contains items that don't fit at the current tier.
  // At 'full': not shown (everything fits).
  // At 'medium': file ops, examples, generate, undo/redo.
  // At 'narrow': all of the above plus sim controls, view toggles, settings, help.
  const OverflowMenu = () => (
    <div className="dropdown-menu right-0 left-auto max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
      {/* File ops — hidden from toolbar at medium and narrow */}
      {tier !== 'full' && (
        <>
          <div className="dropdown-item" onClick={handleNew}>New Model</div>
          <div className="dropdown-item" onClick={handleOpen}>Open</div>
          <div className="dropdown-item" onClick={handleSave}>Save</div>
          <div className="dropdown-item" onClick={handleExportJSON}>Export JSON</div>
          <div className="dropdown-item" onClick={handleExportMDL}>Export MDL (Simulink)</div>
          <div className="dropdown-item" onClick={handleImportModel}>Import Model</div>
          <div className="dropdown-item text-cyan-400" onClick={handleImportLibrary}>Import Library</div>
          <div className="border-t border-editor-border my-1" />
          <div className="dropdown-item" onClick={() => { openExamplesModal(); setShowOverflowMenu(false) }}>
            Browse Examples
          </div>
          <div className="dropdown-item text-purple-400" onClick={() => { openCodeGenModal(); setShowOverflowMenu(false) }}>
            Generate Code
          </div>
          <div className="border-t border-editor-border my-1" />
          <div className="dropdown-item" onClick={() => { undo(); setShowOverflowMenu(false) }}>
            Undo
          </div>
          <div className="dropdown-item" onClick={() => { redo(); setShowOverflowMenu(false) }}>
            Redo
          </div>
        </>
      )}

      {/* Sim controls — hidden from toolbar at narrow */}
      {tier === 'narrow' && (
        <>
          <div className="border-t border-editor-border my-1" />
          {isPaused && (
            <div className="dropdown-item" onClick={() => { handleResume(); setShowOverflowMenu(false) }}>
              Resume
            </div>
          )}
          {isRunning && (
            <div className="dropdown-item" onClick={() => { handlePause(); setShowOverflowMenu(false) }}>
              Pause
            </div>
          )}
          <div className="dropdown-item" onClick={() => { handleStepForward(); setShowOverflowMenu(false) }}>
            {stepModeActive ? 'Step Forward' : 'Enter Step Mode'}
          </div>
          {stepModeActive && (
            <div className="dropdown-item" onClick={() => { handleStepBackward(); setShowOverflowMenu(false) }}>
              Step Backward
            </div>
          )}
          <div className="dropdown-item" onClick={() => { handleReset(); setShowOverflowMenu(false) }}>
            Reset
          </div>
        </>
      )}

      {/* View/panel toggles — only in overflow at narrow */}
      {tier === 'narrow' && (
        <>
          <div className="border-t border-editor-border my-1" />
          <div className="dropdown-item" onClick={() => { toggleSidebar(); setShowOverflowMenu(false) }}>
            {sidebarCollapsed ? 'Show Blocks' : 'Hide Blocks'}
          </div>
          <div className="dropdown-item" onClick={() => { toggleProperties(); setShowOverflowMenu(false) }}>
            {showProperties ? 'Hide Properties' : 'Show Properties'}
          </div>
          <div className="dropdown-item" onClick={() => { handleTogglePlotWindows(); setShowOverflowMenu(false) }}>
            {hasOpenPlotWindows ? 'Hide Scopes' : 'Show Scopes'}
          </div>
          <div className="dropdown-item" onClick={() => { openSettingsModal(); setShowOverflowMenu(false) }}>
            Settings
          </div>
          <div className="dropdown-item" onClick={() => { openHelpModal('shortcuts'); setShowOverflowMenu(false) }}>
            Help & Shortcuts
          </div>
        </>
      )}
    </div>
  )

  return (
    <div className="h-12 bg-editor-surface border-b border-editor-border flex items-center px-2 md:px-4 gap-1 md:gap-2">
      {/* Logo/Title and Model Name */}
      <div className="flex items-center gap-2 pr-2 md:pr-4 border-r border-editor-border shrink-0">
        <span className="font-bold text-lg text-blue-400">LibreSim</span>
        <span className="text-gray-500 hidden sm:inline">|</span>
        <span
          className="text-gray-300 text-sm hidden sm:inline truncate max-w-[200px]"
          title={model?.metadata?.sourceFile || model?.metadata?.name || 'Untitled'}
        >
          {model?.metadata?.name || 'Untitled'}
          {isDirty && <span className="text-yellow-400 ml-1">*</span>}
        </span>
      </div>

      {/* Hidden file inputs */}
      <input ref={fileInputRef} type="file" accept=".json" onChange={handleFileChange} className="hidden" />
      <input ref={importInputRef} type="file" accept=".json,.mdl" onChange={handleImportChange} className="hidden" />
      <input ref={libraryInputRef} type="file" accept=".mdl" onChange={handleLibraryImportChange} className="hidden" />

      {/* === File Operations — full tier only === */}
      {tier === 'full' && (
        <div className="flex items-center gap-1 pr-2 border-r border-editor-border shrink-0">
          <button onClick={handleNew} className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors" title="New Model">New</button>
          <button onClick={handleOpen} className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors" title="Open Model (JSON)">Open</button>
          <button onClick={handleSave} disabled={!model || !isDirty} className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed" title="Save Model">Save{isDirty ? '*' : ''}</button>
          <button onClick={openSaveAsModal} disabled={!model} className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed" title="Save As (choose filename and format)">Save As</button>
          <div className="w-px h-5 bg-editor-border mx-1" />
          <button onClick={undo} disabled={!canUndo()} className="p-1.5 hover:bg-editor-border rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed" title="Undo (Ctrl+Z)">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" /></svg>
          </button>
          <button onClick={redo} disabled={!canRedo()} className="p-1.5 hover:bg-editor-border rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed" title="Redo (Ctrl+Y)">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 10h-10a8 8 0 00-8 8v2M21 10l-6 6m6-6l-6-6" /></svg>
          </button>
          <div className="relative">
            <button onClick={(e) => { e.stopPropagation(); setShowExportMenu(!showExportMenu) }} disabled={!model} className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1" title="Export Model">
              Export
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
            </button>
            {showExportMenu && (
              <div className="dropdown-menu" onClick={(e) => e.stopPropagation()}>
                <div className="dropdown-item" onClick={handleExportJSON}><div className="text-sm">Export as JSON</div><div className="text-xs text-gray-500">LibreSim native format</div></div>
                <div className="dropdown-item" onClick={handleExportMDL}><div className="text-sm">Export as MDL</div><div className="text-xs text-gray-500">Simulink compatible</div></div>
              </div>
            )}
          </div>
          <div className="relative">
            <button onClick={(e) => { e.stopPropagation(); setShowImportMenu(!showImportMenu) }} className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors flex items-center gap-1" title="Import Model or Library">
              Import
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
            </button>
            {showImportMenu && (
              <div className="dropdown-menu" onClick={(e) => e.stopPropagation()}>
                <div className="dropdown-item" onClick={handleImportModel}><div className="text-sm">Import Model</div><div className="text-xs text-gray-500">JSON or Simulink MDL file</div></div>
                <div className="dropdown-item" onClick={handleImportLibrary}><div className="text-sm">Import Library</div><div className="text-xs text-cyan-400">Reusable MDL subsystems</div></div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* === Examples & Generate — full tier only === */}
      {tier === 'full' && (
        <>
          <div className="pr-2 border-r border-editor-border shrink-0">
            <button onClick={openExamplesModal} className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors" title="Load Example Models">Examples</button>
          </div>
          <div className="pr-2 border-r border-editor-border shrink-0">
            <button onClick={openCodeGenModal} disabled={!model} className="px-3 py-1.5 text-sm hover:bg-editor-border rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 text-purple-400 hover:text-purple-300" title="Generate Simulation Code (Python, C, C++, Rust)">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
              Generate
            </button>
          </div>
        </>
      )}

      {/* === Simulation Controls — full and medium tiers show inline === */}
      {tier !== 'narrow' && (
        <div className="flex items-center gap-1 pr-2 border-r border-editor-border shrink-0">
          {(!isRunning && !isPaused && !stepModeActive) ? (
            <button onClick={handleRun} disabled={!model} className="px-3 py-1.5 text-sm bg-green-600 hover:bg-green-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1" title="Run Simulation">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" /></svg>
              Run
            </button>
          ) : (isPaused || stepModeActive) ? (
            <button onClick={handleResume} disabled={!model || isCompleted} className="w-[72px] py-1.5 text-sm bg-green-600 hover:bg-green-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1" title={stepModeActive ? "Continue Running from Current Position" : "Resume Simulation"}>
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" /></svg>
              {stepModeActive ? 'Play' : 'Resume'}
            </button>
          ) : null}
          {isRunning && (
            <button onClick={handlePause} className="px-3 py-1.5 text-sm bg-yellow-600 hover:bg-yellow-700 rounded transition-colors flex items-center gap-1" title="Pause Simulation">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M5.5 3A1.5 1.5 0 004 4.5v11A1.5 1.5 0 005.5 17h2A1.5 1.5 0 009 15.5v-11A1.5 1.5 0 007.5 3h-2zm7 0A1.5 1.5 0 0011 4.5v11a1.5 1.5 0 001.5 1.5h2a1.5 1.5 0 001.5-1.5v-11A1.5 1.5 0 0014.5 3h-2z" clipRule="evenodd" /></svg>
              Pause
            </button>
          )}
          <button onClick={handleStop} disabled={!isRunning && !stepModeActive && !isPaused} className="px-3 py-1.5 text-sm bg-red-600 hover:bg-red-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1" title="Stop Simulation">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M5.75 3A1.75 1.75 0 004 4.75v10.5c0 .966.784 1.75 1.75 1.75h8.5A1.75 1.75 0 0016 15.25V4.75A1.75 1.75 0 0014.25 3h-8.5z" /></svg>
            Stop
          </button>
          <div className="w-px h-5 bg-editor-border mx-1" />
          <button onClick={handleStepBackward} disabled={!model || isRunning || !stepModeActive || stepHistorySize <= 1} className="p-1.5 text-sm hover:bg-editor-border rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed" title="Step Backward">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" /></svg>
          </button>
          <button onClick={handleStepForward} disabled={!model || isRunning || isCompleted} className={`p-1.5 text-sm rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${stepModeActive ? 'bg-blue-600 hover:bg-blue-700' : 'hover:bg-editor-border'}`} title={stepModeActive ? 'Step Forward' : 'Enter Step Mode'}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" /></svg>
          </button>
          <button onClick={handleReset} disabled={!model || isRunning || (simState.status === 'idle' && !stepModeActive && !isPaused && !isCompleted)} className="p-1.5 text-sm hover:bg-editor-border rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed" title="Reset Simulation">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          </button>
        </div>
      )}

      {/* === Narrow tier: compact sim buttons inline === */}
      {tier === 'narrow' && (
        <div className="flex items-center gap-1 shrink-0">
          {(!isRunning && !isPaused && !stepModeActive) ? (
            <button onClick={handleRun} disabled={!model} className="p-2 text-sm bg-green-600 hover:bg-green-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed" title="Run Simulation">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" /></svg>
            </button>
          ) : (isPaused || stepModeActive) ? (
            <button onClick={handleResume} disabled={!model || isCompleted} className="p-2 text-sm bg-green-600 hover:bg-green-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed" title={stepModeActive ? 'Continue Running' : 'Resume'}>
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" /></svg>
            </button>
          ) : null}
          {isRunning && (
            <button onClick={handlePause} className="p-2 text-sm bg-yellow-600 hover:bg-yellow-700 rounded transition-colors" title="Pause">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M5.5 3A1.5 1.5 0 004 4.5v11A1.5 1.5 0 005.5 17h2A1.5 1.5 0 009 15.5v-11A1.5 1.5 0 007.5 3h-2zm7 0A1.5 1.5 0 0011 4.5v11a1.5 1.5 0 001.5 1.5h2a1.5 1.5 0 001.5-1.5v-11A1.5 1.5 0 0014.5 3h-2z" clipRule="evenodd" /></svg>
            </button>
          )}
          <button onClick={handleStop} disabled={!isRunning && !stepModeActive && !isPaused} className="p-2 text-sm bg-red-600 hover:bg-red-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed" title="Stop Simulation">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M5.75 3A1.75 1.75 0 004 4.75v10.5c0 .966.784 1.75 1.75 1.75h8.5A1.75 1.75 0 0016 15.25V4.75A1.75 1.75 0 0014.25 3h-8.5z" /></svg>
          </button>
        </div>
      )}

      {/* === Simulation Status === */}
      {model && (
        <div className="flex items-center gap-2 text-sm text-gray-400 min-w-0 shrink">
          <span className={`w-2 h-2 rounded-full shrink-0 ${
            simState.status === 'running' ? 'bg-green-500 animate-pulse'
            : simState.status === 'paused' ? 'bg-yellow-500'
            : simState.status === 'completed' ? 'bg-blue-500'
            : simState.status === 'error' ? 'bg-red-500'
            : 'bg-gray-500'
          }`} />
          <span className="capitalize truncate">{simState.status}{stepModeActive ? ' (Step)' : ''}</span>
          {tier !== 'narrow' && (isRunning || isPaused || stepModeActive) && (
            <span className="truncate">
              | t = {simState.currentTime.toFixed(3)}s ({Math.round(simState.progress * 100)}%)
            </span>
          )}
          {tier === 'narrow' && (isRunning || isPaused || stepModeActive) && (
            <span className="text-xs">{Math.round(simState.progress * 100)}%</span>
          )}
          {simState.status === 'error' && simState.error && (
            <span className="text-red-400 max-w-xs truncate" title={simState.error}>: {simState.error}</span>
          )}
        </div>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* === View Toggles — full and medium tiers (narrow uses overflow menu) === */}
      {tier !== 'narrow' && (
        <div className="flex items-center gap-1 shrink-0">
          <button onClick={toggleProperties} className={`p-1.5 text-sm rounded transition-colors flex items-center gap-1 ${showProperties ? 'bg-blue-600' : 'hover:bg-editor-border'}`} title="Toggle Properties Panel">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
            {tier === 'full' && <span>Properties</span>}
          </button>
          <button onClick={handleTogglePlotWindows} className={`p-1.5 text-sm rounded transition-colors flex items-center gap-1 ${hasOpenPlotWindows ? 'bg-blue-600' : 'hover:bg-editor-border'}`} title={hasOpenPlotWindows ? 'Close All Plot Windows' : 'Open Plot Windows'}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
            {tier === 'full' ? <>Scopes {hasOpenPlotWindows ? `(${Object.keys(plotWindows).length})` : ''}</> : hasOpenPlotWindows ? <span className="text-xs">{Object.keys(plotWindows).length}</span> : null}
          </button>
          <button onClick={openSettingsModal} className="p-1.5 text-sm rounded transition-colors hover:bg-editor-border" title="Settings">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          </button>
          <button onClick={() => openHelpModal('shortcuts')} className="p-1.5 text-sm rounded transition-colors hover:bg-editor-border" title="Help & Keyboard Shortcuts">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </button>
        </div>
      )}

      {/* === Overflow menu button — medium and narrow tiers === */}
      {tier !== 'full' && (
        <div className="relative shrink-0">
          <button
            onClick={(e) => { e.stopPropagation(); setShowOverflowMenu(!showOverflowMenu) }}
            className="p-2 hover:bg-editor-border rounded transition-colors"
            title="Menu"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          {showOverflowMenu && <OverflowMenu />}
        </div>
      )}

      {/* Examples Modal */}
      <ExamplesModal
        isOpen={showExamplesModal}
        onClose={closeExamplesModal}
        examples={exampleList}
        onLoadExample={handleLoadExample}
        onOpenBlockReference={() => openHelpModal('blocks')}
      />

      {/* Code Generation Modal */}
      <CodeGenModal
        isOpen={showCodeGenModal}
        onClose={closeCodeGenModal}
      />

      {/* Save As Modal */}
      <SaveAsModal />
    </div>
  )
}
