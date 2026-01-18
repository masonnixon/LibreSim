import React, { memo, useCallback, useMemo, useState, useRef } from 'react'
import { BaseEdge, EdgeLabelRenderer, EdgeProps, useReactFlow } from '@xyflow/react'
import { useModelStore } from '../../store/modelStore'

interface WaypointData {
  waypoints?: Array<{ x: number; y: number }>
  connectionId?: string
  label?: string
  signalName?: string
  labelOffset?: { x: number; y: number }
  isBranchTarget?: boolean
  isHighlighted?: boolean
  onDragStateChange?: (isDragging: boolean) => void
}

// Segment represents a horizontal or vertical line segment
interface Segment {
  type: 'h' | 'v' // horizontal or vertical
  x1: number
  y1: number
  x2: number
  y2: number
  // For dragging: which waypoint's coordinate this segment controls
  // -1 means drag will CREATE a new waypoint
  // null means segment is NOT draggable (e.g., output port segment)
  controlsWaypointIndex: number | null
  // Which coordinate of the waypoint this segment controls when dragged
  controlsCoordinate: 'x' | 'y'
  // For segments that create waypoints: where to insert the new waypoint
  insertWaypointAt?: number
}

/**
 * Generate an orthogonal (Manhattan-style) path through waypoints.
 * Follows Simulink behavior:
 * - Output port segment (first segment) is NOT draggable
 * - Input port segment and internal segments ARE draggable
 *
 * With 0 waypoints, the path is:
 *   source(sX, sY) → (midX, sY) → (midX, tY) → target(tX, tY)
 *   - Seg 0: H from source - NOT draggable (output port segment)
 *   - Seg 1: V at midX - draggable (creates wp at index 0, controls X)
 *   - Seg 2: H to target - draggable (creates wp at index 0, controls Y)
 *
 * With 1+ waypoints:
 *   - Seg 0: H from source - NOT draggable (output port segment)
 *   - Internal segments - draggable (control waypoints)
 *   - Last segment to target - draggable (input port side)
 */
function generateOrthogonalPath(
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
  waypoints: Array<{ x: number; y: number }>
): { path: string; segments: Segment[]; labelX: number; labelY: number } {
  const segments: Segment[] = []
  // Collect all path points for center calculation
  const pathPoints: Array<{ x: number; y: number }> = []

  if (waypoints.length === 0) {
    // No waypoints - create simple 3-segment orthogonal route
    // Path: source → (midX, sourceY) → (midX, targetY) → target
    const midX = (sourceX + targetX) / 2

    const path = `M ${sourceX},${sourceY} L ${midX},${sourceY} L ${midX},${targetY} L ${targetX},${targetY}`

    // Segment 0: horizontal from source to midX - NOT draggable (output port segment per Simulink)
    segments.push({
      type: 'h', x1: sourceX, y1: sourceY, x2: midX, y2: sourceY,
      controlsWaypointIndex: null, controlsCoordinate: 'y'
    })
    // Segment 1: vertical at midX - draggable (creates waypoint, controls X)
    segments.push({
      type: 'v', x1: midX, y1: sourceY, x2: midX, y2: targetY,
      controlsWaypointIndex: -1, controlsCoordinate: 'x', insertWaypointAt: 0
    })
    // Segment 2: horizontal from midX to target - draggable (creates waypoint, controls Y)
    segments.push({
      type: 'h', x1: midX, y1: targetY, x2: targetX, y2: targetY,
      controlsWaypointIndex: -1, controlsCoordinate: 'y', insertWaypointAt: 0
    })

    // Calculate center of path (center of vertical segment since it's typically the longest/middle)
    const labelX = midX
    const labelY = (sourceY + targetY) / 2
    return { path, segments, labelX, labelY }
  }

  // With waypoints, build a path that goes through each waypoint
  // For each waypoint, we go: horizontal to wp.x, then vertical to wp.y
  // After all waypoints: horizontal to target.x, then vertical to target.y

  let path = `M ${sourceX},${sourceY}`
  let prevX = sourceX
  let prevY = sourceY
  pathPoints.push({ x: sourceX, y: sourceY })

  for (let i = 0; i < waypoints.length; i++) {
    const wp = waypoints[i]

    // Horizontal segment: from prevX to wp.x at prevY
    path += ` L ${wp.x},${prevY}`
    pathPoints.push({ x: wp.x, y: prevY })
    segments.push({
      type: 'h',
      x1: prevX, y1: prevY, x2: wp.x, y2: prevY,
      // First horizontal segment is NOT draggable (output port segment per Simulink)
      // Others control the previous waypoint's Y
      controlsWaypointIndex: i === 0 ? null : i - 1,
      controlsCoordinate: 'y',
    })
    prevX = wp.x

    // Vertical segment: from prevY to wp.y at wp.x
    path += ` L ${wp.x},${wp.y}`
    pathPoints.push({ x: wp.x, y: wp.y })
    segments.push({
      type: 'v',
      x1: wp.x, y1: prevY, x2: wp.x, y2: wp.y,
      // This controls this waypoint's X
      controlsWaypointIndex: i,
      controlsCoordinate: 'x'
    })
    prevY = wp.y
  }

  const lastWpIndex = waypoints.length - 1

  // Final horizontal segment: from last waypoint X to target X, at last waypoint's Y
  path += ` L ${targetX},${prevY}`
  pathPoints.push({ x: targetX, y: prevY })
  segments.push({
    type: 'h',
    x1: prevX, y1: prevY, x2: targetX, y2: prevY,
    // This controls the last waypoint's Y
    controlsWaypointIndex: lastWpIndex,
    controlsCoordinate: 'y'
  })
  prevX = targetX

  // Final vertical segment: from last waypoint Y to target Y, at target X
  path += ` L ${targetX},${targetY}`
  pathPoints.push({ x: targetX, y: targetY })
  segments.push({
    type: 'v',
    x1: targetX, y1: prevY, x2: targetX, y2: targetY,
    // Creates a new waypoint at the end when dragged
    controlsWaypointIndex: -1,
    controlsCoordinate: 'x',
    insertWaypointAt: waypoints.length
  })

  // Calculate center of path by finding the point at half the total path length
  const { labelX, labelY } = calculatePathCenter(pathPoints)

  return { path, segments, labelX, labelY }
}

/**
 * Calculate the center point along a path (at half the total path length)
 */
function calculatePathCenter(points: Array<{ x: number; y: number }>): { labelX: number; labelY: number } {
  if (points.length < 2) {
    return { labelX: points[0]?.x || 0, labelY: points[0]?.y || 0 }
  }

  // Calculate total path length
  let totalLength = 0
  const segmentLengths: number[] = []
  for (let i = 1; i < points.length; i++) {
    const dx = points[i].x - points[i - 1].x
    const dy = points[i].y - points[i - 1].y
    const len = Math.abs(dx) + Math.abs(dy) // Manhattan distance for orthogonal paths
    segmentLengths.push(len)
    totalLength += len
  }

  // Find the point at half the total length
  const halfLength = totalLength / 2
  let accumulatedLength = 0

  for (let i = 0; i < segmentLengths.length; i++) {
    const segLen = segmentLengths[i]
    if (accumulatedLength + segLen >= halfLength) {
      // The center is on this segment
      const remaining = halfLength - accumulatedLength
      const ratio = segLen > 0 ? remaining / segLen : 0
      const p1 = points[i]
      const p2 = points[i + 1]
      return {
        labelX: p1.x + (p2.x - p1.x) * ratio,
        labelY: p1.y + (p2.y - p1.y) * ratio
      }
    }
    accumulatedLength += segLen
  }

  // Fallback: return midpoint of last segment
  const last = points[points.length - 1]
  const secondLast = points[points.length - 2]
  return {
    labelX: (last.x + secondLast.x) / 2,
    labelY: (last.y + secondLast.y) / 2
  }
}


// Snap position to grid - normal grid is 10px, fine grid (Alt key) is 1px
function snapToGrid(position: { x: number; y: number }, useFineGrid: boolean): { x: number; y: number } {
  const gridSize = useFineGrid ? 1 : 10
  return {
    x: Math.round(position.x / gridSize) * gridSize,
    y: Math.round(position.y / gridSize) * gridSize,
  }
}

// Draggable waypoint handle component (the bend point circles)
// Per Simulink behavior: drag to move, NO double-click to delete
function WaypointHandle({
  x,
  y,
  index,
  connectionId,
  onDragStart,
  onDragEnd,
}: {
  x: number
  y: number
  index: number
  connectionId: string
  onDragStart: () => void
  onDragEnd: () => void
}) {
  const updateConnectionWaypoint = useModelStore((state) => state.updateConnectionWaypoint)
  const pushHistory = useModelStore((state) => state.pushHistory)
  const { screenToFlowPosition } = useReactFlow()
  const [isDragging, setIsDragging] = useState(false)

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation()
      e.preventDefault()

      const startX = e.clientX
      const startY = e.clientY
      let hasMoved = false

      const handleMouseMove = (moveEvent: MouseEvent) => {
        // Only start actual drag after mouse has moved a bit
        const dx = moveEvent.clientX - startX
        const dy = moveEvent.clientY - startY
        if (!hasMoved && Math.abs(dx) < 3 && Math.abs(dy) < 3) {
          return
        }

        if (!hasMoved) {
          hasMoved = true
          setIsDragging(true)
          onDragStart()
          // Push history only when actually starting to drag
          pushHistory()
        }

        const rawPosition = screenToFlowPosition({
          x: moveEvent.clientX,
          y: moveEvent.clientY,
        })
        // Alt key = fine grid (1px), otherwise normal grid (10px)
        const position = snapToGrid(rawPosition, moveEvent.altKey)
        updateConnectionWaypoint(connectionId, index, position)
      }

      const handleMouseUp = () => {
        if (hasMoved) {
          setIsDragging(false)
          onDragEnd()
        }
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }

      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    },
    [connectionId, index, screenToFlowPosition, updateConnectionWaypoint, pushHistory, onDragStart, onDragEnd]
  )

  return (
    <circle
      cx={x}
      cy={y}
      r={6}
      fill={isDragging ? '#60a5fa' : '#3b82f6'}
      stroke="#1e3a8a"
      strokeWidth={2}
      style={{ cursor: 'grab', pointerEvents: 'all' }}
      onMouseDown={handleMouseDown}
      onDoubleClick={(e) => {
        // Prevent double-click from propagating
        e.stopPropagation()
        e.preventDefault()
      }}
    >
      <title>Drag to move waypoint</title>
    </circle>
  )
}

// Draggable segment component (for dragging horizontal/vertical line segments)
function DraggableSegment({
  segment,
  connectionId,
  waypoints,
  onDragStart,
  onDragEnd,
}: {
  segment: Segment
  connectionId: string
  waypoints: Array<{ x: number; y: number }>
  onDragStart: () => void
  onDragEnd: () => void
}) {
  const updateConnectionWaypoint = useModelStore((state) => state.updateConnectionWaypoint)
  const addConnectionWaypoint = useModelStore((state) => state.addConnectionWaypoint)
  const pushHistory = useModelStore((state) => state.pushHistory)
  const { screenToFlowPosition } = useReactFlow()
  const [isDragging, setIsDragging] = useState(false)
  const waypointCreatedRef = useRef(false)
  // Track last mousedown time to detect double-clicks
  const lastMouseDownRef = useRef(0)

  // Use refs to access current waypoints in mouse handlers (avoids stale closure)
  const waypointsRef = useRef(waypoints)
  waypointsRef.current = waypoints

  const segmentRef = useRef(segment)
  segmentRef.current = segment

  // Calculate segment length
  const length = segment.type === 'h'
    ? Math.abs(segment.x2 - segment.x1)
    : Math.abs(segment.y2 - segment.y1)

  // Segments are draggable if:
  // 1. controlsWaypointIndex is not null (null means output port segment, not draggable per Simulink)
  // 2. Segment is long enough to interact with
  const isDraggable = segment.controlsWaypointIndex !== null && length >= 10

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation()
      e.preventDefault()
      e.nativeEvent.stopImmediatePropagation()

      // Check if this is part of a double-click using the event's detail property
      // detail === 1 for single click, detail === 2 for double-click
      if (e.detail >= 2) {
        console.log('[DraggableSegment] Ignoring mouseDown - part of double-click (detail=' + e.detail + ')')
        return
      }

      // Also check timing as a backup (in case component just mounted)
      const now = Date.now()
      const timeSinceLastMouseDown = now - lastMouseDownRef.current
      lastMouseDownRef.current = now

      if (timeSinceLastMouseDown < 300) {
        console.log('[DraggableSegment] Ignoring mouseDown - too fast (likely double-click)')
        return
      }

      setIsDragging(true)
      onDragStart()
      waypointCreatedRef.current = false

      // Push history once at start of drag
      pushHistory()

      console.log('[DraggableSegment] mouseDown segment:', segment.type,
        'controls waypoint', segment.controlsWaypointIndex, 'coord', segment.controlsCoordinate,
        'waypoints:', waypoints.length)

      const handleMouseMove = (moveEvent: MouseEvent) => {
        const rawPos = screenToFlowPosition({
          x: moveEvent.clientX,
          y: moveEvent.clientY,
        })
        // Alt key = fine grid (1px), otherwise normal grid (10px)
        const currentPos = snapToGrid(rawPos, moveEvent.altKey)

        const currentWaypoints = waypointsRef.current
        const currentSegment = segmentRef.current
        const wpIndex = currentSegment.controlsWaypointIndex
        const coord = currentSegment.controlsCoordinate
        const insertAt = currentSegment.insertWaypointAt

        // Skip if segment is not draggable (null means output port segment)
        if (wpIndex === null) return

        // If this segment needs to create a waypoint (wpIndex === -1 with insertWaypointAt defined)
        if (wpIndex === -1 && insertAt !== undefined && !waypointCreatedRef.current) {
          // Create a new waypoint at the appropriate position
          // For horizontal segments (controls Y): create at (current segment's X midpoint, mouse Y)
          // For vertical segments (controls X): create at (mouse X, current segment's Y midpoint)
          let newWp: { x: number; y: number }
          if (coord === 'y') {
            // Horizontal segment - create waypoint with X at segment midpoint, Y at mouse position
            const midX = (currentSegment.x1 + currentSegment.x2) / 2
            newWp = { x: snapToGrid({ x: midX, y: 0 }, moveEvent.altKey).x, y: currentPos.y }
          } else {
            // Vertical segment - create waypoint with X at mouse position, Y at segment midpoint
            const midY = (currentSegment.y1 + currentSegment.y2) / 2
            newWp = { x: currentPos.x, y: snapToGrid({ x: 0, y: midY }, moveEvent.altKey).y }
          }
          addConnectionWaypoint(connectionId, newWp, insertAt)
          waypointCreatedRef.current = true
          console.log('[DraggableSegment] Created waypoint at index', insertAt, 'position:', newWp)
          return
        }

        // If waypoint was just created, now update it
        // The insertAt index tells us where the waypoint was inserted
        const actualWpIndex = waypointCreatedRef.current && insertAt !== undefined ? insertAt : wpIndex as number

        // Skip if we don't have a valid waypoint to control
        if (actualWpIndex < 0 || actualWpIndex >= currentWaypoints.length) {
          console.log('[DraggableSegment] Skipping - invalid wpIndex', actualWpIndex, 'waypoints:', currentWaypoints.length)
          return
        }

        const wp = currentWaypoints[actualWpIndex]

        if (coord === 'x') {
          // Dragging vertical segment left/right - set waypoint's X to mouse X
          console.log('[DraggableSegment] Moving vertical segment, setting X to', currentPos.x)
          updateConnectionWaypoint(connectionId, actualWpIndex, { x: currentPos.x, y: wp.y })
        } else if (coord === 'y') {
          // Dragging horizontal segment up/down - set waypoint's Y to mouse Y
          console.log('[DraggableSegment] Moving horizontal segment, setting Y to', currentPos.y)
          updateConnectionWaypoint(connectionId, actualWpIndex, { x: wp.x, y: currentPos.y })
        }
      }

      const handleMouseUp = () => {
        setIsDragging(false)
        onDragEnd()
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }

      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    },
    [connectionId, screenToFlowPosition, updateConnectionWaypoint, addConnectionWaypoint, pushHistory, onDragStart, onDragEnd, segment.type, segment.controlsCoordinate, segment.controlsWaypointIndex, waypoints.length]
  )

  // Don't render segments that cannot be dragged or are too small
  if (!isDraggable) return null

  // Render an invisible wider line for easier grabbing
  return (
    <line
      x1={segment.x1}
      y1={segment.y1}
      x2={segment.x2}
      y2={segment.y2}
      stroke={isDragging ? 'rgba(59, 130, 246, 0.3)' : 'transparent'}
      strokeWidth={12}
      style={{ cursor: segment.type === 'h' ? 'ns-resize' : 'ew-resize' }}
      onMouseDown={handleMouseDown}
      onDoubleClick={(e) => {
        // Prevent double-click from doing anything
        e.stopPropagation()
        e.preventDefault()
      }}
    >
      <title>Drag to move segment</title>
    </line>
  )
}

// Draggable label component for signal names
function DraggableLabel({
  connectionId,
  labelX,
  labelY,
  offset,
  signalName,
  onDragStart,
  onDragEnd,
}: {
  connectionId: string
  labelX: number
  labelY: number
  offset: { x: number; y: number }
  signalName: string
  onDragStart: () => void
  onDragEnd: () => void
}) {
  const updateConnectionLabelOffset = useModelStore((state) => state.updateConnectionLabelOffset)
  const pushHistory = useModelStore((state) => state.pushHistory)
  const { screenToFlowPosition } = useReactFlow()
  const [isDragging, setIsDragging] = useState(false)

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation()
      e.preventDefault()

      const startClientX = e.clientX
      const startClientY = e.clientY
      const startOffset = { ...offset }
      let hasMoved = false

      const handleMouseMove = (moveEvent: MouseEvent) => {
        const dx = moveEvent.clientX - startClientX
        const dy = moveEvent.clientY - startClientY

        if (!hasMoved && Math.abs(dx) < 3 && Math.abs(dy) < 3) {
          return
        }

        if (!hasMoved) {
          hasMoved = true
          setIsDragging(true)
          onDragStart()
          pushHistory()
        }

        // Convert screen delta to flow delta (accounts for zoom)
        const startFlowPos = screenToFlowPosition({ x: startClientX, y: startClientY })
        const currentFlowPos = screenToFlowPosition({ x: moveEvent.clientX, y: moveEvent.clientY })
        const flowDx = currentFlowPos.x - startFlowPos.x
        const flowDy = currentFlowPos.y - startFlowPos.y

        const newOffset = {
          x: startOffset.x + flowDx,
          y: startOffset.y + flowDy,
        }
        updateConnectionLabelOffset(connectionId, newOffset)
      }

      const handleMouseUp = () => {
        if (hasMoved) {
          setIsDragging(false)
          onDragEnd()
        }
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }

      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    },
    [connectionId, offset, screenToFlowPosition, updateConnectionLabelOffset, pushHistory, onDragStart, onDragEnd]
  )

  const finalX = labelX + offset.x
  const finalY = labelY + offset.y

  return (
    <div
      style={{
        position: 'absolute',
        transform: `translate(-50%, -100%) translate(${finalX}px,${finalY - 4}px)`,
        cursor: isDragging ? 'grabbing' : 'grab',
        padding: '2px 6px',
        borderRadius: 3,
        backgroundColor: isDragging ? '#2d2d3d' : '#1e1e2e',
        border: `1px solid ${isDragging ? '#89b4fa' : '#313244'}`,
        color: '#89b4fa',
        fontSize: '11px',
        fontWeight: 500,
        whiteSpace: 'nowrap',
        zIndex: 10,
        userSelect: 'none',
        pointerEvents: 'all', // Required for EdgeLabelRenderer children to be interactive
      }}
      className="nodrag nopan"
      onMouseDown={handleMouseDown}
    >
      {signalName}
    </div>
  )
}

function CustomEdgeComponent({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  data,
  selected,
  style,
  markerEnd,
  label,
  labelStyle,
  labelBgStyle,
  labelBgPadding,
  labelBgBorderRadius,
}: EdgeProps) {
  const [isWaypointDragging, setIsWaypointDragging] = useState(false)
  const [isLabelDragging, setIsLabelDragging] = useState(false)

  const waypointData = data as WaypointData | undefined
  const waypoints = useMemo(
    () => waypointData?.waypoints || [],
    [waypointData?.waypoints]
  )
  const connectionId = waypointData?.connectionId || id
  const signalName = waypointData?.signalName || ''
  const labelOffset = waypointData?.labelOffset || { x: 0, y: 0 }
  const isBranchTarget = waypointData?.isBranchTarget || false
  const isHighlighted = waypointData?.isHighlighted || false
  const onDragStateChange = waypointData?.onDragStateChange

  // Get padding values
  const padX = Array.isArray(labelBgPadding) ? labelBgPadding[0] : (labelBgPadding || 4)
  const padY = Array.isArray(labelBgPadding) ? labelBgPadding[1] : (labelBgPadding || 4)

  // Generate orthogonal path
  const { path: edgePath, segments, labelX, labelY } = useMemo(() => {
    return generateOrthogonalPath(sourceX, sourceY, targetX, targetY, waypoints)
  }, [sourceX, sourceY, targetX, targetY, waypoints])

  return (
    <g className="react-flow__edge-custom">
      {/* Invisible wider path for easier clicking/selection */}
      <path
        d={edgePath}
        fill="none"
        stroke="rgba(100,100,100,0.01)"
        strokeWidth={20}
        className="react-flow__edge-interaction"
        style={{
          cursor: 'pointer',
          pointerEvents: 'all',
        }}
        onDoubleClick={(e) => {
          // Stop propagation to prevent any default behavior
          e.stopPropagation()
          e.preventDefault()
        }}
      />
      {/* Visible edge path */}
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          ...style,
          // Priority: branch target (green) > highlighted (yellow) > selected (cyan) > default
          stroke: isBranchTarget ? '#22c55e' : isHighlighted ? '#eab308' : selected ? '#22d3ee' : '#94a3b8',
          strokeWidth: isBranchTarget ? 3 : isHighlighted ? 3 : selected ? 2.5 : 2,
          pointerEvents: 'none', // Let the invisible path handle events
        }}
        markerEnd={markerEnd}
      />
      {/* Draggable segments - only show when selected */}
      {selected && segments.map((seg, index) => (
        <DraggableSegment
          key={`seg-${index}`}
          segment={seg}
          connectionId={connectionId}
          waypoints={waypoints}
          onDragStart={() => {
            setIsWaypointDragging(true)
            onDragStateChange?.(true)
          }}
          onDragEnd={() => {
            setIsWaypointDragging(false)
            onDragStateChange?.(false)
          }}
        />
      ))}
      {/* Waypoint handles (bend points) - only show when selected */}
      {selected && waypoints.map((wp, index) => (
        <WaypointHandle
          key={index}
          x={wp.x}
          y={wp.y}
          index={index}
          connectionId={connectionId}
          onDragStart={() => {
            setIsWaypointDragging(true)
            onDragStateChange?.(true)
          }}
          onDragEnd={() => {
            setIsWaypointDragging(false)
            onDragStateChange?.(false)
          }}
        />
      ))}
      {/* Signal name label - show always if name exists, or show dimension label when selected */}
      <EdgeLabelRenderer>
        {/* Signal name display (always visible if set) - positioned above the trace, draggable */}
        {signalName && (
          <DraggableLabel
            connectionId={connectionId}
            labelX={labelX}
            labelY={labelY}
            offset={labelOffset}
            signalName={signalName}
            onDragStart={() => {
              setIsLabelDragging(true)
              onDragStateChange?.(true)
            }}
            onDragEnd={() => {
              setIsLabelDragging(false)
              onDragStateChange?.(false)
            }}
          />
        )}
        {/* Dimension label when selected (signal dimension count) - positioned just below the trace */}
        {selected && label && !isWaypointDragging && !isLabelDragging && (
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, 0%) translate(${labelX + labelOffset.x}px,${labelY + labelOffset.y + 2}px)`,
              pointerEvents: 'none',
              padding: `${padY}px ${padX}px`,
              borderRadius: labelBgBorderRadius || 4,
              ...labelBgStyle,
            }}
            className="nodrag nopan"
          >
            <span style={labelStyle as React.CSSProperties}>{label}</span>
          </div>
        )}
      </EdgeLabelRenderer>
    </g>
  )
}

export const CustomEdge = memo(CustomEdgeComponent)
