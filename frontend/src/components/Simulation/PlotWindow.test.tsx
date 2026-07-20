import { act, fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { PlotWindowState } from '../../store/uiStore'
import type { SignalData } from '../../types/simulation'
import { PlotWindow } from './PlotWindow'

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
    blockId: 'scope-1',
    portId: 'input-0',
    name: 'Signal',
    times: [0, 1, 2],
    values: [1, 2, 3],
    ...overrides,
  }
}

function setup(signals: SignalData[], windowState: PlotWindowState = expandedState) {
  const onFocus = vi.fn()
  const view = render(<PlotWindow blockId="scope-1" blockName="Scope" signals={signals}
    windowState={windowState} zIndex={73} onFocus={onFocus} />)
  return [view, onFocus] as const
}

describe('PlotWindow', function () {
  beforeEach(function () {
    vi.clearAllMocks()
    mocks.dragging = false
  })

  it('wires window chrome and draggable adapters', function () {
    const [view, onFocus] = setup([signal()])
    const outer = view.container.firstElementChild as HTMLElement
    expect(outer).toHaveStyle({ left: '12px', top: '34px', width: '640px', height: '480px', zIndex: '73' })
    expect(outer.style.cursor).toBe('default')
    fireEvent.mouseDown(outer)
    expect(onFocus).toHaveBeenCalled()
    fireEvent.click(screen.getByTitle('Minimize'))
    fireEvent.click(screen.getByTitle('Close'))
    expect(mocks.toggle).toHaveBeenCalledWith('scope-1')
    expect(mocks.close).toHaveBeenCalledWith('scope-1')
    expect(mocks.getResizeProps.mock.calls.map(function (call) { return call[0] }))
      .toEqual(['n', 's', 'e', 'w', 'nw', 'ne', 'sw', 'se'])
    const options = mocks.draggable.mock.calls.at(-1)?.[0] as {
      minSize: { width: number; height: number }
      onPositionChange: (position: { x: number; y: number }) => void
      onSizeChange: (size: { width: number; height: number }) => void
    }
    expect(options.minSize).toEqual({ width: 300, height: 200 })
    act(function () {
      options.onPositionChange({ x: 90, y: 91 })
      options.onSizeChange({ width: 700, height: 500 })
    })
    expect(mocks.updatePosition).toHaveBeenCalledWith('scope-1', { x: 90, y: 91 })
    expect(mocks.updateSize).toHaveBeenCalledWith('scope-1', { width: 700, height: 500 })

    view.unmount()
    vi.clearAllMocks()
    mocks.dragging = true
    const [minimized] = setup([signal()], { ...expandedState, isMinimized: true })
    const minimizedOuter = minimized.container.firstElementChild as HTMLElement
    expect(minimizedOuter).toHaveStyle({ width: '250px', height: 'auto' })
    expect(minimizedOuter.style.cursor).toBe('grabbing')
    expect(screen.getByTitle('Expand')).toBeInTheDocument()
    expect(mocks.plot).not.toHaveBeenCalled()
    expect(mocks.getResizeProps).not.toHaveBeenCalled()
  })

  it('renders signal data states', function () {
    const [view] = setup([])
    expect(screen.getByText('No data available')).toBeInTheDocument()
    expect(mocks.plot).not.toHaveBeenCalled()
    view.rerender(<PlotWindow blockId="scope-1" blockName="Scope" signals={[signal()]}
      windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    expect(mocks.plot).toHaveBeenCalledOnce()
    const single = mocks.plot.mock.lastCall?.[0] as { data: unknown[]; layout: { showlegend: boolean } }
    expect(single.data[0]).toMatchObject({ name: 'Signal', y: [1, 2, 3] })
    expect(single.layout.showlegend).toBe(false)
    const rows = Array.from({ length: 11 }, function (_unused, index) { return [index] })
    view.rerender(<PlotWindow blockId="scope-1" blockName="Scope" signals={[signal({
      times: [0], values: rows, numInputs: 12, inputNames: ['Named'],
    })]} windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    const multi = mocks.plot.mock.lastCall?.[0] as { data: unknown[]; layout: { showlegend: boolean } }
    expect(multi.data).toHaveLength(12)
    expect(multi.layout.showlegend).toBe(true)
    expect(multi.data[0]).toMatchObject({ name: 'Named' })
    expect(multi.data[1]).toMatchObject({ name: 'Input 2' })
    expect(multi.data[11]).toMatchObject({ y: [] })
    const firstTrace = multi.data[0] as { line: { color: string } }
    const wrappedTrace = multi.data[10] as { line: { color: string } }
    expect(wrappedTrace.line.color).toBe(firstTrace.line.color)

    view.rerender(<PlotWindow blockId="scope-1" blockName="Scope" signals={[signal({
      numInputs: 2, values: [4, 5, 6], inputNames: undefined,
    })]} windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    const flat = mocks.plot.mock.lastCall?.[0] as { data: unknown[] }
    expect(flat.data).toHaveLength(1)
  })

  it('preserves user axis ranges and resets to data bounds', function () {
    const [view] = setup([signal({ times: [2, 0, 1], values: [5, 1, 3] })])
    const initial = mocks.plot.mock.lastCall?.[0] as {
      layout: { xaxis: { range: number[] }; yaxis: { range: number[] } }
      onRelayout: (event: Record<string, unknown>) => void
    }
    expect(initial.layout.xaxis.range[0]).toBeLessThan(0)
    expect(initial.layout.xaxis.range[1]).toBeGreaterThan(2)
    expect(initial.layout.yaxis.range).toEqual([0.8, 5.2])
    act(function () {
      initial.onRelayout({})
      initial.onRelayout({ 'xaxis.range[0]': 10 })
      initial.onRelayout({ 'xaxis.range[0]': 10, 'xaxis.range[1]': 20 })
    })
    view.rerender(<PlotWindow blockId="scope-1" blockName="Scope"
      signals={[signal({ name: 'Updated', times: [3, 4], values: [6, 7] })]}
      windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    const xZoom = mocks.plot.mock.lastCall?.[0] as {
      layout: { xaxis: { range: number[] }; yaxis: { range: number[] } }
      onRelayout: (event: Record<string, unknown>) => void
    }
    expect(xZoom.layout.xaxis.range).toEqual([10, 20])
    expect(xZoom.layout.yaxis.range).not.toEqual([30, 40])
    act(function () {
      xZoom.onRelayout({ 'yaxis.range[0]': 30 })
      xZoom.onRelayout({ 'yaxis.range[0]': 30, 'yaxis.range[1]': 40 })
    })
    view.rerender(<PlotWindow blockId="scope-1" blockName="Scope"
      signals={[signal({ name: 'Both ranges', times: [4, 5], values: [7, 8] })]}
      windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    const bothZoomed = mocks.plot.mock.lastCall?.[0] as {
      layout: { xaxis: { range: number[] }; yaxis: { range: number[] } }
      onRelayout: (event: Record<string, unknown>) => void
    }
    expect(bothZoomed.layout.xaxis.range).toEqual([10, 20])
    expect(bothZoomed.layout.yaxis.range).toEqual([30, 40])
    act(function () { bothZoomed.onRelayout({ 'yaxis.autorange': true }) })
    view.rerender(<PlotWindow blockId="scope-1" blockName="Scope"
      signals={[signal({ name: 'Reset', times: [5, 5], values: [8, 8] })]}
      windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    const reset = mocks.plot.mock.lastCall?.[0] as {
      layout: { xaxis: { range: number[] }; yaxis: { range: number[] } }
      onRelayout: (event: Record<string, unknown>) => void
    }
    expect(reset.layout.xaxis.range).toEqual([4.9, 5.1])
    expect(reset.layout.yaxis.range).toEqual([7.9, 8.1])
    act(function () {
      reset.onRelayout({ 'yaxis.range[0]': 50, 'yaxis.range[1]': 60 })
    })
    view.rerender(<PlotWindow blockId="scope-1" blockName="Scope"
      signals={[signal({ name: 'Y only', times: [6, 7], values: [9, 10] })]}
      windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    const yZoom = mocks.plot.mock.lastCall?.[0] as {
      layout: { xaxis: { range: number[] }; yaxis: { range: number[] } }
      onRelayout: (event: Record<string, unknown>) => void
    }
    expect(yZoom.layout.xaxis.range).not.toEqual([10, 20])
    expect(yZoom.layout.yaxis.range).toEqual([50, 60])
    act(function () { yZoom.onRelayout({ 'xaxis.autorange': true }) })
  })
})
