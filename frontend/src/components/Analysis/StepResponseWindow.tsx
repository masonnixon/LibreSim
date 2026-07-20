import { useMemo, useRef, useCallback } from 'react'
import Plot from 'react-plotly.js'
import { useUIStore, PlotWindowState } from '../../store/uiStore'
import type { AnalysisData } from '../../types/simulation'
import { useDraggableWindow, type ResizeDirection } from '../../hooks/useDraggableWindow'

interface StepResponseWindowProps {
  blockId: string
  blockName: string
  data: AnalysisData
  windowState: PlotWindowState
  zIndex: number
  onFocus: () => void
}

const STEP_RESPONSE_MIN_SIZE = { width: 400, height: 350 }

export function StepResponseWindow({
  blockId,
  blockName,
  data,
  windowState,
  zIndex,
  onFocus,
}: StepResponseWindowProps) {
  const {
    closePlotWindow,
    togglePlotWindowMinimized,
    updatePlotWindowPosition,
    updatePlotWindowSize,
  } = useUIStore()

  const { position, size, isMinimized } = windowState

  const modalRef = useRef<HTMLDivElement>(null)
  const handlePositionChange = useCallback(function (nextPosition: { x: number; y: number }) {
    updatePlotWindowPosition(blockId, nextPosition)
  }, [blockId, updatePlotWindowPosition])
  const handleSizeChange = useCallback(function (nextSize: { width: number; height: number }) {
    updatePlotWindowSize(blockId, nextSize)
  }, [blockId, updatePlotWindowSize])
  const { isDragging, dragHandleProps, getResizeHandleProps } = useDraggableWindow({
    position,
    size,
    minSize: STEP_RESPONSE_MIN_SIZE,
    onFocus,
    onPositionChange: handlePositionChange,
    onSizeChange: handleSizeChange,
  })


  const plotData = useMemo(() => {
    if (!data.times || !data.response) return []

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const traces: any[] = [
      // Step response curve
      {
        x: data.times,
        y: data.response,
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: 'Response',
        line: { color: '#89b4fa', width: 2 },
      },
    ]

    // Add steady-state line if available
    if (data.steady_state_value !== null && data.steady_state_value !== undefined) {
      const tMax = data.times[data.times.length - 1]
      traces.push({
        x: [0, tMax],
        y: [data.steady_state_value, data.steady_state_value],
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: 'Steady State',
        line: { color: '#a6e3a1', width: 1, dash: 'dash' as const },
      })
    }

    // Add peak marker if there's overshoot
    if (data.peak_time !== null && data.peak_time !== undefined &&
        data.peak_value !== null && data.peak_value !== undefined &&
        data.overshoot_percent !== null && data.overshoot_percent !== undefined &&
        data.overshoot_percent > 0.5) {
      traces.push({
        x: [data.peak_time],
        y: [data.peak_value],
        type: 'scatter' as const,
        mode: 'markers' as const,
        name: `Peak (${data.overshoot_percent.toFixed(1)}%)`,
        marker: { color: '#f38ba8', size: 10, symbol: 'circle' as const },
      })
    }

    return traces
  }, [data])

  const ResizeHandle = ({ direction, className }: { direction: ResizeDirection; className: string }) => (
    <div
      className={`absolute ${className} opacity-0 hover:opacity-100 transition-opacity`}
      {...getResizeHandleProps(direction)}
      style={{ touchAction: 'none' }}
    />
  )

  const formatValue = (val: number | null | undefined, unit: string = '') => {
    if (val === null || val === undefined) return 'N/A'
    return `${val.toFixed(3)}${unit}`
  }

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
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 py-2 border-b border-editor-border bg-slate-800/80 cursor-grab active:cursor-grabbing select-none shrink-0"
        {...dragHandleProps}
      >
        <div className="flex items-center gap-2 min-w-0">
          <svg className="w-4 h-4 text-gray-500 shrink-0" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 6a2 2 0 11-4 0 2 2 0 014 0zM8 12a2 2 0 11-4 0 2 2 0 014 0zM8 18a2 2 0 11-4 0 2 2 0 014 0zM14 6a2 2 0 11-4 0 2 2 0 014 0zM14 12a2 2 0 11-4 0 2 2 0 014 0zM14 18a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <span className="text-sm font-medium truncate">{blockName} - Step Response</span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
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

      {/* Content */}
      {!isMinimized && (
        <div className="flex-1 flex flex-col p-2 min-h-0">
          <div className="flex-1 min-h-0">
            <Plot
              data={plotData}
              layout={{
                autosize: true,
                margin: { l: 50, r: 20, t: 10, b: 40 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: '#1e1e2e',
                font: { color: '#cdd6f4', size: 10 },
                xaxis: {
                  title: { text: 'Time (s)', font: { size: 10 } },
                  gridcolor: '#45475a',
                  zerolinecolor: '#45475a',
                },
                yaxis: {
                  title: { text: 'Response', font: { size: 10 } },
                  gridcolor: '#45475a',
                  zerolinecolor: '#45475a',
                },
                showlegend: true,
                legend: {
                  orientation: 'h',
                  y: -0.12,
                  x: 0.5,
                  xanchor: 'center',
                  font: { size: 9 },
                  bgcolor: 'rgba(30, 30, 46, 0.8)',
                  bordercolor: '#45475a',
                  borderwidth: 1,
                },
              }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
              config={{ responsive: true, displayModeBar: false }}
            />
          </div>

          {/* Info bar - two rows of metrics */}
          <div className="flex flex-col gap-1 text-xs text-gray-400 px-2 py-1 bg-gray-900/50 rounded mt-1">
            <div className="flex justify-between">
              <span>Rise Time: {formatValue(data.rise_time, 's')}</span>
              <span>Settling Time: {formatValue(data.settling_time, 's')}</span>
              <span>Overshoot: {formatValue(data.overshoot_percent, '%')}</span>
            </div>
            <div className="flex justify-between">
              <span>Peak Time: {formatValue(data.peak_time, 's')}</span>
              <span>Peak Value: {formatValue(data.peak_value)}</span>
              <span>Steady State: {formatValue(data.steady_state_value)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Resize handles */}
      {!isMinimized && (
        <>
          <ResizeHandle direction="n" className="top-0 left-2 right-2 h-1 cursor-n-resize" />
          <ResizeHandle direction="s" className="bottom-0 left-2 right-2 h-1 cursor-s-resize" />
          <ResizeHandle direction="e" className="right-0 top-2 bottom-2 w-1 cursor-e-resize" />
          <ResizeHandle direction="w" className="left-0 top-2 bottom-2 w-1 cursor-w-resize" />
          <ResizeHandle direction="nw" className="top-0 left-0 w-3 h-3 cursor-nw-resize" />
          <ResizeHandle direction="ne" className="top-0 right-0 w-3 h-3 cursor-ne-resize" />
          <ResizeHandle direction="sw" className="bottom-0 left-0 w-3 h-3 cursor-sw-resize" />
          <ResizeHandle direction="se" className="bottom-0 right-0 w-3 h-3 cursor-se-resize" />
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
