import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Sidebar } from './Sidebar'

// Mock the stores with proper selector support
vi.mock('../../store/uiStore', () => ({
  useUIStore: vi.fn(),
}))

vi.mock('../../store/modelStore', () => ({
  useModelStore: vi.fn(),
}))

vi.mock('../../store/libraryStore', () => ({
  useLibraryStore: vi.fn(),
}))

// Mock toast
vi.mock('../Toast/Toast', () => ({
  toast: {
    success: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  },
}))

// Cached empty array for getLibraryBlocks to avoid infinite re-renders with useSyncExternalStore
const emptyLibraryBlocks: never[] = []

// Mock blockRegistry - must be inline for hoisting
// Note: getLibraryBlocks must return a STABLE reference to avoid useSyncExternalStore infinite loop
vi.mock('../../blocks', () => ({
  blockRegistry: {
    getByCategory: vi.fn((category: string) => {
      if (category === 'sources') {
        return [
          {
            type: 'constant',
            name: 'Constant',
            category: 'sources',
            description: 'A constant value',
            icon: 'C',
            inputs: [],
            outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
            parameters: [],
          },
          {
            type: 'step',
            name: 'Step',
            category: 'sources',
            description: 'A step function',
            icon: undefined,
            inputs: [],
            outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
            parameters: [],
          },
        ]
      }
      if (category === 'sinks') {
        return [
          {
            type: 'scope',
            name: 'Scope',
            category: 'sinks',
            description: 'Display signals',
            icon: '📊',
            inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
            outputs: [],
            parameters: [],
          },
        ]
      }
      return []
    }),
    getBlocksByLibrary: vi.fn(() => []),
    subscribe: vi.fn(() => () => {}),
    // IMPORTANT: Must return the same array reference each time to avoid infinite loop in useSyncExternalStore
    getLibraryBlocks: () => emptyLibraryBlocks,
    unregisterLibrary: vi.fn(),
  },
  blockCategories: ['sources', 'sinks', 'continuous', 'discrete', 'math'] as const,
}))

// Get the mocked functions
import { useUIStore } from '../../store/uiStore'
import { useModelStore } from '../../store/modelStore'
import { useLibraryStore } from '../../store/libraryStore'
import { blockRegistry } from '../../blocks'
import { toast } from '../Toast/Toast'

const mockedUseUIStore = vi.mocked(useUIStore)
const mockedUseModelStore = vi.mocked(useModelStore)
const mockedUseLibraryStore = vi.mocked(useLibraryStore)
const mockedBlockRegistry = vi.mocked(blockRegistry)
const mockedToast = vi.mocked(toast)
type LibraryState = ReturnType<typeof useLibraryStore.getState>
const testLibrary: LibraryState['libraries'][number] = {
  id: 'lib-1',
  name: 'Test Library',
  description: 'A test library',
  version: '1.0.0',
  sourcePath: 'test.mdl',
  sourceFormat: 'mdl',
  importedAt: '2026-01-01T00:00:00.000Z',
  blocks: [],
}
const libraryBlocks = [
  { type: 'lib_gain', name: 'Library Gain', category: 'math', description: 'Boost a signal', icon: 'L', inputs: [], outputs: [], parameters: [] },
  { type: 'lib_filter', name: 'Library Filter', category: 'signal_processing', description: 'Special smoothing', icon: undefined, inputs: [], outputs: [], parameters: [] },
]



describe('Sidebar', () => {
  const mockToggleSidebar = vi.fn()
  const mockSetDraggingBlockType = vi.fn()
  const mockAddBlock = vi.fn()
  const mockRemoveLibrary = vi.fn()

  const createMockLibraryState = (
    libraries: LibraryState['libraries'] = []
  ): LibraryState => ({
    libraries,
    libraryMap: new Map(libraries.map((library) => [library.id, library])),
    libraryBlockMap: new Map(),
    importLibrary: vi.fn(),
    removeLibrary: mockRemoveLibrary,
    getLibrary: vi.fn(),
    getLibraryBlock: vi.fn(),
    getLibraryBlocks: vi.fn(() => []),
    getAllLibraryBlocks: vi.fn(() => []),
    isLibraryBlock: vi.fn(() => false),
    getBlockImplementation: vi.fn(),
    clearAllLibraries: vi.fn(),
    _rebuildMaps: vi.fn(),
  })

  beforeEach(() => {
    vi.clearAllMocks()
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: 1024 })
    Object.defineProperty(navigator, 'maxTouchPoints', { configurable: true, value: 0 })

    // Default mock implementations
    mockedUseUIStore.mockReturnValue({
      sidebarCollapsed: false,
      toggleSidebar: mockToggleSidebar,
      setDraggingBlockType: mockSetDraggingBlockType,
    } as ReturnType<typeof useUIStore>)

    mockedUseModelStore.mockReturnValue({
      model: { blocks: [], connections: [] },
      addBlock: mockAddBlock,
    } as unknown as ReturnType<typeof useModelStore>)

    // useLibraryStore is called with selectors, so we need to handle that
    mockedUseLibraryStore.mockImplementation((selector) => selector(createMockLibraryState()))
  })

  describe('rendering', () => {
    it('renders the sidebar with block library header', () => {
      render(<Sidebar />)
      expect(screen.getByText('Block Library')).toBeInTheDocument()
    })

    it('renders search input', () => {
      render(<Sidebar />)
      expect(screen.getByPlaceholderText('Search blocks...')).toBeInTheDocument()
    })

    it('renders category headers', () => {
      render(<Sidebar />)
      expect(screen.getByText('Sources')).toBeInTheDocument()
      expect(screen.getByText('Sinks')).toBeInTheDocument()
    })

    it('shows blocks in expanded categories', () => {
      render(<Sidebar />)
      // Sources is expanded by default
      expect(screen.getByText('Constant')).toBeInTheDocument()
      expect(screen.getByText('Step')).toBeInTheDocument()
    })
  })

  describe('collapsed state', () => {
    it('renders collapsed sidebar when sidebarCollapsed is true', () => {
      mockedUseUIStore.mockReturnValue({
        sidebarCollapsed: true,
        toggleSidebar: mockToggleSidebar,
        setDraggingBlockType: mockSetDraggingBlockType,
      } as ReturnType<typeof useUIStore>)

      render(<Sidebar />)

      // Should not show the full sidebar content
      expect(screen.queryByText('Block Library')).not.toBeInTheDocument()
      expect(screen.queryByPlaceholderText('Search blocks...')).not.toBeInTheDocument()
    })

    it('shows expand button when collapsed', () => {
      mockedUseUIStore.mockReturnValue({
        sidebarCollapsed: true,
        toggleSidebar: mockToggleSidebar,
        setDraggingBlockType: mockSetDraggingBlockType,
      } as ReturnType<typeof useUIStore>)

      render(<Sidebar />)

      const expandButton = screen.getByTitle('Expand sidebar')
      expect(expandButton).toBeInTheDocument()
    })

    it('calls toggleSidebar when expand button is clicked', async () => {
      mockedUseUIStore.mockReturnValue({
        sidebarCollapsed: true,
        toggleSidebar: mockToggleSidebar,
        setDraggingBlockType: mockSetDraggingBlockType,
      } as ReturnType<typeof useUIStore>)

      render(<Sidebar />)

      const expandButton = screen.getByTitle('Expand sidebar')
      await userEvent.click(expandButton)

      expect(mockToggleSidebar).toHaveBeenCalled()
    })
  })

  describe('collapse button', () => {
    it('shows collapse button when expanded', () => {
      render(<Sidebar />)
      expect(screen.getByTitle('Collapse sidebar')).toBeInTheDocument()
    })

    it('calls toggleSidebar when collapse button is clicked', async () => {
      render(<Sidebar />)

      const collapseButton = screen.getByTitle('Collapse sidebar')
      await userEvent.click(collapseButton)

      expect(mockToggleSidebar).toHaveBeenCalled()
    })
  })

  describe('category toggle', () => {
    it('toggles category expansion on click', async () => {
      render(<Sidebar />)

      // Sinks should show Scope initially (it's in default expanded)
      expect(screen.getByText('Scope')).toBeInTheDocument()

      // Click to collapse sinks
      const sinksHeader = screen.getByText('Sinks')
      await userEvent.click(sinksHeader)

      // Scope should now be hidden
      expect(screen.queryByText('Scope')).not.toBeInTheDocument()

      // Click again to expand
      await userEvent.click(sinksHeader)
      expect(screen.getByText('Scope')).toBeInTheDocument()
    })
  })

  describe('search', () => {
    it('filters blocks by name', async () => {
      render(<Sidebar />)

      const searchInput = screen.getByPlaceholderText('Search blocks...')
      await userEvent.type(searchInput, 'constant')

      // Constant should still be visible
      expect(screen.getByText('Constant')).toBeInTheDocument()

      // Step and Scope should be hidden
      expect(screen.queryByText('Step')).not.toBeInTheDocument()
    })

    it('shows no blocks when search has no matches', async () => {
      render(<Sidebar />)

      const searchInput = screen.getByPlaceholderText('Search blocks...')
      await userEvent.type(searchInput, 'nonexistentblock')

      // No blocks should be visible
      expect(screen.queryByText('Constant')).not.toBeInTheDocument()
      expect(screen.queryByText('Step')).not.toBeInTheDocument()
      expect(screen.queryByText('Scope')).not.toBeInTheDocument()
    })
    it('filters blocks by description', () => {
      render(<Sidebar />)
      fireEvent.change(screen.getByPlaceholderText('Search blocks...'), { target: { value: 'display signals' } })
      expect(screen.getByText('Scope')).toBeInTheDocument()
      expect(screen.queryByText('Constant')).not.toBeInTheDocument()
    })

  })

  describe('drag and drop', () => {
    it('sets dragging block type on drag start', () => {
      render(<Sidebar />)

      const constantBlock = screen.getByText('Constant').closest('[draggable="true"]')
      expect(constantBlock).toBeInTheDocument()

      // Create a mock dataTransfer object since jsdom doesn't fully support it
      const dataTransfer = {
        effectAllowed: '',
        setData: vi.fn(),
      }
      fireEvent.dragStart(constantBlock!, { dataTransfer })

      expect(mockSetDraggingBlockType).toHaveBeenCalledWith('constant')
      expect(dataTransfer.effectAllowed).toBe('move')
    })

    it('blocks are draggable', () => {
      render(<Sidebar />)

      const constantBlock = screen.getByText('Constant').closest('div[draggable]')
      expect(constantBlock).toHaveAttribute('draggable', 'true')
    })
    it('does not add blocks from a desktop click', () => {
      render(<Sidebar />)
      fireEvent.click(screen.getByText('Constant'))
      expect(mockAddBlock).not.toHaveBeenCalled()
    })

  })

  describe('mobile placement', () => {
    it('adds a block at the default position', () => {
      Object.defineProperty(window, 'innerWidth', { configurable: true, value: 500 })
      Object.defineProperty(navigator, 'maxTouchPoints', { configurable: true, value: 1 })
      render(<Sidebar />)
      expect(screen.getByText('Tap a block to add it to the canvas')).toBeInTheDocument()
      const constant = screen.getByTitle('Tap to add Constant')
      expect(constant).toHaveAttribute('draggable', 'false')
      fireEvent.click(constant)
      expect(mockAddBlock).toHaveBeenCalledWith(expect.objectContaining({ type: 'constant' }), { x: 200, y: 150 })
      expect(mockedToast.success).toHaveBeenCalledWith('Block Added', 'Added "Constant" to canvas')
      expect(mockToggleSidebar).toHaveBeenCalledOnce()
    })
    it.each([
      [null, { x: 200, y: 150 }],
      [{ blocks: [{ position: { x: 300, y: 40 } }], connections: [] }, { x: 480, y: 150 }],
      [{ blocks: [{ position: { x: 900, y: 250 } }], connections: [] }, { x: 200, y: 350 }],
    ])('places mobile blocks around the current model', (activeModel, expectedPosition) => {
      Object.defineProperty(window, 'innerWidth', { configurable: true, value: 500 })
      Object.defineProperty(navigator, 'maxTouchPoints', { configurable: true, value: 1 })
      mockedUseModelStore.mockReturnValue({ model: activeModel, addBlock: mockAddBlock } as never)
      render(<Sidebar />)
      fireEvent.click(screen.getByTitle('Tap to add Constant'))
      expect(mockAddBlock).toHaveBeenCalledWith(expect.any(Object), expectedPosition)
    })

    it('responds to touch-device resizes and removes its listener', () => {
      Object.defineProperty(window, 'innerWidth', { configurable: true, value: 500 })
      Object.defineProperty(window, 'ontouchstart', { configurable: true, value: null })
      const removeListener = vi.spyOn(window, 'removeEventListener')
      const view = render(<Sidebar />)
      expect(screen.getByText('Tap a block to add it to the canvas')).toBeInTheDocument()
      Object.defineProperty(window, 'innerWidth', { configurable: true, value: 900 })
      fireEvent(window, new Event('resize'))
      expect(screen.queryByText('Tap a block to add it to the canvas')).not.toBeInTheDocument()
      view.unmount()
      expect(removeListener).toHaveBeenCalledWith('resize', expect.any(Function))
      Reflect.deleteProperty(window, 'ontouchstart')
    })

  })

  describe('libraries section', () => {
    it('shows imported libraries section when libraries exist', () => {
      const state = createMockLibraryState([
            {
              id: 'lib-1',
              name: 'Test Library',
              description: 'A test library',
              version: '1.0.0',
              sourcePath: 'test.mdl',
              sourceFormat: 'mdl',
              importedAt: new Date().toISOString(),
              blocks: [],
            },
      ])
      mockedUseLibraryStore.mockImplementation((selector) => selector(state))

      render(<Sidebar />)

      expect(screen.getByText('Imported Libraries')).toBeInTheDocument()
      expect(screen.getByText('Test Library')).toBeInTheDocument()
    })

    it('does not show libraries section when no libraries', () => {
      render(<Sidebar />)
      expect(screen.queryByText('Imported Libraries')).not.toBeInTheDocument()
    })
    it('toggles an empty library and confirms removal', () => {
      const state = createMockLibraryState([testLibrary])
      mockedUseLibraryStore.mockImplementation((selector) => selector(state))
      const confirmRemoval = vi.spyOn(window, 'confirm').mockReturnValue(false)
      render(<Sidebar />)
      const header = screen.getByText('Test Library').closest('[role="button"]') as HTMLElement
      fireEvent.keyDown(header, { key: 'Space' })
      expect(screen.queryByText('No blocks in this library')).not.toBeInTheDocument()
      fireEvent.keyDown(header, { key: 'Enter' })
      expect(screen.getByText('No blocks in this library')).toBeInTheDocument()
      fireEvent.click(header)
      expect(screen.queryByText('No blocks in this library')).not.toBeInTheDocument()
      const remove = screen.getByTitle('Remove library')
      fireEvent.click(remove)
      expect(mockRemoveLibrary).not.toHaveBeenCalled()
      confirmRemoval.mockReturnValue(true)
      fireEvent.click(remove)
      expect(mockRemoveLibrary).toHaveBeenCalledWith('lib-1')
      expect(mockedBlockRegistry.unregisterLibrary).toHaveBeenCalledWith('lib-1')
      expect(mockedToast.success).toHaveBeenCalledWith('Library Removed', '"Test Library" has been removed')
      expect(screen.queryByText('No blocks in this library')).not.toBeInTheDocument()
    })

    it('renders, filters, and drags imported blocks', () => {
      const state = createMockLibraryState([testLibrary])
      mockedUseLibraryStore.mockImplementation((selector) => selector(state))
      mockedBlockRegistry.getBlocksByLibrary.mockReturnValue(libraryBlocks as never)
      render(<Sidebar />)
      fireEvent.click(screen.getByText('Test Library'))
      expect(screen.getByText('Library Gain')).toBeInTheDocument()
      expect(screen.getByText('Library Filter')).toBeInTheDocument()
      const gain = screen.getByText('Library Gain').closest('[draggable="true"]') as HTMLElement
      const dataTransfer = { effectAllowed: '', setData: vi.fn() }
      fireEvent.dragStart(gain, { dataTransfer })
      expect(mockSetDraggingBlockType).toHaveBeenCalledWith('lib_gain')
      fireEvent.click(gain)
      expect(mockAddBlock).not.toHaveBeenCalled()
      const search = screen.getByPlaceholderText('Search blocks...')
      fireEvent.change(search, { target: { value: 'gain' } })
      expect(screen.getByText('Library Gain')).toBeInTheDocument()
      fireEvent.change(search, { target: { value: 'special' } })
      expect(screen.getByText('Library Filter')).toBeInTheDocument()
      expect(screen.queryByText('Library Gain')).not.toBeInTheDocument()
      fireEvent.change(search, { target: { value: 'missing' } })
      expect(screen.queryByText('Test Library')).not.toBeInTheDocument()
    })

    it('adds an imported block on mobile', () => {
      Object.defineProperty(window, 'innerWidth', { configurable: true, value: 500 })
      Object.defineProperty(navigator, 'maxTouchPoints', { configurable: true, value: 1 })
      const state = createMockLibraryState([testLibrary])
      mockedUseLibraryStore.mockImplementation((selector) => selector(state))
      mockedBlockRegistry.getBlocksByLibrary.mockReturnValue(libraryBlocks as never)
      render(<Sidebar />)
      fireEvent.click(screen.getByText('Test Library'))
      const gain = screen.getByTitle('Tap to add Library Gain')
      expect(gain).toHaveAttribute('draggable', 'false')
      fireEvent.click(gain)
      expect(mockAddBlock).toHaveBeenCalledWith(expect.objectContaining({ type: 'lib_gain' }), { x: 200, y: 150 })
    })

  })
})
