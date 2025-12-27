import { useEffect, useState, useCallback } from 'react'
import { PlotWindow } from './PlotWindow'
import { useSimulationStore } from '../../store/simulationStore'
import { useModelStore } from '../../store/modelStore'
import { useUIStore } from '../../store/uiStore'
import type { SignalData } from '../../types/simulation'
import type { BlockInstance } from '../../types/block'

interface ScopeWindowInfo {
  blockId: string
  blockName: string
  signals: SignalData[]
}

/**
 * Recursively find all scope blocks in the model, including inside subsystems.
 * Returns blocks with their flattened IDs (matching backend naming convention).
 *
 * @param blocks - The blocks to search
 * @param parentIdPath - The flattened ID path for backend matching (uses block IDs)
 * @param parentNamePath - The display name path for UI (uses block names)
 */
function findAllScopeBlocks(
  blocks: BlockInstance[],
  parentIdPath: string = '',
  parentNamePath: string = ''
): Array<{ block: BlockInstance; flattenedId: string; displayName: string }> {
  const result: Array<{ block: BlockInstance; flattenedId: string; displayName: string }> = []

  for (const block of blocks) {
    const flattenedId = parentIdPath ? `${parentIdPath}__${block.id}` : block.id
    const displayName = parentNamePath
      ? `${parentNamePath}/${block.name}`
      : block.name

    if (block.type === 'scope' || block.type === 'xy_graph') {
      result.push({ block, flattenedId, displayName })
    }

    // Recursively search in subsystem children
    if (block.type === 'subsystem' && block.children) {
      const childScopes = findAllScopeBlocks(block.children, flattenedId, block.name)
      result.push(...childScopes)
    }
  }

  return result
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
    // Find all scope blocks recursively (including in subsystems)
    const allScopes = findAllScopeBlocks(model.blocks)

    for (const { block, flattenedId, displayName } of allScopes) {
      // Find signals that belong to this scope block (using flattened ID from backend)
      const blockSignals = results.signals.filter(
        (signal) => signal.blockId === flattenedId
      )

      if (blockSignals.length > 0) {
        scopeWindows.push({
          blockId: flattenedId,
          blockName: displayName || block.name || block.type,
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
    // eslint-disable-next-line react-hooks/exhaustive-deps -- We intentionally use scopeWindows.length to trigger, but reference scopeWindows/openPlotWindow/plotWindows for current values
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
        const blockName = scopeInfo?.blockName || 'Plot'
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
