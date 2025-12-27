import { memo } from 'react'
import { Handle, Position, NodeProps, Node } from '@xyflow/react'
import type { BlockInstance, BlockDefinition } from '../../types/block'

interface BlockNodeData extends Record<string, unknown> {
  block: BlockInstance
  definition: BlockDefinition | undefined
}

type BlockNode = Node<BlockNodeData, 'blockNode'>

function BlockNodeComponent({ data, selected }: NodeProps<BlockNode>) {
  const { block, definition } = data

  if (!block || !definition) {
    return <div className="p-2 bg-red-500 text-white rounded">Invalid Block</div>
  }

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

  return (
    <div
      className={`
        px-3 py-2 rounded-lg shadow-lg min-w-[100px]
        ${getCategoryClass()}
        ${selected ? 'ring-2 ring-white ring-opacity-50' : ''}
      `}
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
            background: '#1e1e2e',
            border: '2px solid #cdd6f4',
          }}
          title={port.name}
        />
      ))}

      {/* Block Content */}
      <div className="text-center text-gray-900">
        <div className="font-semibold text-sm truncate max-w-[120px]">{block.name}</div>
        {displayIcon && <div className="text-lg mt-1">{displayIcon}</div>}
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
            background: '#1e1e2e',
            border: '2px solid #cdd6f4',
          }}
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

  // Check if parameters changed (simple JSON comparison for now)
  if (JSON.stringify(prevBlock.parameters) !== JSON.stringify(nextBlock.parameters)) return false

  // Check ports
  if (prevBlock.inputPorts.length !== nextBlock.inputPorts.length) return false
  if (prevBlock.outputPorts.length !== nextBlock.outputPorts.length) return false

  return true
}

export const BlockNode = memo(BlockNodeComponent, arePropsEqual)
