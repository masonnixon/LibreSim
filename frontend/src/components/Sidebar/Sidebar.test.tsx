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
            icon: 'S',
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

const mockedUseUIStore = vi.mocked(useUIStore)
const mockedUseModelStore = vi.mocked(useModelStore)
const mockedUseLibraryStore = vi.mocked(useLibraryStore)

describe('Sidebar', () => {
  const mockToggleSidebar = vi.fn()
  const mockSetDraggingBlockType = vi.fn()
  const mockAddBlock = vi.fn()
  const mockRemoveLibrary = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

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
    mockedUseLibraryStore.mockImplementation((selector?: (state: { libraries: unknown[]; removeLibrary: typeof mockRemoveLibrary }) => unknown) => {
      const state = {
        libraries: [],
        removeLibrary: mockRemoveLibrary,
      }
      return selector ? selector(state) : state
    })
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
  })

  describe('libraries section', () => {
    it('shows imported libraries section when libraries exist', () => {
      mockedUseLibraryStore.mockImplementation((selector?: (state: { libraries: unknown[]; removeLibrary: typeof mockRemoveLibrary }) => unknown) => {
        const state = {
          libraries: [
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
          ],
          removeLibrary: mockRemoveLibrary,
        }
        return selector ? selector(state) : state
      })

      render(<Sidebar />)

      expect(screen.getByText('Imported Libraries')).toBeInTheDocument()
      expect(screen.getByText('Test Library')).toBeInTheDocument()
    })

    it('does not show libraries section when no libraries', () => {
      render(<Sidebar />)
      expect(screen.queryByText('Imported Libraries')).not.toBeInTheDocument()
    })
  })
})
