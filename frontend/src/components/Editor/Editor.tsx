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

export function Editor() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const { screenToFlowPosition, getNodes } = useReactFlow()

  // Mobile detection for responsive MiniMap
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
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
        definition: blockRegistry.get(block.type),
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

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  // Sync React Flow nodes with model state when model or current path changes
  useEffect(() => {
    if (!model) {
      setNodes([])
      setEdges([])
      return
    }

    const newNodes: Node[] = currentBlocks.map((block) => ({
      id: block.id,
      type: block.type === 'subsystem' ? 'subsystemNode' : 'blockNode',
      position: block.position,
      data: {
        block,
        definition: blockRegistry.get(block.type),
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
      .map((conn) => ({
        id: conn.id,
        source: conn.sourceBlockId,
        sourceHandle: conn.sourcePortId,
        target: conn.targetBlockId,
        targetHandle: conn.targetPortId,
        type: 'smoothstep',
        animated: false,
      }))

    setNodes(newNodes)
    setEdges(validEdges)
  }, [model, currentBlocks, currentConnections, setNodes, setEdges])

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

  // Context menu handlers
  const handleContextMenu = useCallback(
    (event: React.MouseEvent) => {
      event.preventDefault()
      if (selectedBlockIds.length >= 2) {
        setContextMenu({ x: event.clientX, y: event.clientY })
      }
    },
    [selectedBlockIds]
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

  // Handle double-click on nodes to enter subsystems
  const onNodeDoubleClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (node.type === 'subsystemNode') {
        enterSubsystem(node.id)
      }
    },
    [enterSubsystem]
  )

  // Handle keyboard navigation (Escape to exit subsystem)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && currentPath.length > 0) {
        exitSubsystem()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentPath, exitSubsystem])

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
        onSelectionChange={onSelectionChange}
        onNodeDoubleClick={onNodeDoubleClick}
        onDragOver={onDragOver}
        onDrop={onDrop}
        onContextMenu={handleContextMenu}
        nodeTypes={nodeTypes}
        fitView
        snapToGrid
        snapGrid={[10, 10]}
        deleteKeyCode={['Backspace', 'Delete']}
        multiSelectionKeyCode="Shift"
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
        </div>
      )}
    </div>
  )
}
