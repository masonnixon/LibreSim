import { memo, useCallback } from 'react'
import { Handle, Position, NodeProps, Node, NodeResizer } from '@xyflow/react'
import type { BlockInstance, BlockDefinition, BlockRotation } from '../../types/block'
import { useModelStore } from '../../store/modelStore'

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
  const updateBlockSize = useModelStore((state) => state.updateBlockSize)

  const handleResizeEnd = useCallback(
    (_event: unknown, params: { width: number; height: number }) => {
      updateBlockSize(block.id, { width: params.width, height: params.height })
    },
    [block, updateBlockSize]
  )

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
      case 'compare_to_zero':
        return block.parameters.operator !== undefined ? `${block.parameters.operator}0` : definition.icon
      case 'compare_to_constant':
        return block.parameters.operator !== undefined ? `${block.parameters.operator}${block.parameters.constant ?? 'K'}` : definition.icon
      case 'relational_operator':
        return block.parameters.operator !== undefined ? String(block.parameters.operator) : definition.icon
      case 'logical_operator':
        return block.parameters.operator !== undefined ? String(block.parameters.operator) : definition.icon
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
      case 'logic':
        return 'bg-amber-600 border-amber-400 border-2'
      case 'control_analysis':
        return 'bg-rose-600 border-rose-400 border-2'
      case 'data_types':
        return 'bg-lime-600 border-lime-400 border-2'
      case 'matrix_ops':
        return 'bg-emerald-600 border-emerald-400 border-2'
      case 'control_design':
        return 'bg-violet-600 border-violet-400 border-2'
      case 'aerospace':
        return 'bg-sky-600 border-sky-400 border-2'
      case 'dsp':
        return 'bg-fuchsia-600 border-fuchsia-400 border-2'
      case 'rf':
        return 'bg-red-600 border-red-400 border-2'
      case 'navigation':
        return 'bg-blue-600 border-blue-400 border-2'
      case 'sensor_fusion':
        return 'bg-yellow-600 border-yellow-400 border-2'
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

  // Calculate block dimensions
  const blockWidth = block.size?.width || 100
  const blockHeight = block.size?.height || 50

  // Font scaling constants
  const baseNameFontSize = 14
  const baseIconFontSize = 18
  const minFontSize = 4

  // Calculate scale factor based on block width (normalize to 100px base)
  const widthScale = blockWidth / 100

  // Calculate actual font sizes, clamped between minimum and reasonable maximum
  const nameFontSize = Math.max(minFontSize, Math.min(baseNameFontSize * 1.2, baseNameFontSize * widthScale))
  const iconFontSize = Math.max(minFontSize, Math.min(baseIconFontSize * 1.2, baseIconFontSize * widthScale))

  // Determine if text should be hidden (font would be smaller than minimum)
  // Hide text when block is too small to display readable text
  const hideText = baseNameFontSize * widthScale < minFontSize

  // When in icon-only mode, scale icon to fit the block nicely
  const iconOnlySize = Math.min(
    blockWidth * 0.6,   // 60% of width
    blockHeight * 0.6,  // 60% of height
    24                  // Maximum icon size
  )

  // Calculate padding based on block size
  const isSmallBlock = blockWidth < 50

  return (
    <>
      {/* NodeResizer - only visible when selected */}
      <NodeResizer
        minWidth={30}
        minHeight={24}
        isVisible={selected}
        lineClassName="border-blue-400"
        handleClassName="h-2 w-2 bg-blue-500 border border-blue-300 rounded-sm"
        onResizeEnd={handleResizeEnd}
      />
      <div
        className={`
          rounded-lg shadow-lg h-full w-full
          ${getCategoryClass()}
          ${selected ? 'ring-2 ring-white ring-opacity-50' : ''}
        `}
        style={{
          transform: `rotate(${rotation}deg)`,
          padding: isSmallBlock ? '4px' : '8px 12px',
          minWidth: '30px',
          minHeight: '24px',
        }}
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
        <div
          className="text-center text-gray-900 flex flex-col items-center justify-center h-full"
          style={{ transform: `rotate(${-rotation}deg)` }}
        >
          {/* Show block name only when block is large enough */}
          {!hideText && (
            <div
              className="font-semibold truncate w-full"
              style={{
                fontSize: `${nameFontSize}px`,
                maxWidth: `${blockWidth - (isSmallBlock ? 8 : 16)}px`,
                lineHeight: 1.2,
              }}
            >
              {block.name}
            </div>
          )}
          {/* Show icon - scale larger when in icon-only mode */}
          {displayIcon && (
            <div
              className={hideText ? '' : 'mt-1'}
              style={{
                fontSize: `${hideText ? iconOnlySize : iconFontSize}px`,
                lineHeight: 1,
              }}
            >
              {displayIcon}
            </div>
          )}
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
    </>
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

  // Check if size changed
  if (prevBlock.size?.width !== nextBlock.size?.width) return false
  if (prevBlock.size?.height !== nextBlock.size?.height) return false

  // Check if parameters changed (simple JSON comparison for now)
  if (JSON.stringify(prevBlock.parameters) !== JSON.stringify(nextBlock.parameters)) return false

  // Check ports
  if (JSON.stringify(prevBlock.inputPorts) !== JSON.stringify(nextBlock.inputPorts)) return false
  if (JSON.stringify(prevBlock.outputPorts) !== JSON.stringify(nextBlock.outputPorts)) return false

  return true
}

export const BlockNode = memo(BlockNodeComponent, arePropsEqual)
