import { describe, expect, it } from 'vitest'
import {
  MAX_LABEL_PERP_OFFSET,
  calculatePathCenter,
  clampPerpendicularOffset,
  generateOrthogonalPath,
  getPositionOnPath,
  getSegmentLength,
  isSegmentDraggable,
  projectOntoPath,
  snapToGrid,
  type EdgeSegment,
} from './edgeRouting'

function segment(overrides: Partial<EdgeSegment> = {}): EdgeSegment {
  return {
    type: 'h',
    x1: 0,
    y1: 0,
    x2: 10,
    y2: 0,
    controlsWaypointIndex: 0,
    controlsCoordinate: 'y',
    ...overrides,
  }
}

describe('edge routing geometry', function () {
  it('generates the default three-segment orthogonal path', function () {
    const route = generateOrthogonalPath(0, 10, 100, 50, [])
    expect(route.path).toBe('M 0,10 L 50,10 L 50,50 L 100,50')
    expect(route.pathPoints).toEqual([
      { x: 0, y: 10 },
      { x: 50, y: 10 },
      { x: 50, y: 50 },
      { x: 100, y: 50 },
    ])
    expect(route.segments.map(function (item) { return item.controlsWaypointIndex })).toEqual([
      null,
      -1,
      -1,
    ])
    expect({ x: route.labelX, y: route.labelY }).toEqual({ x: 50, y: 30 })
  })

  it('routes through multiple waypoints and assigns segment controls', function () {
    const route = generateOrthogonalPath(0, 0, 100, 100, [
      { x: 20, y: 30 },
      { x: 70, y: 80 },
    ])
    expect(route.path).toBe('M 0,0 L 20,0 L 20,30 L 70,30 L 70,80 L 100,80 L 100,100')
    expect(route.segments.map(function (item) { return item.controlsWaypointIndex })).toEqual([
      null,
      0,
      0,
      1,
      1,
      -1,
    ])
    expect(route.segments[5].insertWaypointAt).toBe(2)
    expect({ x: route.labelX, y: route.labelY }).toEqual({ x: 70, y: 30 })
  })

  it('calculates centers for empty, single-point, zero-length, and malformed paths', function () {
    expect(calculatePathCenter([])).toEqual({ labelX: 0, labelY: 0 })
    expect(calculatePathCenter([{ x: 4, y: 6 }])).toEqual({ labelX: 4, labelY: 6 })
    expect(calculatePathCenter([{ x: 0, y: 0 }, { x: 0, y: 0 }])).toEqual({
      labelX: 0,
      labelY: 0,
    })
    expect(calculatePathCenter([{ x: 2, y: 4 }, { x: Number.NaN, y: 8 }])).toEqual({
      labelX: Number.NaN,
      labelY: 6,
    })
  })

  it('snaps to normal and fine grids', function () {
    expect(snapToGrid({ x: 14.8, y: -14.8 }, false)).toEqual({ x: 10, y: -10 })
    expect(snapToGrid({ x: 14.8, y: -14.8 }, true)).toEqual({ x: 15, y: -15 })
  })

  it('measures horizontal and vertical segments and checks drag eligibility', function () {
    expect(getSegmentLength(segment())).toBe(10)
    expect(getSegmentLength(segment({ type: 'v', x2: 0, y2: -8 }))).toBe(8)
    expect(isSegmentDraggable(segment())).toBe(true)
    expect(isSegmentDraggable(segment({ controlsWaypointIndex: null }))).toBe(false)
    expect(isSegmentDraggable(segment({ x2: 2 }))).toBe(false)
  })

  it('clamps perpendicular label offsets', function () {
    expect(clampPerpendicularOffset(-100)).toBe(-MAX_LABEL_PERP_OFFSET)
    expect(clampPerpendicularOffset(7)).toBe(7)
    expect(clampPerpendicularOffset(100)).toBe(MAX_LABEL_PERP_OFFSET)
  })

  it('locates positions along horizontal and vertical path segments', function () {
    expect(getPositionOnPath([], 0.5)).toEqual({ x: 0, y: 0, perpX: 0, perpY: -1 })
    expect(getPositionOnPath([{ x: 3, y: 4 }], 0.5)).toEqual({
      x: 3,
      y: 4,
      perpX: 0,
      perpY: -1,
    })
    expect(getPositionOnPath([{ x: 0, y: 0 }, { x: 100, y: 0 }], -1)).toEqual({
      x: 0,
      y: 0,
      perpX: 0,
      perpY: -1,
    })
    expect(getPositionOnPath([{ x: 0, y: 0 }, { x: 100, y: 0 }], 2)).toEqual({
      x: 100,
      y: 0,
      perpX: 0,
      perpY: -1,
    })
    expect(getPositionOnPath([{ x: 0, y: 0 }, { x: 0, y: 100 }], 0.25)).toEqual({
      x: 0,
      y: 25,
      perpX: -1,
      perpY: 0,
    })
    expect(getPositionOnPath([{ x: 5, y: 5 }, { x: 5, y: 5 }], 0.5)).toEqual({
      x: 5,
      y: 5,
      perpX: -1,
      perpY: 0,
    })
    const corner = [{ x: 0, y: 0 }, { x: 100, y: 0 }, { x: 100, y: 100 }]
    expect(getPositionOnPath(corner, 0.1)).toMatchObject({ x: 20, y: 0 })
    expect(getPositionOnPath(corner, 0.9)).toMatchObject({ x: 100, y: 80 })
  })

  it('projects points onto orthogonal paths with matching offset direction', function () {
    const horizontal = [{ x: 0, y: 0 }, { x: 100, y: 0 }]
    const horizontalProjection = projectOntoPath(horizontal, 30, -12)
    expect(horizontalProjection).toEqual({ t: 0.3, perpOffset: 12 })
    const horizontalPosition = getPositionOnPath(horizontal, horizontalProjection.t)
    expect({
      x: horizontalPosition.x + horizontalPosition.perpX * horizontalProjection.perpOffset,
      y: horizontalPosition.y + horizontalPosition.perpY * horizontalProjection.perpOffset,
    }).toEqual({ x: 30, y: -12 })

    const vertical = [{ x: 0, y: 0 }, { x: 0, y: 100 }]
    const verticalProjection = projectOntoPath(vertical, -8, 40)
    expect(verticalProjection).toEqual({ t: 0.4, perpOffset: 8 })
    const verticalPosition = getPositionOnPath(vertical, verticalProjection.t)
    expect({
      x: verticalPosition.x + verticalPosition.perpX * verticalProjection.perpOffset,
      y: verticalPosition.y + verticalPosition.perpY * verticalProjection.perpOffset,
    }).toEqual({ x: -8, y: 40 })
  })

  it('handles degenerate projections and selects the nearest segment', function () {
    expect(projectOntoPath([], 1, 2)).toEqual({ t: 0.5, perpOffset: 0 })
    expect(projectOntoPath([{ x: 3, y: 4 }], 1, 2)).toEqual({ t: 0.5, perpOffset: 0 })
    expect(projectOntoPath([{ x: 5, y: 5 }, { x: 5, y: 5 }], 8, 9)).toEqual({
      t: 0.5,
      perpOffset: -3,
    })
    expect(projectOntoPath([
      { x: 0, y: 0 },
      { x: 100, y: 0 },
      { x: 100, y: 100 },
    ], 90, 70)).toEqual({ t: 0.85, perpOffset: 10 })
    expect(projectOntoPath([
      { x: 0, y: 0 },
      { x: 100, y: 0 },
      { x: 100, y: 100 },
    ], 20, 5)).toEqual({ t: 0.1, perpOffset: -5 })
  })
})
