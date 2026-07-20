import { act, fireEvent, render, screen } from '@testing-library/react'
import type { ComponentType } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { AnalysisData } from '../../types/simulation'
import type { PlotWindowState } from '../../store/uiStore'
import { BodePlotWindow } from './BodePlotWindow'
import { NyquistPlotWindow } from './NyquistPlotWindow'
import { PoleZeroMapWindow } from './PoleZeroMapWindow'
import { StepResponseWindow } from './StepResponseWindow'

const mocks = vi.hoisted(function () {
  return {
    plot: vi.fn(),
    close: vi.fn(),
    toggle: vi.fn(),
    updatePosition: vi.fn(),
    updateSize: vi.fn(),
    draggable: vi.fn(),
    getResizeProps: vi.fn(function (direction: string) {
      return { 'data-resize-direction': direction }
    }),
    dragging: false,
  }
})

type WindowProps = {
  blockId: string
  blockName: string
  data: AnalysisData
  windowState: PlotWindowState
  zIndex: number
  onFocus: () => void
}

const expandedState: PlotWindowState = {
  isOpen: true,
  isMinimized: false,
  position: { x: 12, y: 34 },
  size: { width: 640, height: 480 },
}

vi.mock('react-plotly.js', function () {
  return {
    default: function PlotStub(props: unknown) {
      mocks.plot(props)
      return null
    },
  }
})

vi.mock('../../store/uiStore', function () {
  return {
    useUIStore: function () {
      return {
        closePlotWindow: mocks.close,
        togglePlotWindowMinimized: mocks.toggle,
        updatePlotWindowPosition: mocks.updatePosition,
        updatePlotWindowSize: mocks.updateSize,
      }
    },
  }
})

vi.mock('../../hooks/useDraggableWindow', function () {
  return {
    useDraggableWindow: function (options: unknown) {
      mocks.draggable(options)
      return {
        isDragging: mocks.dragging,
        dragHandleProps: { 'data-testid': 'drag-handle' },
        getResizeHandleProps: mocks.getResizeProps,
      }
    },
  }
})

function renderWindow(Component: ComponentType<WindowProps>, data: AnalysisData,
  windowState: PlotWindowState = expandedState) {
  const onFocus = vi.fn()
  const view = render(<Component blockId="analysis-1" blockName="Plant" data={data}
    windowState={windowState} zIndex={73} onFocus={onFocus} />)
  return [view, onFocus] as const
}

describe('analysis window chrome', function () {
  beforeEach(function () {
    vi.clearAllMocks()
    mocks.dragging = false
  })

  const cases: Array<[string, ComponentType<WindowProps>, AnalysisData, number]> = [
    ['Bode', BodePlotWindow,
      { analysisType: 'bode', frequencies: [1], magnitude_db: [2], phase_deg: [3] }, 350],
    ['Nyquist', NyquistPlotWindow,
      { analysisType: 'nyquist', real: [1], imag: [2] }, 400],
    ['Pole-Zero', PoleZeroMapWindow,
      { analysisType: 'pzmap', poles: [[-1, 0]], zeros: [[0, 0]] }, 400],
    ['Step', StepResponseWindow,
      { analysisType: 'stepinfo', times: [0, 1], response: [0, 1] }, 350],
  ]

  it.each(cases)('wires the %s window chrome and drag adapters', function (_name, Component, data, minHeight) {
    const [view, onFocus] = renderWindow(Component, data)
    const outer = view.container.firstElementChild as HTMLElement
    expect(outer).toHaveStyle({ left: '12px', top: '34px', width: '640px', height: '480px', zIndex: '73' })
    expect(outer.style.cursor).toBe('default')
    fireEvent.mouseDown(outer)
    expect(onFocus).toHaveBeenCalled()
    fireEvent.click(screen.getByTitle('Minimize'))
    fireEvent.click(screen.getByTitle('Close'))
    expect(mocks.toggle).toHaveBeenCalledWith('analysis-1')
    expect(mocks.close).toHaveBeenCalledWith('analysis-1')
    expect(mocks.getResizeProps.mock.calls.map(function (call) { return call[0] }))
      .toEqual(['n', 's', 'e', 'w', 'nw', 'ne', 'sw', 'se'])

    const options = mocks.draggable.mock.calls.at(-1)?.[0] as {
      minSize: { width: number; height: number }
      onPositionChange: (position: { x: number; y: number }) => void
      onSizeChange: (size: { width: number; height: number }) => void
    }
    expect(options.minSize).toEqual({ width: 400, height: minHeight })
    act(function () {
      options.onPositionChange({ x: 90, y: 91 })
      options.onSizeChange({ width: 700, height: 500 })
    })
    expect(mocks.updatePosition).toHaveBeenCalledWith('analysis-1', { x: 90, y: 91 })
    expect(mocks.updateSize).toHaveBeenCalledWith('analysis-1', { width: 700, height: 500 })

    view.unmount()
    vi.clearAllMocks()
    mocks.dragging = true
    const [minimized] = renderWindow(Component, data, { ...expandedState, isMinimized: true })
    const minimizedOuter = minimized.container.firstElementChild as HTMLElement
    expect(minimizedOuter).toHaveStyle({ width: '250px', height: 'auto' })
    expect(minimizedOuter.style.cursor).toBe('grabbing')
    expect(screen.getByTitle('Expand')).toBeInTheDocument()
    expect(mocks.plot).not.toHaveBeenCalled()
    expect(mocks.getResizeProps).not.toHaveBeenCalled()
  })
})

describe('analysis plot transformations', function () {
  beforeEach(function () {
    vi.clearAllMocks()
    mocks.dragging = false
  })

  it('converts Bode frequencies', function () {
    const [view] = renderWindow(BodePlotWindow, {
      analysisType: 'bode', frequencies: [0.5, 2], magnitude_db: [3, 4], phase_deg: [10, 20],
      gain_margin: 1.234, phase_margin: null,
    })
    expect(mocks.plot).toHaveBeenCalledTimes(2)
    const magnitude = mocks.plot.mock.calls[0][0] as { data: unknown[] }
    const phase = mocks.plot.mock.calls[1][0] as { data: unknown[] }
    expect(magnitude.data[0]).toMatchObject({ x: [Math.PI, 4 * Math.PI], y: [3, 4], name: 'Magnitude' })
    expect(phase.data[0]).toMatchObject({ x: [Math.PI, 4 * Math.PI], y: [10, 20], name: 'Phase' })
    expect(screen.getByText('Gain Margin: 1.23 dB')).toBeInTheDocument()
    expect(screen.getByText('Phase Margin: N/A')).toBeInTheDocument()
    view.rerender(<BodePlotWindow blockId="analysis-1" blockName="Plant" data={{
      analysisType: 'bode', frequencies: [], magnitude_db: [],
    }} windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    expect(screen.getAllByText(/Margin: N\/A/)).toHaveLength(2)
    view.rerender(<BodePlotWindow blockId="analysis-1" blockName="Plant" data={{
      analysisType: 'bode', frequencies: [],
    }} windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    view.rerender(<BodePlotWindow blockId="analysis-1" blockName="Plant" data={{
      analysisType: 'bode',
    }} windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    const last = mocks.plot.mock.lastCall?.[0] as { data: unknown[] }
    expect(last.data).toEqual([])
  })

  it('builds Nyquist curves and reports stability', function () {
    const [view] = renderWindow(NyquistPlotWindow, {
      analysisType: 'nyquist', real: [1, 2], imag: [2, 3], encirclements: 0,
    })
    const first = mocks.plot.mock.calls[0][0] as { data: unknown[] }
    expect(first.data).toHaveLength(3)
    expect(screen.getByText('Stable (0 encirclements)')).toBeInTheDocument()

    view.rerender(<NyquistPlotWindow blockId="analysis-1" blockName="Plant" data={{
      analysisType: 'nyquist', real: [], encirclements: 2,
    }} windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    expect(screen.getByText('Encirclements: 2')).toBeInTheDocument()
    view.rerender(<NyquistPlotWindow blockId="analysis-1" blockName="Plant" data={{
      analysisType: 'nyquist', encirclements: undefined,
    }} windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    expect(screen.getByText('N/A')).toBeInTheDocument()
    const last = mocks.plot.mock.lastCall?.[0] as { data: unknown[] }
    expect(last.data).toEqual([])
  })

  it('separates poles and zeros', function () {
    const negative = Math.cos(Math.PI)
    const [view] = renderWindow(PoleZeroMapWindow, {
      analysisType: 'pzmap', poles: [[negative, 1], [3, negative]], zeros: [[0, 2]],
      is_stable: false, dominant_pole: [negative, 1],
    })
    expect(mocks.plot).toHaveBeenCalled()
    const first = mocks.plot.mock.calls[0][0] as { data: unknown[] }
    expect(first.data).toHaveLength(3)
    expect(screen.getByText('Unstable (poles in RHP)')).toBeInTheDocument()
    view.rerender(<PoleZeroMapWindow blockId="analysis-1" blockName="Plant" data={{
      analysisType: 'pzmap', poles: [[negative, 0]], zeros: [], is_stable: true,
      dominant_pole: [2, 0],
    }} windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    expect(screen.getByText('Stable (all poles in LHP)')).toBeInTheDocument()
    expect(screen.getByText('Dominant: 2.000')).toBeInTheDocument()
    view.rerender(<PoleZeroMapWindow blockId="analysis-1" blockName="Plant" data={{
      analysisType: 'pzmap', poles: [[1, 0]], dominant_pole: [negative, negative],
    }} windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    view.rerender(<PoleZeroMapWindow blockId="analysis-1" blockName="Plant" data={{
      analysisType: 'pzmap', poles: [], dominant_pole: null,
    }} windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    expect(screen.getByText('N/A')).toBeInTheDocument()
    const last = mocks.plot.mock.lastCall?.[0] as { data: unknown[] }
    expect(last.data).toEqual([])
  })

  it('adds optional step response guides', function () {
    const [view] = renderWindow(StepResponseWindow, {
      analysisType: 'stepinfo', times: [0, 2], response: [0, 1.2], steady_state_value: 1,
      peak_time: 1, peak_value: 1.2, overshoot_percent: 20,
      rise_time: 0.5, settling_time: null,
    })
    expect(mocks.plot).toHaveBeenCalled()
    const first = mocks.plot.mock.calls[0][0] as { data: unknown[] }
    expect(first.data).toHaveLength(3)
    expect(screen.getByText('Rise Time: 0.500s')).toBeInTheDocument()
    expect(screen.getByText('Settling Time: N/A')).toBeInTheDocument()
    expect(screen.getByText('Peak Value: 1.200')).toBeInTheDocument()
    const incompletePeaks: AnalysisData[] = [
      { analysisType: 'stepinfo', times: [0], response: [0], steady_state_value: null, peak_time: null },
      { analysisType: 'stepinfo', times: [0], response: [0], steady_state_value: undefined, peak_time: undefined },
      { analysisType: 'stepinfo', times: [0], response: [0], peak_time: 1, peak_value: null },
      { analysisType: 'stepinfo', times: [0], response: [0], peak_time: 1, peak_value: undefined },
      { analysisType: 'stepinfo', times: [0], response: [0], peak_time: 1, peak_value: 2, overshoot_percent: null },
      { analysisType: 'stepinfo', times: [0], response: [0], peak_time: 1, peak_value: 2, overshoot_percent: undefined },
      { analysisType: 'stepinfo', times: [0], response: [0], peak_time: 1, peak_value: 2, overshoot_percent: 0.5 },
    ]
    for (const data of incompletePeaks) {
      view.rerender(<StepResponseWindow blockId="analysis-1" blockName="Plant" data={data}
        windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
      const plot = mocks.plot.mock.lastCall?.[0] as { data: unknown[] }
      expect(plot.data).toHaveLength(1)
    }
    view.rerender(<StepResponseWindow blockId="analysis-1" blockName="Plant" data={{
      analysisType: 'stepinfo', times: [],
    }} windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    view.rerender(<StepResponseWindow blockId="analysis-1" blockName="Plant" data={{
      analysisType: 'stepinfo',
    }} windowState={expandedState} zIndex={73} onFocus={vi.fn()} />)
    const last = mocks.plot.mock.lastCall?.[0] as { data: unknown[] }
    expect(last.data).toEqual([])
  })
})
