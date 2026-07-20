import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Model } from '../types/model'
import { useSimulationStore } from '../store/simulationStore'
import {
  getSimulationErrorMessage,
  useSimulationControls,
} from './useSimulationControls'

const apiMocks = vi.hoisted(function () {
  return {
    startSimulation: vi.fn(),
    stopSimulation: vi.fn(),
    pauseSimulation: vi.fn(),
    resumeSimulation: vi.fn(),
    resetSimulation: vi.fn(),
    getSimulationStatus: vi.fn(),
    getSimulationResults: vi.fn(),
    initStepMode: vi.fn(),
    stepForward: vi.fn(),
    stepBackward: vi.fn(),
    enterStepMode: vi.fn(),
    continueFromStepMode: vi.fn(),
  }
})

const toastMocks = vi.hoisted(function () {
  return {
    success: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  }
})

vi.mock('../api/client', function () { return { api: apiMocks } })
vi.mock('../components/Toast/Toast', function () { return { toast: toastMocks } })
vi.mock('../store/simulationStore', function () { return { useSimulationStore: vi.fn() } })

const mockedUseSimulationStore = vi.mocked(useSimulationStore)

const model = {
  id: 'model-1',
  metadata: {
    name: 'Test',
    description: '',
    author: '',
    createdAt: '2026-01-01',
    modifiedAt: '2026-01-01',
    version: '1.0.0',
  },
  blocks: [],
  connections: [],
  simulationConfig: {
    solver: 'rk4' as const,
    startTime: 0,
    stopTime: 1,
    stepSize: 0.1,
  },
} as Model

const results = {
  signals: [],
  statistics: { totalSteps: 10, executionTime: 1, finalTime: 1 },
}

function makeStore(status = 'idle', stepModeActive = false) {
  return {
    state: { status, currentTime: 0, progress: 0 },
    results: null,
    wsConnected: false,
    stepModeActive,
    stepHistorySize: stepModeActive ? 2 : 0,
    setStatus: vi.fn(),
    setProgress: vi.fn(),
    setError: vi.fn(),
    clearError: vi.fn(),
    addSignalData: vi.fn(),
    appendSignalData: vi.fn(),
    setResults: vi.fn(),
    clearResults: vi.fn(),
    setWsConnected: vi.fn(),
    setStepModeActive: vi.fn(),
    setStepHistorySize: vi.fn(),
    reset: vi.fn(),
  }
}

function renderControls(
  store = makeStore(),
  activeModel: Model | null = model
) {
  mockedUseSimulationStore.mockReturnValue(store as never)
  const onInteractionEnd = vi.fn()
  const hook = renderHook(function () {
    return useSimulationControls({ model: activeModel, onInteractionEnd })
  })
  return { ...hook, store, onInteractionEnd }
}

describe('getSimulationErrorMessage', function () {
  it('prefers API details, then messages, then the fallback', function () {
    expect(getSimulationErrorMessage({
      response: { data: { detail: 'specific detail' } },
      message: 'generic message',
    }, 'fallback')).toBe('specific detail')
    expect(getSimulationErrorMessage({ message: 'generic message' }, 'fallback'))
      .toBe('generic message')
    expect(getSimulationErrorMessage({}, 'fallback')).toBe('fallback')
    expect(getSimulationErrorMessage(null, 'fallback')).toBe('fallback')
  })
})

describe('useSimulationControls', function () {
  beforeEach(function () {
    vi.clearAllMocks()
  })

  afterEach(function () {
    vi.useRealTimers()
  })

  it('returns store state and does nothing when run has no model', async function () {
    const view = renderControls(makeStore('running'), null)
    expect(view.result.current.simState.status).toBe('running')
    expect(view.result.current.isRunning).toBe(true)
    expect(view.result.current.isPaused).toBe(false)
    expect(view.result.current.isCompleted).toBe(false)

    await act(async function () { await view.result.current.handleRun() })
    expect(apiMocks.startSimulation).not.toHaveBeenCalled()
    expect(view.onInteractionEnd).not.toHaveBeenCalled()
  })

  it('reports a start failure and closes the mobile interaction', async function () {
    const store = makeStore()
    const view = renderControls(store)
    apiMocks.startSimulation.mockRejectedValue({
      response: { data: { detail: 'compile failed' } },
    })

    await act(async function () { await view.result.current.handleRun() })

    expect(store.clearResults).toHaveBeenCalledOnce()
    expect(store.setStatus).toHaveBeenCalledWith('running')
    expect(store.setError).toHaveBeenCalledWith('compile failed')
    expect(view.onInteractionEnd).toHaveBeenCalledOnce()
  })

  it('polls a run through completion and stores its results', async function () {
    vi.useFakeTimers()
    const store = makeStore()
    const view = renderControls(store)
    apiMocks.startSimulation.mockResolvedValue({})
    apiMocks.getSimulationStatus.mockResolvedValue({
      status: 'completed',
      progress: 1,
      currentTime: 1,
    })
    apiMocks.getSimulationResults.mockResolvedValue(results)

    await act(async function () { await view.result.current.handleRun() })
    await act(async function () { await vi.advanceTimersByTimeAsync(100) })

    expect(store.setProgress).toHaveBeenCalledWith(1, 1)
    expect(store.setStatus).toHaveBeenLastCalledWith('completed')
    expect(store.setResults).toHaveBeenCalledWith(results)
    expect(vi.getTimerCount()).toBe(0)
  })

  it('handles error, idle, active, and failed polling statuses', async function () {
    vi.useFakeTimers()
    const store = makeStore()
    const view = renderControls(store)
    apiMocks.startSimulation.mockResolvedValue({})

    apiMocks.getSimulationStatus.mockResolvedValueOnce({
      status: 'running',
      progress: 0,
    }).mockResolvedValueOnce({
      status: 'error',
      progress: 0.5,
    })
    await act(async function () { await view.result.current.handleRun() })
    await act(async function () { await vi.advanceTimersByTimeAsync(200) })
    expect(store.setProgress).toHaveBeenNthCalledWith(1, 0, 0)
    expect(store.setError).toHaveBeenCalledWith('Simulation failed')
    expect(toastMocks.warning).toHaveBeenCalledWith('Simulation Error', 'Simulation failed')

    apiMocks.getSimulationStatus.mockResolvedValueOnce({
      status: 'idle',
      progress: 0,
    })
    await act(async function () { await view.result.current.handleRun() })
    await act(async function () { await vi.advanceTimersByTimeAsync(100) })
    expect(store.setStatus).toHaveBeenCalledWith('idle')

    apiMocks.getSimulationStatus.mockRejectedValueOnce(new Error('network'))
      .mockResolvedValueOnce({ status: 'idle', progress: 0 })
    await act(async function () { await view.result.current.handleRun() })
    await act(async function () { await vi.advanceTimersByTimeAsync(200) })
    expect(apiMocks.getSimulationStatus).toHaveBeenCalledTimes(5)
  })

  it('stops successfully and tolerates a stop failure', async function () {
    const store = makeStore('running')
    const view = renderControls(store)
    apiMocks.stopSimulation.mockResolvedValueOnce({ success: true })

    await act(async function () { await view.result.current.handleStop() })
    expect(store.setStatus).toHaveBeenCalledWith('idle')
    expect(store.setStepModeActive).toHaveBeenCalledWith(false)

    apiMocks.stopSimulation.mockRejectedValueOnce(new Error('stop failed'))
    await act(async function () { await view.result.current.handleStop() })
    expect(view.onInteractionEnd).toHaveBeenCalledTimes(2)
  })

  it('resets successful simulations and leaves unsuccessful responses unchanged', async function () {
    const store = makeStore('completed', true)
    const view = renderControls(store)
    expect(view.result.current.isCompleted).toBe(true)
    expect(view.result.current.stepModeActive).toBe(true)
    expect(view.result.current.stepHistorySize).toBe(2)
    apiMocks.resetSimulation.mockResolvedValueOnce({ success: true })

    await act(async function () { await view.result.current.handleReset() })
    expect(store.clearResults).toHaveBeenCalledOnce()
    expect(store.setStepHistorySize).toHaveBeenCalledWith(0)
    expect(store.setProgress).toHaveBeenCalledWith(0, 0)
    expect(toastMocks.info).toHaveBeenCalledWith('Reset', 'Simulation reset to initial state')

    vi.clearAllMocks()
    apiMocks.resetSimulation.mockResolvedValueOnce({ success: false })
    await act(async function () { await view.result.current.handleReset() })
    expect(store.clearResults).not.toHaveBeenCalled()
    expect(view.onInteractionEnd).toHaveBeenCalledOnce()
  })

  it('restores a safe idle state when reset fails', async function () {
    const store = makeStore('error', true)
    const view = renderControls(store)
    apiMocks.resetSimulation.mockRejectedValue(new Error('missing runner'))

    await act(async function () { await view.result.current.handleReset() })

    expect(store.clearResults).toHaveBeenCalledOnce()
    expect(store.setStatus).toHaveBeenCalledWith('idle')
    expect(store.setStepModeActive).toHaveBeenCalledWith(false)
    expect(store.setStepHistorySize).toHaveBeenCalledWith(0)
    expect(store.setProgress).toHaveBeenCalledWith(0, 0)
  })

  it('pauses and captures partial results', async function () {
    const store = makeStore('running')
    const view = renderControls(store)
    apiMocks.pauseSimulation.mockResolvedValue({ success: true })
    apiMocks.getSimulationResults.mockResolvedValue(results)

    await act(async function () { await view.result.current.handlePause() })

    expect(store.setStatus).toHaveBeenCalledWith('paused')
    expect(store.setResults).toHaveBeenCalledWith(results)
    expect(view.onInteractionEnd).toHaveBeenCalledOnce()
  })

  it('tolerates failures while pausing or fetching partial results', async function () {
    const store = makeStore('running')
    const view = renderControls(store)
    apiMocks.pauseSimulation.mockResolvedValueOnce({ success: true })
    apiMocks.getSimulationResults.mockRejectedValueOnce(new Error('no partial results'))
    await act(async function () { await view.result.current.handlePause() })
    expect(store.setStatus).toHaveBeenCalledWith('paused')
    expect(store.setResults).not.toHaveBeenCalled()

    apiMocks.pauseSimulation.mockRejectedValueOnce(new Error('pause failed'))
    await act(async function () { await view.result.current.handlePause() })
    expect(view.onInteractionEnd).toHaveBeenCalledTimes(2)
  })

  it('resumes a normally paused simulation and tolerates failure', async function () {
    const store = makeStore('paused')
    const view = renderControls(store)
    expect(view.result.current.isPaused).toBe(true)
    apiMocks.resumeSimulation.mockResolvedValueOnce({ success: true })
    await act(async function () { await view.result.current.handleResume() })
    expect(store.setStatus).toHaveBeenCalledWith('running')

    apiMocks.resumeSimulation.mockRejectedValueOnce(new Error('resume failed'))
    await act(async function () { await view.result.current.handleResume() })
    expect(view.onInteractionEnd).toHaveBeenCalledTimes(2)
  })

  it('continues from step mode, polls, and restores pause state on failure', async function () {
    vi.useFakeTimers()
    const store = makeStore('paused', true)
    const view = renderControls(store)
    apiMocks.continueFromStepMode.mockResolvedValueOnce({ success: true })
    apiMocks.getSimulationStatus.mockResolvedValueOnce({ status: 'idle', progress: 0 })

    await act(async function () { await view.result.current.handleResume() })
    expect(store.setStepModeActive).toHaveBeenCalledWith(false)
    expect(store.setStatus).toHaveBeenCalledWith('running')
    await act(async function () { await vi.advanceTimersByTimeAsync(100) })
    expect(store.setStatus).toHaveBeenLastCalledWith('idle')

    apiMocks.continueFromStepMode.mockRejectedValueOnce(new Error('continue failed'))
    await act(async function () { await view.result.current.handleResume() })
    expect(store.setStepModeActive).toHaveBeenLastCalledWith(true)
    expect(store.setStatus).toHaveBeenLastCalledWith('paused')
  })

  it('initializes step mode from an idle simulation', async function () {
    const store = makeStore()
    const view = renderControls(store)
    apiMocks.initStepMode.mockResolvedValue({ success: true, currentTime: 0 })

    await act(async function () { await view.result.current.handleStepForward() })

    expect(store.clearResults).toHaveBeenCalledOnce()
    expect(store.setStatus).toHaveBeenNthCalledWith(1, 'compiling')
    expect(store.setStatus).toHaveBeenNthCalledWith(2, 'paused')
    expect(store.setStepModeActive).toHaveBeenCalledWith(true)
    expect(store.setStepHistorySize).toHaveBeenCalledWith(1)
    expect(store.setProgress).toHaveBeenCalledWith(0, 0)
    expect(apiMocks.stepForward).not.toHaveBeenCalled()
  })

  it('handles unavailable models, unsuccessful initialization, and initialization errors', async function () {
    const noModel = renderControls(makeStore(), null)
    await act(async function () { await noModel.result.current.handleStepForward() })
    expect(apiMocks.initStepMode).not.toHaveBeenCalled()

    const store = makeStore()
    const view = renderControls(store)
    apiMocks.initStepMode.mockResolvedValueOnce({ success: false })
    await act(async function () { await view.result.current.handleStepForward() })
    expect(store.setStepModeActive).not.toHaveBeenCalled()

    apiMocks.initStepMode.mockRejectedValueOnce({ message: 'init failed' })
    await act(async function () { await view.result.current.handleStepForward() })
    expect(store.setStatus).toHaveBeenLastCalledWith('error')
    expect(store.setStepModeActive).toHaveBeenCalledWith(false)
    expect(store.setError).toHaveBeenCalledWith('init failed')
  })

  it('enters step mode from pause and advances immediately', async function () {
    const store = makeStore('paused')
    const view = renderControls(store)
    apiMocks.enterStepMode.mockResolvedValue({
      success: true,
      currentTime: 0.4,
      progress: 0.4,
      historySize: 3,
    })
    apiMocks.stepForward.mockResolvedValue({
      success: true,
      currentTime: 0.5,
      progress: 0.5,
      historySize: 4,
      completed: false,
    })
    apiMocks.getSimulationResults.mockResolvedValue(results)

    await act(async function () { await view.result.current.handleStepForward() })

    expect(store.setStepModeActive).toHaveBeenCalledWith(true)
    expect(store.setProgress).toHaveBeenNthCalledWith(1, 0.4, 0.4)
    expect(store.setProgress).toHaveBeenNthCalledWith(2, 0.5, 0.5)
    expect(store.setStepHistorySize).toHaveBeenLastCalledWith(4)
    expect(store.setResults).toHaveBeenCalledWith(results)
  })

  it('returns when entering step mode from pause fails', async function () {
    const store = makeStore('paused')
    const view = renderControls(store)
    apiMocks.enterStepMode.mockRejectedValue(new Error('enter failed'))

    await act(async function () { await view.result.current.handleStepForward() })

    expect(apiMocks.stepForward).not.toHaveBeenCalled()
  })

  it('advances an active step simulation through completion', async function () {
    const store = makeStore('paused', true)
    const view = renderControls(store)
    apiMocks.stepForward.mockResolvedValue({
      success: true,
      currentTime: 1,
      progress: 1,
      historySize: 10,
      completed: true,
    })
    apiMocks.getSimulationResults.mockResolvedValue(results)

    await act(async function () { await view.result.current.handleStepForward() })

    expect(store.setStatus).toHaveBeenCalledWith('completed')
    expect(toastMocks.info).toHaveBeenCalledWith('Step Mode', 'Simulation completed.')
  })

  it('tolerates unsuccessful steps, result failures, and step failures', async function () {
    const store = makeStore('paused', true)
    const view = renderControls(store)
    apiMocks.stepForward.mockResolvedValueOnce({ success: false })
    await act(async function () { await view.result.current.handleStepForward() })
    expect(store.setProgress).not.toHaveBeenCalled()

    apiMocks.stepForward.mockResolvedValueOnce({
      success: true,
      currentTime: 0.5,
      progress: 0.5,
      historySize: 2,
      completed: false,
    })
    apiMocks.getSimulationResults.mockRejectedValueOnce(new Error('results failed'))
    await act(async function () { await view.result.current.handleStepForward() })
    expect(store.setProgress).toHaveBeenCalledWith(0.5, 0.5)

    apiMocks.stepForward.mockRejectedValueOnce(new Error('step failed'))
    await act(async function () { await view.result.current.handleStepForward() })
    expect(apiMocks.stepForward).toHaveBeenCalledTimes(3)
  })

  it('continues to a step when entering paused step mode returns unsuccessful', async function () {
    const store = makeStore('paused')
    const view = renderControls(store)
    apiMocks.enterStepMode.mockResolvedValue({ success: false })
    apiMocks.stepForward.mockResolvedValue({ success: false })

    await act(async function () { await view.result.current.handleStepForward() })

    expect(apiMocks.stepForward).toHaveBeenCalledWith(1)
    expect(store.setStepModeActive).not.toHaveBeenCalled()
  })

  it('steps backward and refreshes results', async function () {
    const store = makeStore('paused', true)
    const view = renderControls(store)
    apiMocks.stepBackward.mockResolvedValue({
      success: true,
      currentTime: 0.4,
      progress: 0.4,
      historySize: 2,
    })
    apiMocks.getSimulationResults.mockResolvedValue(results)

    await act(async function () { await view.result.current.handleStepBackward() })

    expect(store.setProgress).toHaveBeenCalledWith(0.4, 0.4)
    expect(store.setStepHistorySize).toHaveBeenCalledWith(2)
    expect(store.setResults).toHaveBeenCalledWith(results)
  })

  it('handles every non-successful backward-step outcome', async function () {
    const inactive = renderControls(makeStore('paused'))
    await act(async function () { await inactive.result.current.handleStepBackward() })
    expect(apiMocks.stepBackward).not.toHaveBeenCalled()

    const store = makeStore('paused', true)
    const view = renderControls(store)
    apiMocks.stepBackward.mockResolvedValueOnce({ success: false })
    await act(async function () { await view.result.current.handleStepBackward() })
    expect(toastMocks.info).toHaveBeenCalledWith(
      'Step Mode',
      'Cannot step backward - at beginning.'
    )

    apiMocks.stepBackward.mockResolvedValueOnce({
      success: true,
      currentTime: 0.2,
      progress: 0.2,
      historySize: 1,
    })
    apiMocks.getSimulationResults.mockRejectedValueOnce(new Error('results failed'))
    await act(async function () { await view.result.current.handleStepBackward() })
    expect(store.setProgress).toHaveBeenCalledWith(0.2, 0.2)

    apiMocks.stepBackward.mockRejectedValueOnce(new Error('back failed'))
    await act(async function () { await view.result.current.handleStepBackward() })
    expect(apiMocks.stepBackward).toHaveBeenCalledTimes(3)
  })
})
