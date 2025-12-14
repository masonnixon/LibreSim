import { useMemo, useState, useRef, useEffect } from 'react'
import Plot from 'react-plotly.js'
import { useSimulationStore } from '../../store/simulationStore'
import { useUIStore } from '../../store/uiStore'

export function SimulationPanel() {
  const { results, state } = useSimulationStore()
  const { toggleSimulation } = useUIStore()

  // Modal state
  const [isMinimized, setIsMinimized] = useState(false)
  const [position, setPosition] = useState({ x: 20, y: window.innerHeight - 320 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const modalRef = useRef<HTMLDivElement>(null)

  // Responsive sizing
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768
      setIsMobile(mobile)
      // Reset position when switching to/from mobile
      if (mobile) {
        setPosition({ x: 10, y: window.innerHeight - 280 })
      }
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Drag handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('button')) return
    setIsDragging(true)
    setDragOffset({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    })
  }

  const handleTouchStart = (e: React.TouchEvent) => {
    if ((e.target as HTMLElement).closest('button')) return
    const touch = e.touches[0]
    setIsDragging(true)
    setDragOffset({
      x: touch.clientX - position.x,
      y: touch.clientY - position.y,
    })
  }

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return
      const newX = Math.max(0, Math.min(window.innerWidth - 100, e.clientX - dragOffset.x))
      const newY = Math.max(50, Math.min(window.innerHeight - 50, e.clientY - dragOffset.y))
      setPosition({ x: newX, y: newY })
    }

    const handleTouchMove = (e: TouchEvent) => {
      if (!isDragging) return
      const touch = e.touches[0]
      const newX = Math.max(0, Math.min(window.innerWidth - 100, touch.clientX - dragOffset.x))
      const newY = Math.max(50, Math.min(window.innerHeight - 50, touch.clientY - dragOffset.y))
      setPosition({ x: newX, y: newY })
    }

    const handleEnd = () => {
      setIsDragging(false)
    }

    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleEnd)
      window.addEventListener('touchmove', handleTouchMove)
      window.addEventListener('touchend', handleEnd)
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleEnd)
      window.removeEventListener('touchmove', handleTouchMove)
      window.removeEventListener('touchend', handleEnd)
    }
  }, [isDragging, dragOffset])

  const plotData = useMemo(() => {
    if (!results || results.signals.length === 0) return []

    return results.signals.map((signal) => ({
      x: signal.times,
      y: signal.values,
      type: 'scatter' as const,
      mode: 'lines' as const,
      name: signal.name,
    }))
  }, [results])

  // Modal dimensions
  const modalWidth = isMobile ? 'calc(100vw - 20px)' : '500px'
  const modalHeight = isMinimized ? 'auto' : (isMobile ? '220px' : '280px')

  return (
    <div
      ref={modalRef}
      className="fixed z-50 bg-editor-surface border border-editor-border rounded-lg shadow-2xl flex flex-col overflow-hidden"
      style={{
        left: position.x,
        top: position.y,
        width: modalWidth,
        height: modalHeight,
        cursor: isDragging ? 'grabbing' : 'default',
      }}
    >
      {/* Header - Draggable */}
      <div
        className="flex items-center justify-between px-3 py-2 border-b border-editor-border bg-slate-800/80 cursor-grab active:cursor-grabbing select-none"
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
      >
        <div className="flex items-center gap-2">
          {/* Drag handle indicator */}
          <svg className="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 6a2 2 0 11-4 0 2 2 0 014 0zM8 12a2 2 0 11-4 0 2 2 0 014 0zM8 18a2 2 0 11-4 0 2 2 0 014 0zM14 6a2 2 0 11-4 0 2 2 0 014 0zM14 12a2 2 0 11-4 0 2 2 0 014 0zM14 18a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <h3 className="font-semibold text-sm">Simulation Results</h3>
          {results?.statistics && !isMinimized && (
            <span className="text-xs text-gray-400 hidden sm:inline">
              {results.statistics.totalSteps} steps | {results.statistics.executionTime.toFixed(1)}ms
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {/* Minimize/Maximize button */}
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1.5 text-gray-400 hover:text-white hover:bg-editor-border rounded transition-colors"
            title={isMinimized ? 'Expand' : 'Minimize'}
          >
            {isMinimized ? (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            )}
          </button>
          {/* Close button */}
          <button
            onClick={toggleSimulation}
            className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-editor-border rounded transition-colors"
            title="Close panel"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Content - hidden when minimized */}
      {!isMinimized && (
        <div className="flex-1 p-2 min-h-0">
          {state.status === 'idle' && !results && (
            <div className="h-full flex items-center justify-center text-gray-400 text-sm">
              Run a simulation to see results
            </div>
          )}

          {state.status === 'running' && (
            <div className="h-full flex items-center justify-center text-gray-400">
              <div className="text-center">
                <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2" />
                <p className="text-sm">Simulating... {Math.round(state.progress * 100)}%</p>
              </div>
            </div>
          )}

          {state.status === 'error' && (
            <div className="h-full flex items-center justify-center text-red-400">
              <div className="text-center">
                <p className="font-semibold text-sm">Simulation Error</p>
                <p className="text-xs">{state.error}</p>
              </div>
            </div>
          )}

          {results && results.signals.length > 0 && (
            <Plot
              data={plotData}
              layout={{
                autosize: true,
                margin: { l: 40, r: 10, t: 10, b: 30 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: '#1e1e2e',
                font: { color: '#cdd6f4', size: 10 },
                xaxis: {
                  title: { text: 'Time (s)', font: { size: 10 } },
                  gridcolor: '#45475a',
                  zerolinecolor: '#45475a',
                },
                yaxis: {
                  title: { text: 'Value', font: { size: 10 } },
                  gridcolor: '#45475a',
                  zerolinecolor: '#45475a',
                },
                legend: {
                  orientation: 'h',
                  y: -0.25,
                  font: { size: 9 },
                },
                showlegend: results.signals.length > 1,
              }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
              config={{ responsive: true, displayModeBar: false }}
            />
          )}
        </div>
      )}
    </div>
  )
}
