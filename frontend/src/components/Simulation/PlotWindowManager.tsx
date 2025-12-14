import { useEffect, useState, useCallback } from 'react'
import { PlotWindow } from './PlotWindow'
import { useSimulationStore } from '../../store/simulationStore'
import { useModelStore } from '../../store/modelStore'
import { useUIStore } from '../../store/uiStore'
import type { SignalData } from '../../types/simulation'

interface ScopeWindowInfo {
  blockId: string
  blockName: string
  signals: SignalData[]
}

export function PlotWindowManager() {
  const { results, state } = useSimulationStore()
  const { model } = useModelStore()
  const { plotWindows, openPlotWindow, closeAllPlotWindows } = useUIStore()

  // Track z-index for window stacking
  const [windowOrder, setWindowOrder] = useState<string[]>([])

  // Get all scope blocks from the model and their signals
  const scopeWindows: ScopeWindowInfo[] = []

  if (model && results) {
    // Find all scope blocks
    const scopeBlocks = model.blocks.filter(
      (block) => block.type === 'scope' || block.type === 'xy_graph'
    )

    for (const block of scopeBlocks) {
      // Find signals that belong to this scope block
      const blockSignals = results.signals.filter(
        (signal) => signal.blockId === block.id
      )

      if (blockSignals.length > 0) {
        scopeWindows.push({
          blockId: block.id,
          blockName: block.name || block.type,
          signals: blockSignals,
        })
      }
    }
  }

  // Auto-open windows for new scope blocks when simulation completes
  useEffect(() => {
    if (state.status === 'completed' && scopeWindows.length > 0) {
      // Open windows for each scope block
      scopeWindows.forEach((scope, index) => {
        if (!plotWindows[scope.blockId]) {
          openPlotWindow(scope.blockId, {
            x: 20 + (index * 40),
            y: 100 + (index * 40),
          })
        }
      })

      // Initialize window order
      setWindowOrder(scopeWindows.map((s) => s.blockId))
    }
  }, [state.status, scopeWindows.length])

  // Clear windows when simulation resets
  useEffect(() => {
    if (state.status === 'idle' && !results) {
      closeAllPlotWindows()
      setWindowOrder([])
    }
  }, [state.status, results, closeAllPlotWindows])

  // Bring window to front
  const bringToFront = useCallback((blockId: string) => {
    setWindowOrder((prev) => {
      const filtered = prev.filter((id) => id !== blockId)
      return [...filtered, blockId]
    })
  }, [])

  // Render plot windows
  const openWindowIds = Object.keys(plotWindows)

  if (openWindowIds.length === 0) {
    return null
  }

  return (
    <>
      {openWindowIds.map((blockId) => {
        const windowState = plotWindows[blockId]
        if (!windowState?.isOpen) return null

        // Find the scope info for this block
        const scopeInfo = scopeWindows.find((s) => s.blockId === blockId)
        const blockName = scopeInfo?.blockName ||
          model?.blocks.find((b) => b.id === blockId)?.name ||
          'Plot'
        const signals = scopeInfo?.signals || []

        // Calculate z-index based on window order
        const orderIndex = windowOrder.indexOf(blockId)
        const zIndex = 50 + (orderIndex >= 0 ? orderIndex : openWindowIds.length)

        return (
          <PlotWindow
            key={blockId}
            blockId={blockId}
            blockName={blockName}
            signals={signals}
            windowState={windowState}
            zIndex={zIndex}
            onFocus={() => bringToFront(blockId)}
          />
        )
      })}
    </>
  )
}
