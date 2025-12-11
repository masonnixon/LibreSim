import { memo, useCallback } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import type { BlockInstance, BlockDefinition } from '../../types/block'
import { useModelStore } from '../../store/modelStore'

interface SubsystemNodeData {
  block: BlockInstance
  definition: BlockDefinition | undefined
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

  const childCount = block.children?.length || 0
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
      <div className="px-4 py-3">
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="text-xs text-slate-400 uppercase tracking-wide">Subsystem</div>
          <div className="text-xs text-cyan-400">
            {isExpanded ? '[-]' : '[+]'}
          </div>
        </div>

        {/* Name */}
        <div className="font-semibold text-sm text-white truncate max-w-[120px]">
          {block.name}
        </div>

        {/* Icon/representation */}
        <div className="mt-2 p-2 bg-slate-900/50 rounded text-center text-slate-400 text-xs">
          <div className="text-lg mb-1">{ }</div>
          <div>{childCount} blocks</div>
        </div>

        {/* Port labels */}
        <div className="mt-2 flex justify-between text-xs">
          <div className="text-cyan-300">
            {block.inputPorts.map((p) => (
              <div key={p.id} className="truncate max-w-[50px]">{p.name}</div>
            ))}
          </div>
          <div className="text-cyan-300 text-right">
            {block.outputPorts.map((p) => (
              <div key={p.id} className="truncate max-w-[50px]">{p.name}</div>
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
