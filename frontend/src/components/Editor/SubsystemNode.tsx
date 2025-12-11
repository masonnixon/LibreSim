import { memo, useCallback, useMemo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import type { BlockInstance, BlockDefinition, Connection } from '../../types/block'
import { useModelStore } from '../../store/modelStore'
import { blockRegistry } from '../../blocks'

interface SubsystemNodeData {
  block: BlockInstance
  definition: BlockDefinition | undefined
}

// Get color for block category
function getCategoryColor(category: string): string {
  switch (category) {
    case 'sources':
      return '#a6e3a1'
    case 'sinks':
      return '#f38ba8'
    case 'continuous':
      return '#89b4fa'
    case 'discrete':
      return '#fab387'
    case 'math':
      return '#cba6f7'
    case 'routing':
      return '#f9e2af'
    case 'subsystems':
      return '#22d3ee'
    case 'signal_processing':
      return '#2dd4bf' // teal
    case 'nonlinear':
      return '#fb923c' // orange
    case 'observers':
      return '#818cf8' // indigo
    default:
      return '#6c7086'
  }
}

// Mini preview component that renders child blocks
function SubsystemPreview({
  children,
  connections,
}: {
  children: BlockInstance[]
  connections?: Connection[]
}) {
  // Calculate bounds and scale
  const { blocks, scale, offsetX, offsetY, width, height } = useMemo(() => {
    if (!children || children.length === 0) {
      return { blocks: [], scale: 1, offsetX: 0, offsetY: 0, width: 120, height: 80 }
    }

    // Filter out inport/outport for cleaner preview (they're interface blocks)
    const contentBlocks = children.filter(
      (b) => b.type !== 'inport' && b.type !== 'outport'
    )

    if (contentBlocks.length === 0) {
      return { blocks: children, scale: 1, offsetX: 0, offsetY: 0, width: 120, height: 80 }
    }

    const positions = contentBlocks.map((b) => b.position)
    const minX = Math.min(...positions.map((p) => p.x))
    const maxX = Math.max(...positions.map((p) => p.x)) + 100 // block width estimate
    const minY = Math.min(...positions.map((p) => p.y))
    const maxY = Math.max(...positions.map((p) => p.y)) + 50 // block height estimate

    const contentWidth = maxX - minX
    const contentHeight = maxY - minY

    // Target preview size
    const previewWidth = 120
    const previewHeight = 80

    // Calculate scale to fit
    const scaleX = previewWidth / Math.max(contentWidth, 1)
    const scaleY = previewHeight / Math.max(contentHeight, 1)
    const finalScale = Math.min(scaleX, scaleY, 1) * 0.85 // 85% to add padding

    return {
      blocks: contentBlocks,
      scale: finalScale,
      offsetX: minX,
      offsetY: minY,
      width: previewWidth,
      height: previewHeight,
    }
  }, [children])

  // Create connection paths
  const connectionPaths = useMemo(() => {
    if (!connections || !children) return []

    const blockMap = new Map(children.map((b) => [b.id, b]))
    const paths: { id: string; d: string }[] = []

    connections.forEach((conn) => {
      const sourceBlock = blockMap.get(conn.sourceBlockId)
      const targetBlock = blockMap.get(conn.targetBlockId)

      if (sourceBlock && targetBlock) {
        // Skip if either is inport/outport
        if (
          sourceBlock.type === 'inport' ||
          sourceBlock.type === 'outport' ||
          targetBlock.type === 'inport' ||
          targetBlock.type === 'outport'
        ) {
          return
        }

        const x1 = (sourceBlock.position.x - offsetX + 100) * scale // right side of source
        const y1 = (sourceBlock.position.y - offsetY + 25) * scale // middle of source
        const x2 = (targetBlock.position.x - offsetX) * scale // left side of target
        const y2 = (targetBlock.position.y - offsetY + 25) * scale // middle of target

        // Simple bezier curve
        const midX = (x1 + x2) / 2
        paths.push({
          id: conn.id,
          d: `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`,
        })
      }
    })

    return paths
  }, [connections, children, offsetX, offsetY, scale])

  if (blocks.length === 0) {
    return (
      <div className="w-[120px] h-[80px] bg-slate-900/50 rounded flex items-center justify-center text-slate-500 text-xs">
        Empty
      </div>
    )
  }

  return (
    <svg width={width} height={height} className="bg-slate-900/50 rounded overflow-hidden">
      {/* Grid pattern */}
      <defs>
        <pattern id="miniGrid" width="10" height="10" patternUnits="userSpaceOnUse">
          <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#334155" strokeWidth="0.5" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#miniGrid)" />

      {/* Connections */}
      {connectionPaths.map((path) => (
        <path
          key={path.id}
          d={path.d}
          fill="none"
          stroke="#64748b"
          strokeWidth="1"
        />
      ))}

      {/* Blocks */}
      {blocks.map((child) => {
        const def = blockRegistry.get(child.type)
        const color = getCategoryColor(def?.category || '')
        const x = (child.position.x - offsetX) * scale
        const y = (child.position.y - offsetY) * scale
        const blockWidth = 100 * scale
        const blockHeight = 50 * scale

        return (
          <g key={child.id}>
            <rect
              x={x}
              y={y}
              width={blockWidth}
              height={blockHeight}
              rx={4 * scale}
              fill={color}
              opacity={0.9}
            />
            {/* Block name (only if scale is large enough) */}
            {scale > 0.3 && (
              <text
                x={x + blockWidth / 2}
                y={y + blockHeight / 2 + 3}
                textAnchor="middle"
                fill="#1e1e2e"
                fontSize={Math.max(8, 10 * scale)}
                fontWeight="500"
              >
                {child.name.length > 8 ? child.name.slice(0, 7) + '...' : child.name}
              </text>
            )}
          </g>
        )
      })}
    </svg>
  )
}

function SubsystemNodeComponent({ data, selected }: NodeProps<SubsystemNodeData>) {
  const { block, definition } = data
  const toggleSubsystemExpanded = useModelStore((state) => state.toggleSubsystemExpanded)

  const handleDoubleClick = useCallback(() => {
    toggleSubsystemExpanded(block.id)
  }, [block.id, toggleSubsystemExpanded])

  if (!block || !definition) {
    return <div className="p-2 bg-red-500 text-white rounded">Invalid Subsystem</div>
  }

  const isExpanded = block.isExpanded

  return (
    <div
      className={`
        relative rounded-lg shadow-lg min-w-[140px]
        bg-gradient-to-br from-slate-700 to-slate-800
        border-2 border-slate-500
        ${selected ? 'ring-2 ring-cyan-400 ring-opacity-70' : ''}
      `}
      onDoubleClick={handleDoubleClick}
    >
      {/* Input Handles */}
      {block.inputPorts.map((port, index) => (
        <Handle
          key={port.id}
          type="target"
          position={Position.Left}
          id={port.id}
          style={{
            top: `${((index + 1) / (block.inputPorts.length + 1)) * 100}%`,
            background: '#0891b2',
            border: '2px solid #22d3ee',
            width: 10,
            height: 10,
          }}
          title={port.name}
        />
      ))}

      {/* Block Content */}
      <div className="px-3 py-2">
        {/* Header */}
        <div className="flex items-center justify-between mb-1">
          <div className="text-[10px] text-slate-400 uppercase tracking-wide">Subsystem</div>
          <div className="text-[10px] text-cyan-400">
            {isExpanded ? '[-]' : '[+]'}
          </div>
        </div>

        {/* Name */}
        <div className="font-semibold text-sm text-white truncate max-w-[120px] mb-2">
          {block.name}
        </div>

        {/* Mini Preview */}
        <SubsystemPreview
          children={block.children || []}
          connections={block.childConnections}
        />

        {/* Port labels */}
        <div className="mt-2 flex justify-between text-[10px]">
          <div className="text-cyan-300">
            {block.inputPorts.map((p) => (
              <div key={p.id} className="truncate max-w-[45px]">{p.name}</div>
            ))}
          </div>
          <div className="text-cyan-300 text-right">
            {block.outputPorts.map((p) => (
              <div key={p.id} className="truncate max-w-[45px]">{p.name}</div>
            ))}
          </div>
        </div>
      </div>

      {/* Output Handles */}
      {block.outputPorts.map((port, index) => (
        <Handle
          key={port.id}
          type="source"
          position={Position.Right}
          id={port.id}
          style={{
            top: `${((index + 1) / (block.outputPorts.length + 1)) * 100}%`,
            background: '#0891b2',
            border: '2px solid #22d3ee',
            width: 10,
            height: 10,
          }}
          title={port.name}
        />
      ))}
    </div>
  )
}

export const SubsystemNode = memo(SubsystemNodeComponent)
