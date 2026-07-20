import type { BlockInstance, Connection as ConnectionType } from '../types/block'

/**
 * Calculate the minimum distance from a point to a line segment.
 * Used for detecting if a connection drop is near an existing edge (for branching).
 */
export function pointToSegmentDistance(
  px: number, py: number,
  x1: number, y1: number,
  x2: number, y2: number
): number {
  const dx = x2 - x1
  const dy = y2 - y1
  const lengthSquared = dx * dx + dy * dy

  if (lengthSquared === 0) {
    // Segment is a point
    return Math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
  }

  // Parameter t for the closest point on the line
  let t = ((px - x1) * dx + (py - y1) * dy) / lengthSquared
  t = Math.max(0, Math.min(1, t)) // Clamp to segment

  const closestX = x1 + t * dx
  const closestY = y1 + t * dy

  return Math.sqrt((px - closestX) ** 2 + (py - closestY) ** 2)
}

/**
 * Find the nearest edge to a point, within a maximum distance threshold.
 * Returns the connection and distance, or null if none are close enough.
 */
export function findNearestEdge(
  point: { x: number; y: number },
  connections: ConnectionType[],
  blocks: BlockInstance[],
  maxDistance: number = 30
): { connection: ConnectionType; distance: number } | null {
  let nearest: { connection: ConnectionType; distance: number } | null = null

  for (const conn of connections) {
    const sourceBlock = blocks.find(b => b.id === conn.sourceBlockId)
    const targetBlock = blocks.find(b => b.id === conn.targetBlockId)
    if (!sourceBlock || !targetBlock) continue

    // Get source port position (right side of block)
    const sourcePort = sourceBlock.outputPorts.find(p => p.id === conn.sourcePortId)
    if (!sourcePort) continue
    const sourcePortIndex = sourceBlock.outputPorts.indexOf(sourcePort)
    const sourcePortCount = sourceBlock.outputPorts.length
    const sourceX = sourceBlock.position.x + (sourceBlock.size?.width || 100)
    const sourceY = sourceBlock.position.y + ((sourcePortIndex + 1) / (sourcePortCount + 1)) * (sourceBlock.size?.height || 50)

    // Get target port position (left side of block)
    const targetPort = targetBlock.inputPorts.find(p => p.id === conn.targetPortId)
    if (!targetPort) continue
    const targetPortIndex = targetBlock.inputPorts.indexOf(targetPort)
    const targetPortCount = targetBlock.inputPorts.length
    const targetX = targetBlock.position.x
    const targetY = targetBlock.position.y + ((targetPortIndex + 1) / (targetPortCount + 1)) * (targetBlock.size?.height || 50)

    // For orthogonal paths, check distance to each segment
    const waypoints = conn.waypoints || []
    const pathPoints = [
      { x: sourceX, y: sourceY },
      ...waypoints,
      { x: targetX, y: targetY }
    ]

    // Check each segment
    for (let i = 0; i < pathPoints.length - 1; i++) {
      const p1 = pathPoints[i]
      const p2 = pathPoints[i + 1]

      // For Manhattan routing, we have intermediate points
      // Simple case: just check straight line for now
      const dist = pointToSegmentDistance(point.x, point.y, p1.x, p1.y, p2.x, p2.y)

      if (dist < maxDistance && (!nearest || dist < nearest.distance)) {
        nearest = { connection: conn, distance: dist }
      }
    }
  }

  return nearest
}

/**
 * Get block bounding box with margin
 */
export function getBlockBounds(block: BlockInstance, margin: number = 15): {
  left: number; right: number; top: number; bottom: number
} {
  const width = block.size?.width || 100
  const height = block.size?.height || 50
  return {
    left: block.position.x - margin,
    right: block.position.x + width + margin,
    top: block.position.y - margin,
    bottom: block.position.y + height + margin,
  }
}

/**
 * Check if a horizontal or vertical line segment intersects a block's bounding box
 */
export function segmentIntersectsBlock(
  x1: number, y1: number,
  x2: number, y2: number,
  block: BlockInstance,
  excludeBlockIds: Set<string>,
  margin: number = 15
): boolean {
  if (excludeBlockIds.has(block.id)) return false

  const bounds = getBlockBounds(block, margin)

  // For horizontal segment (y1 === y2)
  if (Math.abs(y1 - y2) < 1) {
    const minX = Math.min(x1, x2)
    const maxX = Math.max(x1, x2)
    // Check if the horizontal line passes through the block's Y range
    if (y1 >= bounds.top && y1 <= bounds.bottom) {
      // Check if X ranges overlap
      if (maxX > bounds.left && minX < bounds.right) {
        return true
      }
    }
  }
  // For vertical segment (x1 === x2)
  else if (Math.abs(x1 - x2) < 1) {
    const minY = Math.min(y1, y2)
    const maxY = Math.max(y1, y2)
    // Check if the vertical line passes through the block's X range
    if (x1 >= bounds.left && x1 <= bounds.right) {
      // Check if Y ranges overlap
      if (maxY > bounds.top && minY < bounds.bottom) {
        return true
      }
    }
  }

  return false
}

/**
 * Check if a vertical line at x from y1 to y2 crosses through a block.
 */
export function verticalLineIntersectsBlock(
  x: number,
  y1: number,
  y2: number,
  block: BlockInstance,
  excludeBlockIds: Set<string>,
  margin: number = 15
): boolean {
  if (excludeBlockIds.has(block.id)) return false

  const bounds = getBlockBounds(block, margin)

  // Line must be within horizontal extent of block
  if (x < bounds.left || x > bounds.right) return false

  // Line must overlap vertically with block
  const lineTop = Math.min(y1, y2)
  const lineBottom = Math.max(y1, y2)

  return !(lineBottom < bounds.top || lineTop > bounds.bottom)
}

/**
 * Check if a horizontal line at y from x1 to x2 crosses through a block.
 */
export function horizontalLineIntersectsBlock(
  x1: number,
  x2: number,
  y: number,
  block: BlockInstance,
  excludeBlockIds: Set<string>,
  margin: number = 15
): boolean {
  if (excludeBlockIds.has(block.id)) return false

  const bounds = getBlockBounds(block, margin)

  // Line must be within vertical extent of block
  if (y < bounds.top || y > bounds.bottom) return false

  // Line must overlap horizontally with block
  const lineLeft = Math.min(x1, x2)
  const lineRight = Math.max(x1, x2)

  return !(lineRight < bounds.left || lineLeft > bounds.right)
}

/**
 * Generate smart waypoints for a connection that avoids intersecting blocks.
 * Returns waypoints array (empty if direct path is clear).
 *
 * Routing preferences (matching Simulink convention):
 * - Feedback loops (backwards connections): Route BELOW all blocks
 * - Forward connections crossing blocks: Route ABOVE the blocking blocks
 *
 * Also checks vertical segments to ensure they don't cross blocks.
 */
export function generateSmartWaypoints(
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
  sourceBlockId: string,
  targetBlockId: string,
  allBlocks: BlockInstance[],
  allConnections: ConnectionType[],
  margin: number = 15
): Array<{ x: number; y: number }> {
  const excludeBlockIds = new Set([sourceBlockId, targetBlockId])
  const LINE_SPACING = 20

  // Calculate the default midpoint path (no waypoints = 3-segment path)
  const midX = (sourceX + targetX) / 2

  // Check if the simple 3-segment path intersects any blocks
  let hasCollision = false
  for (const block of allBlocks) {
    if (excludeBlockIds.has(block.id)) continue

    // Check segment 1 (horizontal: sourceX,sourceY to midX,sourceY)
    if (segmentIntersectsBlock(sourceX, sourceY, midX, sourceY, block, excludeBlockIds, margin)) {
      hasCollision = true
      break
    }
    // Check segment 2 (vertical: midX,sourceY to midX,targetY)
    if (segmentIntersectsBlock(midX, sourceY, midX, targetY, block, excludeBlockIds, margin)) {
      hasCollision = true
      break
    }
    // Check segment 3 (horizontal: midX,targetY to targetX,targetY)
    if (segmentIntersectsBlock(midX, targetY, targetX, targetY, block, excludeBlockIds, margin)) {
      hasCollision = true
      break
    }
  }

  // For forward connections with no collision, return empty
  if (!hasCollision && targetX > sourceX) {
    return []
  }

  // Find blocking blocks (blocks between source and target)
  const blockingBlocks: BlockInstance[] = []
  for (const block of allBlocks) {
    if (excludeBlockIds.has(block.id)) continue
    const bounds = getBlockBounds(block, margin)
    // Check if block is between source and target
    if (Math.min(sourceX, targetX) < bounds.right && Math.max(sourceX, targetX) > bounds.left) {
      if (Math.min(sourceY, targetY) - margin < bounds.bottom && Math.max(sourceY, targetY) + margin > bounds.top) {
        blockingBlocks.push(block)
      }
    }
  }

  // Get all block bounds for routing calculations
  const allBounds = allBlocks
    .filter(b => !excludeBlockIds.has(b.id))
    .map(b => getBlockBounds(b, margin))

  // Snap helper
  const snap = (v: number) => Math.round(v / LINE_SPACING) * LINE_SPACING

  // Determine routing strategy based on connection direction
  const isFeedback = targetX < sourceX

  if (isFeedback) {
    // Backwards connection (feedback loop) - ALWAYS route BELOW all blocks
    if (allBounds.length === 0) {
      // No other blocks, simple U-route below
      const routeY = Math.max(sourceY, targetY) + 60
      return [
        { x: snap(sourceX + 20), y: snap(routeY) },
        { x: snap(targetX - 20), y: snap(routeY) },
      ]
    }

    // Find max bottom of all blocks
    const maxBottom = Math.max(...allBounds.map(b => b.bottom))
    let routeY = snap(maxBottom + margin + 10)

    // Find X positions for waypoints that don't cross blocks vertically
    let wp1X = sourceX + 20
    let wp2X = targetX - 20

    // Check if vertical segment at wp1X crosses any block, adjust if needed
    for (const block of allBlocks) {
      if (verticalLineIntersectsBlock(wp1X, sourceY, routeY, block, excludeBlockIds, margin)) {
        const bounds = getBlockBounds(block, margin)
        wp1X = bounds.right + 5
      }
    }

    // Check if vertical segment at wp2X crosses any block, adjust if needed
    for (const block of allBlocks) {
      if (verticalLineIntersectsBlock(wp2X, targetY, routeY, block, excludeBlockIds, margin)) {
        const bounds = getBlockBounds(block, margin)
        wp2X = bounds.left - 5
      }
    }

    // Check for overlapping lines and adjust Y if needed
    routeY = findNonOverlappingY(routeY, wp1X, wp2X, sourceX, targetX, allConnections, allBlocks, excludeBlockIds, true, margin)

    return [
      { x: snap(wp1X), y: routeY },
      { x: snap(wp2X), y: routeY },
    ]
  }

  // Forward connection with blocking blocks - route ABOVE
  if (blockingBlocks.length > 0) {
    const blockingBounds = blockingBlocks.map(b => getBlockBounds(b, margin))
    const minTop = Math.min(...blockingBounds.map(b => b.top))
    let routeY = snap(minTop - margin - 10)

    // Find a good X for the waypoint that doesn't cause vertical segment collisions
    let needsTwoWaypoints = false
    for (const block of allBlocks) {
      if (verticalLineIntersectsBlock(midX, sourceY, routeY, block, excludeBlockIds, margin)) {
        needsTwoWaypoints = true
        break
      }
      if (verticalLineIntersectsBlock(midX, routeY, targetY, block, excludeBlockIds, margin)) {
        needsTwoWaypoints = true
        break
      }
    }

    if (needsTwoWaypoints) {
      // Use two waypoints to route around blocks
      let wp1X = sourceX + 20
      let wp2X = targetX - 20

      // Adjust wp1X if it crosses a block
      for (const block of allBlocks) {
        if (verticalLineIntersectsBlock(wp1X, sourceY, routeY, block, excludeBlockIds, margin)) {
          const bounds = getBlockBounds(block, margin)
          wp1X = bounds.right + 5
        }
      }

      // Adjust wp2X if it crosses a block
      for (const block of allBlocks) {
        if (verticalLineIntersectsBlock(wp2X, routeY, targetY, block, excludeBlockIds, margin)) {
          const bounds = getBlockBounds(block, margin)
          wp2X = bounds.left - 5
        }
      }

      // Check for overlapping lines and adjust Y if needed
      routeY = findNonOverlappingY(routeY, wp1X, wp2X, sourceX, targetX, allConnections, allBlocks, excludeBlockIds, false, margin)

      return [
        { x: snap(wp1X), y: routeY },
        { x: snap(wp2X), y: routeY },
      ]
    }

    // Check for overlapping lines and adjust Y if needed
    routeY = findNonOverlappingY(routeY, midX, midX, sourceX, targetX, allConnections, allBlocks, excludeBlockIds, false, margin)

    return [
      { x: snap(midX), y: routeY },
    ]
  }

  return []
}

/**
 * Find a Y level that doesn't overlap with existing connection routes and doesn't cross blocks.
 */
export function findNonOverlappingY(
  baseY: number,
  wp1X: number,
  wp2X: number,
  sourceX: number,
  targetX: number,
  allConnections: ConnectionType[],
  allBlocks: BlockInstance[],
  excludeBlockIds: Set<string>,
  isFeedback: boolean,
  margin: number
): number {
  const LINE_SPACING = 20
  let routeY = Math.round(baseY / LINE_SPACING) * LINE_SPACING

  // Calculate x-range this route spans
  const allX = [wp1X, wp2X, sourceX, targetX]
  const xMin = Math.min(...allX)
  const xMax = Math.max(...allX)

  // Check if this Y level overlaps with existing connections
  const hasOverlap = (yLevel: number): boolean => {
    for (const conn of allConnections) {
      if (!conn.waypoints || conn.waypoints.length === 0) continue

      // Get the Y level of this connection's waypoints
      const connY = conn.waypoints[0].y

      // Check if Y levels are the same (within tolerance)
      if (Math.abs(connY - yLevel) > LINE_SPACING / 2) continue

      // Check if X ranges overlap
      const connXs = conn.waypoints.map(wp => wp.x)
      const connXMin = Math.min(...connXs)
      const connXMax = Math.max(...connXs)

      if (!(xMax < connXMin - 10 || xMin > connXMax + 10)) {
        return true
      }
    }
    return false
  }

  // Check if routing at this Y level would cross any blocks
  const crossesBlock = (yLevel: number): boolean => {
    for (const block of allBlocks) {
      if (horizontalLineIntersectsBlock(xMin, xMax, yLevel, block, excludeBlockIds, margin)) {
        return true
      }
      // Also check vertical segments
      if (verticalLineIntersectsBlock(wp1X, isFeedback ? targetX : sourceX, yLevel, block, excludeBlockIds, margin)) {
        return true
      }
      if (verticalLineIntersectsBlock(wp2X, yLevel, isFeedback ? sourceX : targetX, block, excludeBlockIds, margin)) {
        return true
      }
    }
    return false
  }

  // Find a Y level without overlap and without crossing blocks
  const maxIterations = 50
  let iterations = 0

  while ((hasOverlap(routeY) || crossesBlock(routeY)) && iterations < maxIterations) {
    if (isFeedback) {
      routeY += LINE_SPACING // Go further down for feedback
    } else {
      routeY -= LINE_SPACING // Go further up for forward connections
    }
    iterations++
  }

  // If we couldn't find a good level, try the other direction
  if (iterations >= maxIterations) {
    routeY = Math.round(baseY / LINE_SPACING) * LINE_SPACING
    iterations = 0
    while ((hasOverlap(routeY) || crossesBlock(routeY)) && iterations < maxIterations) {
      if (isFeedback) {
        routeY -= LINE_SPACING
      } else {
        routeY += LINE_SPACING
      }
      iterations++
    }
  }

  return routeY
}
