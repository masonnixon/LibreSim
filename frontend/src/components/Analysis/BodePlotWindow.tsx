import { useMemo, useState, useRef, useEffect, useCallback } from 'react'
import Plot from 'react-plotly.js'
import { useUIStore, PlotWindowState } from '../../store/uiStore'
import type { AnalysisData } from '../../types/simulation'

interface BodePlotWindowProps {
  blockId: string
  blockName: string
  data: AnalysisData
  windowState: PlotWindowState
  zIndex: number
  onFocus: () => void
}

export function BodePlotWindow({
  blockId,
  blockName,
  data,
  windowState,
  zIndex,
  onFocus,
}: BodePlotWindowProps) {
  const {
    closePlotWindow,
    togglePlotWindowMinimized,
    updatePlotWindowPosition,
    updatePlotWindowSize,
  } = useUIStore()

  const { position, size, isMinimized } = windowState

  // Drag state
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })

  // Resize state
  const [isResizing, setIsResizing] = useState(false)
  const [resizeDirection, setResizeDirection] = useState<string | null>(null)
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, width: 0, height: 0, posX: 0, posY: 0 })

  const modalRef = useRef<HTMLDivElement>(null)

  // Minimum dimensions
  const MIN_WIDTH = 400
  const MIN_HEIGHT = 350

  // Drag handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('button')) return
    onFocus()
    setIsDragging(true)
    setDragOffset({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    })
  }

  const handleTouchStart = (e: React.TouchEvent) => {
    if ((e.target as HTMLElement).closest('button')) return
    onFocus()
    const touch = e.touches[0]
    setIsDragging(true)
    setDragOffset({
      x: touch.clientX - position.x,
      y: touch.clientY - position.y,
    })
  }

  // Resize handlers
  const handleResizeStart = useCallback((e: React.MouseEvent | React.TouchEvent, direction: string) => {
    e.preventDefault()
    e.stopPropagation()
    onFocus()
    setIsResizing(true)
    setResizeDirection(direction)

    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY

    setResizeStart({
      x: clientX,
      y: clientY,
      width: size.width,
      height: size.height,
      posX: position.x,
      posY: position.y,
    })
  }, [onFocus, size, position])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        const newX = Math.max(0, Math.min(window.innerWidth - 100, e.clientX - dragOffset.x))
        const newY = Math.max(50, Math.min(window.innerHeight - 50, e.clientY - dragOffset.y))
        updatePlotWindowPosition(blockId, { x: newX, y: newY })
      }

      if (isResizing && resizeDirection) {
        const deltaX = e.clientX - resizeStart.x
        const deltaY = e.clientY - resizeStart.y
        let newWidth = resizeStart.width
        let newHeight = resizeStart.height
        let newX = resizeStart.posX
        let newY = resizeStart.posY

        if (resizeDirection.includes('e')) {
          newWidth = Math.max(MIN_WIDTH, resizeStart.width + deltaX)
        }
        if (resizeDirection.includes('w')) {
          const possibleWidth = resizeStart.width - deltaX
          if (possibleWidth >= MIN_WIDTH) {
            newWidth = possibleWidth
            newX = resizeStart.posX + deltaX
          }
        }
        if (resizeDirection.includes('s')) {
          newHeight = Math.max(MIN_HEIGHT, resizeStart.height + deltaY)
        }
        if (resizeDirection.includes('n')) {
          const possibleHeight = resizeStart.height - deltaY
          if (possibleHeight >= MIN_HEIGHT) {
            newHeight = possibleHeight
            newY = resizeStart.posY + deltaY
          }
        }

        updatePlotWindowSize(blockId, { width: newWidth, height: newHeight })
        updatePlotWindowPosition(blockId, { x: newX, y: newY })
      }
    }

    const handleEnd = () => {
      setIsDragging(false)
      setIsResizing(false)
      setResizeDirection(null)
    }

    if (isDragging || isResizing) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleEnd)
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleEnd)
    }
  }, [isDragging, isResizing, dragOffset, resizeDirection, resizeStart, blockId, updatePlotWindowPosition, updatePlotWindowSize])

  // Convert frequencies to rad/s for display
  const plotData = useMemo(() => {
    if (!data.frequencies || !data.magnitude_db || !data.phase_deg) return { magnitude: [], phase: [] }

    const omega = data.frequencies.map(f => 2 * Math.PI * f)

    return {
      magnitude: [{
        x: omega,
        y: data.magnitude_db,
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: 'Magnitude',
        line: { color: '#89b4fa', width: 2 },
      }],
      phase: [{
        x: omega,
        y: data.phase_deg,
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: 'Phase',
        line: { color: '#f38ba8', width: 2 },
      }],
    }
  }, [data])

  // Resize handle component
  const ResizeHandle = ({ direction, className }: { direction: string; className: string }) => (
    <div
      className={`absolute ${className} opacity-0 hover:opacity-100 transition-opacity`}
      onMouseDown={(e) => handleResizeStart(e, direction)}
      style={{ touchAction: 'none' }}
    />
  )

  const formatMargin = (value: number | null | undefined, unit: string) => {
    if (value === null || value === undefined) return 'N/A'
    return `${value.toFixed(2)} ${unit}`
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
      {/* Header - Draggable */}
      <div
        className="flex items-center justify-between px-3 py-2 border-b border-editor-border bg-slate-800/80 cursor-grab active:cursor-grabbing select-none shrink-0"
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
      >
        <div className="flex items-center gap-2 min-w-0">
          <svg className="w-4 h-4 text-gray-500 shrink-0" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 6a2 2 0 11-4 0 2 2 0 014 0zM8 12a2 2 0 11-4 0 2 2 0 014 0zM8 18a2 2 0 11-4 0 2 2 0 014 0zM14 6a2 2 0 11-4 0 2 2 0 014 0zM14 12a2 2 0 11-4 0 2 2 0 014 0zM14 18a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <span className="text-sm font-medium truncate">{blockName} - Bode Plot</span>
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

      {/* Content - hidden when minimized */}
      {!isMinimized && (
        <div className="flex-1 flex flex-col p-2 min-h-0">
          {/* Magnitude plot */}
          <div className="flex-1 min-h-0">
            <Plot
              data={plotData.magnitude}
              layout={{
                autosize: true,
                margin: { l: 50, r: 10, t: 10, b: 10 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: '#1e1e2e',
                font: { color: '#cdd6f4', size: 10 },
                xaxis: {
                  type: 'log',
                  showticklabels: false,
                  gridcolor: '#45475a',
                  zerolinecolor: '#45475a',
                },
                yaxis: {
                  title: { text: 'Magnitude (dB)', font: { size: 10 } },
                  gridcolor: '#45475a',
                  zerolinecolor: '#585b70',
                  zeroline: true,
                },
                showlegend: false,
              }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
              config={{ responsive: true, displayModeBar: false }}
            />
          </div>

          {/* Phase plot */}
          <div className="flex-1 min-h-0">
            <Plot
              data={plotData.phase}
              layout={{
                autosize: true,
                margin: { l: 50, r: 10, t: 5, b: 30 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: '#1e1e2e',
                font: { color: '#cdd6f4', size: 10 },
                xaxis: {
                  type: 'log',
                  title: { text: 'Frequency (rad/s)', font: { size: 10 } },
                  gridcolor: '#45475a',
                  zerolinecolor: '#45475a',
                },
                yaxis: {
                  title: { text: 'Phase (deg)', font: { size: 10 } },
                  gridcolor: '#45475a',
                  zerolinecolor: '#585b70',
                  zeroline: true,
                },
                showlegend: false,
              }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
              config={{ responsive: true, displayModeBar: false }}
            />
          </div>

          {/* Margins info bar */}
          <div className="flex justify-between text-xs text-gray-400 px-2 py-1 bg-gray-900/50 rounded mt-1">
            <span>Gain Margin: {formatMargin(data.gain_margin, 'dB')}</span>
            <span>Phase Margin: {formatMargin(data.phase_margin, 'deg')}</span>
          </div>
        </div>
      )}

      {/* Resize handles - only when not minimized */}
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
