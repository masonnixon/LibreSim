import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { createElement } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useModelStore } from '../../store/modelStore'
import { toast } from '../Toast/Toast'
import { CodeGenModal } from './CodeGenModal'

vi.mock('../../store/modelStore', function () { return { useModelStore: vi.fn() } })
vi.mock('../Toast/Toast', function () {
  return { toast: { success: vi.fn(), warning: vi.fn() } }
})

const mockedModelStore = vi.mocked(useModelStore)
const mockedToast = vi.mocked(toast)

const model = {
  id: 'model-1',
  metadata: { name: 'Flight Model' },
  blocks: [],
  connections: [],
  simulationConfig: { solver: 'rk4', startTime: 1, stopTime: 12, stepSize: 0.02 },
}

function setup(activeModel: unknown = model, isOpen = true) {
  const onClose = vi.fn()
  mockedModelStore.mockReturnValue({ model: activeModel } as never)
  const view = render(createElement(CodeGenModal, { isOpen, onClose }))
  return { view, onClose }
}

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>(function (resolvePromise) {
    resolve = resolvePromise
  })
  return { promise, resolve }
}

describe('CodeGenModal', function () {
  beforeEach(function () {
    vi.clearAllMocks()
    vi.stubGlobal('fetch', vi.fn())
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      value: vi.fn(function () { return 'blob:generated' }),
    })
    Object.defineProperty(URL, 'revokeObjectURL', {
      configurable: true,
      value: vi.fn(),
    })
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function () {})
  })

  it('renders nothing while closed and disables generation without a model', function () {
    const closed = setup(model, false)
    expect(closed.view.container).toBeEmptyDOMElement()
    closed.view.unmount()

    setup(null)
    expect(screen.getByText('simulation_python.zip')).toBeInTheDocument()
    const generate = screen.getByRole('button', { name: /Generate & Download/ })
    expect(generate).toBeDisabled()
  })

  it('edits every generation option and renders each language preview', function () {
    setup()
    expect(screen.getByText('flight_model_python.zip')).toBeInTheDocument()
    expect(screen.getByText(/Generated Python code uses NumPy/)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /^C / }))
    expect(screen.getByText('flight_model_c.zip')).toBeInTheDocument()
    expect(screen.getByText(/Build with CMake:/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /^C\+\+/ }))
    expect(screen.getByText('flight_model_cpp.zip')).toBeInTheDocument()
    expect(screen.getByText(/Build with CMake \(C\+\+17\)/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Rust/ }))
    expect(screen.getByText('flight_model_rust.zip')).toBeInTheDocument()
    expect(screen.getByText(/Build with Cargo/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Python/ }))

    fireEvent.click(screen.getByRole('button', { name: /^Euler/ }))
    fireEvent.click(screen.getByRole('button', { name: /^RK2/ }))
    fireEvent.click(screen.getByRole('button', { name: /^Merson/ }))

    const times = screen.getAllByRole('spinbutton')
    expect(times[0]).toHaveValue(1)
    expect(times[1]).toHaveValue(12)
    expect(times[2]).toHaveValue(0.02)
    fireEvent.change(times[0], { target: { value: '' } })
    fireEvent.change(times[1], { target: { value: '' } })
    fireEvent.change(times[2], { target: { value: '' } })
    expect(times[0]).toHaveValue(0)
    expect(times[1]).toHaveValue(10)
    expect(times[2]).toHaveValue(0.01)

    const projectName = screen.getByRole('textbox')
    fireEvent.change(projectName, { target: { value: 'new bad/name' } })
    expect(projectName).toHaveValue('new_bad_name')
    const checkboxes = screen.getAllByRole('checkbox')
    fireEvent.click(checkboxes[0])
    fireEvent.click(checkboxes[1])
    expect(checkboxes[0]).not.toBeChecked()
    expect(checkboxes[1]).not.toBeChecked()
  })

  it('tracks model name changes until the project name is customized', function () {
    const callbacks = setup()
    expect(screen.getByRole('textbox')).toHaveValue('flight_model')

    mockedModelStore.mockReturnValue({
      model: { ...model, metadata: { name: 'Updated Model' } },
    } as never)
    callbacks.view.rerender(createElement(CodeGenModal, { isOpen: true, onClose: callbacks.onClose }))
    expect(screen.getByRole('textbox')).toHaveValue('updated_model')

    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'custom' } })
    mockedModelStore.mockReturnValue({
      model: { ...model, metadata: { name: 'Ignored Model' } },
    } as never)
    callbacks.view.rerender(createElement(CodeGenModal, { isOpen: true, onClose: callbacks.onClose }))
    expect(screen.getByRole('textbox')).toHaveValue('custom')
  })

  it('uses fallback configuration values when model fields are absent', function () {
    setup({ metadata: {} })
    expect(screen.getByRole('textbox')).toHaveValue('simulation')
    const times = screen.getAllByRole('spinbutton')
    expect(times[0]).toHaveValue(0)
    expect(times[1]).toHaveValue(10)
    expect(times[2]).toHaveValue(0.01)
  })

  it('posts the selected configuration and downloads the generated archive', async function () {
    const request = deferred<Response>()
    vi.mocked(fetch).mockReturnValue(request.promise)
    const callbacks = setup()
    fireEvent.click(screen.getByRole('button', { name: /Rust/ }))
    fireEvent.click(screen.getByRole('button', { name: /^Euler/ }))
    const times = screen.getAllByRole('spinbutton')
    fireEvent.change(times[0], { target: { value: '2' } })
    fireEvent.change(times[1], { target: { value: '20' } })
    fireEvent.change(times[2], { target: { value: '0.05' } })
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'generated' } })
    fireEvent.click(screen.getAllByRole('checkbox')[1])

    fireEvent.click(screen.getByRole('button', { name: /Generate & Download/ }))
    expect(screen.getByRole('button', { name: 'Generating...' })).toBeDisabled()
    const archive = new Blob(['zip'])
    request.resolve({
      ok: true,
      blob: vi.fn().mockResolvedValue(archive),
    } as unknown as Response)

    await waitFor(function () {
      expect(callbacks.onClose).toHaveBeenCalledOnce()
    })
    expect(fetch).toHaveBeenCalledWith('/api/codegen/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        language: 'rust',
        integration_method: 'euler',
        step_size: 0.05,
        stop_time: 20,
        start_time: 2,
        project_name: 'generated',
        include_main: true,
        include_csv_output: false,
      }),
    })
    expect(URL.createObjectURL).toHaveBeenCalledWith(archive)
    expect(HTMLAnchorElement.prototype.click).toHaveBeenCalledOnce()
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:generated')
    expect(document.querySelector('a[download="generated_rust.zip"]')).not.toBeInTheDocument()
    expect(mockedToast.success).toHaveBeenCalledWith(
      'Code Generated',
      'Downloaded generated_rust.zip'
    )
    expect(screen.getByRole('button', { name: /Generate & Download/ })).toBeEnabled()
  })

  it.each([
    ['backend rejected the model', 'backend rejected the model'],
    ['', 'Code generation failed'],
  ])('reports an HTTP generation failure with detail %j', async function (detail, expected) {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(function () {})
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      json: vi.fn().mockResolvedValue({ detail }),
    } as unknown as Response)
    const callbacks = setup()

    fireEvent.click(screen.getByRole('button', { name: /Generate & Download/ }))
    await waitFor(function () {
      expect(mockedToast.warning).toHaveBeenCalledWith('Generation Failed', expected)
    })
    expect(callbacks.onClose).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: /Generate & Download/ })).toBeEnabled()
    expect(consoleError).toHaveBeenCalledWith('Code generation failed:', expect.any(Error))
    consoleError.mockRestore()
  })

  it.each([
    [new Error('network unavailable'), 'network unavailable'],
    ['offline', 'Unknown error'],
  ])('reports a rejected generation request', async function (reason, expected) {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(function () {})
    vi.mocked(fetch).mockRejectedValue(reason)
    setup()

    fireEvent.click(screen.getByRole('button', { name: /Generate & Download/ }))
    await waitFor(function () {
      expect(mockedToast.warning).toHaveBeenCalledWith('Generation Failed', expected)
    })
    expect(consoleError).toHaveBeenCalledWith('Code generation failed:', reason)
    consoleError.mockRestore()
  })

  it('closes from the header, cancel button, and backdrop but ignores panel clicks', function () {
    const callbacks = setup()
    const backdrop = callbacks.view.container.firstElementChild as HTMLElement
    const panel = backdrop.firstElementChild as HTMLElement
    fireEvent.click(panel)
    expect(callbacks.onClose).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: 'Close' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    fireEvent.click(backdrop)
    expect(callbacks.onClose).toHaveBeenCalledTimes(3)
  })
})
