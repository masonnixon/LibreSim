import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Toolbar } from './Toolbar'

// Mock all stores
vi.mock('../../store/modelStore', () => ({
  useModelStore: vi.fn(),
}))

vi.mock('../../store/simulationStore', () => ({
  useSimulationStore: vi.fn(),
}))

vi.mock('../../store/uiStore', () => ({
  useUIStore: vi.fn(),
}))

vi.mock('../../store/libraryStore', () => ({
  useLibraryStore: vi.fn(),
}))

// Mock API
vi.mock('../../api/client', () => ({
  api: {
    startSimulation: vi.fn(),
    stopSimulation: vi.fn(),
    pauseSimulation: vi.fn(),
    resumeSimulation: vi.fn(),
    resetSimulation: vi.fn(),
    getSimulationStatus: vi.fn(),
    getSimulationResults: vi.fn(),
    saveModel: vi.fn(),
    initStepMode: vi.fn(),
    stepForward: vi.fn(),
    stepBackward: vi.fn(),
    enterStepMode: vi.fn(),
    continueFromStepMode: vi.fn(),
  },
}))

// Mock toast
vi.mock('../Toast/Toast', () => ({
  toast: {
    success: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  },
}))

// Mock examples
vi.mock('../../data/examples', () => ({
  exampleList: [],
  fetchExample: vi.fn(),
}))

// Mock child components
vi.mock('../Examples/ExamplesModal', () => ({
  ExamplesModal: ({
    onLoadExample,
    onOpenBlockReference,
  }: {
    onLoadExample: (id: string) => void
    onOpenBlockReference: () => void
  }) => (
    <div>
      <button onClick={() => onLoadExample('example-1')}>
        Load Stub Example
      </button>
      <button onClick={onOpenBlockReference}>Open Block Reference</button>
    </div>
  ),
}))

vi.mock('../CodeGen/CodeGenModal', () => ({
  CodeGenModal: () => null,
}))

vi.mock('../SaveAs/SaveAsModal', () => ({
  SaveAsModal: () => null,
}))

// Mock utils
vi.mock('../../utils/mdlExporter', () => ({
  exportModelAsMDL: vi.fn(),
}))

vi.mock('../../utils/mdlImporter', () => ({
  importMDL: vi.fn(),
  isMDLFile: vi.fn(),
  importMDLAsLibrary: vi.fn(),
}))

vi.mock('../../blocks', () => ({
  blockRegistry: {
    registerLibraryBlocks: vi.fn(),
  },
}))

// Get the mocked functions
import { useModelStore } from '../../store/modelStore'
import { useSimulationStore } from '../../store/simulationStore'
import { useUIStore } from '../../store/uiStore'
import { useLibraryStore } from '../../store/libraryStore'
import { api } from '../../api/client'
import { toast } from '../Toast/Toast'
import { fetchExample } from '../../data/examples'
import { exportModelAsMDL } from '../../utils/mdlExporter'
import {
  importMDL,
  isMDLFile,
  importMDLAsLibrary,
} from '../../utils/mdlImporter'
import { blockRegistry } from '../../blocks'

const mockedUseModelStore = vi.mocked(useModelStore)
const mockedUseSimulationStore = vi.mocked(useSimulationStore)
const mockedUseUIStore = vi.mocked(useUIStore)
const mockedUseLibraryStore = vi.mocked(useLibraryStore)
const mockedApi = vi.mocked(api)
const mockedToast = vi.mocked(toast)
const mockedFetchExample = vi.mocked(fetchExample)
const mockedExportModelAsMDL = vi.mocked(exportModelAsMDL)
const mockedImportMDL = vi.mocked(importMDL)
const mockedIsMDLFile = vi.mocked(isMDLFile)
const mockedImportMDLAsLibrary = vi.mocked(importMDLAsLibrary)
const mockedBlockRegistry = vi.mocked(blockRegistry)
type LibraryState = ReturnType<typeof useLibraryStore.getState>

describe('Toolbar', () => {
  const mockModel = {
    id: 'test-model',
    metadata: { name: 'Test Model' },
    blocks: [],
    connections: [],
    simulationConfig: {
      solver: 'rk4',
      startTime: 0,
      stopTime: 10,
      stepSize: 0.01,
    },
  }

  const mockModelStore = {
    model: mockModel,
    isDirty: false,
    createNewModel: vi.fn(),
    saveModel: vi.fn().mockReturnValue(mockModel),
    loadModel: vi.fn(),
    undo: vi.fn(),
    redo: vi.fn(),
    canUndo: vi.fn().mockReturnValue(false),
    canRedo: vi.fn().mockReturnValue(false),
  }

  const mockSimulationStore = {
    state: {
      status: 'idle' as const,
      currentTime: 0,
      progress: 0,
      error: null,
    },
    setStatus: vi.fn(),
    setProgress: vi.fn(),
    setResults: vi.fn(),
    setError: vi.fn(),
    clearResults: vi.fn(),
    stepModeActive: false,
    stepHistorySize: 0,
    setStepModeActive: vi.fn(),
    setStepHistorySize: vi.fn(),
  }

  const mockUIStore = {
    toggleProperties: vi.fn(),
    showProperties: false,
    sidebarCollapsed: false,
    toggleSidebar: vi.fn(),
    plotWindows: {},
    closeAllPlotWindows: vi.fn(),
    openPlotWindow: vi.fn(),
    openSettingsModal: vi.fn(),
    openHelpModal: vi.fn(),
    showExamplesModal: false,
    openExamplesModal: vi.fn(),
    closeExamplesModal: vi.fn(),
    showCodeGenModal: false,
    openCodeGenModal: vi.fn(),
    closeCodeGenModal: vi.fn(),
    openSaveAsModal: vi.fn(),
  }

  const mockImportLibrary = vi.fn()
  const mockLibraryState: LibraryState = {
    libraries: [],
    libraryMap: new Map(),
    libraryBlockMap: new Map(),
    importLibrary: mockImportLibrary,
    removeLibrary: vi.fn(),
    getLibrary: vi.fn(),
    getLibraryBlock: vi.fn(),
    getLibraryBlocks: vi.fn(() => []),
    getAllLibraryBlocks: vi.fn(() => []),
    isLibraryBlock: vi.fn(() => false),
    getBlockImplementation: vi.fn(),
    clearAllLibraries: vi.fn(),
    _rebuildMaps: vi.fn(),
  }

  function makeFile(name: string, text: string) {
    const file = new File([text], name)
    Object.defineProperty(file, 'text', {
      configurable: true,
      value: vi.fn().mockResolvedValue(text),
    })
    return file
  }

  function inputs(container: HTMLElement) {
    return container.getElementsByTagName('input')
  }

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock window.innerWidth for desktop view
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    })

    // Mock localStorage
    const storage: Record<string, string> = {}
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(
      (key) => storage[key] || null
    )
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation((key, value) => {
      storage[key] = value
    })

    mockedUseModelStore.mockReturnValue(
      mockModelStore as unknown as ReturnType<typeof useModelStore>
    )
    mockedUseSimulationStore.mockReturnValue(
      mockSimulationStore as unknown as ReturnType<typeof useSimulationStore>
    )
    mockedUseUIStore.mockReturnValue(
      mockUIStore as unknown as ReturnType<typeof useUIStore>
    )
    mockedUseLibraryStore.mockImplementation((selector) =>
      selector(mockLibraryState)
    )
  })

  describe('rendering', () => {
    it('renders the toolbar with LibreSim logo', () => {
      render(<Toolbar />)
      expect(screen.getByText('LibreSim')).toBeInTheDocument()
    })

    it('renders model name', () => {
      render(<Toolbar />)
      expect(screen.getByText('Test Model')).toBeInTheDocument()
    })

    it('shows dirty indicator when model is modified', () => {
      mockedUseModelStore.mockReturnValue({
        ...mockModelStore,
        isDirty: true,
      } as unknown as ReturnType<typeof useModelStore>)

      render(<Toolbar />)
      // The dirty indicator shows in multiple places (model name and save button)
      const dirtyIndicators = screen.getAllByText('*')
      expect(dirtyIndicators.length).toBeGreaterThan(0)
    })

    it('renders file operation buttons', () => {
      render(<Toolbar />)
      expect(screen.getByText('New')).toBeInTheDocument()
      expect(screen.getByText('Open')).toBeInTheDocument()
      expect(screen.getByText('Save')).toBeInTheDocument()
      expect(screen.getByText('Save As')).toBeInTheDocument()
    })

    it('renders simulation controls', () => {
      render(<Toolbar />)
      expect(screen.getByText('Run')).toBeInTheDocument()
      expect(screen.getByText('Stop')).toBeInTheDocument()
    })

    it('renders status indicator as idle', () => {
      render(<Toolbar />)
      expect(screen.getByText('idle')).toBeInTheDocument()
    })

    it('keeps embed chrome compact without restoring or saving browser state', () => {
      render(<Toolbar embed restoreLastModel={false} />)

      expect(screen.getAllByRole('button').map((button) => button.textContent)).toEqual([
        'Run',
        'Stop',
        'Scopes',
      ])
      expect(screen.queryByText('New')).not.toBeInTheDocument()
      expect(localStorage.getItem).not.toHaveBeenCalled()
      expect(localStorage.setItem).not.toHaveBeenCalled()
      expect(mockModelStore.createNewModel).not.toHaveBeenCalled()
    })
  })

  describe('simulation status display', () => {
    it('shows running status when simulation is running', () => {
      mockedUseSimulationStore.mockReturnValue({
        ...mockSimulationStore,
        state: {
          ...mockSimulationStore.state,
          status: 'running',
          currentTime: 2.5,
          progress: 0.25,
        },
      } as unknown as ReturnType<typeof useSimulationStore>)

      render(<Toolbar />)
      expect(screen.getByText('running')).toBeInTheDocument()
      expect(screen.getByText(/t = 2.500s/)).toBeInTheDocument()
      expect(screen.getByText(/25%/)).toBeInTheDocument()
    })

    it('shows paused status when simulation is paused', () => {
      mockedUseSimulationStore.mockReturnValue({
        ...mockSimulationStore,
        state: {
          ...mockSimulationStore.state,
          status: 'paused',
          currentTime: 5.0,
          progress: 0.5,
        },
      } as unknown as ReturnType<typeof useSimulationStore>)

      render(<Toolbar />)
      expect(screen.getByText('paused')).toBeInTheDocument()
    })

    it('shows step mode indicator when in step mode', () => {
      mockedUseSimulationStore.mockReturnValue({
        ...mockSimulationStore,
        state: {
          ...mockSimulationStore.state,
          status: 'paused',
        },
        stepModeActive: true,
      } as unknown as ReturnType<typeof useSimulationStore>)

      render(<Toolbar />)
      expect(screen.getByText('paused (Step)')).toBeInTheDocument()
    })

    it('shows error status with message', () => {
      mockedUseSimulationStore.mockReturnValue({
        ...mockSimulationStore,
        state: {
          ...mockSimulationStore.state,
          status: 'error',
          error: 'Simulation failed',
        },
      } as unknown as ReturnType<typeof useSimulationStore>)

      render(<Toolbar />)
      expect(screen.getByText('error')).toBeInTheDocument()
      expect(screen.getByText(/Simulation failed/)).toBeInTheDocument()
    })
  })

  describe('button states', () => {
    it('disables save button when model is not dirty', () => {
      render(<Toolbar />)
      const saveButton = screen.getByText('Save')
      expect(saveButton).toBeDisabled()
    })

    it('enables save button when model is dirty', () => {
      mockedUseModelStore.mockReturnValue({
        ...mockModelStore,
        isDirty: true,
      } as unknown as ReturnType<typeof useModelStore>)

      render(<Toolbar />)
      const saveButton = screen.getByText('Save*')
      expect(saveButton).not.toBeDisabled()
    })

    it('disables run button when no model', () => {
      mockedUseModelStore.mockReturnValue({
        ...mockModelStore,
        model: null,
      } as unknown as ReturnType<typeof useModelStore>)

      render(<Toolbar />)
      const runButton = screen.getByText('Run')
      expect(runButton).toBeDisabled()
    })

    it('disables stop button when not running', () => {
      render(<Toolbar />)
      const stopButton = screen.getByText('Stop')
      expect(stopButton).toBeDisabled()
    })

    it('enables stop button when running', () => {
      mockedUseSimulationStore.mockReturnValue({
        ...mockSimulationStore,
        state: {
          ...mockSimulationStore.state,
          status: 'running',
        },
      } as unknown as ReturnType<typeof useSimulationStore>)

      render(<Toolbar />)
      const stopButton = screen.getByText('Stop')
      expect(stopButton).not.toBeDisabled()
    })

    it('disables undo button when cannot undo', () => {
      render(<Toolbar />)
      const undoButton = screen.getByTitle('Undo (Ctrl+Z)')
      expect(undoButton).toBeDisabled()
    })

    it('enables undo button when can undo', () => {
      mockedUseModelStore.mockReturnValue({
        ...mockModelStore,
        canUndo: vi.fn().mockReturnValue(true),
      } as unknown as ReturnType<typeof useModelStore>)

      render(<Toolbar />)
      const undoButton = screen.getByTitle('Undo (Ctrl+Z)')
      expect(undoButton).not.toBeDisabled()
    })
  })

  describe('view toggles', () => {
    it('renders properties button', () => {
      render(<Toolbar />)
      expect(screen.getByText('Properties')).toBeInTheDocument()
    })

    it('renders scopes button', () => {
      render(<Toolbar />)
      expect(screen.getByText('Scopes')).toBeInTheDocument()
    })

    it('shows scope count when plot windows are open', () => {
      mockedUseUIStore.mockReturnValue({
        ...mockUIStore,
        plotWindows: { 'scope-1': { x: 0, y: 0 }, 'scope-2': { x: 0, y: 0 } },
      } as unknown as ReturnType<typeof useUIStore>)

      render(<Toolbar />)
      expect(screen.getByText('Scopes (2)')).toBeInTheDocument()
    })

    it('calls toggleProperties when properties button clicked', () => {
      render(<Toolbar />)
      fireEvent.click(screen.getByText('Properties'))
      expect(mockUIStore.toggleProperties).toHaveBeenCalled()
    })
  })

  describe('menu interactions', () => {
    it('opens export menu when clicked', () => {
      render(<Toolbar />)
      const exportButton = screen.getByText('Export')
      fireEvent.click(exportButton)

      expect(screen.getByText('Export as JSON')).toBeInTheDocument()
      expect(screen.getByText('Export as MDL')).toBeInTheDocument()
    })

    it('opens import menu when clicked', () => {
      render(<Toolbar />)
      const importButton = screen.getByText('Import')
      fireEvent.click(importButton)

      expect(screen.getByText('Import Model')).toBeInTheDocument()
      expect(screen.getByText('Import Library')).toBeInTheDocument()
    })

    it('opens examples modal when examples button clicked', () => {
      render(<Toolbar />)
      fireEvent.click(screen.getByText('Examples'))
      expect(mockUIStore.openExamplesModal).toHaveBeenCalled()
    })

    it('opens code gen modal when generate button clicked', () => {
      render(<Toolbar />)
      fireEvent.click(screen.getByText('Generate'))
      expect(mockUIStore.openCodeGenModal).toHaveBeenCalled()
    })

    it('opens settings modal when settings button clicked', () => {
      render(<Toolbar />)
      fireEvent.click(screen.getByTitle('Settings'))
      expect(mockUIStore.openSettingsModal).toHaveBeenCalled()
    })

    it('opens help modal when help button clicked', () => {
      render(<Toolbar />)
      fireEvent.click(screen.getByTitle('Help & Keyboard Shortcuts'))
      expect(mockUIStore.openHelpModal).toHaveBeenCalledWith('shortcuts')
    })
  })

  describe('file workflows', () => {
    it('handles stored sessions and new/open actions', async () => {
      vi.spyOn(Storage.prototype, 'getItem').mockReturnValueOnce('{')
      const error = vi.spyOn(console, 'error').mockImplementation(() => {})
      const malformed = render(<Toolbar />)
      expect(error).toHaveBeenCalled()
      malformed.unmount()

      const promptSpy = vi
        .spyOn(window, 'prompt')
        .mockReturnValueOnce('Named')
        .mockReturnValueOnce(null)
      const view = render(<Toolbar />)
      fireEvent.click(screen.getByText('New'))
      fireEvent.click(screen.getByText('New'))
      expect(mockModelStore.createNewModel).toHaveBeenCalledWith('Named')
      expect(promptSpy).toHaveBeenCalledTimes(2)
      const click = vi.spyOn(inputs(view.container)[0], 'click')
      fireEvent.click(screen.getByText('Open'))
      expect(click).toHaveBeenCalledOnce()
      fireEvent.change(inputs(view.container)[0], { target: { files: [] } })

      const file = makeFile(
        'sparse.json',
        JSON.stringify({ blocks: [], connections: [] })
      )
      fireEvent.change(inputs(view.container)[0], { target: { files: [file] } })
      await waitFor(() => expect(mockModelStore.loadModel).toHaveBeenCalled())
      const loaded = mockModelStore.loadModel.mock.calls.at(-1)?.[0]
      expect(loaded).toMatchObject({
        blocks: [],
        connections: [],
        metadata: { name: 'sparse' },
        simulationConfig: { solver: 'rk4' },
      })
      expect(loaded.id).toBeTruthy()
    })
  })

  describe('import and export workflows', () => {
    it('imports JSON and both MDL detection paths', async () => {
      const view = render(<Toolbar />)
      const input = inputs(view.container)[1]
      fireEvent.change(input, { target: { files: [] } })
      fireEvent.change(input, {
        target: { files: [makeFile('native.json', JSON.stringify(mockModel))] },
      })
      await waitFor(() =>
        expect(mockModelStore.loadModel).toHaveBeenCalledWith(
          expect.objectContaining({ id: 'test-model' })
        )
      )

      mockedImportMDL.mockReturnValue({
        ...mockModel,
        metadata: { name: 'Imported Model' },
      } as never)
      fireEvent.change(input, {
        target: { files: [makeFile('plant.mdl', 'mdl text')] },
      })
      await waitFor(() =>
        expect(mockModelStore.loadModel).toHaveBeenLastCalledWith(
          expect.objectContaining({
            metadata: expect.objectContaining({
              name: 'plant',
              sourceFile: 'plant.mdl',
            }),
          })
        )
      )

      mockedIsMDLFile.mockReturnValue(true)
      mockedImportMDL.mockReturnValue({
        ...mockModel,
        metadata: { name: 'Meaningful' },
      } as never)
      fireEvent.change(input, {
        target: { files: [makeFile('content.txt', 'mdl content')] },
      })
      await waitFor(() =>
        expect(mockedToast.success).toHaveBeenCalledWith(
          'MDL Import Complete',
          expect.stringContaining('Meaningful')
        )
      )

      mockedIsMDLFile.mockReturnValue(false)
      fireEvent.change(input, {
        target: { files: [makeFile('other.txt', 'other')] },
      })
      await waitFor(() =>
        expect(mockedToast.warning).toHaveBeenCalledWith(
          'Unsupported Format',
          expect.any(String)
        )
      )
    })

    it('reports model open and import failures', async () => {
      const view = render(<Toolbar />)
      const badOpen = makeFile('bad.json', JSON.stringify({ blocks: [] }))
      fireEvent.change(inputs(view.container)[0], {
        target: { files: [badOpen] },
      })
      await waitFor(() =>
        expect(mockedToast.warning).toHaveBeenCalledWith(
          'Load Failed',
          expect.stringContaining('missing blocks or connections')
        )
      )

      const rejected = makeFile('bad.mdl', 'x')
      Object.defineProperty(rejected, 'text', {
        value: vi.fn().mockRejectedValue('failure'),
      })
      fireEvent.change(inputs(view.container)[1], {
        target: { files: [rejected] },
      })
      await waitFor(() =>
        expect(mockedToast.warning).toHaveBeenCalledWith(
          'Import Failed',
          'Unknown error'
        )
      )
    })
  })

  describe('library workflow', () => {
    const library = {
      id: 'lib',
      name: 'Reusable',
      version: '1',
      blocks: [{ id: 'block' }],
    }
    const dependencies = {
      missingLibraries: ['Missing'],
      externalReferences: [
        { path: 'Found/Block', isResolvable: true },
        { path: 'Lost/Block', isResolvable: false },
      ],
      availableLibraries: ['Available'],
    }

    it('handles invalid, empty, and successful library files', async () => {
      const view = render(<Toolbar />)
      const input = inputs(view.container)[2]
      fireEvent.change(input, { target: { files: [] } })
      mockedIsMDLFile.mockReturnValue(false)
      fireEvent.change(input, {
        target: { files: [makeFile('invalid.mdl', 'bad')] },
      })
      await waitFor(() =>
        expect(mockedToast.warning).toHaveBeenCalledWith(
          'Invalid Format',
          expect.any(String)
        )
      )

      mockedIsMDLFile.mockReturnValue(true)
      mockedImportMDLAsLibrary.mockReturnValue({
        library: { ...library, blocks: [] },
        unresolvedReferences: [],
        dependencies: {
          missingLibraries: [],
          externalReferences: [],
          availableLibraries: [],
        },
      } as never)
      fireEvent.change(input, {
        target: { files: [makeFile('empty.mdl', 'mdl')] },
      })
      await waitFor(() =>
        expect(mockedToast.warning).toHaveBeenCalledWith(
          'No Library Blocks',
          expect.any(String)
        )
      )

      mockedImportMDLAsLibrary.mockReturnValue({
        library,
        unresolvedReferences: ['Lost/Block'],
        dependencies,
      } as never)
      mockImportLibrary.mockReturnValue({
        success: true,
        library,
        errors: [],
        warnings: ['renamed'],
      } as never)
      fireEvent.change(input, {
        target: { files: [makeFile('library.mdl', 'mdl')] },
      })
      await waitFor(() =>
        expect(mockedBlockRegistry.registerLibraryBlocks).toHaveBeenCalledWith(
          library.blocks
        )
      )
      expect(mockedToast.warning).toHaveBeenCalledWith(
        'Missing Dependencies',
        expect.stringContaining('Missing')
      )
      expect(mockedToast.success).toHaveBeenCalledWith(
        'Library Imported',
        expect.stringContaining('unresolved')
      )
      expect(mockedToast.info).toHaveBeenCalledWith('Note', 'renamed')
      expect(mockedToast.info).toHaveBeenCalledWith(
        'Dependencies Resolved',
        expect.stringContaining('Available')
      )
    })

    it('reports store and parser library failures', async () => {
      const view = render(<Toolbar />)
      mockedIsMDLFile.mockReturnValue(true)
      mockedImportMDLAsLibrary.mockReturnValue({
        library,
        unresolvedReferences: [],
        dependencies: {
          missingLibraries: [],
          externalReferences: [],
          availableLibraries: [],
        },
      } as never)
      mockImportLibrary.mockReturnValue({
        success: false,
        errors: ['duplicate'],
        warnings: [],
      } as never)
      fireEvent.change(inputs(view.container)[2], {
        target: { files: [makeFile('failure.mdl', 'mdl')] },
      })
      await waitFor(() =>
        expect(mockedToast.warning).toHaveBeenCalledWith(
          'Import Failed',
          'duplicate'
        )
      )

      mockedImportMDLAsLibrary.mockImplementation(() => {
        throw new Error('parser failed')
      })
      fireEvent.change(inputs(view.container)[2], {
        target: { files: [makeFile('throw.mdl', 'mdl')] },
      })
      await waitFor(() =>
        expect(mockedToast.warning).toHaveBeenCalledWith(
          'Library Import Failed',
          'parser failed'
        )
      )
    })
  })

  describe('save and export workflows', () => {
    it('exports JSON and MDL and saves remotely or locally', async () => {
      Object.defineProperty(URL, 'createObjectURL', {
        configurable: true,
        value: vi.fn().mockReturnValue('blob:url'),
      })
      Object.defineProperty(URL, 'revokeObjectURL', {
        configurable: true,
        value: vi.fn(),
      })
      vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(
        () => {}
      )
      mockedUseModelStore.mockReturnValue({
        ...mockModelStore,
        isDirty: true,
      } as unknown as ReturnType<typeof useModelStore>)
      render(<Toolbar />)
      fireEvent.click(screen.getByText('Export'))
      fireEvent.click(screen.getByText('Export as JSON'))
      expect(URL.createObjectURL).toHaveBeenCalled()
      expect(mockedToast.success).toHaveBeenCalledWith(
        'JSON Exported',
        expect.stringContaining('Test Model.json')
      )
      fireEvent.click(screen.getByText('Export'))
      fireEvent.click(screen.getByText('Export as MDL'))
      expect(mockedExportModelAsMDL).toHaveBeenCalledWith(mockModel)
      mockedApi.saveModel.mockResolvedValue({} as never)
      fireEvent.click(screen.getByText('Save*'))
      await waitFor(() =>
        expect(mockedToast.success).toHaveBeenCalledWith(
          'Model Saved',
          expect.any(String)
        )
      )
      mockedApi.saveModel.mockRejectedValue(new Error('offline'))
      fireEvent.click(screen.getByText('Save*'))
      await waitFor(() =>
        expect(mockedToast.info).toHaveBeenCalledWith(
          'Saved Locally',
          expect.any(String)
        )
      )
    })
  })

  describe('example workflows', () => {
    it('handles loaded, missing, and rejected examples', async () => {
      mockedFetchExample.mockResolvedValue(mockModel as never)
      render(<Toolbar />)
      fireEvent.click(screen.getByText('Load Stub Example'))
      await waitFor(() =>
        expect(mockModelStore.loadModel).toHaveBeenCalledWith(mockModel)
      )
      fireEvent.click(screen.getByText('Open Block Reference'))
      expect(mockUIStore.openHelpModal).toHaveBeenCalledWith('blocks')
      mockedFetchExample.mockResolvedValue(undefined)
      fireEvent.click(screen.getByText('Load Stub Example'))
      await waitFor(() =>
        expect(mockedToast.warning).toHaveBeenCalledWith(
          'Example Not Found',
          expect.any(String)
        )
      )
      mockedFetchExample.mockRejectedValue(new Error('network'))
      fireEvent.click(screen.getByText('Load Stub Example'))
      await waitFor(() =>
        expect(mockedToast.warning).toHaveBeenCalledWith(
          'Load Failed',
          expect.any(String)
        )
      )
    })
  })

  describe('scope workflows', () => {
    it('closes open scopes and reopens nested scopes', () => {
      mockedUseUIStore.mockReturnValue({
        ...mockUIStore,
        plotWindows: { open: { x: 0, y: 0 } },
      } as unknown as ReturnType<typeof useUIStore>)
      const open = render(<Toolbar />)
      fireEvent.click(screen.getByText('Scopes (1)'))
      expect(mockUIStore.closeAllPlotWindows).toHaveBeenCalled()
      open.unmount()
      mockedUseModelStore.mockReturnValue({
        ...mockModelStore,
        model: {
          ...mockModel,
          blocks: [
            { id: 'scope', type: 'scope' },
            {
              id: 'sub',
              type: 'subsystem',
              children: [{ id: 'xy', type: 'xy_graph' }],
            },
          ],
        },
      } as never)
      mockedUseUIStore.mockReturnValue(
        mockUIStore as unknown as ReturnType<typeof useUIStore>
      )
      render(<Toolbar />)
      fireEvent.click(screen.getByText('Scopes'))
      expect(mockUIStore.openPlotWindow).toHaveBeenNthCalledWith(1, 'scope', {
        x: 20,
        y: 100,
      })
      expect(mockUIStore.openPlotWindow).toHaveBeenNthCalledWith(2, 'sub__xy', {
        x: 60,
        y: 140,
      })
    })
  })

  describe('mobile workflows', () => {
    it('runs mobile menu view actions and running status', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      })
      mockedUseSimulationStore.mockReturnValue({
        ...mockSimulationStore,
        state: {
          ...mockSimulationStore.state,
          status: 'running',
          progress: 0.42,
        },
      } as unknown as ReturnType<typeof useSimulationStore>)
      render(<Toolbar />)
      expect(screen.getByText('42%')).toBeInTheDocument()
      const choose = (label: string) => {
        fireEvent.click(screen.getByTitle('Menu'))
        fireEvent.click(screen.getByText(label))
      }
      choose('Browse Examples')
      choose('Generate Code')
      choose('Hide Blocks')
      choose('Show Properties')
      choose('Show Scopes')
      choose('Settings')
      choose('Help & Shortcuts')
      expect(mockUIStore.openExamplesModal).toHaveBeenCalled()
      expect(mockUIStore.openCodeGenModal).toHaveBeenCalled()
      expect(mockUIStore.toggleSidebar).toHaveBeenCalled()
      expect(mockUIStore.toggleProperties).toHaveBeenCalled()
      expect(mockUIStore.openSettingsModal).toHaveBeenCalled()
      expect(mockUIStore.openHelpModal).toHaveBeenCalledWith('shortcuts')
    })
  })

  describe('remaining file branches', () => {
    it('restores complete sessions and preserves complete open models', async () => {
      vi.spyOn(Storage.prototype, 'getItem').mockReturnValueOnce(
        JSON.stringify(mockModel)
      )
      const restored = render(<Toolbar />)
      expect(mockModelStore.loadModel).toHaveBeenCalledWith(mockModel)
      restored.unmount()
      mockModelStore.loadModel.mockClear()

      vi.spyOn(Storage.prototype, 'getItem').mockReturnValueOnce(
        JSON.stringify({ id: 'incomplete' })
      )
      const incomplete = render(<Toolbar />)
      expect(mockModelStore.loadModel).not.toHaveBeenCalled()
      incomplete.unmount()

      const view = render(<Toolbar />)
      fireEvent.change(inputs(view.container)[0], {
        target: {
          files: [makeFile('complete.json', JSON.stringify(mockModel))],
        },
      })
      await waitFor(() =>
        expect(mockModelStore.loadModel).toHaveBeenCalledWith(
          expect.objectContaining({
            id: 'test-model',
            metadata: mockModel.metadata,
            simulationConfig: mockModel.simulationConfig,
          })
        )
      )
      const rejected = makeFile('unknown.json', 'x')
      Object.defineProperty(rejected, 'text', {
        configurable: true,
        value: vi.fn().mockRejectedValue('bad value'),
      })
      fireEvent.change(inputs(view.container)[0], {
        target: { files: [rejected] },
      })
      await waitFor(() =>
        expect(mockedToast.warning).toHaveBeenCalledWith(
          'Load Failed',
          'Unknown error'
        )
      )
    })

    it('opens both import pickers and imports JSON without an id', async () => {
      const view = render(<Toolbar />)
      const modelClick = vi.spyOn(inputs(view.container)[1], 'click')
      const libraryClick = vi.spyOn(inputs(view.container)[2], 'click')
      fireEvent.click(screen.getByText('Import'))
      const importMenu = screen.getByText('Import Model').parentElement
        ?.parentElement as HTMLElement
      fireEvent.click(importMenu)
      fireEvent.click(screen.getByText('Import Model'))
      expect(modelClick).toHaveBeenCalled()
      fireEvent.click(screen.getByText('Import'))
      fireEvent.click(screen.getByText('Import Library'))
      expect(libraryClick).toHaveBeenCalled()

      fireEvent.change(inputs(view.container)[1], {
        target: {
          files: [
            makeFile(
              'no-id.json',
              JSON.stringify({ ...mockModel, id: undefined })
            ),
          ],
        },
      })
      await waitFor(() =>
        expect(mockModelStore.loadModel).toHaveBeenCalledWith(
          expect.objectContaining({ id: expect.any(String) })
        )
      )
    })
  })

  describe('remaining library and export branches', () => {
    it('imports a clean library and handles a missing result library', async () => {
      const library = {
        id: 'clean',
        name: 'Clean',
        version: '1',
        blocks: [{ id: 'block' }],
      }
      const dependencies = {
        missingLibraries: [],
        externalReferences: [],
        availableLibraries: [],
      }
      mockedIsMDLFile.mockReturnValue(true)
      mockedImportMDLAsLibrary.mockReturnValue({
        library,
        unresolvedReferences: [],
        dependencies,
      } as never)
      mockImportLibrary
        .mockReturnValueOnce({
          success: true,
          library,
          errors: [],
          warnings: [],
        } as never)
        .mockReturnValueOnce({
          success: true,
          errors: [],
          warnings: [],
        } as never)
      const view = render(<Toolbar />)
      fireEvent.change(inputs(view.container)[2], {
        target: { files: [makeFile('clean.mdl', 'mdl')] },
      })
      await waitFor(() =>
        expect(mockedToast.success).toHaveBeenCalledWith(
          'Library Imported',
          expect.not.stringContaining('unresolved')
        )
      )
      fireEvent.change(inputs(view.container)[2], {
        target: { files: [makeFile('missing.mdl', 'mdl')] },
      })
      await waitFor(() =>
        expect(mockedToast.warning).toHaveBeenCalledWith('Import Failed', '')
      )
    })

    it('uses fallback export names and reports both MDL failure values', async () => {
      Object.defineProperty(URL, 'createObjectURL', {
        configurable: true,
        value: vi.fn().mockReturnValue('blob:url'),
      })
      Object.defineProperty(URL, 'revokeObjectURL', {
        configurable: true,
        value: vi.fn(),
      })
      vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(
        () => {}
      )
      const unnamed = { ...mockModel, metadata: { name: '' } }
      mockedUseModelStore.mockReturnValue({
        ...mockModelStore,
        model: unnamed,
        isDirty: true,
        saveModel: vi.fn(),
      } as never)
      const view = render(<Toolbar />)
      fireEvent.click(screen.getByText('Export'))
      fireEvent.click(screen.getByText('Export as JSON'))
      expect(mockedToast.success).toHaveBeenCalledWith(
        'JSON Exported',
        expect.stringContaining('model.json')
      )
      mockedExportModelAsMDL
        .mockImplementationOnce(() => {
          throw new Error('writer')
        })
        .mockImplementationOnce(() => {
          throw 'value'
        })
      fireEvent.click(screen.getByText('Export'))
      fireEvent.click(screen.getByText('Export as MDL'))
      expect(mockedToast.warning).toHaveBeenCalledWith(
        'Export Failed',
        'writer'
      )
      fireEvent.click(screen.getByText('Export'))
      fireEvent.click(screen.getByText('Export as MDL'))
      expect(mockedToast.warning).toHaveBeenCalledWith(
        'Export Failed',
        'Unknown error'
      )
      fireEvent.click(screen.getByText('Save*'))
      await waitFor(() => expect(mockedApi.saveModel).not.toHaveBeenCalled())
      expect(view.container).toBeInTheDocument()
    })
  })

  describe('residual presentation branches', () => {
    it('covers completed styling and active view labels', () => {
      mockedUseSimulationStore.mockReturnValue({
        ...mockSimulationStore,
        state: { ...mockSimulationStore.state, status: 'completed' },
      } as never)
      mockedUseUIStore.mockReturnValue({
        ...mockUIStore,
        showProperties: true,
        sidebarCollapsed: true,
      } as never)
      const view = render(<Toolbar />)
      expect(view.container.querySelector('.bg-blue-500')).toBeInTheDocument()
      expect(screen.getByText('Properties')).toHaveClass('bg-blue-600')
    })

    it('runs on mobile and keeps unavailable exports inert', async () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      })
      mockedApi.startSimulation.mockResolvedValue({} as never)
      const running = render(<Toolbar />)
      fireEvent.click(screen.getByTitle('Run Simulation'))
      await waitFor(() => expect(mockedApi.startSimulation).toHaveBeenCalled())
      running.unmount()

      mockedUseModelStore.mockReturnValue({
        ...mockModelStore,
        model: null,
      } as never)
      render(<Toolbar />)
      fireEvent.click(screen.getByTitle('Menu'))
      fireEvent.click(screen.getByText('Export JSON'))
      expect(URL.createObjectURL).not.toHaveBeenCalled()
      fireEvent.click(screen.getByText('Export MDL (Simulink)'))
      expect(mockedExportModelAsMDL).not.toHaveBeenCalled()
    })
  })

  describe('final toolbar branch arms', () => {
    it('covers identifier fallbacks and typed failure messages', async () => {
      vi.spyOn(crypto, 'randomUUID').mockReturnValue('' as never)
      const view = render(<Toolbar />)
      fireEvent.change(inputs(view.container)[0], {
        target: {
          files: [
            makeFile(
              'fallback.json',
              JSON.stringify({ blocks: [], connections: [] })
            ),
          ],
        },
      })
      await waitFor(() =>
        expect(mockModelStore.loadModel).toHaveBeenCalledWith(
          expect.objectContaining({ id: expect.any(String) })
        )
      )
      fireEvent.change(inputs(view.container)[1], {
        target: {
          files: [
            makeFile(
              'fallback-import.json',
              JSON.stringify({ ...mockModel, id: undefined })
            ),
          ],
        },
      })
      await waitFor(() =>
        expect(mockModelStore.loadModel).toHaveBeenCalledTimes(2)
      )

      const importError = makeFile('error.mdl', 'x')
      Object.defineProperty(importError, 'text', {
        configurable: true,
        value: vi.fn().mockRejectedValue(new Error('import error')),
      })
      fireEvent.change(inputs(view.container)[1], {
        target: { files: [importError] },
      })
      await waitFor(() =>
        expect(mockedToast.warning).toHaveBeenCalledWith(
          'Import Failed',
          'import error'
        )
      )

      mockedIsMDLFile.mockReturnValue(true)
      mockedImportMDLAsLibrary.mockImplementation(() => {
        throw 'library value'
      })
      fireEvent.change(inputs(view.container)[2], {
        target: { files: [makeFile('value.mdl', 'mdl')] },
      })
      await waitFor(() =>
        expect(mockedToast.warning).toHaveBeenCalledWith(
          'Library Import Failed',
          'Unknown error'
        )
      )
    })

    it('exports unnamed MDL and renders active mobile labels', () => {
      const unnamed = { ...mockModel, metadata: { name: '' } }
      mockedUseModelStore.mockReturnValue({
        ...mockModelStore,
        model: unnamed,
      } as never)
      const desktop = render(<Toolbar />)
      fireEvent.click(screen.getByText('Export'))
      fireEvent.click(screen.getByText('Export as MDL'))
      expect(mockedToast.success).toHaveBeenCalledWith(
        'MDL Exported',
        expect.stringContaining('model.mdl')
      )
      desktop.unmount()

      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      })
      mockedUseUIStore.mockReturnValue({
        ...mockUIStore,
        sidebarCollapsed: true,
        showProperties: true,
        plotWindows: { open: { x: 0, y: 0 } },
      } as never)
      render(<Toolbar />)
      fireEvent.click(screen.getByTitle('Menu'))
      expect(screen.getByText('Show Blocks')).toBeInTheDocument()
      expect(screen.getByText('Hide Properties')).toBeInTheDocument()
      expect(screen.getByText('Hide Scopes')).toBeInTheDocument()
    })
  })
})
