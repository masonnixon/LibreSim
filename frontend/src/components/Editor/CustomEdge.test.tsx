import { fireEvent, render, screen } from '@testing-library/react'
import { createElement } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  CustomEdge,
  DraggableLabel,
  DraggableSegment,
  WaypointHandle,
} from './CustomEdge'

const updateConnectionWaypoint = vi.fn()
const addConnectionWaypoint = vi.fn()
const updateConnectionLabelOffset = vi.fn()
const pushHistory = vi.fn()

vi.mock('../../store/modelStore', function () {
  return {
    useModelStore: function (selector: (state: object) => unknown) {
      return selector({
        updateConnectionWaypoint,
        addConnectionWaypoint,
        updateConnectionLabelOffset,
        pushHistory,
      })
    },
  }
})

vi.mock('@xyflow/react', function () {
  return {
    BaseEdge: function (props: Record<string, unknown>) {
      return createElement('path', {
        'data-testid': 'base-edge',
        'data-props': JSON.stringify(props),
      })
    },
    EdgeLabelRenderer: function ({ children }: { children: React.ReactNode }) {
      return createElement('div', {}, children)
    },
    useReactFlow: function () {
      return {
        screenToFlowPosition: function ({ x, y }: { x: number; y: number }) {
          return { x, y }
        },
      }
    },
  }
})

const callbacks = { onDragStart: vi.fn(), onDragEnd: vi.fn() }

function renderSvg(element: React.ReactElement) {
  return render(createElement('svg', {}, element))
}

function segment(overrides: Record<string, unknown> = {}) {
  return {
    type: 'v',
    x1: 20,
    y1: 0,
    x2: 20,
    y2: 50,
    controlsWaypointIndex: 0,
    controlsCoordinate: 'x',
    ...overrides,
  } as never
}

function edgeProps(overrides: Record<string, unknown> = {}): React.ComponentProps<typeof CustomEdge> {
  return {
    id: 'edge-1',
    sourceX: 0,
    sourceY: 0,
    targetX: 100,
    targetY: 50,
    sourcePosition: 'right',
    targetPosition: 'left',
    source: 'a',
    target: 'b',
    selected: false,
    ...overrides,
  } as React.ComponentProps<typeof CustomEdge>
}

describe('edge drag controls', function () {
  beforeEach(function () {
    vi.clearAllMocks()
  })

  it('moves a waypoint after the threshold and reports the drag lifecycle', function () {
    renderSvg(
      <WaypointHandle
        x={10}
        y={20}
        index={1}
        connectionId="c1"
        {...callbacks}
      />
    )
    const handle = screen.getByText('Drag to move waypoint')
      .parentElement as HTMLElement

    fireEvent.mouseDown(handle, { clientX: 10, clientY: 20 })
    fireEvent.mouseMove(document, { clientX: 12, clientY: 22 })
    expect(updateConnectionWaypoint).not.toHaveBeenCalled()
    fireEvent.mouseMove(document, { clientX: 24, clientY: 36 })
    fireEvent.mouseMove(document, { clientX: 25, clientY: 37, altKey: true })

    expect(pushHistory).toHaveBeenCalledOnce()
    expect(callbacks.onDragStart).toHaveBeenCalledOnce()
    expect(updateConnectionWaypoint).toHaveBeenNthCalledWith(1, 'c1', 1, {
      x: 20,
      y: 40,
    })
    expect(updateConnectionWaypoint).toHaveBeenNthCalledWith(2, 'c1', 1, {
      x: 25,
      y: 37,
    })
    expect(handle).toHaveAttribute('fill', '#60a5fa')

    fireEvent.mouseUp(document)
    expect(callbacks.onDragEnd).toHaveBeenCalledOnce()
    expect(handle).toHaveAttribute('fill', '#3b82f6')
  })

  it('keeps a click inert and consumes waypoint double-clicks', function () {
    renderSvg(
      <WaypointHandle
        x={10}
        y={20}
        index={0}
        connectionId="c1"
        {...callbacks}
      />
    )
    const handle = screen.getByText('Drag to move waypoint')
      .parentElement as HTMLElement
    fireEvent.mouseDown(handle, { clientX: 1, clientY: 1 })
    fireEvent.mouseUp(document)
    expect(callbacks.onDragStart).not.toHaveBeenCalled()
    expect(callbacks.onDragEnd).not.toHaveBeenCalled()
    expect(fireEvent.doubleClick(handle)).toBe(false)
  })
})

describe('draggable segments', function () {
  beforeEach(function () {
    vi.clearAllMocks()
  })

  it('moves existing vertical segments', function () {
    renderSvg(
      <DraggableSegment
        segment={segment()}
        connectionId="c1"
        waypoints={[{ x: 20, y: 30 }]}
        {...callbacks}
      />
    )
    const line = screen.getByText('Drag to move segment')
      .parentElement as HTMLElement
    fireEvent.mouseDown(line, { clientX: 20, clientY: 20, detail: 2 })
    expect(pushHistory).not.toHaveBeenCalled()
    fireEvent.mouseDown(line, { clientX: 20, clientY: 20, detail: 1 })
    expect(line).toHaveAttribute('stroke', 'rgba(59, 130, 246, 0.3)')
    fireEvent.mouseMove(document, { clientX: 44, clientY: 60 })
    expect(updateConnectionWaypoint).toHaveBeenCalledWith('c1', 0, {
      x: 40,
      y: 30,
    })
    fireEvent.mouseUp(document)
    expect(callbacks.onDragEnd).toHaveBeenCalledOnce()
  })

  it('moves horizontal segments', function () {
    renderSvg(
      <DraggableSegment
        segment={segment({
          type: 'h',
          x1: 0,
          y1: 20,
          x2: 50,
          y2: 20,
          controlsCoordinate: 'y',
        })}
        connectionId="c2"
        waypoints={[{ x: 12, y: 20 }]}
        {...callbacks}
      />
    )
    const line = screen.getByText('Drag to move segment')
      .parentElement as HTMLElement
    expect(line).toHaveStyle({ cursor: 'ns-resize' })
    fireEvent.mouseDown(line, { detail: 1 })
    fireEvent.mouseMove(document, { clientX: 7, clientY: 26, altKey: true })
    expect(updateConnectionWaypoint).toHaveBeenLastCalledWith('c2', 0, {
      x: 12,
      y: 26,
    })
    expect(fireEvent.doubleClick(line)).toBe(false)
  })

  it('creates vertical insertion waypoints and tolerates a stale parent', function () {
    renderSvg(
      <DraggableSegment
        segment={segment({ controlsWaypointIndex: -1, insertWaypointAt: 0 })}
        connectionId="new-x"
        waypoints={[]}
        {...callbacks}
      />
    )
    const line = screen.getByText('Drag to move segment')
      .parentElement as HTMLElement
    fireEvent.mouseDown(line, { detail: 1 })
    fireEvent.mouseMove(document, { clientX: 23, clientY: 31 })
    expect(addConnectionWaypoint).toHaveBeenCalledWith(
      'new-x',
      { x: 20, y: 30 },
      0
    )
    fireEvent.mouseMove(document, { clientX: 42, clientY: 50 })
    expect(updateConnectionWaypoint).not.toHaveBeenCalled()
    fireEvent.mouseUp(document)
  })

  it('creates horizontal insertion waypoints', function () {
    renderSvg(
      <DraggableSegment
        segment={segment({
          type: 'h',
          x1: 0,
          y1: 20,
          x2: 40,
          y2: 20,
          controlsCoordinate: 'y',
          controlsWaypointIndex: -1,
          insertWaypointAt: 0,
        })}
        connectionId="new-y"
        waypoints={[]}
        {...callbacks}
      />
    )
    const line = screen.getByText('Drag to move segment')
      .parentElement as HTMLElement
    fireEvent.mouseDown(line, { detail: 1 })
    fireEvent.mouseMove(document, { clientX: 27, clientY: 33, altKey: true })
    expect(addConnectionWaypoint).toHaveBeenCalledWith(
      'new-y',
      { x: 20, y: 33 },
      0
    )
  })

  it('does not render fixed segments', function () {
    renderSvg(
      <DraggableSegment
        segment={segment({ controlsWaypointIndex: JSON.parse('null') })}
        connectionId="c"
        waypoints={[]}
        {...callbacks}
      />
    )
    expect(screen.queryByText('Drag to move segment')).not.toBeInTheDocument()
  })

  it('does not render undersized segments', function () {
    renderSvg(
      <DraggableSegment
        segment={segment({ y2: 2 })}
        connectionId="c"
        waypoints={[]}
        {...callbacks}
      />
    )
    expect(screen.queryByText('Drag to move segment')).not.toBeInTheDocument()
  })
})

describe('draggable labels', function () {
  beforeEach(function () {
    vi.clearAllMocks()
  })

  it('projects label movement onto the path and clamps its offset', function () {
    render(
      <DraggableLabel
        connectionId="c"
        pathPoints={[
          { x: 0, y: 0 },
          { x: 100, y: 0 },
        ]}
        offset={{ t: 0.5, perpOffset: 5 }}
        signalName="speed"
        {...callbacks}
      />
    )
    const label = screen.getByText('speed')
    expect(label).toHaveStyle({ cursor: 'grab' })
    fireEvent.mouseDown(label, { clientX: 50, clientY: 0 })
    fireEvent.mouseMove(document, { clientX: 52, clientY: 2 })
    expect(updateConnectionLabelOffset).not.toHaveBeenCalled()
    fireEvent.mouseMove(document, { clientX: 60, clientY: 100 })
    fireEvent.mouseMove(document, { clientX: 70, clientY: -100 })
    expect(updateConnectionLabelOffset).toHaveBeenNthCalledWith(1, 'c', {
      t: 0.6,
      perpOffset: -25,
    })
    expect(updateConnectionLabelOffset).toHaveBeenNthCalledWith(2, 'c', {
      t: 0.7,
      perpOffset: 25,
    })
    expect(pushHistory).toHaveBeenCalledOnce()
    expect(callbacks.onDragStart).toHaveBeenCalledOnce()
    expect(label).toHaveStyle({ cursor: 'grabbing' })
    fireEvent.mouseUp(document)
    expect(callbacks.onDragEnd).toHaveBeenCalledOnce()
    expect(label).toHaveStyle({ cursor: 'grab' })
  })

  it('keeps a label click inert', function () {
    render(
      <DraggableLabel
        connectionId="c"
        pathPoints={[{ x: 0, y: 0 }]}
        offset={{ t: 0.5, perpOffset: 0 }}
        signalName="name"
        {...callbacks}
      />
    )
    fireEvent.mouseDown(screen.getByText('name'), { clientX: 5, clientY: 5 })
    fireEvent.mouseUp(document)
    expect(callbacks.onDragStart).not.toHaveBeenCalled()
    expect(callbacks.onDragEnd).not.toHaveBeenCalled()
  })
})

describe('CustomEdge', function () {
  beforeEach(function () {
    vi.clearAllMocks()
  })

  it('forwards the path, marker, style, and default visual state', function () {
    const view = renderSvg(
      <CustomEdge
        {...edgeProps({ style: { opacity: 0.5 }, markerEnd: 'arrow' })}
      />
    )
    const props = JSON.parse(
      screen.getByTestId('base-edge').getAttribute('data-props') || '{}'
    )
    expect(props).toMatchObject({ id: 'edge-1', markerEnd: 'arrow' })
    expect(props.path).toContain('M 0,0')
    expect(props.style).toMatchObject({
      opacity: 0.5,
      stroke: '#94a3b8',
      strokeWidth: 2,
      pointerEvents: 'none',
    })
    const interaction = view.container.querySelector(
      '.react-flow__edge-interaction'
    ) as SVGPathElement
    expect(fireEvent.doubleClick(interaction)).toBe(false)
    expect(screen.queryByText('Drag to move segment')).not.toBeInTheDocument()
  })

  it('applies selected, highlighted, and branch color priorities', function () {
    const cases = [
      [{ selected: true }, '#22d3ee', 2.5],
      [{ selected: true, data: { isHighlighted: true } }, '#eab308', 3],
      [
        { selected: true, data: { isHighlighted: true, isBranchTarget: true } },
        '#22c55e',
        3,
      ],
    ] as const
    for (const [overrides, stroke, strokeWidth] of cases) {
      const view = renderSvg(<CustomEdge {...edgeProps(overrides)} />)
      const props = JSON.parse(
        screen.getByTestId('base-edge').getAttribute('data-props') || '{}'
      )
      expect(props.style).toMatchObject({ stroke, strokeWidth })
      view.unmount()
    }
  })

  it('renders signal, dimension, waypoints, and custom label presentation', function () {
    renderSvg(
      <CustomEdge
        {...edgeProps({
          selected: true,
          label: '3',
          labelStyle: { color: 'rgb(255, 0, 0)' },
          labelBgStyle: { background: 'white' },
          labelBgPadding: [0, 2],
          labelBgBorderRadius: 0,
          data: {
            connectionId: 'connection',
            signalName: 'velocity',
            waypoints: [{ x: 20, y: 30 }],
            labelOffset: { t: 0.25, perpOffset: 4 },
          },
        })}
      />
    )
    expect(screen.getByText('velocity')).toBeInTheDocument()
    const dimension = screen.getByText('3')
    expect(dimension).toHaveStyle({ color: 'rgb(255, 0, 0)' })
    expect(dimension.parentElement).toHaveStyle({
      padding: '2px 0px',
      borderRadius: '0',
      background: 'white',
    })
    expect(screen.getByText('Drag to move waypoint')).toBeInTheDocument()
    expect(screen.getAllByText('Drag to move segment').length).toBeGreaterThan(
      0
    )
  })

  it('uses default label padding and radius', function () {
    renderSvg(<CustomEdge {...edgeProps({ selected: true, label: '1' })} />)
    expect(screen.getByText('1').parentElement).toHaveStyle({
      padding: '4px 4px',
      borderRadius: '4px',
    })
  })

  it('hides the dimension while waypoint and label controls are dragging', function () {
    const onDragStateChange = vi.fn()
    renderSvg(
      <CustomEdge
        {...edgeProps({
          selected: true,
          label: '2',
          data: {
            waypoints: [{ x: 20, y: 30 }],
            signalName: 'signal',
            onDragStateChange,
          },
        })}
      />
    )
    const waypoint = screen.getByText('Drag to move waypoint')
      .parentElement as HTMLElement
    fireEvent.mouseDown(waypoint, { clientX: 20, clientY: 30 })
    fireEvent.mouseMove(document, { clientX: 30, clientY: 40 })
    expect(screen.queryByText('2')).not.toBeInTheDocument()
    fireEvent.mouseUp(document)
    expect(screen.getByText('2')).toBeInTheDocument()

    const signal = screen.getByText('signal')
    fireEvent.mouseDown(signal, { clientX: 20, clientY: 30 })
    fireEvent.mouseMove(document, { clientX: 30, clientY: 40 })
    expect(screen.queryByText('2')).not.toBeInTheDocument()
    fireEvent.mouseUp(document)
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(onDragStateChange.mock.calls).toEqual([
      [true],
      [false],
      [true],
      [false],
    ])
  })

  it('allows a selected segment drag without a drag-state callback', function () {
    renderSvg(<CustomEdge {...edgeProps({ selected: true })} />)
    const segmentHandle = screen.getAllByText('Drag to move segment')[0]
      .parentElement as HTMLElement
    fireEvent.mouseDown(segmentHandle, { detail: 1 })
    fireEvent.mouseUp(document)
    expect(pushHistory).toHaveBeenCalledOnce()
  })
})
