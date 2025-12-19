import { useCallback, useMemo, useRef, useEffect, useState } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Connection,
  Node,
  Edge,
  NodeTypes,
  useReactFlow,
  OnConnect,
  Panel,
} from '@xyflow/react'
import { useModelStore } from '../../store/modelStore'
import { useUIStore } from '../../store/uiStore'
import { BlockNode } from './BlockNode'
import { SubsystemNode } from './SubsystemNode'
import { blockRegistry } from '../../blocks'
import { getIsPropertiesFocused } from '../Properties/PropertiesPanel'
import type { BlockDefinition, BlockInstance } from '../../types/block'

// Create a fallback definition for unknown block types
function getDefinitionOrFallback(block: BlockInstance): BlockDefinition {
  const def = blockRegistry.get(block.type)
  if (def) return def

  // Create a fallback definition for unknown block types
  return {
    type: block.type,
    category: 'math', // neutral gray color
    name: block.name || block.type,
    description: `Unknown block type: ${block.type}`,
    inputs: block.inputPorts.map((p) => ({
      name: p.name,
      dataType: p.dataType || 'double',
      dimensions: p.dimensions || [1],
    })),
    outputs: block.outputPorts.map((p) => ({
      name: p.name,
      dataType: p.dataType || 'double',
      dimensions: p.dimensions || [1],
    })),
    parameters: [],
    icon: '?',
  }
}

export function Editor() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const { screenToFlowPosition, getNodes } = useReactFlow()

  // Mobile detection for responsive MiniMap
  const [isMobile, setIsMobile] = useState(false)

  // Track if an input field is focused (to disable ReactFlow keyboard shortcuts)
  const [inputFocused, setInputFocused] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Listen for focus/blur events on input fields globally
  useEffect(() => {
    const handleFocusIn = (e: FocusEvent) => {
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') {
        setInputFocused(true)
      }
    }
    const handleFocusOut = (e: FocusEvent) => {
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') {
        setInputFocused(false)
      }
    }
    document.addEventListener('focusin', handleFocusIn)
    document.addEventListener('focusout', handleFocusOut)
    return () => {
      document.removeEventListener('focusin', handleFocusIn)
      document.removeEventListener('focusout', handleFocusOut)
    }
  }, [])

  // Prevent ReactFlow from receiving keyboard events when input is focused
  // This stops node deselection when typing in Properties panel
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      // If we're in an input field, stop the event from reaching ReactFlow
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') {
        e.stopPropagation()
      }
    }
    // Use capture phase to intercept before ReactFlow gets the event
    document.addEventListener('keydown', handleKeyDown, true)
    return () => {
      document.removeEventListener('keydown', handleKeyDown, true)
    }
  }, [])

  const {
    model,
    addBlock,
    updateBlockPosition,
    addConnection,
    removeBlock,
    removeConnection,
    selectBlocks,
    selectedBlockIds,
    createSubsystem,
    expandSubsystem,
    currentPath,
    enterSubsystem,
    exitSubsystem,
    navigateToPath,
    getCurrentBlocks,
    getCurrentConnections,
  } = useModelStore()
  const { draggingBlockType, setDraggingBlockType } = useUIStore()

  // Context menu state
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null)

  // Selection toolbar position
  const [selectionBounds, setSelectionBounds] = useState<{ x: number; y: number; width: number; height: number } | null>(null)

  // Selected edge ID for showing signal dimensions
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null)

  // Clipboard for copy/paste functionality
  const [clipboard, setClipboard] = useState<{
    blocks: BlockInstance[]
    connections: { sourceBlockId: string; sourcePortId: string; targetBlockId: string; targetPortId: string }[]
  }>({ blocks: [], connections: [] })

  // Get current view blocks and connections (handles subsystem navigation)
  const currentBlocks = getCurrentBlocks()
  const currentConnections = getCurrentConnections()

  // Convert model blocks to React Flow nodes
  const initialNodes: Node[] = useMemo(() => {
    if (!model) return []
    return currentBlocks.map((block) => ({
      id: block.id,
      type: block.type === 'subsystem' ? 'subsystemNode' : 'blockNode',
      position: block.position,
      data: {
        block,
        definition: getDefinitionOrFallback(block),
      },
    }))
  }, [model, currentBlocks])

  // Convert model connections to React Flow edges
  const initialEdges: Edge[] = useMemo(() => {
    if (!model) return []
    return currentConnections.map((conn) => ({
      id: conn.id,
      source: conn.sourceBlockId,
      sourceHandle: conn.sourcePortId,
      target: conn.targetBlockId,
      targetHandle: conn.targetPortId,
      type: 'smoothstep',
      animated: false,
    }))
  }, [model, currentConnections])

  const [nodes, setNodes, onNodesChangeBase] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  // Wrap onNodesChange to prevent selection changes when input is focused
  const onNodesChange = useCallback(
    (changes: Parameters<typeof onNodesChangeBase>[0]) => {
      // If an input field is focused, filter out selection changes
      // This prevents ReactFlow from deselecting nodes when typing in Properties panel
      if (inputFocused) {
        const filteredChanges = changes.filter(
          (change) => change.type !== 'select'
        )
        if (filteredChanges.length > 0) {
          onNodesChangeBase(filteredChanges)
        }
      } else {
        onNodesChangeBase(changes)
      }
    },
    [inputFocused, onNodesChangeBase]
  )

  // Sync React Flow nodes with model state when model or current path changes
  useEffect(() => {
    if (!model) {
      setNodes([])
      setEdges([])
      return
    }

    // Preserve selection state from current nodes
    const selectedNodeIds = new Set(selectedBlockIds)

    const newNodes: Node[] = currentBlocks.map((block) => ({
      id: block.id,
      type: block.type === 'subsystem' ? 'subsystemNode' : 'blockNode',
      position: block.position,
      selected: selectedNodeIds.has(block.id),
      data: {
        block,
        definition: getDefinitionOrFallback(block),
      },
    }))

    // Build a map of block IDs to their port IDs for validation
    const blockPortMap = new Map<string, { inputs: Set<string>; outputs: Set<string> }>()
    currentBlocks.forEach((block) => {
      blockPortMap.set(block.id, {
        inputs: new Set(block.inputPorts.map((p) => p.id)),
        outputs: new Set(block.outputPorts.map((p) => p.id)),
      })
    })

    // Filter out invalid edges (where source/target block or port doesn't exist)
    const validEdges: Edge[] = currentConnections
      .filter((conn) => {
        const srcBlock = blockPortMap.get(conn.sourceBlockId)
        const dstBlock = blockPortMap.get(conn.targetBlockId)

        if (!srcBlock) {
          console.warn(`[Editor] Skipping edge: source block ${conn.sourceBlockId} not found`)
          return false
        }
        if (!dstBlock) {
          console.warn(`[Editor] Skipping edge: target block ${conn.targetBlockId} not found`)
          return false
        }
        if (!srcBlock.outputs.has(conn.sourcePortId)) {
          console.warn(`[Editor] Skipping edge: source port ${conn.sourcePortId} not found on block`)
          return false
        }
        if (!dstBlock.inputs.has(conn.targetPortId)) {
          console.warn(`[Editor] Skipping edge: target port ${conn.targetPortId} not found on block`)
          return false
        }
        return true
      })
      .map((conn) => {
        const isSelected = conn.id === selectedEdgeId
        // Get dimensions from source port
        const sourceBlock = currentBlocks.find(b => b.id === conn.sourceBlockId)
        const sourcePort = sourceBlock?.outputPorts.find(p => p.id === conn.sourcePortId)
        const dims = sourcePort?.dimensions || [1]
        const dimLabel = dims.length === 1 && dims[0] === 1 ? '1' : dims.join('×')

        return {
          id: conn.id,
          source: conn.sourceBlockId,
          sourceHandle: conn.sourcePortId,
          target: conn.targetBlockId,
          targetHandle: conn.targetPortId,
          type: 'smoothstep',
          animated: false,
          selected: isSelected,
          style: isSelected ? { stroke: '#22d3ee', strokeWidth: 2 } : undefined,
          label: isSelected ? dimLabel : undefined,
          labelStyle: isSelected ? {
            fill: '#fff',
            fontWeight: 600,
            fontSize: 11,
          } : undefined,
          labelBgStyle: isSelected ? {
            fill: '#1e293b',
            fillOpacity: 0.9,
          } : undefined,
          labelBgPadding: [4, 4] as [number, number],
          labelBgBorderRadius: 4,
        }
      })

    setNodes(newNodes)
    setEdges(validEdges)
  }, [model, currentBlocks, currentConnections, selectedEdgeId, selectedBlockIds, setNodes, setEdges])

  // Sync React Flow state back to model store
  const onNodeDragStop = useCallback(
    (_: React.MouseEvent, node: Node) => {
      updateBlockPosition(node.id, node.position)
    },
    [updateBlockPosition]
  )

  const onConnect: OnConnect = useCallback(
    (params: Connection) => {
      if (params.source && params.target && params.sourceHandle && params.targetHandle) {
        // Add connection to model - the useEffect will sync edges automatically
        addConnection({
          sourceBlockId: params.source,
          sourcePortId: params.sourceHandle,
          targetBlockId: params.target,
          targetPortId: params.targetHandle,
        })
      }
    },
    [addConnection]
  )

  const onNodesDelete = useCallback(
    (deleted: Node[]) => {
      deleted.forEach((node) => removeBlock(node.id))
    },
    [removeBlock]
  )

  const onEdgesDelete = useCallback(
    (deleted: Edge[]) => {
      deleted.forEach((edge) => removeConnection(edge.id))
    },
    [removeConnection]
  )

  // Handle edge click to show signal dimensions
  const onEdgeClick = useCallback(
    (_: React.MouseEvent, edge: Edge) => {
      // Toggle selection - if clicking same edge, deselect it
      setSelectedEdgeId(prev => prev === edge.id ? null : edge.id)
    },
    []
  )

  // Deselect edge when clicking on the pane
  const onPaneClick = useCallback(() => {
    setSelectedEdgeId(null)
  }, [])

  // Get signal dimensions for a connection
  const getSignalDimensions = useCallback((sourceBlockId: string, sourcePortId: string): string => {
    const sourceBlock = currentBlocks.find(b => b.id === sourceBlockId)
    if (!sourceBlock) return '?'

    const sourcePort = sourceBlock.outputPorts.find(p => p.id === sourcePortId)
    if (!sourcePort) return '?'

    const dims = sourcePort.dimensions || [1]
    if (dims.length === 1 && dims[0] === 1) {
      return '1'  // Scalar
    }
    return dims.join('×')
  }, [currentBlocks])

  const onSelectionChange = useCallback(
    ({ nodes: selectedNodes }: { nodes: Node[] }) => {
      selectBlocks(selectedNodes.map((n) => n.id))

      // Calculate selection bounds for toolbar positioning
      if (selectedNodes.length >= 2) {
        const positions = selectedNodes.map((n) => n.position)
        const minX = Math.min(...positions.map((p) => p.x))
        const maxX = Math.max(...positions.map((p) => p.x)) + 140 // approximate block width
        const minY = Math.min(...positions.map((p) => p.y))
        const maxY = Math.max(...positions.map((p) => p.y)) + 60 // approximate block height
        setSelectionBounds({
          x: (minX + maxX) / 2,
          y: minY - 50, // Position above the selection
          width: maxX - minX,
          height: maxY - minY,
        })
      } else {
        setSelectionBounds(null)
      }
    },
    [selectBlocks]
  )

  // Handle drop from block library
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()

      if (!draggingBlockType) return

      const definition = blockRegistry.get(draggingBlockType)
      if (!definition) return

      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      })

      // Add block to model - the useEffect will sync nodes automatically
      addBlock(definition, position)
      setDraggingBlockType(null)
    },
    [draggingBlockType, screenToFlowPosition, addBlock, setDraggingBlockType]
  )

  const nodeTypes: NodeTypes = useMemo(
    () => ({
      blockNode: BlockNode,
      subsystemNode: SubsystemNode,
    }),
    []
  )

  // Check if selected block is a subsystem
  const selectedSubsystem = useMemo(() => {
    if (selectedBlockIds.length !== 1) return null
    const block = currentBlocks.find(b => b.id === selectedBlockIds[0])
    return block?.type === 'subsystem' ? block : null
  }, [selectedBlockIds, currentBlocks])

  // Context menu handlers
  const handleContextMenu = useCallback(
    (event: React.MouseEvent) => {
      event.preventDefault()
      // Show context menu for 2+ selected blocks OR single subsystem
      if (selectedBlockIds.length >= 2 || selectedSubsystem) {
        setContextMenu({ x: event.clientX, y: event.clientY })
      }
    },
    [selectedBlockIds, selectedSubsystem]
  )

  const handleCloseContextMenu = useCallback(() => {
    setContextMenu(null)
  }, [])

  const handleCreateSubsystem = useCallback(() => {
    if (selectedBlockIds.length >= 2) {
      createSubsystem(selectedBlockIds)
    }
    setContextMenu(null)
    setSelectionBounds(null)
  }, [selectedBlockIds, createSubsystem])

  const handleExpandSubsystem = useCallback(() => {
    if (selectedSubsystem) {
      expandSubsystem(selectedSubsystem.id)
    }
    setContextMenu(null)
  }, [selectedSubsystem, expandSubsystem])

  // Handle double-click on nodes to enter subsystems or open scope plots
  const { openPlotWindow } = useUIStore()

  const onNodeDoubleClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (node.type === 'subsystemNode') {
        enterSubsystem(node.id)
      } else {
        // Check if this is a scope block
        const block = currentBlocks.find(b => b.id === node.id)
        if (block?.type === 'scope') {
          openPlotWindow(block.id)
        }
      }
    },
    [enterSubsystem, currentBlocks, openPlotWindow]
  )

  // Handle keyboard navigation (Escape to exit subsystem)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't handle keyboard events when Properties panel inputs are focused
      if (getIsPropertiesFocused()) return

      if (e.key === 'Escape' && currentPath.length > 0) {
        exitSubsystem()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentPath, exitSubsystem])

  // Handle keyboard shortcuts (Delete, Ctrl+C, Ctrl+V, Ctrl+A)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't handle keyboard events when input fields are focused
      if (inputFocused || getIsPropertiesFocused()) return

      const isCtrlOrCmd = e.ctrlKey || e.metaKey

      // Delete key - delete selected blocks and/or selected edge
      if (e.key === 'Delete' || e.key === 'Backspace') {
        e.preventDefault()

        // Delete selected blocks
        if (selectedBlockIds.length > 0) {
          selectedBlockIds.forEach(blockId => removeBlock(blockId))
        }

        // Delete selected edge
        if (selectedEdgeId) {
          removeConnection(selectedEdgeId)
          setSelectedEdgeId(null)
        }
      }

      // Ctrl+A - Select all blocks
      if (isCtrlOrCmd && e.key === 'a') {
        e.preventDefault()
        const allBlockIds = currentBlocks.map(b => b.id)
        selectBlocks(allBlockIds)
      }

      // Ctrl+C - Copy selected blocks and their internal connections
      if (isCtrlOrCmd && e.key === 'c') {
        e.preventDefault()
        if (selectedBlockIds.length > 0) {
          const blocksToCopy = currentBlocks.filter(b => selectedBlockIds.includes(b.id))

          // Find connections between selected blocks
          const connectionsToCopy = currentConnections
            .filter(conn =>
              selectedBlockIds.includes(conn.sourceBlockId) &&
              selectedBlockIds.includes(conn.targetBlockId)
            )
            .map(conn => ({
              sourceBlockId: conn.sourceBlockId,
              sourcePortId: conn.sourcePortId,
              targetBlockId: conn.targetBlockId,
              targetPortId: conn.targetPortId,
            }))

          // Deep copy the blocks and connections
          setClipboard({
            blocks: JSON.parse(JSON.stringify(blocksToCopy)),
            connections: JSON.parse(JSON.stringify(connectionsToCopy)),
          })
        }
      }

      // Ctrl+V - Paste copied blocks and their connections
      if (isCtrlOrCmd && e.key === 'v') {
        e.preventDefault()
        if (clipboard.blocks.length > 0) {
          // Calculate offset for pasted blocks (paste slightly offset from original)
          const pasteOffset = { x: 50, y: 50 }

          const newBlockIds: string[] = []
          const oldToNewIdMap = new Map<string, string>()
          const oldToNewPortIdMap = new Map<string, string>()

          clipboard.blocks.forEach(block => {
            const definition = blockRegistry.get(block.type)
            if (definition) {
              const newPosition = {
                x: block.position.x + pasteOffset.x,
                y: block.position.y + pasteOffset.y,
              }
              const newId = addBlock(definition, newPosition)
              if (newId) {
                newBlockIds.push(newId)
                oldToNewIdMap.set(block.id, newId)

                // Map old port IDs to new port IDs
                block.inputPorts.forEach((port, idx) => {
                  oldToNewPortIdMap.set(port.id, `${newId}-in-${idx}`)
                })
                block.outputPorts.forEach((port, idx) => {
                  oldToNewPortIdMap.set(port.id, `${newId}-out-${idx}`)
                })

                // Copy parameters from the original block
                if (Object.keys(block.parameters).length > 0) {
                  // Use setTimeout to ensure the block is created before updating
                  setTimeout(() => {
                    useModelStore.getState().updateBlockParameters(newId, block.parameters)
                  }, 0)
                }
              }
            }
          })

          // Recreate connections between pasted blocks
          if (clipboard.connections.length > 0) {
            setTimeout(() => {
              clipboard.connections.forEach(conn => {
                const newSourceBlockId = oldToNewIdMap.get(conn.sourceBlockId)
                const newTargetBlockId = oldToNewIdMap.get(conn.targetBlockId)
                const newSourcePortId = oldToNewPortIdMap.get(conn.sourcePortId)
                const newTargetPortId = oldToNewPortIdMap.get(conn.targetPortId)

                if (newSourceBlockId && newTargetBlockId && newSourcePortId && newTargetPortId) {
                  addConnection({
                    sourceBlockId: newSourceBlockId,
                    sourcePortId: newSourcePortId,
                    targetBlockId: newTargetBlockId,
                    targetPortId: newTargetPortId,
                  })
                }
              })
            }, 10)
          }

          // Select the newly pasted blocks
          if (newBlockIds.length > 0) {
            selectBlocks(newBlockIds)
          }

          // Update clipboard positions for next paste
          setClipboard(prev => ({
            ...prev,
            blocks: prev.blocks.map(b => ({
              ...b,
              position: {
                x: b.position.x + pasteOffset.x,
                y: b.position.y + pasteOffset.y,
              }
            }))
          }))
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [
    inputFocused,
    selectedBlockIds,
    selectedEdgeId,
    currentBlocks,
    currentConnections,
    clipboard,
    removeBlock,
    removeConnection,
    selectBlocks,
    addBlock,
    addConnection,
  ])

  if (!model) {
    return (
      <div className="flex-1 flex items-center justify-center bg-editor-bg text-gray-400">
        <div className="text-center">
          <p className="text-lg mb-2">No model loaded</p>
          <p className="text-sm">Create a new model or open an existing one</p>
        </div>
      </div>
    )
  }

  return (
    <div ref={reactFlowWrapper} className="flex-1 relative" onClick={handleCloseContextMenu}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeDragStop={onNodeDragStop}
        onNodesDelete={onNodesDelete}
        onEdgesDelete={onEdgesDelete}
        onEdgeClick={onEdgeClick}
        onPaneClick={onPaneClick}
        onSelectionChange={onSelectionChange}
        onNodeDoubleClick={onNodeDoubleClick}
        onDragOver={onDragOver}
        onDrop={onDrop}
        onContextMenu={handleContextMenu}
        nodeTypes={nodeTypes}
        fitView
        snapToGrid
        snapGrid={[10, 10]}
        deleteKeyCode={inputFocused ? null : ['Backspace', 'Delete']}
        selectionKeyCode={inputFocused ? null : 'Shift'}
        multiSelectionKeyCode={inputFocused ? null : 'Shift'}
      >
        <Background color="#45475a" gap={20} />
        <Controls className="bg-editor-surface border-editor-border" />
        <MiniMap
          className="bg-editor-surface border-editor-border"
          style={isMobile ? { width: 100, height: 60 } : undefined}
          nodeColor={(node) => {
            const def = node.data?.definition
            if (!def) return '#6c7086'
            switch (def.category) {
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
              default:
                return '#6c7086'
            }
          }}
        />

        {/* Breadcrumb Navigation - shows path when inside a subsystem */}
        {currentPath.length > 0 && (
          <Panel position="top-left" className="!top-2 !left-2">
            <div className="bg-slate-800/95 backdrop-blur-sm border border-slate-600 rounded-lg shadow-xl px-3 py-2 flex items-center gap-1 text-sm">
              {/* Root/Model link */}
              <button
                onClick={() => navigateToPath(-1)}
                className="text-cyan-400 hover:text-cyan-300 font-medium transition-colors"
              >
                {model?.metadata.name || 'Model'}
              </button>

              {/* Path items */}
              {currentPath.map((item, index) => (
                <div key={item.id} className="flex items-center">
                  <svg className="w-4 h-4 text-slate-500 mx-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  {index === currentPath.length - 1 ? (
                    <span className="text-white font-medium">{item.name}</span>
                  ) : (
                    <button
                      onClick={() => navigateToPath(index)}
                      className="text-cyan-400 hover:text-cyan-300 font-medium transition-colors"
                    >
                      {item.name}
                    </button>
                  )}
                </div>
              ))}

              {/* Exit button */}
              <button
                onClick={exitSubsystem}
                className="ml-3 px-2 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 rounded transition-colors flex items-center gap-1"
                title="Exit subsystem (Esc)"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Exit
              </button>
            </div>
          </Panel>
        )}

        {/* Selection Toolbar - appears when 2+ blocks are selected */}
        {selectedBlockIds.length >= 2 && (
          <Panel position="top-center" className="!top-4">
            <div className="bg-slate-800/95 backdrop-blur-sm border border-cyan-500/50 rounded-lg shadow-xl px-4 py-2 flex items-center gap-3">
              <span className="text-cyan-400 text-sm font-medium">
                {selectedBlockIds.length} blocks selected
              </span>
              <div className="w-px h-5 bg-slate-600" />
              <button
                onClick={handleCreateSubsystem}
                className="flex items-center gap-2 px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-medium rounded-md transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                </svg>
                Create Subsystem
              </button>
            </div>
          </Panel>
        )}
      </ReactFlow>

      {/* Context Menu */}
      {contextMenu && (
        <div
          className="absolute z-50 bg-slate-800 border border-slate-600 rounded-lg shadow-xl py-1 min-w-[180px]"
          style={{ left: contextMenu.x, top: contextMenu.y }}
        >
          {/* Show "Create Subsystem" when 2+ blocks selected */}
          {selectedBlockIds.length >= 2 && (
            <button
              className="w-full px-4 py-2 text-left text-sm text-white hover:bg-slate-700 flex items-center gap-2"
              onClick={handleCreateSubsystem}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
              </svg>
              <span>Create Subsystem</span>
              <span className="ml-auto text-slate-400 text-xs">{selectedBlockIds.length} blocks</span>
            </button>
          )}
          {/* Show "Expand Subsystem" when single subsystem selected */}
          {selectedSubsystem && (
            <>
              <button
                className="w-full px-4 py-2 text-left text-sm text-white hover:bg-slate-700 flex items-center gap-2"
                onClick={() => { enterSubsystem(selectedSubsystem.id); setContextMenu(null) }}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                </svg>
                <span>Enter Subsystem</span>
              </button>
              <button
                className="w-full px-4 py-2 text-left text-sm text-white hover:bg-slate-700 flex items-center gap-2"
                onClick={handleExpandSubsystem}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
                <span>Expand Subsystem</span>
                <span className="ml-auto text-slate-400 text-xs">{selectedSubsystem.children?.length || 0} blocks</span>
              </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}
