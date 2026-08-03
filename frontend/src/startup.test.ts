import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fetchExample } from './data/examples'
import { useModelStore } from './store/modelStore'
import { EMBED_PARENT_ORIGIN, makeReadyNotifier, prepareStartup } from './startup'
import type { Model } from './types/model'

vi.mock('./data/examples', () => ({ fetchExample: vi.fn() }))

const exampleModel = {
  id: 'pid',
  metadata: {
    name: 'PID Controller',
    description: '',
    author: '',
    createdAt: '2026-08-03T00:00:00.000Z',
    modifiedAt: '2026-08-03T00:00:00.000Z',
    version: '1.0.0',
  },
  blocks: [],
  connections: [],
  simulationConfig: { solver: 'rk4', startTime: 0, stopTime: 10, stepSize: 0.01 },
} satisfies Model

describe('URL startup', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useModelStore.setState({ model: null })
  })

  it('fetches and loads a requested example through the model store', async () => {
    vi.mocked(fetchExample).mockResolvedValue(exampleModel)
    const loadModel = vi.spyOn(useModelStore.getState(), 'loadModel')

    await expect(prepareStartup('?example=03_pid_controller&embed=1')).resolves.toEqual({
      embed: true,
      example: '03_pid_controller',
    })
    expect(fetchExample).toHaveBeenCalledOnce()
    expect(fetchExample).toHaveBeenCalledWith('03_pid_controller')
    expect(loadModel).toHaveBeenCalledWith(exampleModel)
    expect(useModelStore.getState().model).toBe(exampleModel)
  })

  it('leaves normal standalone startup to the existing restore path', async () => {
    await expect(prepareStartup('')).resolves.toEqual({ embed: false })
    expect(fetchExample).not.toHaveBeenCalled()
    expect(useModelStore.getState().model).toBeNull()
  })

  it('does not fall back to browser state when the requested example is missing', async () => {
    vi.mocked(fetchExample).mockResolvedValue(undefined)
    await expect(prepareStartup('?example=missing')).resolves.toEqual({
      embed: false,
      example: 'missing',
      error: "Example 'missing' could not be loaded.",
    })
    expect(useModelStore.getState().model).toBeNull()
  })

  it('posts the iframe-ready event exactly once to the presentation origin', () => {
    const parentWindow = { postMessage: vi.fn() }
    const notify = makeReadyNotifier(parentWindow, window)

    notify('03_pid_controller')
    notify('03_pid_controller')

    expect(parentWindow.postMessage).toHaveBeenCalledOnce()
    expect(parentWindow.postMessage).toHaveBeenCalledWith(
      { type: 'orbitlink:libresim-ready', example: '03_pid_controller' },
      EMBED_PARENT_ORIGIN,
    )
  })
})
