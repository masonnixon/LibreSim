import { create } from 'zustand'

export interface PlotWindowState {
  isOpen: boolean
  isMinimized: boolean
  position: { x: number; y: number }
  size: { width: number; height: number }
}

interface UIState {
  // Panel visibility
  showProperties: boolean
  showSimulation: boolean
  sidebarCollapsed: boolean

  // Plot windows state (keyed by blockId)
  plotWindows: Record<string, PlotWindowState>

  // Drag state for block library
  draggingBlockType: string | null

  // Modal states
  showNewModelModal: boolean
  showOpenModelModal: boolean
  showSettingsModal: boolean
  showImportModal: boolean

  // Actions
  toggleProperties: () => void
  toggleSimulation: () => void
  setShowSimulation: (show: boolean) => void
  toggleSidebar: () => void

  setDraggingBlockType: (type: string | null) => void

  // Plot window actions
  openPlotWindow: (blockId: string, initialPosition?: { x: number; y: number }) => void
  closePlotWindow: (blockId: string) => void
  togglePlotWindowMinimized: (blockId: string) => void
  updatePlotWindowPosition: (blockId: string, position: { x: number; y: number }) => void
  updatePlotWindowSize: (blockId: string, size: { width: number; height: number }) => void
  closeAllPlotWindows: () => void
  closePlotWindowsWithPrefix: (prefix: string) => void
  bringPlotWindowToFront: (blockId: string) => void

  openNewModelModal: () => void
  closeNewModelModal: () => void
  openOpenModelModal: () => void
  closeOpenModelModal: () => void
  openSettingsModal: () => void
  closeSettingsModal: () => void
  openImportModal: () => void
  closeImportModal: () => void
}

// Track z-index order for plot windows
let plotWindowZCounter = 100

export const useUIStore = create<UIState>((set) => ({
  showProperties: true,
  showSimulation: false,
  sidebarCollapsed: false,
  plotWindows: {},
  draggingBlockType: null,
  showNewModelModal: false,
  showOpenModelModal: false,
  showSettingsModal: false,
  showImportModal: false,

  toggleProperties: () => set((state) => ({ showProperties: !state.showProperties })),
  toggleSimulation: () => set((state) => ({ showSimulation: !state.showSimulation })),
  setShowSimulation: (show) => set({ showSimulation: show }),
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  setDraggingBlockType: (type) => set({ draggingBlockType: type }),

  // Plot window management
  openPlotWindow: (blockId, initialPosition) => set((state) => {
    const existingWindows = Object.keys(state.plotWindows).length
    const defaultPosition = initialPosition || {
      x: 20 + (existingWindows * 30),
      y: 100 + (existingWindows * 30),
    }
    return {
      plotWindows: {
        ...state.plotWindows,
        [blockId]: {
          isOpen: true,
          isMinimized: false,
          position: state.plotWindows[blockId]?.position || defaultPosition,
          size: state.plotWindows[blockId]?.size || { width: 450, height: 280 },
        },
      },
    }
  }),

  closePlotWindow: (blockId) => set((state) => {
    const { [blockId]: _, ...rest } = state.plotWindows
    return { plotWindows: rest }
  }),

  togglePlotWindowMinimized: (blockId) => set((state) => ({
    plotWindows: {
      ...state.plotWindows,
      [blockId]: {
        ...state.plotWindows[blockId],
        isMinimized: !state.plotWindows[blockId]?.isMinimized,
      },
    },
  })),

  updatePlotWindowPosition: (blockId, position) => set((state) => ({
    plotWindows: {
      ...state.plotWindows,
      [blockId]: {
        ...state.plotWindows[blockId],
        position,
      },
    },
  })),

  updatePlotWindowSize: (blockId, size) => set((state) => ({
    plotWindows: {
      ...state.plotWindows,
      [blockId]: {
        ...state.plotWindows[blockId],
        size,
      },
    },
  })),

  closeAllPlotWindows: () => set({ plotWindows: {} }),

  closePlotWindowsWithPrefix: (prefix) => set((state) => {
    // Close all plot windows whose blockId starts with the given prefix
    // This is used when expanding a subsystem to remove windows for blocks that were inside it
    const filtered = Object.fromEntries(
      Object.entries(state.plotWindows).filter(([blockId]) => !blockId.startsWith(prefix))
    )
    return { plotWindows: filtered }
  }),

  bringPlotWindowToFront: (_blockId) => {
    plotWindowZCounter++
    // z-index ordering is handled in PlotWindowManager component state
  },

  openNewModelModal: () => set({ showNewModelModal: true }),
  closeNewModelModal: () => set({ showNewModelModal: false }),
  openOpenModelModal: () => set({ showOpenModelModal: true }),
  closeOpenModelModal: () => set({ showOpenModelModal: false }),
  openSettingsModal: () => set({ showSettingsModal: true }),
  closeSettingsModal: () => set({ showSettingsModal: false }),
  openImportModal: () => set({ showImportModal: true }),
  closeImportModal: () => set({ showImportModal: false }),
}))
