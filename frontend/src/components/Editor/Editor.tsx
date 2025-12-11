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
} from '@xyflow/react'
import { useModelStore } from '../../store/modelStore'
import { useUIStore } from '../../store/uiStore'
import { BlockNode } from './BlockNode'
import { SubsystemNode } from './SubsystemNode'
import { blockRegistry } from '../../blocks'

export function Editor() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const { screenToFlowPosition } = useReactFlow()

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
  } = useModelStore()
  const { draggingBlockType, setDraggingBlockType } = useUIStore()

  // Context menu state
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null)

  // Convert model blocks to React Flow nodes
  const initialNodes: Node[] = useMemo(() => {
    if (!model) return []
    return model.blocks.map((block) => ({
      id: block.id,
      type: block.type === 'subsystem' ? 'subsystemNode' : 'blockNode',
      position: block.position,
      data: {
        block,
        definition: blockRegistry.get(block.type),
      },
    }))
  }, [model?.blocks])

  // Convert model connections to React Flow edges
  const initialEdges: Edge[] = useMemo(() => {
    if (!model) return []
    return model.connections.map((conn) => ({
      id: conn.id,
      source: conn.sourceBlockId,
      sourceHandle: conn.sourcePortId,
      target: conn.targetBlockId,
      targetHandle: conn.targetPortId,
      type: 'smoothstep',
      animated: false,
    }))
  }, [model?.connections])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  // Sync React Flow nodes with model state when model changes
  useEffect(() => {
    if (!model) {
      setNodes([])
      setEdges([])
      return
    }

    const newNodes: Node[] = model.blocks.map((block) => ({
      id: block.id,
      type: block.type === 'subsystem' ? 'subsystemNode' : 'blockNode',
      position: block.position,
      data: {
        block,
        definition: blockRegistry.get(block.type),
      },
    }))

    const newEdges: Edge[] = model.connections.map((conn) => ({
      id: conn.id,
      source: conn.sourceBlockId,
      sourceHandle: conn.sourcePortId,
      target: conn.targetBlockId,
      targetHandle: conn.targetPortId,
      type: 'smoothstep',
      animated: false,
    }))

    setNodes(newNodes)
    setEdges(newEdges)
  }, [model, setNodes, setEdges])

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
  }, [selectedBlockIds, createSubsystem])

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
            <span>{ }</span>
            <span>Create Subsystem</span>
            <span className="ml-auto text-slate-400 text-xs">{selectedBlockIds.length} blocks</span>
          </button>
        </div>
      )}
    </div>
  )
}
