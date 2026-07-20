import React, { memo, useCallback, useMemo, useState, useRef } from 'react'
import { BaseEdge, EdgeLabelRenderer, EdgeProps, useReactFlow } from '@xyflow/react'
import { useModelStore } from '../../store/modelStore'
import {
  clampPerpendicularOffset,
  generateOrthogonalPath,
  getPositionOnPath,
  isSegmentDraggable,
  projectOntoPath,
  snapToGrid,
  type EdgeSegment,
} from '../../utils/edgeRouting'

interface WaypointData {
  waypoints?: Array<{ x: number; y: number }>
  connectionId?: string
  label?: string
  signalName?: string
  // t: position along path (0-1), perpOffset: perpendicular offset in pixels
  labelOffset?: { t: number; perpOffset: number }
  isBranchTarget?: boolean
  isHighlighted?: boolean
  onDragStateChange?: (isDragging: boolean) => void
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
  segment: EdgeSegment
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

  const canDrag = isSegmentDraggable(segment)

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
  if (!canDrag) return null

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


// Draggable label component for signal names - tethered to the path
function DraggableLabel({
  connectionId,
  pathPoints,
  offset,
  signalName,
  onDragStart,
  onDragEnd,
}: {
  connectionId: string
  pathPoints: Array<{ x: number; y: number }>
  offset: { t: number; perpOffset: number }
  signalName: string
  onDragStart: () => void
  onDragEnd: () => void
}) {
  const updateConnectionLabelOffset = useModelStore((state) => state.updateConnectionLabelOffset)
  const pushHistory = useModelStore((state) => state.pushHistory)
  const { screenToFlowPosition } = useReactFlow()
  const [isDragging, setIsDragging] = useState(false)

  // Calculate label position from t and perpOffset
  const { x: pathX, y: pathY, perpX, perpY } = useMemo(
    () => getPositionOnPath(pathPoints, offset.t),
    [pathPoints, offset.t]
  )

  const finalX = pathX + perpX * offset.perpOffset
  const finalY = pathY + perpY * offset.perpOffset

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation()
      e.preventDefault()

      const startClientX = e.clientX
      const startClientY = e.clientY
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

        // Convert mouse position to flow coordinates
        const flowPos = screenToFlowPosition({ x: moveEvent.clientX, y: moveEvent.clientY })

        // Project onto path to get new t and perpOffset
        const { t, perpOffset: rawPerpOffset } = projectOntoPath(pathPoints, flowPos.x, flowPos.y)

        // Constrain perpendicular offset
        const constrainedPerpOffset = clampPerpendicularOffset(rawPerpOffset)

        updateConnectionLabelOffset(connectionId, { t, perpOffset: constrainedPerpOffset })
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
    [connectionId, pathPoints, screenToFlowPosition, updateConnectionLabelOffset, pushHistory, onDragStart, onDragEnd]
  )

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
  // labelOffset: { t: position along path 0-1, perpOffset: perpendicular offset in pixels }
  // Default to center (t=0.5) with no perpendicular offset
  const labelOffset = waypointData?.labelOffset || { t: 0.5, perpOffset: 0 }
  const isBranchTarget = waypointData?.isBranchTarget || false
  const isHighlighted = waypointData?.isHighlighted || false
  const onDragStateChange = waypointData?.onDragStateChange

  // Get padding values
  const padX = Array.isArray(labelBgPadding) ? labelBgPadding[0] : (labelBgPadding || 4)
  const padY = Array.isArray(labelBgPadding) ? labelBgPadding[1] : (labelBgPadding || 4)

  // Generate orthogonal path
  const { path: edgePath, segments, labelX, labelY, pathPoints } = useMemo(() => {
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
        {/* Signal name display (always visible if set) - positioned along the trace, draggable */}
        {signalName && (
          <DraggableLabel
            connectionId={connectionId}
            pathPoints={pathPoints}
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
        {/* Dimension label when selected (signal dimension count) - positioned at path center */}
        {selected && label && !isWaypointDragging && !isLabelDragging && (
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, 0%) translate(${labelX}px,${labelY + 2}px)`,
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
