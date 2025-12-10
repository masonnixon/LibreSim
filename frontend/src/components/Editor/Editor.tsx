import { useCallback, useMemo, useRef } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
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
import { blockRegistry } from '../../blocks'

export function Editor() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const { screenToFlowPosition } = useReactFlow()

  const { model, addBlock, updateBlockPosition, addConnection, removeBlock, removeConnection, selectBlocks } =
    useModelStore()
  const { draggingBlockType, setDraggingBlockType } = useUIStore()

  // Convert model blocks to React Flow nodes
  const initialNodes: Node[] = useMemo(() => {
    if (!model) return []
    return model.blocks.map((block) => ({
      id: block.id,
      type: 'blockNode',
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
        const connectionId = addConnection({
          sourceBlockId: params.source,
          sourcePortId: params.sourceHandle,
          targetBlockId: params.target,
          targetPortId: params.targetHandle,
        })
        if (connectionId) {
          setEdges((eds) =>
            addEdge(
              {
                ...params,
                id: connectionId,
                type: 'smoothstep',
              },
              eds
            )
          )
        }
      }
    },
    [addConnection, setEdges]
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

      const blockId = addBlock(definition, position)
      if (blockId) {
        setNodes((nds) => [
          ...nds,
          {
            id: blockId,
            type: 'blockNode',
            position,
            data: {
              block: model?.blocks.find((b) => b.id === blockId),
              definition,
            },
          },
        ])
      }

      setDraggingBlockType(null)
    },
    [draggingBlockType, screenToFlowPosition, addBlock, setNodes, setDraggingBlockType, model]
  )

  const nodeTypes: NodeTypes = useMemo(
    () => ({
      blockNode: BlockNode,
    }),
    []
  )

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
    <div ref={reactFlowWrapper} className="flex-1">
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
              default:
                return '#6c7086'
            }
          }}
        />
      </ReactFlow>
    </div>
  )
}
