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
  EdgeTypes,
  NodeTypes,
  useReactFlow,
  OnConnect,
  OnConnectEnd,
  Panel,
  OnConnectStart,
} from '@xyflow/react'
import { useModelStore } from '../../store/modelStore'
import { useUIStore } from '../../store/uiStore'
import { BlockNode } from './BlockNode'
import { SubsystemNode } from './SubsystemNode'
import { CustomEdge } from './CustomEdge'
import { blockRegistry } from '../../blocks'
import { getIsPropertiesFocused } from '../Properties/PropertiesPanel'
import { findNearestEdge, generateSmartWaypoints } from '../../utils/smartRouting'
import { getDownstreamConnectionIds, getSourceBranchConnectionIds } from '../../utils/signalTraversal'
import type { BlockDefinition, BlockInstance } from '../../types/block'
import { useEditorKeyboardShortcuts } from '../../hooks/useEditorKeyboardShortcuts'

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
  const { screenToFlowPosition, fitView } = useReactFlow()

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
    addScopeInput,
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
    spreadBlocks,
    rotateSelectedBlocks,
    undo,
    redo,
    pushHistory,
  } = useModelStore()
  const { draggingBlockType, setDraggingBlockType } = useUIStore()

  // Context menu state
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null)

  // Signal context menu state (right-click on edge)
  const [signalContextMenu, setSignalContextMenu] = useState<{
    x: number
    y: number
    edgeId: string
    connectionId: string
  } | null>(null)

  // Signal renaming state (inline text input)
  const [renamingSignal, setRenamingSignal] = useState<{
    connectionId: string
    x: number
    y: number
  } | null>(null)
  const signalNameInputRef = useRef<HTMLInputElement>(null)

  // Highlighted connections for signal tracing
  const [highlightedConnections, setHighlightedConnections] = useState<Set<string>>(new Set())

  // Selection toolbar position (used for future toolbar positioning, currently tracked but not displayed)
  const [, setSelectionBounds] = useState<{ x: number; y: number; width: number; height: number } | null>(null)

  // Selected edge ID for showing signal dimensions
  const [selectedEdgeId, setSelectedEdgeIdInternal] = useState<string | null>(null)

  // Wrap setSelectedEdgeId to log all changes with stack trace
  const setSelectedEdgeId = useCallback((value: string | null | ((prev: string | null) => string | null)) => {
    setSelectedEdgeIdInternal(prev => {
      const newValue = typeof value === 'function' ? value(prev) : value
      if (newValue !== prev) {
        console.log('[Editor] setSelectedEdgeId:', prev, '->', newValue)
        console.trace('[Editor] setSelectedEdgeId stack')
      }
      return newValue
    })
  }, [])

  // Track if we're dragging from an input port (for visual feedback)
  const [isDraggingFromInput, setIsDraggingFromInput] = useState(false)
  const [nearestEdgeForBranch, setNearestEdgeForBranch] = useState<string | null>(null)

  // Get current view blocks and connections (handles subsystem navigation)
  const currentBlocks = getCurrentBlocks()
  const currentConnections = getCurrentConnections()

  useEditorKeyboardShortcuts({
    inputFocused,
    selectedBlockIds,
    selectedEdgeId,
    currentBlocks,
    currentConnections,
    dropBlock: removeBlock,
    dropConnection: removeConnection,
    selectBlocks,
    addBlock,
    addConnection,
    spreadBlocks,
    rotateSelectedBlocks,
    undo,
    redo,
    pushHistory,
    setSelectedEdgeId,
    setHighlightedConnections,
  })

  // Convert model blocks to React Flow nodes
  const initialNodes: Node[] = useMemo(() => {
    if (!model) return []
    return currentBlocks.map((block) => ({
      id: block.id,
      type: block.type === 'subsystem' ? 'subsystemNode' : 'blockNode',
      position: block.position,
      // Pass explicit size if stored in model (for resizable blocks)
      ...(block.size && { width: block.size.width, height: block.size.height }),
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
      type: 'custom',
      animated: false,
      data: {
        waypoints: conn.waypoints || [],
        connectionId: conn.id,
        signalName: conn.signalName,
        labelOffset: conn.labelOffset,
      },
    }))
  }, [model, currentConnections])

  const [nodes, setNodes, onNodesChangeBase] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChangeBase] = useEdgesState(initialEdges)

  // Wrap onEdgesChange to log and filter edge changes
  const onEdgesChange = useCallback(
    (changes: Parameters<typeof onEdgesChangeBase>[0]) => {
      // Log all edge changes to understand what's happening
      const removeChanges = changes.filter((c) => c.type === 'remove')
      if (removeChanges.length > 0) {
        console.log('[Editor] onEdgesChange - REMOVE changes:', removeChanges)
        console.trace('[Editor] onEdgesChange remove stack')
        // Don't process remove changes from ReactFlow - let our model handle deletion
        const nonRemoveChanges = changes.filter((c) => c.type !== 'remove')
        if (nonRemoveChanges.length > 0) {
          onEdgesChangeBase(nonRemoveChanges)
        }
        return
      }
      onEdgesChangeBase(changes)
    },
    [onEdgesChangeBase]
  )

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
    console.log('[Editor] useEffect sync - model:', model ? 'exists' : 'null',
      'currentBlocks:', currentBlocks.length, 'currentConnections:', currentConnections.length,
      'selectedEdgeId:', selectedEdgeId)

    if (!model) {
      console.log('[Editor] Model is null - clearing nodes and edges')
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
        const isBranchTarget = conn.id === nearestEdgeForBranch
        const isHighlighted = highlightedConnections.has(conn.id)
        // Get dimensions from source port
        const sourceBlock = currentBlocks.find(b => b.id === conn.sourceBlockId)
        const sourcePort = sourceBlock?.outputPorts.find(p => p.id === conn.sourcePortId)
        const dims = sourcePort?.dimensions || [1]
        const dimLabel = dims.length === 1 && dims[0] === 1 ? '1' : dims.join('×')

        // Determine edge style: branch target (green), highlighted (yellow), selected (cyan), or default
        let edgeStyle: React.CSSProperties | undefined
        if (isBranchTarget) {
          edgeStyle = { stroke: '#22c55e', strokeWidth: 3 } // Green for branch target
        } else if (isHighlighted) {
          edgeStyle = { stroke: '#eab308', strokeWidth: 3 } // Yellow for signal tracing highlight
        } else if (isSelected) {
          edgeStyle = { stroke: '#22d3ee', strokeWidth: 2 }
        }

        return {
          id: conn.id,
          source: conn.sourceBlockId,
          sourceHandle: conn.sourcePortId,
          target: conn.targetBlockId,
          targetHandle: conn.targetPortId,
          type: 'custom',
          animated: false,
          selected: isSelected,
          data: {
            waypoints: conn.waypoints || [],
            connectionId: conn.id,
            signalName: conn.signalName,
            labelOffset: conn.labelOffset,
            isBranchTarget, // Pass to CustomEdge for additional visual feedback
            isHighlighted, // Pass for signal tracing highlighting
            onDragStateChange: setIsEdgeDragging, // Callback to track edge drag state
          },
          style: edgeStyle,
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

    console.log('[Editor] Setting nodes:', newNodes.length, 'edges:', validEdges.length)
    setNodes(newNodes)
    setEdges(validEdges)
  }, [model, currentBlocks, currentConnections, selectedEdgeId, selectedBlockIds, nearestEdgeForBranch, highlightedConnections, setNodes, setEdges])

  // Sync React Flow state back to model store
  const onNodeDragStart = useCallback(
    () => {
      // Push history when drag starts so we can undo the move
      pushHistory()
    },
    [pushHistory]
  )

  const onNodeDragStop = useCallback(
    (_: React.MouseEvent, node: Node) => {
      updateBlockPosition(node.id, node.position)
    },
    [updateBlockPosition]
  )

  const onConnect: OnConnect = useCallback(
    (params: Connection) => {
      if (params.source && params.target && params.sourceHandle && params.targetHandle) {
        // Push history before adding connection
        pushHistory()

        // Calculate smart waypoints to avoid intersecting blocks
        const sourceBlock = currentBlocks.find(b => b.id === params.source)
        const targetBlock = currentBlocks.find(b => b.id === params.target)

        let waypoints: Array<{ x: number; y: number }> | undefined

        if (sourceBlock && targetBlock) {
          // Get source port position (right side of block)
          const sourcePort = sourceBlock.outputPorts.find(p => p.id === params.sourceHandle)
          const sourcePortIndex = sourcePort ? sourceBlock.outputPorts.indexOf(sourcePort) : 0
          const sourcePortCount = sourceBlock.outputPorts.length
          const sourceX = sourceBlock.position.x + (sourceBlock.size?.width || 100)
          const sourceY = sourceBlock.position.y + ((sourcePortIndex + 1) / (sourcePortCount + 1)) * (sourceBlock.size?.height || 50)

          // Get target port position (left side of block)
          const targetPort = targetBlock.inputPorts.find(p => p.id === params.targetHandle)
          const targetPortIndex = targetPort ? targetBlock.inputPorts.indexOf(targetPort) : 0
          const targetPortCount = targetBlock.inputPorts.length
          const targetX = targetBlock.position.x
          const targetY = targetBlock.position.y + ((targetPortIndex + 1) / (targetPortCount + 1)) * (targetBlock.size?.height || 50)

          // Generate smart waypoints that avoid other blocks
          const smartWaypoints = generateSmartWaypoints(
            sourceX, sourceY,
            targetX, targetY,
            params.source, params.target,
            currentBlocks,
            currentConnections
          )

          if (smartWaypoints.length > 0) {
            waypoints = smartWaypoints
          }
        }

        // Add connection to model - the useEffect will sync edges automatically
        addConnection({
          sourceBlockId: params.source,
          sourcePortId: params.sourceHandle,
          targetBlockId: params.target,
          targetPortId: params.targetHandle,
          waypoints,
        })
      }
    },
    [addConnection, pushHistory, currentBlocks, currentConnections]
  )

  // Track connection start info for branching detection
  const connectStartRef = useRef<{
    nodeId: string | null
    handleId: string | null
    handleType: 'source' | 'target' | null
  }>({ nodeId: null, handleId: null, handleType: null })

  // Handle connection start - track where connection started from
  const onConnectStart: OnConnectStart = useCallback(
    (_, { nodeId, handleId, handleType }) => {
      connectStartRef.current = { nodeId, handleId, handleType }
      setIsDraggingFromInput(handleType === 'target')
      console.log('[Editor] onConnectStart:', { nodeId, handleId, handleType })
    },
    []
  )

  // Handle connection end for:
  // 1. Branching - dragging from input port to existing line
  // 2. Auto-expanding Scope inputs
  const onConnectEnd: OnConnectEnd = useCallback(
    (event, connectionState) => {
      // Reset visual feedback state
      setIsDraggingFromInput(false)
      setNearestEdgeForBranch(null)

      const fromNodeId = connectionState.fromNode?.id
      const fromHandleId = connectionState.fromHandle?.id
      if (!fromNodeId || !fromHandleId) return

      const mouseEvent = event as MouseEvent
      const dropPosition = screenToFlowPosition({
        x: mouseEvent.clientX,
        y: mouseEvent.clientY,
      })

      // Check if we're dragging FROM an input port (target handle)
      // This is the Simulink behavior for creating branches
      const startInfo = connectStartRef.current
      const isDraggingFromInput = startInfo.handleType === 'target'

      // Case: Branching - dragging from input port to existing line
      if (isDraggingFromInput && !connectionState.isValid) {
        console.log('[Editor] Checking for branch - dragging from input port')

        // Find if dropped near an existing edge
        const nearestEdge = findNearestEdge(dropPosition, currentConnections, currentBlocks, 30)

        if (nearestEdge) {
          console.log('[Editor] Found nearby edge for branching:', nearestEdge.connection.id, 'distance:', nearestEdge.distance)

          // Create a branch: connect the edge's source to this input port
          pushHistory()
          addConnection({
            sourceBlockId: nearestEdge.connection.sourceBlockId,
            sourcePortId: nearestEdge.connection.sourcePortId,
            targetBlockId: fromNodeId,
            targetPortId: fromHandleId,
          })
          return
        }
      }

      // Case 1: Invalid connection - check if dropped on Scope body
      if (!connectionState.isValid) {
        const target = (event as MouseEvent).target as HTMLElement
        if (!target) return

        const nodeElement = target.closest('.react-flow__node')
        if (!nodeElement) return

        const nodeId = nodeElement.getAttribute('data-id')
        if (!nodeId) return

        const targetBlock = currentBlocks.find(b => b.id === nodeId)
        if (!targetBlock || targetBlock.type !== 'scope') return

        // Auto-expand the Scope and connect to the new port
        const newPortId = addScopeInput(nodeId)
        if (newPortId) {
          setTimeout(() => {
            addConnection({
              sourceBlockId: fromNodeId,
              sourcePortId: fromHandleId,
              targetBlockId: nodeId,
              targetPortId: newPortId,
            })
          }, 0)
        }
        return
      }

      // Case 2: Valid connection to a Scope - check if port was already connected BEFORE this connection
      // We need to check this BEFORE onConnect added the new connection, so we use a microtask
      // to let onConnect finish, then check if there are now 2+ connections to the same port
      const toNodeId = connectionState.toNode?.id
      const toHandleId = connectionState.toHandle?.id
      if (!toNodeId || !toHandleId) return

      const targetBlock = currentBlocks.find(b => b.id === toNodeId)
      if (!targetBlock || targetBlock.type !== 'scope') return

      // Use setTimeout to run after onConnect has completed
      setTimeout(() => {
        const freshConnections = getCurrentConnections()

        // Since addConnection prevents duplicate target ports,
        // if the port was already connected, our connection was rejected.
        // So we need to check if our connection exists - if not, auto-expand
        const ourConnection = freshConnections.find(
          c => c.sourceBlockId === fromNodeId &&
               c.sourcePortId === fromHandleId &&
               c.targetBlockId === toNodeId &&
               c.targetPortId === toHandleId
        )

        if (!ourConnection) {
          // Our connection was rejected (port already connected) - auto-expand
          const newPortId = addScopeInput(toNodeId)
          if (newPortId) {
            addConnection({
              sourceBlockId: fromNodeId,
              sourcePortId: fromHandleId,
              targetBlockId: toNodeId,
              targetPortId: newPortId,
            })
          }
        }
      }, 10) // Small delay to ensure onConnect has completed
    },
    [currentBlocks, currentConnections, addScopeInput, addConnection, getCurrentConnections, screenToFlowPosition, pushHistory]
  )

  const onNodesDelete = useCallback(
    (deleted: Node[]) => {
      console.log('[Editor] onNodesDelete triggered, nodes:', deleted.map(n => n.id))
      deleted.forEach((node) => removeBlock(node.id))
    },
    [removeBlock]
  )

  const onEdgesDelete = useCallback(
    (deleted: Edge[]) => {
      console.log('[Editor] onEdgesDelete triggered, edges:', deleted.map(e => e.id))
      console.trace('[Editor] onEdgesDelete stack trace')
      deleted.forEach((edge) => removeConnection(edge.id))
    },
    [removeConnection]
  )

  // Track when edge segment/waypoint is being dragged
  const [isEdgeDragging, setIsEdgeDragging] = useState(false)

  // Track click timing to detect double-clicks in onEdgeClick
  const lastEdgeClickRef = useRef<{ edgeId: string; time: number } | null>(null)

  // Handle edge click to show signal dimensions
  const onEdgeClick = useCallback(
    (_: React.MouseEvent, edge: Edge) => {
      const now = Date.now()
      const lastClick = lastEdgeClickRef.current

      // If this is a rapid click on the same edge (within 500ms), ignore it
      // This handles double-clicks, triple-clicks, and rapid clicking
      if (lastClick && lastClick.edgeId === edge.id && (now - lastClick.time) < 500) {
        console.log('[Editor] onEdgeClick - ignoring rapid click on same edge')
        // Update timestamp but don't change selection
        lastEdgeClickRef.current = { edgeId: edge.id, time: now }
        return
      }

      lastEdgeClickRef.current = { edgeId: edge.id, time: now }

      // Select the edge (don't toggle - clicking a selected edge keeps it selected)
      // To deselect, click elsewhere on the canvas
      setSelectedEdgeId(edge.id)
    },
    [setSelectedEdgeId]
  )

  // Track double-click timing to ignore pane clicks that follow edge double-clicks
  const lastEdgeDoubleClickRef = useRef<number>(0)

  // Handle edge double-click - prevent default behavior (which can cause deletion)
  const onEdgeDoubleClick = useCallback(
    (event: React.MouseEvent, _edge: Edge) => {
      // Prevent any default ReactFlow behavior on double-click
      event.stopPropagation()
      event.preventDefault()
      // Record timestamp so paneClick can ignore events too close to this
      lastEdgeDoubleClickRef.current = Date.now()
      console.log('[Editor] onEdgeDoubleClick - prevented default behavior')
    },
    []
  )

  // Deselect edge when clicking on the pane (but not during segment/waypoint drag or after edge click)
  const onPaneClick = useCallback(() => {
    // Don't deselect if we're dragging an edge segment or waypoint
    if (isEdgeDragging) {
      console.log('[Editor] onPaneClick - ignoring, edge drag in progress')
      return
    }
    // Don't deselect if this click is immediately after any edge click/double-click
    // (clicks can propagate through in some edge cases)
    const timeSinceDoubleClick = Date.now() - lastEdgeDoubleClickRef.current
    const timeSinceEdgeClick = lastEdgeClickRef.current ? Date.now() - lastEdgeClickRef.current.time : Infinity
    if (timeSinceDoubleClick < 500 || timeSinceEdgeClick < 500) {
      console.log('[Editor] onPaneClick - ignoring, too close to edge interaction')
      return
    }
    console.log('[Editor] onPaneClick - deselecting edge')
    setSelectedEdgeId(null)
  }, [isEdgeDragging, setSelectedEdgeId])

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

      // Push history before adding block
      pushHistory()
      // Add block to model - the useEffect will sync nodes automatically
      addBlock(definition, position)
      setDraggingBlockType(null)
    },
    [draggingBlockType, screenToFlowPosition, addBlock, setDraggingBlockType, pushHistory]
  )

  const nodeTypes: NodeTypes = useMemo(
    () => ({
      blockNode: BlockNode,
      subsystemNode: SubsystemNode,
    }),
    []
  )

  const edgeTypes: EdgeTypes = useMemo(
    () => ({
      custom: CustomEdge,
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
    setSignalContextMenu(null)
  }, [])

  // Signal context menu handlers
  const handleSignalContextMenu = useCallback(
    (event: React.MouseEvent, edge: Edge) => {
      event.preventDefault()
      event.stopPropagation()
      const connectionId = (edge.data as { connectionId?: string })?.connectionId || edge.id
      setSignalContextMenu({
        x: event.clientX,
        y: event.clientY,
        edgeId: edge.id,
        connectionId,
      })
      setContextMenu(null) // Close block context menu if open
    },
    []
  )

  const handleDeleteSignal = useCallback(() => {
    if (signalContextMenu) {
      pushHistory()
      removeConnection(signalContextMenu.connectionId)
      setSignalContextMenu(null)
      setSelectedEdgeId(null)
    }
  }, [signalContextMenu, removeConnection, pushHistory, setSelectedEdgeId])

  const handleDeleteSignalLabel = useCallback(() => {
    if (signalContextMenu) {
      pushHistory()
      useModelStore.getState().updateConnectionSignalName(signalContextMenu.connectionId, undefined)
      setSignalContextMenu(null)
    }
  }, [signalContextMenu, pushHistory])

  const handleAutoRouteSignal = useCallback(() => {
    if (signalContextMenu) {
      // Find the connection
      const conn = currentConnections.find(c => c.id === signalContextMenu.connectionId)
      if (!conn) {
        setSignalContextMenu(null)
        return
      }

      // Find source and target blocks
      const sourceBlock = currentBlocks.find(b => b.id === conn.sourceBlockId)
      const targetBlock = currentBlocks.find(b => b.id === conn.targetBlockId)

      if (!sourceBlock || !targetBlock) {
        setSignalContextMenu(null)
        return
      }

      // Calculate source port position
      const sourcePort = sourceBlock.outputPorts.find(p => p.id === conn.sourcePortId)
      const sourcePortIndex = sourcePort ? sourceBlock.outputPorts.indexOf(sourcePort) : 0
      const sourcePortCount = sourceBlock.outputPorts.length
      const sourceX = sourceBlock.position.x + (sourceBlock.size?.width || 100)
      const sourceY = sourceBlock.position.y + ((sourcePortIndex + 1) / (sourcePortCount + 1)) * (sourceBlock.size?.height || 50)

      // Calculate target port position
      const targetPort = targetBlock.inputPorts.find(p => p.id === conn.targetPortId)
      const targetPortIndex = targetPort ? targetBlock.inputPorts.indexOf(targetPort) : 0
      const targetPortCount = targetBlock.inputPorts.length
      const targetX = targetBlock.position.x
      const targetY = targetBlock.position.y + ((targetPortIndex + 1) / (targetPortCount + 1)) * (targetBlock.size?.height || 50)

      // Generate smart waypoints (excluding this connection from overlap check)
      const otherConnections = currentConnections.filter(c => c.id !== conn.id)
      const smartWaypoints = generateSmartWaypoints(
        sourceX, sourceY,
        targetX, targetY,
        conn.sourceBlockId, conn.targetBlockId,
        currentBlocks,
        otherConnections
      )

      pushHistory()

      // Update the connection with smart waypoints
      if (smartWaypoints.length > 0) {
        // Set the new waypoints
        useModelStore.getState().updateConnectionWaypoints(signalContextMenu.connectionId, smartWaypoints)
      } else {
        // No waypoints needed - clear existing ones
        useModelStore.getState().clearConnectionWaypoints(signalContextMenu.connectionId)
      }

      setSignalContextMenu(null)
    }
  }, [signalContextMenu, pushHistory, currentBlocks, currentConnections])

  const handleRenameSignal = useCallback(() => {
    if (signalContextMenu) {
      setRenamingSignal({
        connectionId: signalContextMenu.connectionId,
        x: signalContextMenu.x,
        y: signalContextMenu.y,
      })
      setSignalContextMenu(null)
    }
  }, [signalContextMenu])

  const handleSaveSignalName = useCallback((newName: string) => {
    if (renamingSignal) {
      const trimmedName = newName.trim()
      pushHistory()
      useModelStore.getState().updateConnectionSignalName(renamingSignal.connectionId, trimmedName || undefined)
      setRenamingSignal(null)
    }
  }, [renamingSignal, pushHistory])

  // Focus input when renaming starts
  useEffect(() => {
    if (renamingSignal && signalNameInputRef.current) {
      signalNameInputRef.current.focus()
      signalNameInputRef.current.select()
    }
  }, [renamingSignal])

  const handleHighlightToSource = useCallback(() => {
    if (!signalContextMenu) return
    const conn = currentConnections.find(c => c.id === signalContextMenu.connectionId)
    if (!conn) return

    setHighlightedConnections(getSourceBranchConnectionIds(conn, currentConnections))
    setSignalContextMenu(null)
  }, [signalContextMenu, currentConnections])

  const handleHighlightToDestination = useCallback(() => {
    if (!signalContextMenu) return
    const conn = currentConnections.find(c => c.id === signalContextMenu.connectionId)
    if (!conn) return

    setHighlightedConnections(getDownstreamConnectionIds(conn, currentConnections))
    setSignalContextMenu(null)
  }, [signalContextMenu, currentConnections])

  const handleRemoveHighlighting = useCallback(() => {
    setHighlightedConnections(new Set())
    setSignalContextMenu(null)
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
        // Check if this is a scope block (any type that displays plots)
        const block = currentBlocks.find(b => b.id === node.id)
        if (block?.type === 'scope' || block?.type === 'scope_3d' || block?.type === 'xy_graph') {
          openPlotWindow(block.id)
        }
      }
    },
    [enterSubsystem, currentBlocks, openPlotWindow]
  )

  // Handle keyboard navigation (Escape to exit subsystem, Space to fit view)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't handle keyboard events when input fields are focused
      if (inputFocused || getIsPropertiesFocused()) return

      if (e.key === 'Escape' && currentPath.length > 0) {
        exitSubsystem()
      }

      // Space bar - fit view to show all elements
      if (e.key === ' ' || e.code === 'Space') {
        e.preventDefault()
        fitView({ padding: 0.2, duration: 300 })
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentPath, exitSubsystem, fitView, inputFocused])

  // Track nearest edge during branching drag for visual feedback
  useEffect(() => {
    if (!isDraggingFromInput) {
      setNearestEdgeForBranch(null)
      return
    }

    const handleMouseMove = (e: MouseEvent) => {
      const position = screenToFlowPosition({ x: e.clientX, y: e.clientY })
      const nearest = findNearestEdge(position, currentConnections, currentBlocks, 30)
      setNearestEdgeForBranch(nearest?.connection.id || null)
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [isDraggingFromInput, currentConnections, currentBlocks, screenToFlowPosition])

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
        onConnectStart={onConnectStart}
        onConnectEnd={onConnectEnd}
        onNodeDragStart={onNodeDragStart}
        onNodeDragStop={onNodeDragStop}
        onNodesDelete={onNodesDelete}
        onEdgesDelete={onEdgesDelete}
        onEdgeClick={onEdgeClick}
        onEdgeDoubleClick={onEdgeDoubleClick}
        onEdgeContextMenu={handleSignalContextMenu}
        onPaneClick={onPaneClick}
        onSelectionChange={onSelectionChange}
        onNodeDoubleClick={onNodeDoubleClick}
        onDragOver={onDragOver}
        onDrop={onDrop}
        onContextMenu={handleContextMenu}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
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
            const def = node.data?.definition as { category?: string } | undefined
            if (!def || !def.category) return '#6c7086'
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

      {/* Signal Context Menu (right-click on edge) */}
      {signalContextMenu && (
        <div
          className="absolute z-50 bg-slate-800 border border-slate-600 rounded-lg shadow-xl py-1 min-w-[200px]"
          style={{ left: signalContextMenu.x, top: signalContextMenu.y }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Rename Signal */}
          <button
            className="w-full px-4 py-2 text-left text-sm text-white hover:bg-slate-700 flex items-center gap-2"
            onClick={handleRenameSignal}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            <span>Rename Signal</span>
          </button>

          {/* Delete Signal */}
          <button
            className="w-full px-4 py-2 text-left text-sm text-white hover:bg-slate-700 flex items-center gap-2"
            onClick={handleDeleteSignal}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            <span>Delete</span>
            <span className="ml-auto text-slate-400 text-xs">Del</span>
          </button>

          {/* Delete Label - only show if signal has a name */}
          {(() => {
            const conn = currentConnections.find(c => c.id === signalContextMenu.connectionId)
            return conn?.signalName ? (
              <button
                className="w-full px-4 py-2 text-left text-sm text-white hover:bg-slate-700 flex items-center gap-2"
                onClick={handleDeleteSignalLabel}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                <span>Delete Label</span>
              </button>
            ) : null
          })()}

          <div className="border-t border-slate-600 my-1" />

          {/* Highlight to Source */}
          <button
            className="w-full px-4 py-2 text-left text-sm text-white hover:bg-slate-700 flex items-center gap-2"
            onClick={handleHighlightToSource}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
            <span>Highlight to Source</span>
            <span className="ml-auto text-slate-400 text-xs">Ctrl+Shift+S</span>
          </button>

          {/* Highlight to Destination */}
          <button
            className="w-full px-4 py-2 text-left text-sm text-white hover:bg-slate-700 flex items-center gap-2"
            onClick={handleHighlightToDestination}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
            </svg>
            <span>Highlight to Destination</span>
            <span className="ml-auto text-slate-400 text-xs">Ctrl+Shift+D</span>
          </button>

          {/* Remove Highlighting - only show if there are highlighted connections */}
          {highlightedConnections.size > 0 && (
            <button
              className="w-full px-4 py-2 text-left text-sm text-white hover:bg-slate-700 flex items-center gap-2"
              onClick={handleRemoveHighlighting}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              <span>Remove Highlighting</span>
              <span className="ml-auto text-slate-400 text-xs">Ctrl+Shift+H</span>
            </button>
          )}

          <div className="border-t border-slate-600 my-1" />

          {/* Auto-route Line */}
          <button
            className="w-full px-4 py-2 text-left text-sm text-white hover:bg-slate-700 flex items-center gap-2"
            onClick={handleAutoRouteSignal}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Auto-route Line</span>
          </button>
        </div>
      )}

      {/* Signal Rename Input (inline text editor) */}
      {renamingSignal && (
        <div
          className="absolute z-50"
          style={{ left: renamingSignal.x, top: renamingSignal.y }}
          onClick={(e) => e.stopPropagation()}
        >
          <input
            ref={signalNameInputRef}
            type="text"
            defaultValue={currentConnections.find(c => c.id === renamingSignal.connectionId)?.signalName || ''}
            onKeyDown={(e) => {
              e.stopPropagation()
              if (e.key === 'Enter') {
                handleSaveSignalName(e.currentTarget.value)
              } else if (e.key === 'Escape') {
                setRenamingSignal(null)
              }
            }}
            onBlur={(e) => handleSaveSignalName(e.currentTarget.value)}
            className="px-2 py-1 text-sm border border-blue-500 rounded bg-slate-800 text-white outline-none min-w-[120px]"
            placeholder="Signal name"
          />
        </div>
      )}
    </div>
  )
}
