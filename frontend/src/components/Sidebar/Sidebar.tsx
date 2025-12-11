import { useState } from 'react'
import { useUIStore } from '../../store/uiStore'
import { blockRegistry, blockCategories } from '../../blocks'
import type { BlockCategory } from '../../types/block'

const categoryLabels: Record<BlockCategory, string> = {
  sources: 'Sources',
  sinks: 'Sinks',
  continuous: 'Continuous',
  discrete: 'Discrete',
  math: 'Math Operations',
  routing: 'Signal Routing',
  subsystems: 'Subsystems',
  signal_processing: 'Signal Processing',
  nonlinear: 'Nonlinear',
  observers: 'State Observers',
}

const categoryColors: Record<BlockCategory, string> = {
  sources: 'bg-block-source',
  sinks: 'bg-block-sink',
  continuous: 'bg-block-continuous',
  discrete: 'bg-block-discrete',
  math: 'bg-block-math',
  routing: 'bg-block-routing',
  subsystems: 'bg-purple-600',
  signal_processing: 'bg-teal-600',
  nonlinear: 'bg-orange-600',
  observers: 'bg-indigo-600',
}

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar, setDraggingBlockType } = useUIStore()
  const [expandedCategories, setExpandedCategories] = useState<Set<BlockCategory>>(
    new Set(['sources', 'sinks', 'continuous'])
  )
  const [searchQuery, setSearchQuery] = useState('')

  const toggleCategory = (category: BlockCategory) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev)
      if (next.has(category)) {
        next.delete(category)
      } else {
        next.add(category)
      }
      return next
    })
  }

  const onDragStart = (event: React.DragEvent, blockType: string) => {
    event.dataTransfer.effectAllowed = 'move'
    setDraggingBlockType(blockType)
  }

  const filteredCategories = blockCategories.filter((category) => {
    if (!searchQuery) return true
    const blocks = blockRegistry.getByCategory(category)
    return blocks.some(
      (block) =>
        block.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        block.description.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })

  if (sidebarCollapsed) {
    return (
      <div className="w-10 bg-editor-surface border-r border-editor-border flex flex-col items-center py-2">
        <button
          onClick={toggleSidebar}
          className="p-2 text-gray-400 hover:text-white hover:bg-editor-border rounded"
          title="Expand sidebar"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      </div>
    )
  }

  return (
    <div className="w-64 bg-editor-surface border-r border-editor-border flex flex-col">
      {/* Header */}
      <div className="p-3 border-b border-editor-border flex items-center justify-between">
        <h2 className="font-semibold text-sm">Block Library</h2>
        <button
          onClick={toggleSidebar}
          className="p-1 text-gray-400 hover:text-white hover:bg-editor-border rounded"
          title="Collapse sidebar"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>
      </div>

      {/* Search */}
      <div className="p-3 border-b border-editor-border">
        <input
          type="text"
          placeholder="Search blocks..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-3 py-1.5 bg-editor-bg border border-editor-border rounded text-sm focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* Block Categories */}
      <div className="flex-1 overflow-y-auto">
        {filteredCategories.map((category) => {
          const blocks = blockRegistry.getByCategory(category)
          const filteredBlocks = searchQuery
            ? blocks.filter(
                (block) =>
                  block.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  block.description.toLowerCase().includes(searchQuery.toLowerCase())
              )
            : blocks

          if (filteredBlocks.length === 0) return null

          return (
            <div key={category} className="border-b border-editor-border">
              {/* Category Header */}
              <button
                onClick={() => toggleCategory(category)}
                className="w-full px-3 py-2 flex items-center justify-between hover:bg-editor-border text-left"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`w-3 h-3 rounded ${categoryColors[category]}`}
                  />
                  <span className="text-sm font-medium">
                    {categoryLabels[category]}
                  </span>
                </div>
                <svg
                  className={`w-4 h-4 transition-transform ${
                    expandedCategories.has(category) ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>

              {/* Block List */}
              {expandedCategories.has(category) && (
                <div className="pb-2">
                  {filteredBlocks.map((block) => (
                    <div
                      key={block.type}
                      draggable
                      onDragStart={(e) => onDragStart(e, block.type)}
                      className="mx-2 my-1 px-3 py-2 bg-editor-bg rounded cursor-grab hover:bg-editor-border transition-colors"
                      title={block.description}
                    >
                      <div className="flex items-center gap-2">
                        {block.icon && (
                          <span className="text-sm">{block.icon}</span>
                        )}
                        <span className="text-sm">{block.name}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
