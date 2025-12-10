import { create } from 'zustand'

interface UIState {
  // Panel visibility
  showProperties: boolean
  showSimulation: boolean
  sidebarCollapsed: boolean

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

  openNewModelModal: () => void
  closeNewModelModal: () => void
  openOpenModelModal: () => void
  closeOpenModelModal: () => void
  openSettingsModal: () => void
  closeSettingsModal: () => void
  openImportModal: () => void
  closeImportModal: () => void
}

export const useUIStore = create<UIState>((set) => ({
  showProperties: true,
  showSimulation: false,
  sidebarCollapsed: false,
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

  openNewModelModal: () => set({ showNewModelModal: true }),
  closeNewModelModal: () => set({ showNewModelModal: false }),
  openOpenModelModal: () => set({ showOpenModelModal: true }),
  closeOpenModelModal: () => set({ showOpenModelModal: false }),
  openSettingsModal: () => set({ showSettingsModal: true }),
  closeSettingsModal: () => set({ showSettingsModal: false }),
  openImportModal: () => set({ showImportModal: true }),
  closeImportModal: () => set({ showImportModal: false }),
}))
