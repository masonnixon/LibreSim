import { memo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import type { BlockInstance, BlockDefinition } from '../../types/block'

interface BlockNodeData {
  block: BlockInstance
  definition: BlockDefinition | undefined
}

function BlockNodeComponent({ data, selected }: NodeProps<BlockNodeData>) {
  const { block, definition } = data

  if (!block || !definition) {
    return <div className="p-2 bg-red-500 text-white rounded">Invalid Block</div>
  }

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
        {definition.icon && <div className="text-lg mt-1">{definition.icon}</div>}
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

export const BlockNode = memo(BlockNodeComponent)
