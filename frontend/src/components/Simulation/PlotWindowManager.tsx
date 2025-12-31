import { useEffect, useState, useCallback } from 'react'
import { PlotWindow } from './PlotWindow'
import { BodePlotWindow, NyquistPlotWindow, PoleZeroMapWindow, StepResponseWindow } from '../Analysis'
import { useSimulationStore } from '../../store/simulationStore'
import { useModelStore } from '../../store/modelStore'
import { useUIStore } from '../../store/uiStore'
import type { SignalData, AnalysisData } from '../../types/simulation'
import type { BlockInstance } from '../../types/block'

interface ScopeWindowInfo {
  blockId: string
  blockName: string
  signals: SignalData[]
}

interface AnalysisWindowInfo {
  blockId: string
  blockName: string
  data: AnalysisData
}

// Analysis block types
const ANALYSIS_BLOCK_TYPES = ['bode_plot', 'nyquist_plot', 'pole_zero_map', 'step_info']

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

/**
 * Recursively find all analysis blocks in the model.
 */
function findAllAnalysisBlocks(
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

    if (ANALYSIS_BLOCK_TYPES.includes(block.type)) {
      result.push({ block, flattenedId, displayName })
    }

    // Recursively search in subsystem children
    if (block.type === 'subsystem' && block.children) {
      const childAnalysis = findAllAnalysisBlocks(block.children, flattenedId, block.name)
      result.push(...childAnalysis)
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
  // Get all analysis blocks from the model and their data
  const analysisWindows: AnalysisWindowInfo[] = []

  if (model && results) {
    // Find all scope blocks recursively (including in subsystems)
    const allScopes = findAllScopeBlocks(model.blocks)

    // DEBUG: Log scope matching info
    console.log('[PlotWindowManager] Matching scopes to signals:', {
      modelScopeCount: allScopes.length,
      resultSignalCount: results.signals?.length,
      modelScopes: allScopes.map(s => ({ id: s.flattenedId, name: s.displayName })),
      resultBlockIds: results.signals?.map(s => s.blockId)
    })

    for (const { block, flattenedId, displayName } of allScopes) {
      // Find signals that belong to this scope block (using flattened ID from backend)
      const blockSignals = results.signals.filter(
        (signal) => signal.blockId === flattenedId
      )

      // DEBUG: Log each scope's signal matching
      console.log(`[PlotWindowManager] Scope "${displayName}" (${flattenedId}):`, {
        matchedSignals: blockSignals.length,
        signalDetails: blockSignals.map(s => ({
          name: s.name,
          numInputs: s.numInputs,
          inputNames: s.inputNames
        }))
      })

      if (blockSignals.length > 0) {
        scopeWindows.push({
          blockId: flattenedId,
          blockName: displayName || block.name || block.type,
          signals: blockSignals,
        })
      }
    }

    // Find all analysis blocks and their data
    if (results.analyses) {
      const allAnalysis = findAllAnalysisBlocks(model.blocks)

      for (const { block, flattenedId, displayName } of allAnalysis) {
        const analysisData = results.analyses[flattenedId]
        if (analysisData) {
          analysisWindows.push({
            blockId: flattenedId,
            blockName: displayName || block.name || block.type,
            data: analysisData,
          })
        }
      }

      console.log('[PlotWindowManager] Analysis windows:', analysisWindows.map(a => ({
        id: a.blockId,
        name: a.blockName,
        type: a.data.analysisType
      })))
    }
  }

  // Auto-open windows for new scope and analysis blocks when simulation completes
  useEffect(() => {
    if (state.status === 'completed' && (scopeWindows.length > 0 || analysisWindows.length > 0)) {
      let windowIndex = 0

      // Open windows for each scope block
      scopeWindows.forEach((scope) => {
        if (!plotWindows[scope.blockId]) {
          openPlotWindow(scope.blockId, {
            x: 20 + (windowIndex * 40),
            y: 100 + (windowIndex * 40),
          })
          windowIndex++
        }
      })

      // Open windows for each analysis block
      analysisWindows.forEach((analysis) => {
        if (!plotWindows[analysis.blockId]) {
          openPlotWindow(analysis.blockId, {
            x: 20 + (windowIndex * 40),
            y: 100 + (windowIndex * 40),
          })
          windowIndex++
        }
      })

      // Initialize window order
      setWindowOrder([
        ...scopeWindows.map((s) => s.blockId),
        ...analysisWindows.map((a) => a.blockId),
      ])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- We intentionally use scopeWindows.length/analysisWindows.length to trigger, but reference arrays for current values
  }, [state.status, scopeWindows.length, analysisWindows.length])

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

        // Calculate z-index based on window order
        const orderIndex = windowOrder.indexOf(blockId)
        const zIndex = 50 + (orderIndex >= 0 ? orderIndex : openWindowIds.length)

        // Check if this is an analysis window
        const analysisInfo = analysisWindows.find((a) => a.blockId === blockId)
        if (analysisInfo) {
          const { data, blockName } = analysisInfo
          const commonProps = {
            key: blockId,
            blockId,
            blockName,
            data,
            windowState,
            zIndex,
            onFocus: () => bringToFront(blockId),
          }

          switch (data.analysisType) {
            case 'bode':
              return <BodePlotWindow {...commonProps} />
            case 'nyquist':
              return <NyquistPlotWindow {...commonProps} />
            case 'pzmap':
              return <PoleZeroMapWindow {...commonProps} />
            case 'stepinfo':
              return <StepResponseWindow {...commonProps} />
            default:
              return null
          }
        }

        // Find the scope info for this block
        const scopeInfo = scopeWindows.find((s) => s.blockId === blockId)
        const blockName = scopeInfo?.blockName || 'Plot'
        const signals = scopeInfo?.signals || []

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
