import { describe, expect, it } from 'vitest'
import type { BlockInstance, Connection } from '../types/block'
import {
  findNearestEdge,
  findNonOverlappingY,
  generateSmartWaypoints,
  getBlockBounds,
  horizontalLineIntersectsBlock,
  pointToSegmentDistance,
  segmentIntersectsBlock,
  verticalLineIntersectsBlock,
} from './smartRouting'

function port(id: string) {
  return {
    id,
    name: id,
    dataType: 'double' as const,
    dimensions: [1],
  }
}

function block(
  id: string,
  x: number,
  y: number,
  options: { width?: number; height?: number; inputs?: string[]; outputs?: string[] } = {}
): BlockInstance {
  const result: BlockInstance = {
    id,
    type: 'gain',
    name: id,
    position: { x, y },
    parameters: {},
    inputPorts: (options.inputs ?? [`${id}-in`]).map(port),
    outputPorts: (options.outputs ?? [`${id}-out`]).map(port),
  }
  if (options.width !== undefined || options.height !== undefined) {
    result.size = { width: options.width ?? 100, height: options.height ?? 50 }
  }
  return result
}

function connection(
  id: string,
  sourceBlockId: string,
  targetBlockId: string,
  options: Partial<Connection> = {}
): Connection {
  return {
    id,
    sourceBlockId,
    sourcePortId: `${sourceBlockId}-out`,
    targetBlockId,
    targetPortId: `${targetBlockId}-in`,
    ...options,
  }
}

describe('smart routing geometry', function () {
  it('calculates distances before, on, after, and on a degenerate segment', function () {
    expect(pointToSegmentDistance(3, 4, 0, 0, 0, 0)).toBe(5)
    expect(pointToSegmentDistance(-2, 0, 0, 0, 10, 0)).toBe(2)
    expect(pointToSegmentDistance(5, 3, 0, 0, 10, 0)).toBe(3)
    expect(pointToSegmentDistance(12, 0, 0, 0, 10, 0)).toBe(2)
  })

  it('calculates default, zero-valued, and explicit block bounds', function () {
    expect(getBlockBounds(block('default', 10, 20))).toEqual({ left: -5, right: 125, top: 5, bottom: 85 })
    expect(getBlockBounds(block('zero', 10, 20, { width: 0, height: 0 }), 0)).toEqual({
      left: 10,
      right: 110,
      top: 20,
      bottom: 70,
    })
    expect(getBlockBounds(block('sized', 10, 20, { width: 40, height: 30 }), 5)).toEqual({
      left: 5,
      right: 55,
      top: 15,
      bottom: 55,
    })
  })

  it.each([
    ['excluded', [0, 25, 100, 25], new Set(['box']), false],
    ['horizontal hit', [-10, 25, 120, 25], new Set<string>(), true],
    ['horizontal outside y', [-10, 80, 120, 80], new Set<string>(), false],
    ['horizontal outside x', [-50, 25, -20, 25], new Set<string>(), false],
    ['vertical hit', [50, -20, 50, 80], new Set<string>(), true],
    ['vertical outside x', [140, -20, 140, 80], new Set<string>(), false],
    ['vertical outside y', [50, 80, 50, 100], new Set<string>(), false],
    ['diagonal', [-10, -10, 120, 80], new Set<string>(), false],
  ])('%s segment intersection', function (_name, coordinates, excluded, expected) {
    const [x1, y1, x2, y2] = coordinates as number[]
    expect(segmentIntersectsBlock(x1, y1, x2, y2, block('box', 0, 0), excluded, 0)).toBe(expected)
  })

  it('uses the default segment margin', function () {
    expect(segmentIntersectsBlock(-20, 25, 120, 25, block('box', 0, 0), new Set())).toBe(true)
  })

  it('checks vertical lines against exclusions, bounds, and overlap', function () {
    const box = block('box', 0, 0)
    expect(verticalLineIntersectsBlock(50, -20, 80, box, new Set())).toBe(true)
    expect(verticalLineIntersectsBlock(50, -20, 80, box, new Set(['box']), 0)).toBe(false)
    expect(verticalLineIntersectsBlock(-1, -20, 80, box, new Set(), 0)).toBe(false)
    expect(verticalLineIntersectsBlock(101, -20, 80, box, new Set(), 0)).toBe(false)
    expect(verticalLineIntersectsBlock(50, 60, 80, box, new Set(), 0)).toBe(false)
    expect(verticalLineIntersectsBlock(50, -30, -1, box, new Set(), 0)).toBe(false)
    expect(verticalLineIntersectsBlock(50, 80, -20, box, new Set(), 0)).toBe(true)
  })

  it('checks horizontal lines against exclusions, bounds, and overlap', function () {
    const box = block('box', 0, 0)
    expect(horizontalLineIntersectsBlock(-20, 120, 25, box, new Set())).toBe(true)
    expect(horizontalLineIntersectsBlock(-20, 120, 25, box, new Set(['box']), 0)).toBe(false)
    expect(horizontalLineIntersectsBlock(-20, 120, -1, box, new Set(), 0)).toBe(false)
    expect(horizontalLineIntersectsBlock(-20, 120, 51, box, new Set(), 0)).toBe(false)
    expect(horizontalLineIntersectsBlock(-30, -1, 25, box, new Set(), 0)).toBe(false)
    expect(horizontalLineIntersectsBlock(101, 130, 25, box, new Set(), 0)).toBe(false)
    expect(horizontalLineIntersectsBlock(120, -20, 25, box, new Set(), 0)).toBe(true)
  })
})

describe('findNearestEdge', function () {
  it('skips malformed endpoints and chooses the closest valid segment', function () {
    const source = block('source', 0, 0, { width: 0, height: 0, outputs: ['source-out', 'source-alt'] })
    const target = block('target', 200, 0, { width: 80, height: 80, inputs: ['target-in', 'target-alt'] })
    const closer = connection('closer', 'source', 'target', {
      sourcePortId: 'source-alt',
      targetPortId: 'target-alt',
      waypoints: [{ x: 150, y: 60 }],
    })
    const candidates = [
      connection('missing-source', 'missing', 'target'),
      connection('missing-target', 'source', 'missing'),
      connection('missing-source-port', 'source', 'target', { sourcePortId: 'bad' }),
      connection('missing-target-port', 'source', 'target', { targetPortId: 'bad' }),
      connection('farther', 'source', 'target'),
      closer,
    ]

    const nearest = findNearestEdge({ x: 150, y: 58 }, candidates, [source, target])
    expect(nearest?.connection).toBe(closer)
    expect(nearest?.distance).toBeCloseTo(1.7647)
  })

  it('returns null when every edge is outside an explicit threshold', function () {
    const source = block('source', 0, 0)
    const target = block('target', 200, 0)
    expect(findNearestEdge({ x: 150, y: 100 }, [connection('edge', 'source', 'target')], [source, target], 5)).toBeNull()
  })
})

describe('generateSmartWaypoints', function () {
  it('leaves a clear forward route and an equal-x route without blockers unchanged', function () {
    const source = block('source', 0, 0)
    const target = block('target', 200, 0)
    expect(generateSmartWaypoints(100, 25, 200, 25, 'source', 'target', [source, target], [])).toEqual([])
    expect(generateSmartWaypoints(0, 25, 200, 25, 'source', 'target', [block('far', 300, 300)], [])).toEqual([])
    expect(generateSmartWaypoints(100, 25, 100, 125, 'source', 'target', [source, target], [])).toEqual([])
  })

  it('routes a feedback edge below its endpoints when no other blocks exist', function () {
    expect(generateSmartWaypoints(200, 20, 20, 40, 'source', 'target', [], [])).toEqual([
      { x: 220, y: 100 },
      { x: 0, y: 100 },
    ])
  })

  it('routes a blocked forward edge above the blocker with one waypoint', function () {
    const obstacle = block('obstacle', 40, 0, { width: 20, height: 50 })
    expect(generateSmartWaypoints(0, 25, 200, 25, 'source', 'target', [obstacle], [], 0)).toEqual([
      { x: 100, y: -20 },
    ])
  })

  it('detects collisions on the middle and final default-route segments', function () {
    const middle = block('middle', 95, 50, { width: 10, height: 20 })
    const outsideX = block('outside-x', 300, 0)
    const outsideY = block('outside-y', 120, 300)
    const middleRoute = generateSmartWaypoints(
      0, 0, 200, 100, 'source', 'target', [middle, outsideX, outsideY], [], 0
    )
    expect(middleRoute).toHaveLength(2)

    const final = block('final', 140, 90, { width: 20, height: 20 })
    expect(generateSmartWaypoints(0, 0, 200, 100, 'source', 'target', [final], [], 0)).toHaveLength(1)
  })

  it('adjusts both forward waypoint columns around vertical blockers', function () {
    const primary = block('primary', 40, 0, { width: 20, height: 20 })
    const middle = block('middle', 95, 50, { width: 10, height: 10 })
    const firstColumn = block('first-column', 15, -10, { width: 10, height: 10 })
    const secondColumn = block('second-column', 175, 50, { width: 10, height: 10 })
    const route = generateSmartWaypoints(
      0, 10, 200, 100, 'source', 'target', [primary, middle, firstColumn, secondColumn], [], 0
    )
    expect(route).toHaveLength(2)
    expect(route[0].x).toBe(40)
    expect(route[1].x).toBe(180)
  })

  it('uses two adjusted waypoints when the middle vertical route is blocked', function () {
    const horizontalBlocker = block('horizontal', 80, 0, { width: 40, height: 30 })
    const verticalBlocker = block('vertical', 95, -40, { width: 10, height: 50 })
    const route = generateSmartWaypoints(0, 15, 200, 15, 'source', 'target', [horizontalBlocker, verticalBlocker], [], 0)
    expect(route).toHaveLength(2)
    expect(route[0].y).toBe(route[1].y)
  })

  it('adjusts feedback waypoint x positions around blocks and separates overlapping routes', function () {
    const left = block('left', 200, 0, { width: 30, height: 100 })
    const right = block('right', 0, 0, { width: 30, height: 100 })
    const existing = connection('existing', 'a', 'b', {
      waypoints: [{ x: -100, y: 120 }, { x: 300, y: 120 }],
    })
    const route = generateSmartWaypoints(210, 20, 20, 40, 'source', 'target', [left, right], [existing], 0)
    expect(route).toHaveLength(2)
    expect(route[0].y).toBeGreaterThanOrEqual(140)
  })
})

describe('findNonOverlappingY', function () {
  const excluded = new Set<string>()

  it('ignores empty, distant, and non-overlapping connection routes', function () {
    const connections = [
      connection('none', 'a', 'b'),
      connection('empty', 'a', 'b', { waypoints: [] }),
      connection('different-y', 'a', 'b', { waypoints: [{ x: 0, y: 100 }] }),
      connection('different-x', 'a', 'b', { waypoints: [{ x: 1000, y: 20 }, { x: 1100, y: 20 }] }),
    ]
    expect(findNonOverlappingY(20, 20, 80, 0, 100, connections, [], excluded, false, 0)).toBe(20)
  })

  it('moves feedback and forward routes away from an existing overlap', function () {
    const existing = [connection('existing', 'a', 'b', {
      waypoints: [{ x: 0, y: 20 }, { x: 100, y: 20 }],
    })]
    expect(findNonOverlappingY(20, 20, 80, 0, 100, existing, [], excluded, true, 0)).toBe(40)
    expect(findNonOverlappingY(20, 20, 80, 0, 100, existing, [], excluded, false, 0)).toBe(0)
  })

  it('detects horizontal and both vertical block crossings', function () {
    const horizontal = block('horizontal', 30, 10, { width: 40, height: 20 })
    expect(findNonOverlappingY(20, 20, 80, 0, 100, [], [horizontal], excluded, false, 0)).toBe(0)

    const firstVertical = block('first', 15, 65, { width: 10, height: 5 })
    expect(findNonOverlappingY(60, 20, 80, 0, 100, [], [firstVertical], excluded, true, 0)).toBe(80)

    const secondVertical = block('second', 75, 50, { width: 10, height: 5 })
    expect(findNonOverlappingY(60, 20, 80, 0, 100, [], [secondVertical], excluded, true, 0)).toBe(40)
  })

  it('falls back to the opposite search direction after fifty blocked levels', function () {
    const wall = block('wall', -100, -5000, { width: 300, height: 10000 })
    expect(findNonOverlappingY(0, 20, 80, 0, 100, [], [wall], excluded, false, 0)).toBe(1000)
    expect(findNonOverlappingY(0, 20, 80, 0, 100, [], [wall], excluded, true, 0)).toBe(-1000)
  })
})
