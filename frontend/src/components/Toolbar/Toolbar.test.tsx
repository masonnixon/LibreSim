import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
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
  ExamplesModal: () => null,
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

const mockedUseModelStore = vi.mocked(useModelStore)
const mockedUseSimulationStore = vi.mocked(useSimulationStore)
const mockedUseUIStore = vi.mocked(useUIStore)
const mockedUseLibraryStore = vi.mocked(useLibraryStore)

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
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => storage[key] || null)
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation((key, value) => {
      storage[key] = value
    })

    mockedUseModelStore.mockReturnValue(mockModelStore as unknown as ReturnType<typeof useModelStore>)
    mockedUseSimulationStore.mockReturnValue(mockSimulationStore as unknown as ReturnType<typeof useSimulationStore>)
    mockedUseUIStore.mockReturnValue(mockUIStore as unknown as ReturnType<typeof useUIStore>)
    mockedUseLibraryStore.mockImplementation((selector?: (state: { importLibrary: typeof mockImportLibrary }) => unknown) => {
      const state = { importLibrary: mockImportLibrary }
      return selector ? selector(state) : state
    })
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
})
