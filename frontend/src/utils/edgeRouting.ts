export interface EdgePoint {
  x: number
  y: number
}

export interface EdgeSegment {
  type: 'h' | 'v'
  x1: number
  y1: number
  x2: number
  y2: number
  controlsWaypointIndex: number | null
  controlsCoordinate: 'x' | 'y'
  insertWaypointAt?: number
}

export interface OrthogonalPath {
  path: string
  segments: EdgeSegment[]
  labelX: number
  labelY: number
  pathPoints: EdgePoint[]
}

export interface PathPosition extends EdgePoint {
  perpX: number
  perpY: number
}

export interface PathProjection {
  t: number
  perpOffset: number
}

export const MAX_LABEL_PERP_OFFSET = 25

export function calculatePathCenter(points: EdgePoint[]) {
  if (points.length < 2) {
    return { labelX: points[0]?.x || 0, labelY: points[0]?.y || 0 }
  }

  let totalLength = 0
  const segmentLengths: number[] = []
  for (let index = 1; index < points.length; index++) {
    const deltaX = points[index].x - points[index - 1].x
    const deltaY = points[index].y - points[index - 1].y
    const length = Math.abs(deltaX) + Math.abs(deltaY)
    segmentLengths.push(length)
    totalLength += length
  }

  const halfLength = totalLength / 2
  let accumulatedLength = 0
  for (let index = 0; index < segmentLengths.length; index++) {
    const segmentLength = segmentLengths[index]
    if (accumulatedLength + segmentLength >= halfLength) {
      const remaining = halfLength - accumulatedLength
      const ratio = segmentLength > 0 ? remaining / segmentLength : 0
      const first = points[index]
      const second = points[index + 1]
      return {
        labelX: first.x + (second.x - first.x) * ratio,
        labelY: first.y + (second.y - first.y) * ratio,
      }
    }
    accumulatedLength += segmentLength
  }

  const last = points[points.length - 1]
  const secondLast = points[points.length - 2]
  return {
    labelX: (last.x + secondLast.x) / 2,
    labelY: (last.y + secondLast.y) / 2,
  }
}

export function snapToGrid(position: EdgePoint, useFineGrid: boolean): EdgePoint {
  const gridSize = useFineGrid ? 1 : 10
  return {
    x: Math.round(position.x / gridSize) * gridSize,
    y: Math.round(position.y / gridSize) * gridSize,
  }
}

export function getSegmentLength(segment: EdgeSegment) {
  return segment.type === 'h'
    ? Math.abs(segment.x2 - segment.x1)
    : Math.abs(segment.y2 - segment.y1)
}

export function isSegmentDraggable(segment: EdgeSegment) {
  return segment.controlsWaypointIndex !== null && getSegmentLength(segment) >= 3
}

export function clampPerpendicularOffset(offset: number) {
  return Math.max(-MAX_LABEL_PERP_OFFSET, Math.min(MAX_LABEL_PERP_OFFSET, offset))
}

export function generateOrthogonalPath(
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
  waypoints: EdgePoint[]
): OrthogonalPath {
  const segments: EdgeSegment[] = []
  const pathPoints: EdgePoint[] = []

  if (waypoints.length === 0) {
    const midX = (sourceX + targetX) / 2
    const path = `M ${sourceX},${sourceY} L ${midX},${sourceY} L ${midX},${targetY} L ${targetX},${targetY}`

    pathPoints.push({ x: sourceX, y: sourceY })
    pathPoints.push({ x: midX, y: sourceY })
    pathPoints.push({ x: midX, y: targetY })
    pathPoints.push({ x: targetX, y: targetY })

    segments.push({
      type: 'h',
      x1: sourceX,
      y1: sourceY,
      x2: midX,
      y2: sourceY,
      controlsWaypointIndex: null,
      controlsCoordinate: 'y',
    })
    segments.push({
      type: 'v',
      x1: midX,
      y1: sourceY,
      x2: midX,
      y2: targetY,
      controlsWaypointIndex: -1,
      controlsCoordinate: 'x',
      insertWaypointAt: 0,
    })
    segments.push({
      type: 'h',
      x1: midX,
      y1: targetY,
      x2: targetX,
      y2: targetY,
      controlsWaypointIndex: -1,
      controlsCoordinate: 'y',
      insertWaypointAt: 0,
    })

    return {
      path,
      segments,
      labelX: midX,
      labelY: (sourceY + targetY) / 2,
      pathPoints,
    }
  }

  let path = `M ${sourceX},${sourceY}`
  let previousX = sourceX
  let previousY = sourceY
  pathPoints.push({ x: sourceX, y: sourceY })

  for (let index = 0; index < waypoints.length; index++) {
    const waypoint = waypoints[index]
    path += ` L ${waypoint.x},${previousY}`
    pathPoints.push({ x: waypoint.x, y: previousY })
    segments.push({
      type: 'h',
      x1: previousX,
      y1: previousY,
      x2: waypoint.x,
      y2: previousY,
      controlsWaypointIndex: index === 0 ? null : index - 1,
      controlsCoordinate: 'y',
    })
    previousX = waypoint.x

    path += ` L ${waypoint.x},${waypoint.y}`
    pathPoints.push({ x: waypoint.x, y: waypoint.y })
    segments.push({
      type: 'v',
      x1: waypoint.x,
      y1: previousY,
      x2: waypoint.x,
      y2: waypoint.y,
      controlsWaypointIndex: index,
      controlsCoordinate: 'x',
    })
    previousY = waypoint.y
  }

  const lastWaypointIndex = waypoints.length - 1
  path += ` L ${targetX},${previousY}`
  pathPoints.push({ x: targetX, y: previousY })
  segments.push({
    type: 'h',
    x1: previousX,
    y1: previousY,
    x2: targetX,
    y2: previousY,
    controlsWaypointIndex: lastWaypointIndex,
    controlsCoordinate: 'y',
  })

  path += ` L ${targetX},${targetY}`
  pathPoints.push({ x: targetX, y: targetY })
  segments.push({
    type: 'v',
    x1: targetX,
    y1: previousY,
    x2: targetX,
    y2: targetY,
    controlsWaypointIndex: -1,
    controlsCoordinate: 'x',
    insertWaypointAt: waypoints.length,
  })

  return { path, segments, ...calculatePathCenter(pathPoints), pathPoints }
}

export function getPositionOnPath(pathPoints: EdgePoint[], t: number): PathPosition {
  if (pathPoints.length < 2) {
    return {
      x: pathPoints[0]?.x || 0,
      y: pathPoints[0]?.y || 0,
      perpX: 0,
      perpY: -1,
    }
  }

  let totalLength = 0
  const segmentLengths: number[] = []
  for (let index = 1; index < pathPoints.length; index++) {
    const deltaX = pathPoints[index].x - pathPoints[index - 1].x
    const deltaY = pathPoints[index].y - pathPoints[index - 1].y
    const length = Math.abs(deltaX) + Math.abs(deltaY)
    segmentLengths.push(length)
    totalLength += length
  }

  const targetLength = Math.max(0, Math.min(1, t)) * totalLength
  let accumulatedLength = 0
  let targetSegmentIndex = segmentLengths.length - 1
  for (let index = 0; index < segmentLengths.length - 1; index++) {
    if (accumulatedLength + segmentLengths[index] >= targetLength) {
      targetSegmentIndex = index
      break
    }
    accumulatedLength += segmentLengths[index]
  }

  const segmentLength = segmentLengths[targetSegmentIndex]
  const remaining = targetLength - accumulatedLength
  const ratio = segmentLength > 0 ? remaining / segmentLength : 0
  const first = pathPoints[targetSegmentIndex]
  const second = pathPoints[targetSegmentIndex + 1]
  const deltaX = second.x - first.x
  const deltaY = second.y - first.y
  const isHorizontal = Math.abs(deltaX) > Math.abs(deltaY)

  return {
    x: first.x + deltaX * ratio,
    y: first.y + deltaY * ratio,
    perpX: isHorizontal ? 0 : -1,
    perpY: isHorizontal ? -1 : 0,
  }
}

export function projectOntoPath(
  pathPoints: EdgePoint[],
  pointX: number,
  pointY: number
): PathProjection {
  if (pathPoints.length < 2) {
    return { t: 0.5, perpOffset: 0 }
  }

  let totalLength = 0
  const segmentLengths: number[] = []
  for (let index = 1; index < pathPoints.length; index++) {
    const deltaX = pathPoints[index].x - pathPoints[index - 1].x
    const deltaY = pathPoints[index].y - pathPoints[index - 1].y
    const length = Math.abs(deltaX) + Math.abs(deltaY)
    segmentLengths.push(length)
    totalLength += length
  }

  let bestT = 0.5
  let bestDistance = Infinity
  let bestPerpendicularOffset = 0
  let accumulatedLength = 0

  for (let index = 0; index < segmentLengths.length; index++) {
    const first = pathPoints[index]
    const second = pathPoints[index + 1]
    const segmentLength = segmentLengths[index]
    const deltaX = second.x - first.x
    const deltaY = second.y - first.y
    let projectionRatio: number
    let closestX: number
    let closestY: number
    let perpendicularOffset: number

    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      projectionRatio = Math.max(0, Math.min(1, (pointX - first.x) / deltaX))
      closestX = first.x + deltaX * projectionRatio
      closestY = first.y
      perpendicularOffset = closestY - pointY
    } else {
      projectionRatio = deltaY !== 0
        ? Math.max(0, Math.min(1, (pointY - first.y) / deltaY))
        : 0
      closestX = first.x
      closestY = first.y + deltaY * projectionRatio
      perpendicularOffset = closestX - pointX
    }

    const distance = Math.abs(pointX - closestX) + Math.abs(pointY - closestY)
    if (distance < bestDistance) {
      bestDistance = distance
      bestT = totalLength > 0
        ? (accumulatedLength + projectionRatio * segmentLength) / totalLength
        : 0.5
      bestPerpendicularOffset = perpendicularOffset
    }
    accumulatedLength += segmentLength
  }

  return { t: bestT, perpOffset: bestPerpendicularOffset }
}
