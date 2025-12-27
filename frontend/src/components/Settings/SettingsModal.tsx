import { useState, useEffect } from 'react'
import { useModelStore } from '../../store/modelStore'
import { useUIStore } from '../../store/uiStore'
import type { SolverType } from '../../types/simulation'

export function SettingsModal() {
  const { model, updateSimulationConfig, updateMetadata } = useModelStore()
  const { showSettingsModal, closeSettingsModal } = useUIStore()

  // Local state for form values
  const [solver, setSolver] = useState<SolverType>('rk4')
  const [stepSize, setStepSize] = useState(0.01)
  const [startTime, setStartTime] = useState(0)
  const [stopTime, setStopTime] = useState(10)
  const [modelName, setModelName] = useState('')
  const [description, setDescription] = useState('')

  // Sync local state with model when modal opens
  useEffect(() => {
    if (showSettingsModal && model) {
      setSolver(model.simulationConfig.solver)
      setStepSize(model.simulationConfig.stepSize)
      setStartTime(model.simulationConfig.startTime)
      setStopTime(model.simulationConfig.stopTime)
      setModelName(model.metadata.name)
      setDescription(model.metadata.description)
    }
  }, [showSettingsModal, model])

  if (!showSettingsModal || !model) return null

  const handleSave = () => {
    updateSimulationConfig({
      solver,
      stepSize,
      startTime,
      stopTime,
    })
    updateMetadata({
      name: modelName,
      description,
    })
    closeSettingsModal()
  }

  const handleCancel = () => {
    closeSettingsModal()
  }

  // Close on Escape key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleCancel()
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100]"
      onClick={handleCancel}
      onKeyDown={handleKeyDown}
    >
      <div
        className="bg-editor-surface border border-editor-border rounded-lg shadow-xl w-full max-w-md mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-editor-border">
          <h2 className="text-lg font-semibold">Settings</h2>
          <button
            onClick={handleCancel}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-6">
          {/* Model Information */}
          <div>
            <h3 className="text-sm font-semibold text-gray-400 uppercase mb-3">Model Information</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm mb-1">Name</label>
                <input
                  type="text"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full px-3 py-2 bg-editor-bg border border-editor-border rounded text-sm focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm mb-1">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-editor-bg border border-editor-border rounded text-sm focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>
            </div>
          </div>

          {/* Simulation Settings */}
          <div>
            <h3 className="text-sm font-semibold text-gray-400 uppercase mb-3">Simulation Settings</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm mb-1">Solver</label>
                <select
                  value={solver}
                  onChange={(e) => setSolver(e.target.value as SolverType)}
                  className="w-full px-3 py-2 bg-editor-bg border border-editor-border rounded text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="euler">Euler (ode1)</option>
                  <option value="rk4">Runge-Kutta 4 (ode4)</option>
                  <option value="merson">Merson (ode45)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm mb-1">Step Size</label>
                <input
                  type="number"
                  value={stepSize}
                  onChange={(e) => setStepSize(parseFloat(e.target.value) || 0.01)}
                  step={0.001}
                  min={0.0001}
                  className="w-full px-3 py-2 bg-editor-bg border border-editor-border rounded text-sm focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm mb-1">Start Time</label>
                <input
                  type="number"
                  value={startTime}
                  onChange={(e) => setStartTime(parseFloat(e.target.value) || 0)}
                  step={0.1}
                  className="w-full px-3 py-2 bg-editor-bg border border-editor-border rounded text-sm focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm mb-1">Stop Time</label>
                <input
                  type="number"
                  value={stopTime}
                  onChange={(e) => setStopTime(parseFloat(e.target.value) || 10)}
                  step={0.1}
                  min={startTime + 0.1}
                  className="w-full px-3 py-2 bg-editor-bg border border-editor-border rounded text-sm focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 px-4 py-3 border-t border-editor-border">
          <button
            onClick={handleCancel}
            className="px-4 py-2 text-sm border border-editor-border rounded hover:bg-editor-border transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 rounded transition-colors"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  )
}
