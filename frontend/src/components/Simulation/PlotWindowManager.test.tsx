import { act, render } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { AnalysisData, SimulationResults } from '../../types/simulation'
import type { BlockInstance } from '../../types/block'
import type { PlotWindowState } from '../../store/uiStore'
import { PlotWindowManager } from './PlotWindowManager'

const mocks = vi.hoisted(function () {
  return {
    open: vi.fn(), closeAll: vi.fn(), plot: vi.fn(), scope3d: vi.fn(),
    bode: vi.fn(), nyquist: vi.fn(), pzmap: vi.fn(), step: vi.fn(),
  }
})

const stores = vi.hoisted(function () {
  return {
    simulation: { results: null as unknown, state: { status: 'idle' }, stepModeActive: false },
    model: { model: null as unknown },
    ui: { plotWindows: {} as unknown },
  }
})

vi.mock('../../store/simulationStore', function () {
  return { useSimulationStore: function () { return stores.simulation } }
})
vi.mock('../../store/modelStore', function () {
  return { useModelStore: function () { return stores.model } }
})
vi.mock('../../store/uiStore', function () {
  return { useUIStore: function () { return {
    plotWindows: stores.ui.plotWindows,
    openPlotWindow: mocks.open,
    closeAllPlotWindows: mocks.closeAll,
  } } }
})

vi.mock('./PlotWindow', function () {
  return { PlotWindow: function (props: unknown) { mocks.plot(props); return null } }
})
vi.mock('./Scope3DWindow', function () {
  return { Scope3DWindow: function (props: unknown) { mocks.scope3d(props); return null } }
})
vi.mock('../Analysis', function () {
  return {
    BodePlotWindow: function (props: unknown) { mocks.bode(props); return null },
    NyquistPlotWindow: function (props: unknown) { mocks.nyquist(props); return null },
    PoleZeroMapWindow: function (props: unknown) { mocks.pzmap(props); return null },
    StepResponseWindow: function (props: unknown) { mocks.step(props); return null },
  }
})

function block(id: string, type: string, name: string, children?: BlockInstance[]): BlockInstance {
  return {
    id, type, name, position: { x: 0, y: 0 }, parameters: {},
    inputPorts: [], outputPorts: [], children,
  }
}

function windowState(isOpen = true): PlotWindowState {
  return {
    isOpen, isMinimized: false,
    position: { x: 20, y: 100 }, size: { width: 450, height: 280 },
  }
}

function results(
  signals: SimulationResults['signals'] = [],
  analyses?: Record<string, AnalysisData>,
): SimulationResults {
  return {
    signals, analyses,
    statistics: { totalSteps: 1, executionTime: 1, finalTime: 1 },
  }
}

function scopeSignal(blockId: string, overrides: Partial<SimulationResults['signals'][number]> = {}) {
  return {
    blockId, portId: 'input', name: 'Signal', times: [0, 1], values: [1, 2],
    ...overrides,
  }
}

function childProps(mock: typeof mocks.plot, blockId: string) {
  return mock.mock.calls.map(function (call) { return call[0] as {
    blockId: string
    blockName: string
    zIndex: number
    onFocus: () => void
    signals?: unknown[]
  } }).reverse().find(function (props) { return props.blockId === blockId })
}

describe('PlotWindowManager', function () {
  beforeEach(function () {
    vi.clearAllMocks()
    stores.simulation.results = null
    stores.simulation.state = { status: 'idle' }
    stores.simulation.stepModeActive = false
    stores.model.model = null
    stores.ui.plotWindows = {}
    vi.spyOn(console, 'log').mockImplementation(function () {})
  })

  it('clears windows only for an idle simulation without results', function () {
    const view = render(<PlotWindowManager />)
    expect(view.container).toBeEmptyDOMElement()
    expect(mocks.closeAll).toHaveBeenCalledOnce()

    mocks.closeAll.mockClear()
    stores.simulation.results = results()
    view.rerender(<PlotWindowManager />)
    expect(mocks.closeAll).not.toHaveBeenCalled()

    stores.simulation.results = null
    stores.simulation.state = { status: 'running' }
    view.rerender(<PlotWindowManager />)
    expect(mocks.closeAll).not.toHaveBeenCalled()
  })

  it('discovers nested scopes and analyses and opens them in order', function () {
    const nestedScope = block('nested-scope', 'scope', 'Nested Scope')
    const nestedBode = block('nested-bode', 'bode_plot', 'Nested Bode')
    const inner = block('inner', 'subsystem', 'Inner', [nestedScope, nestedBode])
    const outer = block('outer', 'subsystem', 'Outer', [inner])
    stores.model.model = { blocks: [
      block('root-scope', 'scope', 'Root Scope'),
      block('xy', 'xy_graph', ''),
      block('three-d', 'scope_3d', 'Three D'),
      block('ordinary', 'gain', 'Gain'),
      block('empty-subsystem', 'subsystem', 'Empty'),
      outer,
      block('nyquist', 'nyquist_plot', 'Nyquist'),
      block('pz', 'pole_zero_map', 'PZ'),
      block('step', 'step_info', 'Step'),
    ] }
    stores.simulation.results = results([
      scopeSignal('root-scope'), scopeSignal('xy'),
      scopeSignal('three-d', { is3D: true, x: [1], y: [2], z: [3] }),
      scopeSignal('outer__inner__nested-scope', { x: [4], y: [5], z: [6] }),
      scopeSignal('unmatched'),
    ], {
      'outer__inner__nested-bode': { analysisType: 'bode' },
      nyquist: { analysisType: 'nyquist' },
      pz: { analysisType: 'pzmap' },
      step: { analysisType: 'stepinfo' },
      unmatched: { analysisType: 'bode' },
    })
    stores.simulation.state = { status: 'completed' }
    render(<PlotWindowManager />)
    expect(mocks.open).toHaveBeenCalledTimes(8)
    expect(mocks.open).toHaveBeenNthCalledWith(1, 'root-scope', { x: 20, y: 100 }, undefined)
    expect(mocks.open).toHaveBeenNthCalledWith(3, 'three-d', { x: 100, y: 180 }, { width: 500, height: 450 })
    expect(mocks.open).toHaveBeenNthCalledWith(4, 'outer__inner__nested-scope',
      { x: 140, y: 220 }, { width: 500, height: 450 })
    expect(mocks.open).toHaveBeenNthCalledWith(8, 'step', { x: 300, y: 380 })
  })

  it('opens analysis-only results while paused or stepping', function () {
    stores.model.model = { blocks: [block('bode', 'bode_plot', 'Bode')] }
    stores.simulation.results = results([], { bode: { analysisType: 'bode' } })
    stores.simulation.state = { status: 'paused' }
    const view = render(<PlotWindowManager />)
    expect(mocks.open).toHaveBeenCalledWith('bode', { x: 20, y: 100 })

    mocks.open.mockClear()
    stores.simulation.state = { status: 'running' }
    stores.simulation.stepModeActive = true
    view.rerender(<PlotWindowManager />)
    expect(mocks.open).toHaveBeenCalledWith('bode', { x: 20, y: 100 })

    mocks.open.mockClear()
    stores.simulation.results = null
    view.rerender(<PlotWindowManager />)
    expect(mocks.open).not.toHaveBeenCalled()
  })

  it('does not reopen an existing scope window', function () {
    stores.model.model = { blocks: [block('scope', 'scope', 'Scope')] }
    stores.simulation.results = results([scopeSignal('scope')])
    stores.simulation.state = { status: 'completed' }
    stores.ui.plotWindows = { scope: windowState() }
    render(<PlotWindowManager />)
    expect(mocks.open).not.toHaveBeenCalled()
    expect(mocks.plot).toHaveBeenCalled()
  })

  it('renders every child window type and fallback', function () {
    const nested = block('nested', 'scope_3d', 'Nested 3D')
    const inner = block('inner', 'subsystem', 'Inner', [nested])
    const outer = block('outer', 'subsystem', 'Outer', [inner])
    stores.model.model = { blocks: [
      block('scope', 'scope', 'Scope'),
      block('no-signal', 'scope', 'No Signal'),
      block('partial-y', 'scope', 'Partial Y'),
      block('partial-z', 'scope', 'Partial Z'),
      outer,
      block('bode', 'bode_plot', 'Bode'),
      block('nyquist', 'nyquist_plot', 'Nyquist'),
      block('pz', 'pole_zero_map', 'PZ'),
      block('step', 'step_info', 'Step'),
      block('unknown', 'bode_plot', 'Unknown'),
      block('missing-analysis', 'bode_plot', 'Missing'),
      block('empty-analysis', 'bode_plot', ''),
    ] }
    stores.simulation.results = results([
      scopeSignal('scope'),
      scopeSignal('partial-y', { x: [1], y: undefined, z: undefined }),
      scopeSignal('partial-z', { x: [1], y: [2], z: undefined }),
      scopeSignal('outer__inner__nested', { is3D: true, x: [1], y: [2], z: [3] }),
    ], {
      bode: { analysisType: 'bode' },
      nyquist: { analysisType: 'nyquist' },
      pz: { analysisType: 'pzmap' },
      step: { analysisType: 'stepinfo' },
      unknown: { analysisType: 'unsupported' as AnalysisData['analysisType'] },
      'empty-analysis': { analysisType: 'bode' },
    })
    stores.simulation.state = { status: 'completed' }
    const ids = [
      'scope', 'partial-y', 'partial-z', 'outer__inner__nested',
      'bode', 'nyquist', 'pz', 'step', 'unknown', 'empty-analysis', 'orphan',
    ]
    stores.ui.plotWindows = Object.fromEntries(ids.map(function (id) { return [id, windowState()] }))
    stores.ui.plotWindows = {
      ...(stores.ui.plotWindows as Record<string, PlotWindowState>),
      closed: windowState(false),
    }
    render(<PlotWindowManager />)
    expect(mocks.plot).toHaveBeenCalled()
    expect(mocks.scope3d).toHaveBeenCalled()
    expect(mocks.bode).toHaveBeenCalled()
    expect(mocks.nyquist).toHaveBeenCalled()
    expect(mocks.pzmap).toHaveBeenCalled()
    expect(mocks.step).toHaveBeenCalled()
    expect(childProps(mocks.scope3d, 'outer__inner__nested')?.blockName)
      .toBe('Outer/Inner/Nested 3D')
    expect(childProps(mocks.bode, 'empty-analysis')?.blockName).toBe('bode_plot')
    expect(childProps(mocks.plot, 'orphan')).toMatchObject({
      blockName: 'Plot', signals: [],
    })
    expect(childProps(mocks.plot, 'closed')).toBeUndefined()

    const scopeBefore = childProps(mocks.plot, 'scope')
    const bodeBefore = childProps(mocks.bode, 'bode')
    expect(scopeBefore).toBeDefined()
    expect(bodeBefore).toBeDefined()
    act(function () {
      bodeBefore?.onFocus()
      childProps(mocks.scope3d, 'outer__inner__nested')?.onFocus()
      scopeBefore?.onFocus()
    })
    const scopeAfter = childProps(mocks.plot, 'scope')
    const bodeAfter = childProps(mocks.bode, 'bode')
    expect(scopeAfter?.zIndex).toBeGreaterThan(bodeAfter?.zIndex ?? 0)
  })
})
