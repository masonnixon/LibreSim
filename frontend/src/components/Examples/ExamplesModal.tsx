import { useState } from 'react'

export interface ExampleInfo {
  id: string
  name: string
  description: string
  category: 'basic' | 'control' | 'signal' | 'advanced' | 'aerospace' | 'control_design'
}

interface ExamplesModalProps {
  isOpen: boolean
  onClose: () => void
  examples: ExampleInfo[]
  onLoadExample: (id: string) => void
  onOpenBlockReference?: () => void
}

const categoryInfo: Record<string, { title: string; description: string; icon: string }> = {
  basic: {
    title: 'Basic Examples',
    description: 'Simple models to get started with LibreSim',
    icon: '📘',
  },
  control: {
    title: 'Control Systems',
    description: 'Feedback control and system analysis examples',
    icon: '🎛️',
  },
  signal: {
    title: 'Signal Processing',
    description: 'Filters, noise, and signal manipulation',
    icon: '📊',
  },
  advanced: {
    title: 'Advanced',
    description: 'State estimation, observers, and complex systems',
    icon: '🔬',
  },
  aerospace: {
    title: 'Aerospace Blockset',
    description: 'Quaternions, atmosphere models, and flight dynamics',
    icon: '🚀',
  },
  control_design: {
    title: 'Control Design',
    description: 'PID, LQR, pole placement, and compensator design',
    icon: '⚙️',
  },
}

const categoryOrder = ['basic', 'control', 'control_design', 'signal', 'aerospace', 'advanced']

export function ExamplesModal({ isOpen, onClose, examples, onLoadExample, onOpenBlockReference }: ExamplesModalProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('basic')
  const [searchQuery, setSearchQuery] = useState('')

  if (!isOpen) return null

  const filteredExamples = examples.filter((ex) => {
    const matchesCategory = selectedCategory === 'all' || ex.category === selectedCategory
    const matchesSearch =
      searchQuery === '' ||
      ex.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ex.description.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCategory && matchesSearch
  })

  const handleLoadExample = (id: string) => {
    onLoadExample(id)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-editor-bg border border-editor-border rounded-lg shadow-2xl w-[900px] max-w-[95vw] h-[600px] max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-editor-border">
          <div>
            <h2 className="text-xl font-semibold text-white">Example Models</h2>
            <p className="text-sm text-gray-400 mt-1">
              Load example models to learn LibreSim capabilities
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors p-1"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Search */}
        <div className="px-6 py-3 border-b border-editor-border">
          <input
            type="text"
            placeholder="Search examples..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-editor-border rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Content */}
        <div className="flex flex-1 overflow-hidden">
          {/* Category Sidebar */}
          <div className="w-56 border-r border-editor-border overflow-y-auto bg-gray-900/50">
            <div className="p-2">
              <button
                onClick={() => setSelectedCategory('all')}
                className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                  selectedCategory === 'all'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800'
                }`}
              >
                <span className="mr-2">📁</span>
                All Examples
                <span className="float-right text-xs opacity-60">{examples.length}</span>
              </button>
            </div>
            <div className="border-t border-editor-border my-1" />
            <div className="p-2 space-y-1">
              {categoryOrder.map((cat) => {
                const info = categoryInfo[cat]
                const count = examples.filter((ex) => ex.category === cat).length
                if (count === 0) return null
                return (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                      selectedCategory === cat
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-300 hover:bg-gray-800'
                    }`}
                  >
                    <span className="mr-2">{info.icon}</span>
                    {info.title}
                    <span className="float-right text-xs opacity-60">{count}</span>
                  </button>
                )
              })}
            </div>
            <div className="border-t border-editor-border my-2" />
            <div className="p-3 text-xs text-gray-500">
              <a
                href="https://github.com/masonnixon/LibreSim/tree/master/examples"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 flex items-center gap-1"
              >
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                </svg>
                View on GitHub
              </a>
            </div>
          </div>

          {/* Examples List */}
          <div className="flex-1 overflow-y-auto p-4">
            {selectedCategory !== 'all' && categoryInfo[selectedCategory] && (
              <div className="mb-4 pb-3 border-b border-editor-border">
                <h3 className="text-lg font-medium text-white flex items-center gap-2">
                  <span>{categoryInfo[selectedCategory].icon}</span>
                  {categoryInfo[selectedCategory].title}
                </h3>
                <p className="text-sm text-gray-400 mt-1">
                  {categoryInfo[selectedCategory].description}
                </p>
              </div>
            )}

            {filteredExamples.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                No examples found matching your search.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {filteredExamples.map((ex) => (
                  <button
                    key={ex.id}
                    onClick={() => handleLoadExample(ex.id)}
                    className="text-left p-4 bg-gray-800/50 hover:bg-gray-700/50 border border-editor-border hover:border-blue-500/50 rounded-lg transition-all group"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-white group-hover:text-blue-400 transition-colors">
                          {ex.name}
                        </div>
                        <div className="text-sm text-gray-400 mt-1">{ex.description}</div>
                      </div>
                      <span className="text-xs px-2 py-0.5 bg-gray-700 rounded text-gray-400">
                        {categoryInfo[ex.category]?.icon}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-editor-border bg-gray-900/50 flex items-center justify-between text-sm">
          <div className="text-gray-500">
            {filteredExamples.length} example{filteredExamples.length !== 1 ? 's' : ''} available
          </div>
          <div className="flex items-center gap-4 text-gray-400">
            {onOpenBlockReference && (
              <button
                onClick={() => {
                  onClose()
                  onOpenBlockReference()
                }}
                className="hover:text-blue-400 transition-colors"
              >
                View Block Reference
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
