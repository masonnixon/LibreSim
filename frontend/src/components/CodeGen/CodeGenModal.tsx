import { useState, useCallback } from 'react'
import { useModelStore } from '../../store/modelStore'
import { toast } from '../Toast/Toast'

// Language options
const LANGUAGES = [
  { value: 'python', label: 'Python', icon: '🐍', description: 'Python with NumPy support' },
  { value: 'c', label: 'C', icon: 'C', description: 'C for embedded systems' },
  { value: 'cpp', label: 'C++', icon: 'C++', description: 'C++ with OOP design' },
  { value: 'rust', label: 'Rust', icon: '🦀', description: 'Rust with safety guarantees' },
] as const

// Integration method options
const INTEGRATION_METHODS = [
  { value: 'euler', label: 'Euler', description: 'Fast, less accurate' },
  { value: 'rk2', label: 'RK2', description: 'Midpoint rule' },
  { value: 'rk4', label: 'RK4', description: 'Classic 4th order (Recommended)' },
  { value: 'merson', label: 'Merson', description: '4th order with error estimation' },
] as const

interface CodeGenConfig {
  language: string
  integrationMethod: string
  stepSize: number
  stopTime: number
  startTime: number
  projectName: string
  includeMain: boolean
  includeCsvOutput: boolean
}

interface CodeGenModalProps {
  isOpen: boolean
  onClose: () => void
}

export function CodeGenModal({ isOpen, onClose }: CodeGenModalProps) {
  const { model } = useModelStore()
  const [isGenerating, setIsGenerating] = useState(false)

  // Derive project name from model - update when model changes
  const defaultProjectName = model?.metadata?.name?.toLowerCase().replace(/\s+/g, '_') ?? 'simulation'

  const [config, setConfig] = useState<CodeGenConfig>({
    language: 'python',
    integrationMethod: 'rk4',
    stepSize: model?.simulationConfig?.stepSize ?? 0.01,
    stopTime: model?.simulationConfig?.stopTime ?? 10.0,
    startTime: model?.simulationConfig?.startTime ?? 0.0,
    projectName: defaultProjectName,
    includeMain: true,
    includeCsvOutput: true,
  })

  // Update project name when model changes (if user hasn't customized it)
  const [hasCustomizedName, setHasCustomizedName] = useState(false)
  if (!hasCustomizedName && config.projectName !== defaultProjectName && defaultProjectName !== 'simulation') {
    setConfig(prev => ({ ...prev, projectName: defaultProjectName }))
  }

  const handleGenerate = useCallback(async () => {
    setIsGenerating(true)

    try {
      const response = await fetch('/api/codegen/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          language: config.language,
          integration_method: config.integrationMethod,
          step_size: config.stepSize,
          stop_time: config.stopTime,
          start_time: config.startTime,
          project_name: config.projectName,
          include_main: config.includeMain,
          include_csv_output: config.includeCsvOutput,
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Code generation failed')
      }

      // Download the ZIP file
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const filename = `${config.projectName}_${config.language}.zip`
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast.success('Code Generated', `Downloaded ${filename}`)
      onClose()
    } catch (error) {
      console.error('Code generation failed:', error)
      toast.warning('Generation Failed', error instanceof Error ? error.message : 'Unknown error')
    } finally {
      setIsGenerating(false)
    }
  }, [model, config, onClose])

  if (!isOpen) return null

  const selectedLang = LANGUAGES.find((l) => l.value === config.language)

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-editor-surface border border-editor-border rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-editor-border">
          <div>
            <h2 className="text-xl font-semibold text-white">Generate Code</h2>
            <p className="text-sm text-gray-400 mt-1">Export your model as standalone simulation code</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-editor-border rounded transition-colors"
            title="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Language Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-3">Target Language</label>
            <div className="grid grid-cols-4 gap-3">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang.value}
                  onClick={() => setConfig({ ...config, language: lang.value })}
                  className={`p-4 rounded-lg border-2 transition-all text-center ${
                    config.language === lang.value
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-editor-border hover:border-gray-600 bg-editor-bg'
                  }`}
                >
                  <div className="text-2xl mb-1">{lang.icon}</div>
                  <div className="font-medium">{lang.label}</div>
                  <div className="text-xs text-gray-500 mt-1">{lang.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Integration Method */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-3">Integration Method</label>
            <div className="grid grid-cols-4 gap-3">
              {INTEGRATION_METHODS.map((method) => (
                <button
                  key={method.value}
                  onClick={() => setConfig({ ...config, integrationMethod: method.value })}
                  className={`p-3 rounded-lg border-2 transition-all text-center ${
                    config.integrationMethod === method.value
                      ? 'border-green-500 bg-green-500/10'
                      : 'border-editor-border hover:border-gray-600 bg-editor-bg'
                  }`}
                >
                  <div className="font-medium">{method.label}</div>
                  <div className="text-xs text-gray-500 mt-1">{method.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Simulation Parameters */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-3">Simulation Parameters</label>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Start Time (s)</label>
                <input
                  type="number"
                  value={config.startTime}
                  onChange={(e) => setConfig({ ...config, startTime: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 bg-editor-bg border border-editor-border rounded text-white focus:border-blue-500 focus:outline-none"
                  step="0.1"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Stop Time (s)</label>
                <input
                  type="number"
                  value={config.stopTime}
                  onChange={(e) => setConfig({ ...config, stopTime: parseFloat(e.target.value) || 10 })}
                  className="w-full px-3 py-2 bg-editor-bg border border-editor-border rounded text-white focus:border-blue-500 focus:outline-none"
                  step="0.1"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Step Size (s)</label>
                <input
                  type="number"
                  value={config.stepSize}
                  onChange={(e) => setConfig({ ...config, stepSize: parseFloat(e.target.value) || 0.01 })}
                  className="w-full px-3 py-2 bg-editor-bg border border-editor-border rounded text-white focus:border-blue-500 focus:outline-none"
                  step="0.001"
                />
              </div>
            </div>
          </div>

          {/* Project Settings */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-3">Project Settings</label>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Project Name</label>
                <input
                  type="text"
                  value={config.projectName}
                  onChange={(e) => {
                    setHasCustomizedName(true)
                    setConfig({ ...config, projectName: e.target.value.replace(/[^a-zA-Z0-9_-]/g, '_') })
                  }}
                  className="w-full px-3 py-2 bg-editor-bg border border-editor-border rounded text-white focus:border-blue-500 focus:outline-none"
                  placeholder="simulation"
                />
              </div>
              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.includeMain}
                    onChange={(e) => setConfig({ ...config, includeMain: e.target.checked })}
                    className="w-4 h-4 rounded border-editor-border bg-editor-bg text-blue-500 focus:ring-blue-500"
                  />
                  <span className="text-sm">Include main() entry point</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.includeCsvOutput}
                    onChange={(e) => setConfig({ ...config, includeCsvOutput: e.target.checked })}
                    className="w-4 h-4 rounded border-editor-border bg-editor-bg text-blue-500 focus:ring-blue-500"
                  />
                  <span className="text-sm">Include CSV output</span>
                </label>
              </div>
            </div>
          </div>

          {/* Output Preview */}
          <div className="bg-editor-bg rounded-lg p-4 border border-editor-border">
            <div className="text-sm font-medium text-gray-300 mb-2">Output Preview</div>
            <div className="text-xs text-gray-500 font-mono">
              {config.projectName}_{config.language}.zip
              <div className="ml-4 mt-1 space-y-0.5">
                {config.language === 'python' && (
                  <>
                    <div>├── main.py</div>
                    <div>├── simulation.py</div>
                    <div>├── blocks.py</div>
                    <div>├── integration.py</div>
                    <div>├── requirements.txt</div>
                    <div>├── README.md</div>
                    <div>├── Dockerfile</div>
                    <div>└── build.sh</div>
                  </>
                )}
                {config.language === 'c' && (
                  <>
                    <div>├── include/</div>
                    <div>│   ├── simulation.h</div>
                    <div>│   └── blocks.h</div>
                    <div>├── src/</div>
                    <div>│   ├── main.c</div>
                    <div>│   └── simulation.c</div>
                    <div>├── CMakeLists.txt</div>
                    <div>├── README.md</div>
                    <div>├── Dockerfile</div>
                    <div>└── build.sh</div>
                  </>
                )}
                {config.language === 'cpp' && (
                  <>
                    <div>├── include/</div>
                    <div>│   ├── simulation.hpp</div>
                    <div>│   └── blocks.hpp</div>
                    <div>├── src/</div>
                    <div>│   ├── main.cpp</div>
                    <div>│   └── simulation.cpp</div>
                    <div>├── CMakeLists.txt</div>
                    <div>├── README.md</div>
                    <div>├── Dockerfile</div>
                    <div>└── build.sh</div>
                  </>
                )}
                {config.language === 'rust' && (
                  <>
                    <div>├── src/</div>
                    <div>│   ├── main.rs</div>
                    <div>│   ├── lib.rs</div>
                    <div>│   └── integration.rs</div>
                    <div>├── Cargo.toml</div>
                    <div>├── README.md</div>
                    <div>├── Dockerfile</div>
                    <div>└── build.sh</div>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Language-specific notes */}
          {selectedLang && (
            <div className="text-sm text-gray-400">
              {config.language === 'python' && (
                <p>Generated Python code uses NumPy for numerical operations. Run with: <code className="bg-editor-bg px-1 rounded">python main.py</code></p>
              )}
              {config.language === 'c' && (
                <p>Build with CMake: <code className="bg-editor-bg px-1 rounded">mkdir build && cd build && cmake .. && make</code></p>
              )}
              {config.language === 'cpp' && (
                <p>Build with CMake (C++17): <code className="bg-editor-bg px-1 rounded">mkdir build && cd build && cmake .. && make</code></p>
              )}
              {config.language === 'rust' && (
                <p>Build with Cargo: <code className="bg-editor-bg px-1 rounded">cargo build --release</code></p>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-editor-border bg-editor-bg">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleGenerate}
            disabled={isGenerating || !model}
            className="px-6 py-2 text-sm bg-blue-600 hover:bg-blue-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isGenerating ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Generating...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Generate & Download
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
