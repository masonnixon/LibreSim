import { memo } from 'react'
import { Handle, Position, NodeProps, Node } from '@xyflow/react'
import type { BlockInstance, BlockDefinition, BlockRotation } from '../../types/block'

interface BlockNodeData extends Record<string, unknown> {
  block: BlockInstance
  definition: BlockDefinition | undefined
}

type BlockNode = Node<BlockNodeData, 'blockNode'>

// Get handle position based on rotation
function getRotatedPosition(basePosition: Position, rotation: BlockRotation): Position {
  const rotationMap: Record<BlockRotation, Record<Position, Position>> = {
    0: { [Position.Left]: Position.Left, [Position.Right]: Position.Right, [Position.Top]: Position.Top, [Position.Bottom]: Position.Bottom },
    90: { [Position.Left]: Position.Top, [Position.Right]: Position.Bottom, [Position.Top]: Position.Right, [Position.Bottom]: Position.Left },
    180: { [Position.Left]: Position.Right, [Position.Right]: Position.Left, [Position.Top]: Position.Bottom, [Position.Bottom]: Position.Top },
    270: { [Position.Left]: Position.Bottom, [Position.Right]: Position.Top, [Position.Top]: Position.Left, [Position.Bottom]: Position.Right },
  }
  return rotationMap[rotation][basePosition]
}

function BlockNodeComponent({ data, selected }: NodeProps<BlockNode>) {
  const { block, definition } = data

  if (!block || !definition) {
    return <div className="p-2 bg-red-500 text-white rounded">Invalid Block</div>
  }

  const rotation = block.rotation || 0
  const inputPosition = getRotatedPosition(Position.Left, rotation)
  const outputPosition = getRotatedPosition(Position.Right, rotation)

  // Get dynamic icon based on block type and parameters
  const getDynamicIcon = () => {
    switch (block.type) {
      case 'constant':
        return block.parameters.value !== undefined ? String(block.parameters.value) : definition.icon
      case 'gain':
        return block.parameters.gain !== undefined ? String(block.parameters.gain) : definition.icon
      default:
        return definition.icon
    }
  }

  const displayIcon = getDynamicIcon()

  const getCategoryClass = () => {
    switch (definition.category) {
      case 'sources':
        return 'block-source'
      case 'sinks':
        return 'block-sink'
      case 'continuous':
        return 'block-continuous'
      case 'discrete':
        return 'block-discrete'
      case 'math':
        return 'block-math'
      case 'routing':
        return 'block-routing'
      case 'subsystems':
        return 'bg-cyan-600 border-cyan-400 border-2'
      case 'signal_processing':
        return 'bg-teal-600 border-teal-400 border-2'
      case 'nonlinear':
        return 'bg-orange-600 border-orange-400 border-2'
      case 'observers':
        return 'bg-indigo-600 border-indigo-400 border-2'
      default:
        return 'bg-gray-600 border-gray-500'
    }
  }

  // Calculate handle position style based on orientation (horizontal vs vertical)
  const getHandleStyle = (index: number, total: number, position: Position) => {
    const percentage = ((index + 1) / (total + 1)) * 100
    const baseStyle = {
      background: '#1e1e2e',
      border: '2px solid #cdd6f4',
    }

    if (position === Position.Left || position === Position.Right) {
      return { ...baseStyle, top: `${percentage}%` }
    } else {
      return { ...baseStyle, left: `${percentage}%` }
    }
  }

  return (
    <div
      className={`
        px-3 py-2 rounded-lg shadow-lg min-w-[100px]
        ${getCategoryClass()}
        ${selected ? 'ring-2 ring-white ring-opacity-50' : ''}
      `}
      style={{ transform: `rotate(${rotation}deg)` }}
    >
      {/* Input Handles */}
      {block.inputPorts.map((port, index) => (
        <Handle
          key={port.id}
          type="target"
          position={inputPosition}
          id={port.id}
          style={getHandleStyle(index, block.inputPorts.length, inputPosition)}
          title={port.name}
        />
      ))}

      {/* Block Content - counter-rotate to keep text upright */}
      <div className="text-center text-gray-900" style={{ transform: `rotate(${-rotation}deg)` }}>
        <div className="font-semibold text-sm truncate max-w-[120px]">{block.name}</div>
        {displayIcon && <div className="text-lg mt-1">{displayIcon}</div>}
      </div>

      {/* Output Handles */}
      {block.outputPorts.map((port, index) => (
        <Handle
          key={port.id}
          type="source"
          position={outputPosition}
          id={port.id}
          style={getHandleStyle(index, block.outputPorts.length, outputPosition)}
          title={port.name}
        />
      ))}
    </div>
  )
}

// Custom comparison to ensure re-render when block data changes
function arePropsEqual(
  prevProps: NodeProps<BlockNode>,
  nextProps: NodeProps<BlockNode>
): boolean {
  // Always re-render if selected state changes
  if (prevProps.selected !== nextProps.selected) return false

  // Compare block data
  const prevBlock = prevProps.data.block
  const nextBlock = nextProps.data.block

  if (!prevBlock || !nextBlock) return prevBlock === nextBlock

  // Check if key properties changed
  if (prevBlock.id !== nextBlock.id) return false
  if (prevBlock.name !== nextBlock.name) return false
  if (prevBlock.type !== nextBlock.type) return false
  if (prevBlock.rotation !== nextBlock.rotation) return false

  // Check if parameters changed (simple JSON comparison for now)
  if (JSON.stringify(prevBlock.parameters) !== JSON.stringify(nextBlock.parameters)) return false

  // Check ports
  if (prevBlock.inputPorts.length !== nextBlock.inputPorts.length) return false
  if (prevBlock.outputPorts.length !== nextBlock.outputPorts.length) return false

  return true
}

export const BlockNode = memo(BlockNodeComponent, arePropsEqual)
