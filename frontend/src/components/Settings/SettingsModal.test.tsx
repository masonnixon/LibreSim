import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useModelStore } from '../../store/modelStore'
import { useUIStore } from '../../store/uiStore'
import { SettingsModal } from './SettingsModal'

vi.mock('../../store/modelStore', function () { return { useModelStore: vi.fn() } })
vi.mock('../../store/uiStore', function () { return { useUIStore: vi.fn() } })

const mockedModelStore = vi.mocked(useModelStore)
const mockedUIStore = vi.mocked(useUIStore)

const model = {
  id: 'model-1',
  metadata: {
    name: 'Original model',
    description: 'Original description',
    author: '',
    createdAt: '2026-01-01',
    modifiedAt: '2026-01-01',
    version: '1.0.0',
  },
  blocks: [],
  connections: [],
  simulationConfig: {
    solver: 'merson' as const,
    startTime: 1,
    stopTime: 8,
    stepSize: 0.02,
  },
}

function setup(showSettingsModal = true, activeModel: typeof model | null = model) {
  const updateSimulationConfig = vi.fn()
  const updateMetadata = vi.fn()
  const closeSettingsModal = vi.fn()
  mockedModelStore.mockReturnValue({
    model: activeModel,
    updateSimulationConfig,
    updateMetadata,
  } as never)
  mockedUIStore.mockReturnValue({ showSettingsModal, closeSettingsModal } as never)
  return { updateSimulationConfig, updateMetadata, closeSettingsModal }
}

describe('SettingsModal', function () {
  beforeEach(function () {
    vi.clearAllMocks()
  })

  it('renders nothing when closed or when no model exists', function () {
    setup(false)
    const closed = render(<SettingsModal />)
    expect(closed.container).toBeEmptyDOMElement()
    closed.unmount()

    setup(true, null)
    const noModel = render(<SettingsModal />)
    expect(noModel.container).toBeEmptyDOMElement()
  })

  it('loads the current model settings when opened', function () {
    setup()
    render(<SettingsModal />)
    const [name, description] = screen.getAllByRole('textbox')
    const [stepSize, startTime, stopTime] = screen.getAllByRole('spinbutton')

    expect(name).toHaveValue('Original model')
    expect(description).toHaveValue('Original description')
    expect(screen.getByRole('combobox')).toHaveValue('merson')
    expect(stepSize).toHaveValue(0.02)
    expect(startTime).toHaveValue(1)
    expect(stopTime).toHaveValue(8)
  })

  it('saves edited metadata and simulation settings', function () {
    const stores = setup()
    render(<SettingsModal />)
    const [name, description] = screen.getAllByRole('textbox')
    const [stepSize, startTime, stopTime] = screen.getAllByRole('spinbutton')

    fireEvent.change(name, { target: { value: 'Renamed' } })
    fireEvent.change(description, { target: { value: 'Updated' } })
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'euler' } })
    fireEvent.change(stepSize, { target: { value: '0.005' } })
    fireEvent.change(startTime, { target: { value: '2.5' } })
    fireEvent.change(stopTime, { target: { value: '12.5' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(stores.updateSimulationConfig).toHaveBeenCalledWith({
      solver: 'euler',
      stepSize: 0.005,
      startTime: 2.5,
      stopTime: 12.5,
    })
    expect(stores.updateMetadata).toHaveBeenCalledWith({
      name: 'Renamed',
      description: 'Updated',
    })
    expect(stores.closeSettingsModal).toHaveBeenCalledOnce()
  })

  it('normalizes empty numeric inputs to their safe defaults', function () {
    const stores = setup()
    render(<SettingsModal />)
    const [stepSize, startTime, stopTime] = screen.getAllByRole('spinbutton')

    fireEvent.change(stepSize, { target: { value: '' } })
    fireEvent.change(startTime, { target: { value: '' } })
    fireEvent.change(stopTime, { target: { value: '' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(stores.updateSimulationConfig).toHaveBeenCalledWith({
      solver: 'merson',
      stepSize: 0.01,
      startTime: 0,
      stopTime: 10,
    })
  })

  it('closes from cancel, the backdrop, and Escape but not inner or other key events', function () {
    const stores = setup()
    const view = render(<SettingsModal />)
    const backdrop = view.container.firstElementChild as HTMLElement

    fireEvent.click(screen.getByText('Model Information'))
    fireEvent.keyDown(backdrop, { key: 'Enter' })
    expect(stores.closeSettingsModal).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    fireEvent.click(backdrop)
    fireEvent.keyDown(backdrop, { key: 'Escape' })
    expect(stores.closeSettingsModal).toHaveBeenCalledTimes(3)
  })
})
