import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { SimulationWebSocket, api } from './client'
import axios from 'axios'
import type { Model } from '../types/model'
import type { SimulationConfig } from '../types/simulation'

const branchCase = it

// Mock axios
vi.mock('axios', () => {
  const mockAxiosInstance = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
    },
  }
})

branchCase('targets every session-specific simulation control', async function () {
  vi.clearAllMocks()
  const response = { data: { success: true } }
  mockAxiosInstance.post.mockResolvedValue(response)
  mockAxiosInstance.get.mockResolvedValue(response)
  const target = { params: { sessionId: 'target-session' } }

  await api.resetSimulation({ sessionId: 'target-session' })
  await api.pauseSimulation({ sessionId: 'target-session' })
  await api.resumeSimulation({ sessionId: 'target-session' })
  await api.getSimulationResults({ sessionId: 'target-session' })
  await api.stepBackward(2, { sessionId: 'target-session' })
  await api.resetStepMode({ sessionId: 'target-session' })
  await api.continueFromStepMode({ sessionId: 'target-session' })
  await api.enterStepMode({ sessionId: 'target-session' })

  expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/reset', undefined, target)
  expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/pause', undefined, target)
  expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/resume', undefined, target)
  expect(mockAxiosInstance.get).toHaveBeenCalledWith('/simulate/results', target)
  expect(mockAxiosInstance.post).toHaveBeenCalledWith(
    '/simulate/step/backward',
    { numSteps: 2 },
    target,
  )
  expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/step/reset', undefined, target)
  expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/step/continue', undefined, target)
  expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/step/enter', undefined, target)
})

branchCase('preserves documentation responses through the configured transformers', async function () {
  vi.clearAllMocks()
  mockAxiosInstance.get.mockResolvedValue({ data: 'documentation' })

  await api.getProjectReadme()
  await api.getExamplesReadme()

  const projectConfig = mockAxiosInstance.get.mock.calls[0][1]
  const examplesConfig = mockAxiosInstance.get.mock.calls[1][1]
  expect(projectConfig.transformResponse[0]('# project')).toBe('# project')
  expect(examplesConfig.transformResponse[0]('# examples')).toBe('# examples')
})

// Get the mocked axios instance
const mockAxiosInstance = axios.create() as unknown as {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  put: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

const createMockModel = (overrides: Partial<Model> = {}): Model => ({
  id: 'model-1',
  metadata: {
    name: 'Test Model',
    description: '',
    author: '',
    createdAt: '2026-01-01T00:00:00.000Z',
    modifiedAt: '2026-01-01T00:00:00.000Z',
    version: '1.0.0',
  },
  blocks: [],
  connections: [],
  simulationConfig: {
    solver: 'rk4',
    startTime: 0,
    stopTime: 10,
    stepSize: 0.01,
  },
  ...overrides,
})

describe('SimulationWebSocket', () => {
  let mockWebSocket: {
    onopen: (() => void) | null
    onmessage: ((event: { data: string }) => void) | null
    onerror: (() => void) | null
    onclose: (() => void) | null
    send: ReturnType<typeof vi.fn>
    close: ReturnType<typeof vi.fn>
    readyState: number
  }
  let MockWebSocketClass: ReturnType<typeof vi.fn> & {
    OPEN: number
    CLOSED: number
  }

  beforeEach(() => {
    mockWebSocket = {
      onopen: null,
      onmessage: null,
      onerror: null,
      onclose: null,
      send: vi.fn(),
      close: vi.fn(),
      readyState: 1, // OPEN
    }

    const mockFn = vi.fn(() => mockWebSocket)
    // Create the mock class with static constants
    MockWebSocketClass = Object.assign(mockFn, {
      OPEN: 1,
      CLOSED: 3,
    }) as ReturnType<typeof vi.fn> & { OPEN: number; CLOSED: number }
    vi.stubGlobal('WebSocket', MockWebSocketClass)
    vi.stubGlobal('window', { location: { protocol: 'http:', host: 'localhost:4200' } })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('connects to WebSocket server', () => {
    const onData = vi.fn()
    const onStatus = vi.fn()
    const onError = vi.fn()
    const onConnect = vi.fn()
    const onDisconnect = vi.fn()

    const ws = new SimulationWebSocket(onData, onStatus, onError, onConnect, onDisconnect)
    ws.connect()

    expect(MockWebSocketClass).toHaveBeenCalledWith('ws://localhost:4200/ws/simulation')
  })

  it('uses wss for https connections', () => {
    vi.stubGlobal('window', { location: { protocol: 'https:', host: 'localhost:4200' } })

    const ws = new SimulationWebSocket(vi.fn(), vi.fn(), vi.fn(), vi.fn(), vi.fn())
    ws.connect()

    expect(MockWebSocketClass).toHaveBeenCalledWith('wss://localhost:4200/ws/simulation')
  })

  it('calls onConnect when connection opens', () => {
    const onConnect = vi.fn()
    const ws = new SimulationWebSocket(vi.fn(), vi.fn(), vi.fn(), onConnect, vi.fn())

    ws.connect()
    mockWebSocket.onopen?.()

    expect(onConnect).toHaveBeenCalled()
  })

  it('resets reconnect attempts on successful connect', () => {
    const onConnect = vi.fn()
    const ws = new SimulationWebSocket(vi.fn(), vi.fn(), vi.fn(), onConnect, vi.fn())

    ws.connect()
    mockWebSocket.onopen?.()

    // Verify connection was established
    expect(onConnect).toHaveBeenCalled()
  })

  it('handles data messages', () => {
    const onData = vi.fn()
    const ws = new SimulationWebSocket(onData, vi.fn(), vi.fn(), vi.fn(), vi.fn())

    ws.connect()
    mockWebSocket.onmessage?.({
      data: JSON.stringify({ type: 'data', payload: { time: 1, signals: { a: 1 } } }),
    })

    expect(onData).toHaveBeenCalledWith({ time: 1, signals: { a: 1 } })
  })

  it('handles status messages', () => {
    const onStatus = vi.fn()
    const ws = new SimulationWebSocket(vi.fn(), onStatus, vi.fn(), vi.fn(), vi.fn())

    ws.connect()
    mockWebSocket.onmessage?.({
      data: JSON.stringify({ type: 'status', payload: { status: 'running', progress: 0.5 } }),
    })

    expect(onStatus).toHaveBeenCalledWith('running', 0.5)
  })

  it('handles error messages', () => {
    const onError = vi.fn()
    const ws = new SimulationWebSocket(vi.fn(), vi.fn(), onError, vi.fn(), vi.fn())

    ws.connect()
    mockWebSocket.onmessage?.({
      data: JSON.stringify({ type: 'error', payload: { message: 'Test error' } }),
    })

    expect(onError).toHaveBeenCalledWith('Test error')
  })

  it('handles unknown message types gracefully', () => {
    const onData = vi.fn()
    const onStatus = vi.fn()
    const onError = vi.fn()
    const ws = new SimulationWebSocket(onData, onStatus, onError, vi.fn(), vi.fn())

    ws.connect()
    // Unknown message type should not cause an error
    mockWebSocket.onmessage?.({
      data: JSON.stringify({ type: 'unknown', payload: {} }),
    })

    expect(onData).not.toHaveBeenCalled()
    expect(onStatus).not.toHaveBeenCalled()
    expect(onError).not.toHaveBeenCalled()
  })

  it('handles connection errors', () => {
    const onError = vi.fn()
    const ws = new SimulationWebSocket(vi.fn(), vi.fn(), onError, vi.fn(), vi.fn())

    ws.connect()
    mockWebSocket.onerror?.()

    expect(onError).toHaveBeenCalledWith('WebSocket connection error')
  })

  it('calls onDisconnect when connection closes', () => {
    const onDisconnect = vi.fn()
    const ws = new SimulationWebSocket(vi.fn(), vi.fn(), vi.fn(), vi.fn(), onDisconnect)

    ws.connect()
    mockWebSocket.onclose?.()

    expect(onDisconnect).toHaveBeenCalled()
  })

  it('sends messages when connected', () => {
    // Create websocket with readyState already set to OPEN
    const wsWithOpenState = {
      ...mockWebSocket,
      readyState: 1, // WebSocket.OPEN
    }
    MockWebSocketClass.mockReturnValue(wsWithOpenState)

    const ws = new SimulationWebSocket(vi.fn(), vi.fn(), vi.fn(), vi.fn(), vi.fn())
    ws.connect()

    ws.send({ type: 'test', data: 123 })

    expect(wsWithOpenState.send).toHaveBeenCalledWith('{"type":"test","data":123}')
  })

  it('does not send when not connected', () => {
    const ws = new SimulationWebSocket(vi.fn(), vi.fn(), vi.fn(), vi.fn(), vi.fn())

    ws.connect()

    // Simulate closed connection
    Object.defineProperty(mockWebSocket, 'readyState', { value: 3, writable: true })

    ws.send({ type: 'test' })

    expect(mockWebSocket.send).not.toHaveBeenCalled()
  })

  it('disconnects properly', () => {
    const ws = new SimulationWebSocket(vi.fn(), vi.fn(), vi.fn(), vi.fn(), vi.fn())

    ws.connect()
    ws.disconnect()

    expect(mockWebSocket.close).toHaveBeenCalled()
  })

  it('handles disconnect when not connected', () => {
    const ws = new SimulationWebSocket(vi.fn(), vi.fn(), vi.fn(), vi.fn(), vi.fn())

    // Should not throw when disconnecting without being connected
    expect(() => ws.disconnect()).not.toThrow()
  })

  it('handles invalid JSON gracefully', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const ws = new SimulationWebSocket(vi.fn(), vi.fn(), vi.fn(), vi.fn(), vi.fn())

    ws.connect()
    mockWebSocket.onmessage?.({ data: 'invalid json' })

    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })

  it('attempts to reconnect after disconnect', () => {
    vi.useFakeTimers()

    const ws = new SimulationWebSocket(vi.fn(), vi.fn(), vi.fn(), vi.fn(), vi.fn())

    ws.connect()

    // Clear the initial call
    MockWebSocketClass.mockClear()

    // Trigger disconnect
    mockWebSocket.onclose?.()

    // Fast forward to trigger reconnect (2 second delay for first attempt)
    vi.advanceTimersByTime(2000)

    expect(MockWebSocketClass).toHaveBeenCalledTimes(1)

    vi.useRealTimers()
  })
})

describe('api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('model operations', () => {
    it('getModels fetches models list', async () => {
      const mockModels = [{ id: '1', metadata: { name: 'Test' } }]
      mockAxiosInstance.get.mockResolvedValueOnce({ data: mockModels })

      const result = await api.getModels()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/models')
      expect(result).toEqual(mockModels)
    })

    it('getModel fetches single model', async () => {
      const mockModel = { id: '1', metadata: { name: 'Test' } }
      mockAxiosInstance.get.mockResolvedValueOnce({ data: mockModel })

      const result = await api.getModel('1')

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/models/1')
      expect(result).toEqual(mockModel)
    })

    it('saveModel creates new model when no id', async () => {
      const mockModel = createMockModel({
        id: '',
        metadata: {
          ...createMockModel().metadata,
          name: 'New Model',
        },
      })
      const savedModel = { ...mockModel, id: 'new-id' }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: savedModel })

      const result = await api.saveModel(mockModel)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/models', mockModel)
      expect(result).toEqual(savedModel)
    })

    it('saveModel updates existing model when has id', async () => {
      const mockModel = createMockModel({
        id: '1',
        metadata: {
          ...createMockModel().metadata,
          name: 'Updated',
        },
      })
      mockAxiosInstance.put.mockResolvedValueOnce({ data: mockModel })

      const result = await api.saveModel(mockModel)

      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/models/1', mockModel)
      expect(result).toEqual(mockModel)
    })

    it('deleteModel deletes a model', async () => {
      mockAxiosInstance.delete.mockResolvedValueOnce({})

      await api.deleteModel('1')

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/models/1')
    })
  })

  describe('simulation operations', () => {
    it('validateModel validates a model', async () => {
      const mockResult = { valid: true, errors: [] }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult })

      const result = await api.validateModel('1')

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/models/1/validate')
      expect(result).toEqual(mockResult)
    })

    it('compileModel compiles a model', async () => {
      const mockResult = { success: true, message: 'Compiled' }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult })

      const result = await api.compileModel('1')

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/models/1/compile')
      expect(result).toEqual(mockResult)
    })

    it('startSimulation starts a simulation', async () => {
      const mockModel = createMockModel({ id: '1' })
      const mockConfig: SimulationConfig = { solver: 'rk4', startTime: 0, stopTime: 10, stepSize: 0.01 }
      const mockResult = { sessionId: 'session-1' }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult })

      const result = await api.startSimulation(mockModel, mockConfig)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/start', {
        model: mockModel,
        config: mockConfig,
      })
      expect(result).toEqual(mockResult)
    })

    it('startSimulation opts into coexistence explicitly', async () => {
      const mockModel = createMockModel({ id: '1' })
      const mockConfig: SimulationConfig = { solver: 'rk4', startTime: 0, stopTime: 10, stepSize: 0.01 }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: { sessionId: 'session-2' } })

      await api.startSimulation(mockModel, mockConfig, { replaceCurrent: false })

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/start', {
        model: mockModel,
        config: mockConfig,
        replaceCurrent: false,
      })
    })

    it('stopSimulation stops a simulation', async () => {
      mockAxiosInstance.post.mockResolvedValueOnce({})

      await api.stopSimulation()

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/stop')
    })

    it('resetSimulation resets a simulation', async () => {
      const mockResult = { success: true, message: 'Reset', currentTime: 0, progress: 0, status: 'idle' }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult })

      const result = await api.resetSimulation()

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/reset')
      expect(result).toEqual(mockResult)
    })

    it('pauseSimulation pauses a simulation', async () => {
      mockAxiosInstance.post.mockResolvedValueOnce({})

      await api.pauseSimulation()

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/pause')
    })

    it('resumeSimulation resumes a simulation', async () => {
      mockAxiosInstance.post.mockResolvedValueOnce({})

      await api.resumeSimulation()

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/resume')
    })

    it('getSimulationStatus gets simulation status', async () => {
      const mockResult = { status: 'running', progress: 0.5 }
      mockAxiosInstance.get.mockResolvedValueOnce({ data: mockResult })

      const result = await api.getSimulationStatus()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/simulate/status')
      expect(result).toEqual(mockResult)
    })

    it('targets simulation reads and controls by session ID', async () => {
      mockAxiosInstance.get.mockResolvedValueOnce({ data: { status: 'running', progress: 0 } })
      mockAxiosInstance.post.mockResolvedValueOnce({})

      await api.getSimulationStatus({ sessionId: 'session-1' })
      await api.stopSimulation({ sessionId: 'session-1' })

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/simulate/status', {
        params: { sessionId: 'session-1' },
      })
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/stop', undefined, {
        params: { sessionId: 'session-1' },
      })
    })

    it('deletes an encoded simulation session', async () => {
      mockAxiosInstance.delete.mockResolvedValueOnce({})

      await api.deleteSimulationSession('session/one')

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/simulate/sessions/session%2Fone')
    })

    it('getSimulationResults gets simulation results', async () => {
      const mockResult = { signals: [], statistics: {} }
      mockAxiosInstance.get.mockResolvedValueOnce({ data: mockResult })

      const result = await api.getSimulationResults()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/simulate/results')
      expect(result).toEqual(mockResult)
    })
  })

  describe('step mode operations', () => {
    it('initStepMode initializes step mode', async () => {
      const mockModel = createMockModel({ id: '1' })
      const mockConfig: SimulationConfig = { solver: 'rk4', startTime: 0, stopTime: 10, stepSize: 0.01 }
      const mockResult = { success: true, sessionId: 's1', currentTime: 0, status: 'step_mode' }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult })

      const result = await api.initStepMode(mockModel, mockConfig)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/step/init', {
        model: mockModel,
        config: mockConfig,
      })
      expect(result).toEqual(mockResult)
    })

    it('initStepMode opts into coexistence explicitly', async () => {
      const mockModel = createMockModel({ id: '1' })
      const mockConfig: SimulationConfig = { solver: 'rk4', startTime: 0, stopTime: 10, stepSize: 0.01 }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: { success: true } })

      await api.initStepMode(mockModel, mockConfig, { replaceCurrent: false })

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/step/init', {
        model: mockModel,
        config: mockConfig,
        replaceCurrent: false,
      })
    })

    it('stepForward advances simulation', async () => {
      const mockResult = {
        success: true,
        stepsExecuted: 1,
        currentTime: 0.01,
        progress: 0.001,
        completed: false,
        status: 'step_mode',
        historySize: 1,
      }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult })

      const result = await api.stepForward(1)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/step/forward', { numSteps: 1 })
      expect(result).toEqual(mockResult)
    })

    it('targets step operations without changing their request body', async () => {
      mockAxiosInstance.post.mockResolvedValueOnce({ data: { success: true } })

      await api.stepForward(3, { sessionId: 'session-1' })

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/simulate/step/forward',
        { numSteps: 3 },
        { params: { sessionId: 'session-1' } }
      )
    })

    it('stepBackward reverses simulation', async () => {
      const mockResult = {
        success: true,
        stepsExecuted: 1,
        currentTime: 0,
        progress: 0,
        historySize: 0,
        status: 'step_mode',
      }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult })

      const result = await api.stepBackward(1)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/step/backward', { numSteps: 1 })
      expect(result).toEqual(mockResult)
    })

    it('resetStepMode resets step mode', async () => {
      const mockResult = { success: true, currentTime: 0, status: 'step_mode' }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult })

      const result = await api.resetStepMode()

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/step/reset')
      expect(result).toEqual(mockResult)
    })

    it('continueFromStepMode continues simulation', async () => {
      const mockResult = { success: true, currentTime: 0.5, status: 'running' }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult })

      const result = await api.continueFromStepMode()

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/step/continue')
      expect(result).toEqual(mockResult)
    })

    it('enterStepMode enters step mode from running', async () => {
      const mockResult = {
        success: true,
        currentTime: 0.5,
        progress: 0.05,
        status: 'step_mode',
        historySize: 1,
      }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult })

      const result = await api.enterStepMode()

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/step/enter')
      expect(result).toEqual(mockResult)
    })
  })

  describe('import operations', () => {
    it('importMDL imports MDL file', async () => {
      const mockFile = new File(['content'], 'test.mdl', { type: 'text/plain' })
      const mockModel = { id: '1', metadata: { name: 'Imported' } }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockModel })

      const result = await api.importMDL(mockFile)

      expect(mockAxiosInstance.post).toHaveBeenCalled()
      // Verify FormData was used
      const callArgs = mockAxiosInstance.post.mock.calls[0]
      expect(callArgs[0]).toBe('/import/mdl')
      expect(result).toEqual(mockModel)
    })
  })

  describe('block library operations', () => {
    it('getBlockDefinitions fetches block definitions', async () => {
      const mockBlocks = [{ type: 'constant', name: 'Constant' }]
      mockAxiosInstance.get.mockResolvedValueOnce({ data: mockBlocks })

      const result = await api.getBlockDefinitions()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/blocks')
      expect(result).toEqual(mockBlocks)
    })
  })

  describe('documentation operations', () => {
    it('getProjectReadme fetches project readme', async () => {
      const mockReadme = '# Project'
      mockAxiosInstance.get.mockResolvedValueOnce({ data: mockReadme })

      const result = await api.getProjectReadme()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/docs/readme', expect.any(Object))
      expect(result).toEqual(mockReadme)
    })

    it('getExamplesReadme fetches examples readme', async () => {
      const mockReadme = '# Examples'
      mockAxiosInstance.get.mockResolvedValueOnce({ data: mockReadme })

      const result = await api.getExamplesReadme()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/docs/examples', expect.any(Object))
      expect(result).toEqual(mockReadme)
    })
  })

  describe('examples operations', () => {
    it('getExampleList fetches examples list', async () => {
      const mockExamples = [{ id: '1', name: 'Test', description: 'Desc', category: 'basic' }]
      mockAxiosInstance.get.mockResolvedValueOnce({ data: mockExamples })

      const result = await api.getExampleList()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/examples')
      expect(result).toEqual(mockExamples)
    })

    it('getExample fetches single example', async () => {
      const mockModel = { id: '1', metadata: { name: 'Example' } }
      mockAxiosInstance.get.mockResolvedValueOnce({ data: mockModel })

      const result = await api.getExample('1')

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/examples/1')
      expect(result).toEqual(mockModel)
    })
  })
})

describe('SimulationWebSocket additional scenarios', () => {
  let mockWebSocket: {
    onopen: (() => void) | null
    onmessage: ((event: { data: string }) => void) | null
    onerror: (() => void) | null
    onclose: (() => void) | null
    send: ReturnType<typeof vi.fn>
    close: ReturnType<typeof vi.fn>
    readyState: number
  }
  let MockWebSocketClass: ReturnType<typeof vi.fn> & {
    OPEN: number
    CLOSED: number
  }

  beforeEach(() => {
    mockWebSocket = {
      onopen: null,
      onmessage: null,
      onerror: null,
      onclose: null,
      send: vi.fn(),
      close: vi.fn(),
      readyState: 1,
    }

    const mockFn = vi.fn(() => mockWebSocket)
    MockWebSocketClass = Object.assign(mockFn, {
      OPEN: 1,
      CLOSED: 3,
    }) as ReturnType<typeof vi.fn> & { OPEN: number; CLOSED: number }
    vi.stubGlobal('WebSocket', MockWebSocketClass)
    vi.stubGlobal('window', { location: { protocol: 'http:', host: 'localhost:4200' } })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('stops reconnecting after max attempts', () => {
    vi.useFakeTimers()

    const ws = new SimulationWebSocket(vi.fn(), vi.fn(), vi.fn(), vi.fn(), vi.fn())
    ws.connect()

    // Simulate 5 disconnects (max reconnect attempts)
    for (let i = 0; i < 5; i++) {
      MockWebSocketClass.mockClear()
      mockWebSocket.onclose?.()
      // Fast forward past the reconnect delay (exponentially increasing)
      vi.advanceTimersByTime(Math.pow(2, i + 1) * 1000)
    }

    // Clear the call count after reconnects
    MockWebSocketClass.mockClear()

    // One more disconnect should not trigger reconnect
    mockWebSocket.onclose?.()
    vi.advanceTimersByTime(100000) // Wait a long time

    // Should not have attempted to reconnect
    expect(MockWebSocketClass).not.toHaveBeenCalled()

    vi.useRealTimers()
  })

  it('does not send when websocket is null', () => {
    const ws = new SimulationWebSocket(vi.fn(), vi.fn(), vi.fn(), vi.fn(), vi.fn())
    // Don't call connect, so ws is null

    // Should not throw
    expect(() => ws.send({ type: 'test' })).not.toThrow()
  })

  it('stepForward uses default numSteps', async () => {
    vi.clearAllMocks()
    const mockResult = {
      success: true,
      stepsExecuted: 1,
      currentTime: 0.01,
      progress: 0.001,
      completed: false,
      status: 'step_mode',
      historySize: 1,
    }
    mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult })

    // Call without providing numSteps to test default parameter
    const result = await api.stepForward()

    expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/step/forward', { numSteps: 1 })
    expect(result).toEqual(mockResult)
  })

  it('stepBackward uses default numSteps', async () => {
    vi.clearAllMocks()
    const mockResult = {
      success: true,
      stepsExecuted: 1,
      currentTime: 0,
      progress: 0,
      historySize: 0,
      status: 'step_mode',
    }
    mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult })

    // Call without providing numSteps to test default parameter
    const result = await api.stepBackward()

    expect(mockAxiosInstance.post).toHaveBeenCalledWith('/simulate/step/backward', { numSteps: 1 })
    expect(result).toEqual(mockResult)
  })
})
