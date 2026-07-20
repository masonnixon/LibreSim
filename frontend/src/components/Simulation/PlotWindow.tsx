import { useMemo, useRef, useCallback } from 'react'
import Plot from 'react-plotly.js'
import type { PlotRelayoutEvent } from 'plotly.js'
import { useUIStore, PlotWindowState } from '../../store/uiStore'
import type { SignalData } from '../../types/simulation'
import { useDraggableWindow, type ResizeDirection } from '../../hooks/useDraggableWindow'

interface AxisRange {
  xRange?: [number, number]
  yRange?: [number, number]
}

interface PlotWindowProps {
  blockId: string
  blockName: string
  signals: SignalData[]
  windowState: PlotWindowState
  zIndex: number
  onFocus: () => void
}

const PLOT_WINDOW_MIN_SIZE = { width: 300, height: 200 }

export function PlotWindow({
  blockId,
  blockName,
  signals,
  windowState,
  zIndex,
  onFocus,
}: PlotWindowProps) {
  const {
    closePlotWindow,
    togglePlotWindowMinimized,
    updatePlotWindowPosition,
    updatePlotWindowSize,
  } = useUIStore()

  const { position, size, isMinimized } = windowState

  // Store user-set axis ranges to preserve zoom/pan across data updates
  const axisRangeRef = useRef<AxisRange>({})
  const userHasZoomed = useRef(false)

  const modalRef = useRef<HTMLDivElement>(null)
  const handlePositionChange = useCallback(function (nextPosition: { x: number; y: number }) {
    updatePlotWindowPosition(blockId, nextPosition)
  }, [blockId, updatePlotWindowPosition])
  const handleSizeChange = useCallback(function (nextSize: { width: number; height: number }) {
    updatePlotWindowSize(blockId, nextSize)
  }, [blockId, updatePlotWindowSize])
  const {
    isDragging,
    dragHandleProps,
    getResizeHandleProps,
  } = useDraggableWindow({
    position,
    size,
    minSize: PLOT_WINDOW_MIN_SIZE,
    onFocus,
    onPositionChange: handlePositionChange,
    onSizeChange: handleSizeChange,
  })

  // Color palette for multiple traces
  const traceColors = [
    '#89b4fa', // Blue
    '#f38ba8', // Red/Pink
    '#a6e3a1', // Green
    '#fab387', // Orange
    '#cba6f7', // Purple
    '#f9e2af', // Yellow
    '#94e2d5', // Teal
    '#f5c2e7', // Pink
    '#74c7ec', // Light Blue
    '#b4befe', // Lavender
  ]

  const plotData = useMemo(() => {
    if (!signals || signals.length === 0) return []

    // DEBUG: Log raw signal data received by PlotWindow
    console.log(`[PlotWindow ${blockName}] Raw signals:`, JSON.stringify(signals.map(s => ({
      blockId: s.blockId,
      name: s.name,
      numInputs: s.numInputs,
      inputNames: s.inputNames,
      timesLength: s.times?.length,
      valuesType: Array.isArray(s.values) ? (Array.isArray(s.values[0]) ? 'number[][]' : 'number[]') : typeof s.values,
      valuesLength: Array.isArray(s.values) ? s.values.length : 0,
      sampleValues: Array.isArray(s.values) ?
        (Array.isArray(s.values[0]) ?
          (s.values as number[][]).map((arr) => arr?.slice(0, 3)) :
          (s.values as number[]).slice(0, 5)) :
        s.values
    })), null, 2))

    const traces: Array<{
      x: number[]
      y: number[]
      type: 'scatter'
      mode: 'lines'
      name: string
      line: { color: string; width: number }
    }> = []

    signals.forEach((signal) => {
      const numInputs = signal.numInputs || 1
      const inputNames = signal.inputNames || []
      const values = signal.values

      // DEBUG: Log each signal processing
      console.log(`[PlotWindow ${blockName}] Processing signal:`, {
        numInputs,
        inputNames,
        isMultiInput: numInputs > 1 && Array.isArray(values) && Array.isArray(values[0])
      })

      if (numInputs > 1 && Array.isArray(values) && Array.isArray(values[0])) {
        // Multi-input scope: create a trace for each input
        for (let i = 0; i < numInputs; i++) {
          const traceName = inputNames[i] || `Input ${i + 1}`
          const traceValues = (values as number[][])[i] || []
          // DEBUG: Log trace values
          console.log(`[PlotWindow ${blockName}] Trace ${i} (${traceName}):`, {
            valuesLength: traceValues.length,
            first5: traceValues.slice(0, 5),
            last5: traceValues.slice(-5),
            min: Math.min(...traceValues),
            max: Math.max(...traceValues)
          })
          traces.push({
            x: signal.times,
            y: traceValues,
            type: 'scatter' as const,
            mode: 'lines' as const,
            name: traceName,
            line: { color: traceColors[i % traceColors.length], width: 2 },
          })
        }
      } else {
        // Single-input scope or backward compatible format
        const flatValues = values as number[]
        // DEBUG: Log single trace values
        console.log(`[PlotWindow ${blockName}] Single trace (${signal.name}):`, {
          valuesLength: flatValues.length,
          first5: flatValues.slice(0, 5),
          last5: flatValues.slice(-5),
          min: Math.min(...flatValues),
          max: Math.max(...flatValues)
        })
        traces.push({
          x: signal.times,
          y: flatValues,
          type: 'scatter' as const,
          mode: 'lines' as const,
          name: signal.name,
          line: { color: traceColors[0], width: 2 },
        })
      }
    })

    return traces
    // eslint-disable-next-line react-hooks/exhaustive-deps -- traceColors is a constant array defined above, never changes
  }, [signals, blockName])

  // Determine if we should show the legend (multiple traces)
  const showLegend = plotData.length > 1

  // Calculate data bounds for auto-fit when user hasn't zoomed
  const dataBounds = useMemo(() => {
    let xMin = Infinity, xMax = -Infinity, yMin = Infinity, yMax = -Infinity
    for (const trace of plotData) {
      if (trace.x && trace.y) {
        for (const x of trace.x as number[]) {
          if (x < xMin) xMin = x
          if (x > xMax) xMax = x
        }
        for (const y of trace.y as number[]) {
          if (y < yMin) yMin = y
          if (y > yMax) yMax = y
        }
      }
    }
    // Add some padding (5%)
    const xPad = (xMax - xMin) * 0.05 || 0.1
    const yPad = (yMax - yMin) * 0.05 || 0.1
    return {
      xRange: [xMin - xPad, xMax + xPad] as [number, number],
      yRange: [yMin - yPad, yMax + yPad] as [number, number],
    }
  }, [plotData])

  // Handle relayout events to capture user zoom/pan
  const handleRelayout = useCallback((event: PlotRelayoutEvent) => {
    // Check if user has zoomed or panned (explicit range set)
    if (event['xaxis.range[0]'] !== undefined && event['xaxis.range[1]'] !== undefined) {
      axisRangeRef.current.xRange = [event['xaxis.range[0]'] as number, event['xaxis.range[1]'] as number]
      userHasZoomed.current = true
    }
    if (event['yaxis.range[0]'] !== undefined && event['yaxis.range[1]'] !== undefined) {
      axisRangeRef.current.yRange = [event['yaxis.range[0]'] as number, event['yaxis.range[1]'] as number]
      userHasZoomed.current = true
    }
    // Handle autorange reset (double-click to reset)
    if (event['xaxis.autorange'] === true || event['yaxis.autorange'] === true) {
      userHasZoomed.current = false
      axisRangeRef.current = {}
    }
  }, [])

  // Resize handle component
  const ResizeHandle = ({ direction, className }: { direction: ResizeDirection; className: string }) => (
    <div
      className={`absolute ${className} opacity-0 hover:opacity-100 transition-opacity`}
      {...getResizeHandleProps(direction)}
      style={{ touchAction: 'none' }}
    />
  )

  return (
    <div
      ref={modalRef}
      className="fixed bg-editor-surface border border-editor-border rounded-lg shadow-2xl flex flex-col overflow-hidden"
      style={{
        left: position.x,
        top: position.y,
        width: isMinimized ? 250 : size.width,
        height: isMinimized ? 'auto' : size.height,
        zIndex,
        cursor: isDragging ? 'grabbing' : 'default',
      }}
      onMouseDown={onFocus}
    >
      {/* Header - Draggable */}
      <div
        className="flex items-center justify-between px-3 py-2 border-b border-editor-border bg-slate-800/80 cursor-grab active:cursor-grabbing select-none shrink-0"
        {...dragHandleProps}
      >
        <div className="flex items-center gap-2 min-w-0">
          {/* Drag handle indicator */}
          <svg className="w-4 h-4 text-gray-500 shrink-0" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 6a2 2 0 11-4 0 2 2 0 014 0zM8 12a2 2 0 11-4 0 2 2 0 014 0zM8 18a2 2 0 11-4 0 2 2 0 014 0zM14 6a2 2 0 11-4 0 2 2 0 014 0zM14 12a2 2 0 11-4 0 2 2 0 014 0zM14 18a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <span className="text-sm font-medium truncate">{blockName}</span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {/* Minimize/Maximize button */}
          <button
            onClick={() => togglePlotWindowMinimized(blockId)}
            className="p-1.5 text-gray-400 hover:text-white hover:bg-editor-border rounded transition-colors"
            title={isMinimized ? 'Expand' : 'Minimize'}
          >
            {isMinimized ? (
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            ) : (
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            )}
          </button>
          {/* Close button */}
          <button
            onClick={() => closePlotWindow(blockId)}
            className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-editor-border rounded transition-colors"
            title="Close"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Content - hidden when minimized */}
      {!isMinimized && (
        <div className="flex-1 p-2 min-h-0 relative">
          {signals.length === 0 ? (
            <div className="h-full flex items-center justify-center text-gray-400 text-sm">
              No data available
            </div>
          ) : (
            <Plot
              data={plotData}
              layout={{
                autosize: true,
                uirevision: blockId, // Preserve zoom/pan across data updates
                margin: { l: 40, r: 10, t: 10, b: 30 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: '#1e1e2e',
                font: { color: '#cdd6f4', size: 10 },
                xaxis: {
                  title: { text: 'Time (s)', font: { size: 10 } },
                  gridcolor: '#45475a',
                  zerolinecolor: '#45475a',
                  // Always use explicit range to allow panning beyond data
                  range: userHasZoomed.current && axisRangeRef.current.xRange
                    ? axisRangeRef.current.xRange
                    : dataBounds.xRange,
                  autorange: false,
                },
                yaxis: {
                  title: { text: 'Value', font: { size: 10 } },
                  gridcolor: '#45475a',
                  zerolinecolor: '#45475a',
                  // Always use explicit range to allow panning beyond data
                  range: userHasZoomed.current && axisRangeRef.current.yRange
                    ? axisRangeRef.current.yRange
                    : dataBounds.yRange,
                  autorange: false,
                },
                dragmode: 'pan',
                legend: {
                  orientation: 'h',
                  y: -0.15,
                  x: 0.5,
                  xanchor: 'center',
                  font: { size: 9 },
                  bgcolor: 'rgba(30, 30, 46, 0.8)',
                  bordercolor: '#45475a',
                  borderwidth: 1,
                },
                showlegend: showLegend,
              }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
              config={{
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: [
                  'select2d',
                  'lasso2d',
                  'hoverClosestCartesian',
                  'hoverCompareCartesian',
                ],
                modeBarButtonsToAdd: [],
              }}
              onRelayout={handleRelayout}
            />
          )}
        </div>
      )}

      {/* Resize handles - only when not minimized */}
      {!isMinimized && (
        <>
          {/* Edge handles */}
          <ResizeHandle direction="n" className="top-0 left-2 right-2 h-1 cursor-n-resize" />
          <ResizeHandle direction="s" className="bottom-0 left-2 right-2 h-1 cursor-s-resize" />
          <ResizeHandle direction="e" className="right-0 top-2 bottom-2 w-1 cursor-e-resize" />
          <ResizeHandle direction="w" className="left-0 top-2 bottom-2 w-1 cursor-w-resize" />

          {/* Corner handles */}
          <ResizeHandle direction="nw" className="top-0 left-0 w-3 h-3 cursor-nw-resize" />
          <ResizeHandle direction="ne" className="top-0 right-0 w-3 h-3 cursor-ne-resize" />
          <ResizeHandle direction="sw" className="bottom-0 left-0 w-3 h-3 cursor-sw-resize" />
          <ResizeHandle direction="se" className="bottom-0 right-0 w-3 h-3 cursor-se-resize" />

          {/* Visual resize indicator in bottom-right corner */}
          <div className="absolute bottom-1 right-1 w-3 h-3 pointer-events-none opacity-50">
            <svg viewBox="0 0 24 24" fill="currentColor" className="text-gray-500">
              <path d="M22 22H20V20H22V22ZM22 18H20V16H22V18ZM18 22H16V20H18V22ZM22 14H20V12H22V14ZM18 18H16V16H18V18ZM14 22H12V20H14V22Z" />
            </svg>
          </div>
        </>
      )}
    </div>
  )
}
