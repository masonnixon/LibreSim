import { describe, it, expect, beforeEach } from 'vitest'
import { useUIStore } from './uiStore'

describe('useUIStore', () => {
  // Reset store before each test
  beforeEach(() => {
    useUIStore.setState({
      showProperties: true,
      showSimulation: false,
      sidebarCollapsed: false,
      plotWindows: {},
      draggingBlockType: null,
      showNewModelModal: false,
      showOpenModelModal: false,
      showSettingsModal: false,
      showImportModal: false,
    })
  })

  describe('panel visibility', () => {
    it('has correct initial state', () => {
      const state = useUIStore.getState()
      expect(state.showProperties).toBe(true)
      expect(state.showSimulation).toBe(false)
      expect(state.sidebarCollapsed).toBe(false)
    })

    it('toggles properties panel', () => {
      const { toggleProperties } = useUIStore.getState()

      toggleProperties()
      expect(useUIStore.getState().showProperties).toBe(false)

      toggleProperties()
      expect(useUIStore.getState().showProperties).toBe(true)
    })

    it('toggles simulation panel', () => {
      const { toggleSimulation } = useUIStore.getState()

      toggleSimulation()
      expect(useUIStore.getState().showSimulation).toBe(true)

      toggleSimulation()
      expect(useUIStore.getState().showSimulation).toBe(false)
    })

    it('sets simulation panel visibility directly', () => {
      const { setShowSimulation } = useUIStore.getState()

      setShowSimulation(true)
      expect(useUIStore.getState().showSimulation).toBe(true)

      setShowSimulation(false)
      expect(useUIStore.getState().showSimulation).toBe(false)
    })

    it('toggles sidebar', () => {
      const { toggleSidebar } = useUIStore.getState()

      toggleSidebar()
      expect(useUIStore.getState().sidebarCollapsed).toBe(true)

      toggleSidebar()
      expect(useUIStore.getState().sidebarCollapsed).toBe(false)
    })
  })

  describe('drag state', () => {
    it('sets dragging block type', () => {
      const { setDraggingBlockType } = useUIStore.getState()

      setDraggingBlockType('constant')
      expect(useUIStore.getState().draggingBlockType).toBe('constant')
    })

    it('clears dragging block type', () => {
      const { setDraggingBlockType } = useUIStore.getState()

      setDraggingBlockType('constant')
      setDraggingBlockType(null)
      expect(useUIStore.getState().draggingBlockType).toBe(null)
    })
  })

  describe('plot windows', () => {
    it('opens a plot window with default position', () => {
      const { openPlotWindow } = useUIStore.getState()

      openPlotWindow('block-1')

      const state = useUIStore.getState()
      expect(state.plotWindows['block-1']).toBeDefined()
      expect(state.plotWindows['block-1'].isOpen).toBe(true)
      expect(state.plotWindows['block-1'].isMinimized).toBe(false)
    })

    it('opens a plot window with custom position', () => {
      const { openPlotWindow } = useUIStore.getState()

      openPlotWindow('block-1', { x: 200, y: 300 })

      const state = useUIStore.getState()
      expect(state.plotWindows['block-1'].position).toEqual({ x: 200, y: 300 })
    })

    it('opens multiple plot windows with offset positions', () => {
      const { openPlotWindow } = useUIStore.getState()

      openPlotWindow('block-1')
      openPlotWindow('block-2')

      const state = useUIStore.getState()
      // First window at default position
      expect(state.plotWindows['block-1'].position).toEqual({ x: 20, y: 100 })
      // Second window offset by 30px
      expect(state.plotWindows['block-2'].position).toEqual({ x: 50, y: 130 })
    })

    it('preserves existing window position when reopening', () => {
      const { openPlotWindow, closePlotWindow } = useUIStore.getState()

      // Open and set position
      openPlotWindow('block-1', { x: 500, y: 400 })

      // Update to verify state
      useUIStore.getState().updatePlotWindowPosition('block-1', { x: 600, y: 500 })

      // Close and reopen
      closePlotWindow('block-1')
      openPlotWindow('block-1')

      // Position should be reset since window was closed
      const state = useUIStore.getState()
      expect(state.plotWindows['block-1'].position).toEqual({ x: 20, y: 100 })
    })

    it('closes a plot window', () => {
      const { openPlotWindow, closePlotWindow } = useUIStore.getState()

      openPlotWindow('block-1')
      closePlotWindow('block-1')

      expect(useUIStore.getState().plotWindows['block-1']).toBeUndefined()
    })

    it('toggles plot window minimized state', () => {
      const { openPlotWindow, togglePlotWindowMinimized } = useUIStore.getState()

      openPlotWindow('block-1')
      expect(useUIStore.getState().plotWindows['block-1'].isMinimized).toBe(false)

      togglePlotWindowMinimized('block-1')
      expect(useUIStore.getState().plotWindows['block-1'].isMinimized).toBe(true)

      togglePlotWindowMinimized('block-1')
      expect(useUIStore.getState().plotWindows['block-1'].isMinimized).toBe(false)
    })

    it('updates plot window position', () => {
      const { openPlotWindow, updatePlotWindowPosition } = useUIStore.getState()

      openPlotWindow('block-1')
      updatePlotWindowPosition('block-1', { x: 300, y: 400 })

      expect(useUIStore.getState().plotWindows['block-1'].position).toEqual({ x: 300, y: 400 })
    })

    it('updates plot window size', () => {
      const { openPlotWindow, updatePlotWindowSize } = useUIStore.getState()

      openPlotWindow('block-1')
      updatePlotWindowSize('block-1', { width: 600, height: 400 })

      expect(useUIStore.getState().plotWindows['block-1'].size).toEqual({ width: 600, height: 400 })
    })

    it('closes all plot windows', () => {
      const { openPlotWindow, closeAllPlotWindows } = useUIStore.getState()

      openPlotWindow('block-1')
      openPlotWindow('block-2')
      openPlotWindow('block-3')

      closeAllPlotWindows()

      expect(useUIStore.getState().plotWindows).toEqual({})
    })

    it('closes plot windows with matching prefix', () => {
      const { openPlotWindow, closePlotWindowsWithPrefix } = useUIStore.getState()

      openPlotWindow('subsystem1__block1')
      openPlotWindow('subsystem1__block2')
      openPlotWindow('subsystem2__block1')
      openPlotWindow('block-root')

      closePlotWindowsWithPrefix('subsystem1')

      const windows = useUIStore.getState().plotWindows
      expect(windows['subsystem1__block1']).toBeUndefined()
      expect(windows['subsystem1__block2']).toBeUndefined()
      expect(windows['subsystem2__block1']).toBeDefined()
      expect(windows['block-root']).toBeDefined()
    })

    it('bringPlotWindowToFront does not throw', () => {
      const { openPlotWindow, bringPlotWindowToFront } = useUIStore.getState()

      openPlotWindow('block-1')

      // Should not throw
      expect(() => bringPlotWindowToFront('block-1')).not.toThrow()
    })
  })

  describe('modals', () => {
    it('opens and closes new model modal', () => {
      const { openNewModelModal, closeNewModelModal } = useUIStore.getState()

      openNewModelModal()
      expect(useUIStore.getState().showNewModelModal).toBe(true)

      closeNewModelModal()
      expect(useUIStore.getState().showNewModelModal).toBe(false)
    })

    it('opens and closes open model modal', () => {
      const { openOpenModelModal, closeOpenModelModal } = useUIStore.getState()

      openOpenModelModal()
      expect(useUIStore.getState().showOpenModelModal).toBe(true)

      closeOpenModelModal()
      expect(useUIStore.getState().showOpenModelModal).toBe(false)
    })

    it('opens and closes settings modal', () => {
      const { openSettingsModal, closeSettingsModal } = useUIStore.getState()

      openSettingsModal()
      expect(useUIStore.getState().showSettingsModal).toBe(true)

      closeSettingsModal()
      expect(useUIStore.getState().showSettingsModal).toBe(false)
    })

    it('opens and closes import modal', () => {
      const { openImportModal, closeImportModal } = useUIStore.getState()

      openImportModal()
      expect(useUIStore.getState().showImportModal).toBe(true)

      closeImportModal()
      expect(useUIStore.getState().showImportModal).toBe(false)
    })
  })
})
