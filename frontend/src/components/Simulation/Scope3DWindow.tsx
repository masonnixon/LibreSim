import { useMemo, useRef, useCallback } from 'react'
import Plot from 'react-plotly.js'
import type { PlotRelayoutEvent } from 'plotly.js'
import { useUIStore, PlotWindowState } from '../../store/uiStore'
import type { SignalData } from '../../types/simulation'
import { useDraggableWindow, type ResizeDirection } from '../../hooks/useDraggableWindow'

interface CameraState {
  eye?: { x: number; y: number; z: number }
  center?: { x: number; y: number; z: number }
  up?: { x: number; y: number; z: number }
}

interface Scope3DWindowProps {
  blockId: string
  blockName: string
  signal: SignalData
  windowState: PlotWindowState
  zIndex: number
  onFocus: () => void
}

const SCOPE_3D_MIN_SIZE = { width: 450, height: 400 }

export function Scope3DWindow({
  blockId,
  blockName,
  signal,
  windowState,
  zIndex,
  onFocus,
}: Scope3DWindowProps) {
  const {
    closePlotWindow,
    togglePlotWindowMinimized,
    updatePlotWindowPosition,
    updatePlotWindowSize,
  } = useUIStore()

  // Store camera state to preserve orientation across data updates
  const cameraRef = useRef<CameraState | null>(null)

  // Track data revision to help Plotly know when to update data vs layout
  const dataRevision = useRef(0)
  const prevDataLength = useRef(0)

  // Increment revision only when data length changes
  if (signal.x && signal.x.length !== prevDataLength.current) {
    dataRevision.current += 1
    prevDataLength.current = signal.x.length
  }

  const { position, size, isMinimized } = windowState

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
    minSize: SCOPE_3D_MIN_SIZE,
    onFocus,
    onPositionChange: handlePositionChange,
    onSizeChange: handleSizeChange,
  })

  // Build 3D plot data
  const plotData = useMemo(() => {
    if (!signal.x || !signal.y || !signal.z) return []

    const inputNames = signal.inputNames || ['X', 'Y', 'Z']

    return [{
      type: 'scatter3d' as const,
      mode: 'lines' as const,
      x: signal.x,
      y: signal.y,
      z: signal.z,
      line: {
        color: '#89b4fa',
        width: 3,
      },
      name: signal.name,
      hovertemplate:
        `${inputNames[0]}: %{x:.4f}<br>` +
        `${inputNames[1]}: %{y:.4f}<br>` +
        `${inputNames[2]}: %{z:.4f}<br>` +
        '<extra></extra>',
    }]
  }, [signal])

  // Axis labels from signal
  const axisLabels = signal.inputNames || ['X', 'Y', 'Z']

  // Track if user has interacted with the camera
  const userHasRotated = useRef(false)

  // Handle camera changes from user interaction
  const handleRelayout = useCallback((event: PlotRelayoutEvent) => {
    // Cast to record type to access dynamic scene.camera keys
    const evt = event as Record<string, unknown>

    // Check if this is a camera change event (full camera object)
    if (evt['scene.camera']) {
      cameraRef.current = evt['scene.camera'] as CameraState
      userHasRotated.current = true
    }
    // Also handle individual camera property updates
    else if (evt['scene.camera.eye'] || evt['scene.camera.center'] || evt['scene.camera.up']) {
      cameraRef.current = {
        ...cameraRef.current,
        eye: (evt['scene.camera.eye'] as CameraState['eye']) || cameraRef.current?.eye,
        center: (evt['scene.camera.center'] as CameraState['center']) || cameraRef.current?.center,
        up: (evt['scene.camera.up'] as CameraState['up']) || cameraRef.current?.up,
      }
      userHasRotated.current = true
    }
    // Handle reset camera button
    if (evt['scene.camera'] === undefined &&
        evt['scene.camera.eye'] === undefined &&
        evt['scene.camera.center'] === undefined &&
        evt['scene.camera.up'] === undefined &&
        Object.keys(event).some(k => k.startsWith('scene'))) {
      // This might be a reset - check for autorange or similar
      userHasRotated.current = false
      cameraRef.current = null
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
          <span className="text-sm font-medium truncate">{blockName} - 3D Plot</span>
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
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 min-h-0">
            {!signal.x || signal.x.length === 0 ? (
              <div className="h-full flex items-center justify-center text-gray-400 text-sm">
                No data available
              </div>
            ) : (
              <Plot
                data={plotData}
                revision={dataRevision.current}
                layout={{
                  autosize: true,
                  uirevision: blockId, // Preserve camera orientation/zoom across data updates
                  datarevision: dataRevision.current,
                  margin: { l: 0, r: 0, t: 0, b: 0 },
                  paper_bgcolor: 'transparent',
                  scene: {
                    bgcolor: '#1e1e2e',
                    domain: { x: [0, 1], y: [0, 1] },
                    xaxis: {
                      title: { text: axisLabels[0], font: { size: 10, color: '#cdd6f4' } },
                      gridcolor: '#45475a',
                      zerolinecolor: '#585b70',
                      tickfont: { size: 9, color: '#a6adc8' },
                    },
                    yaxis: {
                      title: { text: axisLabels[1], font: { size: 10, color: '#cdd6f4' } },
                      gridcolor: '#45475a',
                      zerolinecolor: '#585b70',
                      tickfont: { size: 9, color: '#a6adc8' },
                    },
                    zaxis: {
                      title: { text: axisLabels[2], font: { size: 10, color: '#cdd6f4' } },
                      gridcolor: '#45475a',
                      zerolinecolor: '#585b70',
                      tickfont: { size: 9, color: '#a6adc8' },
                    },
                    aspectmode: 'cube',
                    // Use stored camera state if user has rotated, otherwise use default
                    ...(userHasRotated.current && cameraRef.current
                      ? { camera: cameraRef.current }
                      : { camera: { eye: { x: 1.5, y: 1.5, z: 1.2 } } }),
                  },
                  showlegend: false,
                }}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler
                config={{
                  responsive: true,
                  displayModeBar: true,
                  displaylogo: false,
                  modeBarButtonsToRemove: ['sendDataToCloud'],
                }}
                onRelayout={handleRelayout}
              />
            )}
          </div>
        </div>
      )}

      {/* Info bar */}
      {!isMinimized && signal.x && signal.x.length > 0 && (
        <div className="flex justify-between text-xs text-gray-400 px-2 py-1 bg-gray-900/50 border-t border-editor-border">
          <span>Points: {signal.x.length}</span>
          <span>Drag to rotate, scroll to zoom</span>
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
