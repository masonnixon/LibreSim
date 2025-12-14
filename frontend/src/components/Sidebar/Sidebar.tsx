import { useState, useEffect } from 'react'
import { useUIStore } from '../../store/uiStore'
import { useModelStore } from '../../store/modelStore'
import { blockRegistry, blockCategories } from '../../blocks'
import { toast } from '../Toast/Toast'
import type { BlockCategory, BlockDefinition } from '../../types/block'

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
  const { model, addBlock } = useModelStore()
  const [expandedCategories, setExpandedCategories] = useState<Set<BlockCategory>>(
    new Set(['sources', 'sinks', 'continuous'])
  )
  const [searchQuery, setSearchQuery] = useState('')
  const [isMobile, setIsMobile] = useState(false)

  // Check for mobile/touch device
  useEffect(() => {
    const checkMobile = () => {
      // Check for touch capability and small screen
      const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0
      const isSmallScreen = window.innerWidth < 768
      setIsMobile(hasTouch && isSmallScreen)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

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

  // Calculate a position for new blocks that avoids overlapping
  const calculateNewBlockPosition = () => {
    if (!model || model.blocks.length === 0) {
      return { x: 200, y: 150 }
    }

    // Find the rightmost and bottommost block positions
    const maxX = Math.max(...model.blocks.map(b => b.position.x))
    const maxY = Math.max(...model.blocks.map(b => b.position.y))

    // Add new block to the right of existing blocks, or below if too far right
    if (maxX < 800) {
      return { x: maxX + 180, y: 150 }
    } else {
      return { x: 200, y: maxY + 100 }
    }
  }

  // Handle tap/click to add block on mobile
  const handleBlockTap = (block: BlockDefinition) => {
    if (!isMobile) return

    const position = calculateNewBlockPosition()
    addBlock(block, position)
    toast.success('Block Added', `Added "${block.name}" to canvas`)

    // Auto-collapse sidebar after adding block on mobile for better UX
    toggleSidebar()
  }

  // Handle click - on mobile it adds the block, on desktop it does nothing (drag is used)
  const handleBlockClick = (block: BlockDefinition) => {
    if (isMobile) {
      handleBlockTap(block)
    }
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
    <div className="w-52 md:w-64 bg-editor-surface border-r border-editor-border flex flex-col">
      {/* Header */}
      <div className="p-2 md:p-3 border-b border-editor-border flex items-center justify-between">
        <h2 className="font-semibold text-xs md:text-sm">Block Library</h2>
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

      {/* Mobile hint */}
      {isMobile && (
        <div className="px-3 py-2 bg-blue-900/30 border-b border-editor-border">
          <p className="text-xs text-blue-300">Tap a block to add it to the canvas</p>
        </div>
      )}

      {/* Search */}
      <div className="p-2 md:p-3 border-b border-editor-border">
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
                      draggable={!isMobile}
                      onDragStart={(e) => onDragStart(e, block.type)}
                      onClick={() => handleBlockClick(block)}
                      className={`mx-2 my-1 px-3 py-2 bg-editor-bg rounded transition-colors ${
                        isMobile
                          ? 'cursor-pointer active:bg-blue-600/30'
                          : 'cursor-grab hover:bg-editor-border'
                      }`}
                      title={isMobile ? `Tap to add ${block.name}` : block.description}
                    >
                      <div className="flex items-center gap-2">
                        {block.icon && (
                          <span className="text-sm">{block.icon}</span>
                        )}
                        <span className="text-sm">{block.name}</span>
                        {isMobile && (
                          <svg className="w-4 h-4 ml-auto text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                          </svg>
                        )}
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
