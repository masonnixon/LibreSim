import { useMemo } from 'react'
import Plot from 'react-plotly.js'
import { useSimulationStore } from '../../store/simulationStore'
import { useUIStore } from '../../store/uiStore'

export function SimulationPanel() {
  const { results, state } = useSimulationStore()
  const { toggleSimulation } = useUIStore()

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

  return (
    <div className="h-64 bg-editor-surface border-t border-editor-border flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-editor-border">
        <div className="flex items-center gap-4">
          <h3 className="font-semibold text-sm">Simulation Results</h3>
          {results?.statistics && (
            <div className="text-xs text-gray-400">
              Steps: {results.statistics.totalSteps} | Execution:{' '}
              {results.statistics.executionTime.toFixed(2)}ms
            </div>
          )}
        </div>
        <button
          onClick={toggleSimulation}
          className="p-1 text-gray-400 hover:text-white hover:bg-editor-border rounded"
          title="Close panel"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 p-2">
        {state.status === 'idle' && !results && (
          <div className="h-full flex items-center justify-center text-gray-400">
            Run a simulation to see results here
          </div>
        )}

        {state.status === 'running' && (
          <div className="h-full flex items-center justify-center text-gray-400">
            <div className="text-center">
              <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2" />
              <p>Simulating... {Math.round(state.progress * 100)}%</p>
            </div>
          </div>
        )}

        {state.status === 'error' && (
          <div className="h-full flex items-center justify-center text-red-400">
            <div className="text-center">
              <p className="font-semibold">Simulation Error</p>
              <p className="text-sm">{state.error}</p>
            </div>
          </div>
        )}

        {results && results.signals.length > 0 && (
          <Plot
            data={plotData}
            layout={{
              autosize: true,
              margin: { l: 50, r: 20, t: 20, b: 40 },
              paper_bgcolor: 'transparent',
              plot_bgcolor: '#1e1e2e',
              font: { color: '#cdd6f4' },
              xaxis: {
                title: 'Time (s)',
                gridcolor: '#45475a',
                zerolinecolor: '#45475a',
              },
              yaxis: {
                title: 'Value',
                gridcolor: '#45475a',
                zerolinecolor: '#45475a',
              },
              legend: {
                orientation: 'h',
                y: -0.2,
              },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true, displayModeBar: false }}
          />
        )}
      </div>
    </div>
  )
}
