import { act, fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { PlotWindowState } from '../../store/uiStore'
import type { SignalData } from '../../types/simulation'
import { Scope3DWindow } from './Scope3DWindow'

const mocks = vi.hoisted(function () {
  return {
    plot: vi.fn(), close: vi.fn(), toggle: vi.fn(),
    updatePosition: vi.fn(), updateSize: vi.fn(), draggable: vi.fn(),
    getResizeProps: vi.fn(function (direction: string) {
      return { 'data-resize-direction': direction }
    }),
    dragging: false,
  }
})

vi.mock('react-plotly.js', function () {
  return { default: function PlotStub(props: unknown) { mocks.plot(props); return null } }
})

vi.mock('../../store/uiStore', function () {
  return { useUIStore: function () { return {
    closePlotWindow: mocks.close, togglePlotWindowMinimized: mocks.toggle,
    updatePlotWindowPosition: mocks.updatePosition, updatePlotWindowSize: mocks.updateSize,
  } } }
})

vi.mock('../../hooks/useDraggableWindow', function () {
  return { useDraggableWindow: function (options: unknown) {
    mocks.draggable(options)
    return {
      isDragging: mocks.dragging,
      dragHandleProps: { 'data-testid': 'drag-handle' },
      getResizeHandleProps: mocks.getResizeProps,
    }
  } }
})

const expandedState: PlotWindowState = {
  isOpen: true,
  isMinimized: false,
  position: { x: 12, y: 34 },
  size: { width: 640, height: 480 },
}

function signal(overrides: Partial<SignalData> = {}): SignalData {
  return {
    blockId: 'scope-3d', portId: 'input-0', name: 'Trajectory',
    times: [0, 1], values: [], x: [1, 2], y: [3, 4], z: [5, 6], is3D: true,
    ...overrides,
  }
}

function setup(data: SignalData, windowState: PlotWindowState = expandedState) {
  const onFocus = vi.fn()
  const view = render(<Scope3DWindow blockId="scope-3d" blockName="Orbit" signal={data}
    windowState={windowState} zIndex={73} onFocus={onFocus} />)
  return [view, onFocus] as const
}

describe('Scope3DWindow', function () {
  beforeEach(function () {
    vi.clearAllMocks()
    mocks.dragging = false
  })

  it('wires window chrome and draggable adapters', function () {
    const [view, onFocus] = setup(signal())
    const outer = view.container.firstElementChild as HTMLElement
    expect(outer).toHaveStyle({ left: '12px', top: '34px', width: '640px', height: '480px', zIndex: '73' })
    fireEvent.mouseDown(outer)
    expect(onFocus).toHaveBeenCalled()
    fireEvent.click(screen.getByTitle('Minimize'))
    fireEvent.click(screen.getByTitle('Close'))
    expect(mocks.toggle).toHaveBeenCalledWith('scope-3d')
    expect(mocks.close).toHaveBeenCalledWith('scope-3d')
    expect(mocks.getResizeProps.mock.calls.map(function (call) { return call[0] }))
      .toEqual(['n', 's', 'e', 'w', 'nw', 'ne', 'sw', 'se'])
    const options = mocks.draggable.mock.calls.at(-1)?.[0] as {
      minSize: { width: number; height: number }
      onPositionChange: (position: { x: number; y: number }) => void
      onSizeChange: (size: { width: number; height: number }) => void
    }
    expect(options.minSize).toEqual({ width: 450, height: 400 })
    act(function () {
      options.onPositionChange({ x: 90, y: 91 })
      options.onSizeChange({ width: 700, height: 500 })
    })
    expect(mocks.updatePosition).toHaveBeenCalledWith('scope-3d', { x: 90, y: 91 })
    expect(mocks.updateSize).toHaveBeenCalledWith('scope-3d', { width: 700, height: 500 })

    view.unmount()
    vi.clearAllMocks()
    mocks.dragging = true
    const [minimized] = setup(signal(), { ...expandedState, isMinimized: true })
    const minimizedOuter = minimized.container.firstElementChild as HTMLElement
    expect(minimizedOuter).toHaveStyle({ width: '250px', height: 'auto' })
    expect(minimizedOuter.style.cursor).toBe('grabbing')
    expect(screen.getByTitle('Expand')).toBeInTheDocument()
    expect(mocks.plot).not.toHaveBeenCalled()
    expect(mocks.getResizeProps).not.toHaveBeenCalled()
  })

  it('shows an empty state until all three coordinates are available', function () {
    const [view] = setup(signal({ x: undefined }))
    expect(screen.getByText('No data available')).toBeInTheDocument()
    expect(mocks.plot).not.toHaveBeenCalled()

    view.rerender(<Scope3DWindow blockId="scope-3d" blockName="Orbit"
      signal={signal({ y: undefined, z: undefined })}
      windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    expect(screen.getByText('No data available')).toBeInTheDocument()
    expect(mocks.plot).not.toHaveBeenCalled()

    view.rerender(<Scope3DWindow blockId="scope-3d" blockName="Orbit"
      signal={signal({ z: undefined })}
      windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    expect(screen.getByText('No data available')).toBeInTheDocument()
    expect(mocks.plot).not.toHaveBeenCalled()
  })

  it('renders coordinate data revisions', function () {
    const original = signal()
    const [view] = setup(original)
    expect(mocks.plot).toHaveBeenCalledOnce()
    const initial = mocks.plot.mock.calls[0][0] as { data: unknown[]; revision: number }
    expect(initial.data[0]).toMatchObject({ x: [1, 2], y: [3, 4], z: [5, 6] })
    expect(initial.revision).toBe(1)
    view.rerender(<Scope3DWindow blockId="scope-3d" blockName="Orbit" signal={original}
      windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    const unchanged = mocks.plot.mock.lastCall?.[0] as { revision: number }
    expect(unchanged.revision).toBe(1)
    view.rerender(<Scope3DWindow blockId="scope-3d" blockName="Orbit" signal={signal({
      x: [7, 8], y: [9, 10], z: [11, 12], inputNames: ['East', 'North', 'Up'],
    })} windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    const updated = mocks.plot.mock.lastCall?.[0] as { data: unknown[]; revision: number }
    expect(updated.revision).toBe(2)
    const updatedTrace = updated.data[0] as { hovertemplate: string }
    expect(updatedTrace.hovertemplate).toContain('East:')
    const updatedLayout = mocks.plot.mock.lastCall?.[0] as {
      layout: { scene: { xaxis: { title: { text: string } } } }
    }
    expect(updatedLayout.layout.scene.xaxis.title.text).toBe('East')
  })

  it('preserves and resets camera interactions', function () {
    const [view] = setup(signal())
    const initial = mocks.plot.mock.calls[0][0] as {
      onRelayout: (event: Record<string, unknown>) => void
    }
    expect(initial.onRelayout).toBeTypeOf('function')
    const camera = {
      eye: { x: 2, y: 3, z: 4 },
      center: { x: 1, y: 1, z: 1 },
      up: { x: 0, y: 0, z: 1 },
    }
    act(function () { initial.onRelayout({ 'scene.camera': camera }) })
    view.rerender(<Scope3DWindow blockId="scope-3d" blockName="Orbit" signal={signal({ x: [2, 3] })}
      windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    const rotated = mocks.plot.mock.lastCall?.[0] as { layout: { scene: { camera: unknown } } }
    expect(rotated.layout.scene.camera).toEqual(camera)
    act(function () {
      initial.onRelayout({ 'scene.camera.eye': { x: 5, y: 5, z: 5 } })
      initial.onRelayout({ 'scene.camera.center': { x: 2, y: 2, z: 2 } })
      initial.onRelayout({ 'scene.camera.up': { x: 1, y: 0, z: 0 } })
      initial.onRelayout({ unrelated: true })
    })
    view.rerender(<Scope3DWindow blockId="scope-3d" blockName="Orbit" signal={signal({ x: [3, 4] })}
      windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    const individual = mocks.plot.mock.lastCall?.[0] as { layout: { scene: { camera: unknown } } }
    expect(individual.layout.scene.camera).toEqual({
      eye: { x: 5, y: 5, z: 5 },
      center: { x: 2, y: 2, z: 2 },
      up: { x: 1, y: 0, z: 0 },
    })
    act(function () { initial.onRelayout({ 'scene.xaxis.range': [0, 1] }) })
    view.rerender(<Scope3DWindow blockId="scope-3d" blockName="Orbit" signal={signal({ x: [4, 5] })}
      windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    const reset = mocks.plot.mock.lastCall?.[0] as { layout: { scene: { camera: unknown } } }
    expect(reset.layout.scene.camera).toEqual({ eye: { x: 1.5, y: 1.5, z: 1.2 } })
  })
})
