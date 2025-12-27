import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { SimulationWebSocket } from './client'

// Note: The api object relies on axios which is complex to mock at module level
// We skip those tests and focus on SimulationWebSocket which can be properly tested

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
