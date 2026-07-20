import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useModelStore } from '../../store/modelStore'
import { useUIStore } from '../../store/uiStore'
import { exportModelAsMDL } from '../../utils/mdlExporter'
import { toast } from '../Toast/Toast'
import { SaveAsModal } from './SaveAsModal'

vi.mock('../../store/modelStore', function () { return { useModelStore: vi.fn() } })
vi.mock('../../store/uiStore', function () { return { useUIStore: vi.fn() } })
vi.mock('../../utils/mdlExporter', function () { return { exportModelAsMDL: vi.fn() } })
vi.mock('../Toast/Toast', function () {
  return { toast: { success: vi.fn(), warning: vi.fn() } }
})

const mockedModelStore = vi.mocked(useModelStore)
const mockedUIStore = vi.mocked(useUIStore)
const mockedExporter = vi.mocked(exportModelAsMDL)
const mockedToast = vi.mocked(toast)

const model = {
  id: 'model-1',
  metadata: {
    name: 'Original model',
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
}

function setup(showSaveAsModal = true, activeModel: typeof model | null = model) {
  const updateMetadata = vi.fn()
  const closeSaveAsModal = vi.fn()
  mockedModelStore.mockReturnValue({ model: activeModel, updateMetadata } as never)
  mockedUIStore.mockReturnValue({ showSaveAsModal, closeSaveAsModal } as never)
  return { updateMetadata, closeSaveAsModal }
}

describe('SaveAsModal', function () {
  beforeEach(function () {
    vi.clearAllMocks()
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      value: vi.fn(function () { return 'blob:test' }),
    })
    Object.defineProperty(URL, 'revokeObjectURL', {
      configurable: true,
      value: vi.fn(),
    })
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function () {})
  })

  it('renders nothing when closed or when no model exists', function () {
    setup(false)
    const closed = render(<SaveAsModal />)
    expect(closed.container).toBeEmptyDOMElement()
    closed.unmount()

    setup(true, null)
    const noModel = render(<SaveAsModal />)
    expect(noModel.container).toBeEmptyDOMElement()
  })

  it('opens with the model name and default JSON options', function () {
    setup()
    render(<SaveAsModal />)

    expect(screen.getByPlaceholderText('Enter filename')).toHaveValue('Original model')
    expect(screen.getByRole('radio', { name: /JSON/ })).toBeChecked()
    expect(screen.getByRole('radio', { name: /MDL/ })).not.toBeChecked()
    expect(screen.getByRole('checkbox')).toBeChecked()
  })

  it('exports trimmed JSON and updates the model name', function () {
    const stores = setup()
    render(<SaveAsModal />)
    fireEvent.change(screen.getByPlaceholderText('Enter filename'), {
      target: { value: '  Renamed model  ' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(stores.updateMetadata).toHaveBeenCalledWith({ name: 'Renamed model' })
    expect(URL.createObjectURL).toHaveBeenCalledOnce()
    expect(HTMLAnchorElement.prototype.click).toHaveBeenCalledOnce()
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:test')
    expect(mockedToast.success).toHaveBeenCalledWith('Saved', 'Exported as "Renamed model.json"')
    expect(stores.closeSaveAsModal).toHaveBeenCalledOnce()
    expect(document.querySelector('a[download="Renamed model.json"]')).not.toBeInTheDocument()
  })

  it('exports JSON without changing the model name when unchecked', function () {
    const stores = setup()
    render(<SaveAsModal />)
    fireEvent.change(screen.getByPlaceholderText('Enter filename'), {
      target: { value: 'Copy' },
    })
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(stores.updateMetadata).not.toHaveBeenCalled()
    expect(URL.createObjectURL).toHaveBeenCalledOnce()
    expect(stores.closeSaveAsModal).toHaveBeenCalledOnce()
  })

  it('warns for blank filenames entered through the keyboard shortcut', function () {
    const stores = setup()
    const view = render(<SaveAsModal />)
    const backdrop = view.container.firstElementChild as HTMLElement
    fireEvent.change(screen.getByPlaceholderText('Enter filename'), {
      target: { value: '   ' },
    })
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()

    fireEvent.keyDown(backdrop, { key: 'Enter' })

    expect(mockedToast.warning).toHaveBeenCalledWith(
      'Invalid Filename',
      'Please enter a filename.'
    )
    expect(stores.closeSaveAsModal).not.toHaveBeenCalled()
  })

  it('exports MDL with an updated name', function () {
    const stores = setup()
    render(<SaveAsModal />)
    fireEvent.change(screen.getByPlaceholderText('Enter filename'), {
      target: { value: 'Control system' },
    })
    fireEvent.click(screen.getByRole('radio', { name: /MDL/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(mockedExporter).toHaveBeenCalledWith({
      ...model,
      metadata: { ...model.metadata, name: 'Control system' },
    }, 'Control system.mdl')
    expect(mockedToast.success).toHaveBeenCalledWith(
      'Saved',
      'Exported as "Control system.mdl" (Simulink format)'
    )
    expect(stores.closeSaveAsModal).toHaveBeenCalledOnce()
  })

  it('keeps the original model and modal open when MDL export fails', function () {
    const stores = setup()
    render(<SaveAsModal />)
    fireEvent.change(screen.getByPlaceholderText('Enter filename'), {
      target: { value: 'Copy' },
    })
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(screen.getByRole('radio', { name: /MDL/ }))
    mockedExporter.mockImplementationOnce(function () { throw new Error('writer failed') })

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(mockedExporter).toHaveBeenCalledWith(model, 'Copy.mdl')
    expect(mockedToast.warning).toHaveBeenCalledWith('Export Failed', 'writer failed')
    expect(stores.closeSaveAsModal).not.toHaveBeenCalled()
  })

  it('uses an unknown-error message for non-Error MDL failures', function () {
    const stores = setup()
    render(<SaveAsModal />)
    fireEvent.click(screen.getByRole('radio', { name: /MDL/ }))
    mockedExporter.mockImplementationOnce(function () { throw 'failure' })

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(mockedToast.warning).toHaveBeenCalledWith('Export Failed', 'Unknown error')
    expect(stores.closeSaveAsModal).not.toHaveBeenCalled()
  })

  it('switches formats and supports every close and keyboard path', function () {
    const stores = setup()
    const view = render(<SaveAsModal />)
    const backdrop = view.container.firstElementChild as HTMLElement
    fireEvent.click(screen.getByRole('radio', { name: /MDL/ }))
    fireEvent.click(screen.getByRole('radio', { name: /JSON/ }))
    expect(screen.getByRole('radio', { name: /JSON/ })).toBeChecked()

    fireEvent.click(screen.getByText('Format'))
    fireEvent.keyDown(backdrop, { key: 'Enter', shiftKey: true })
    fireEvent.keyDown(backdrop, { key: 'x' })
    expect(stores.closeSaveAsModal).not.toHaveBeenCalled()
    expect(URL.createObjectURL).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    fireEvent.click(backdrop)
    fireEvent.keyDown(backdrop, { key: 'Escape' })
    expect(stores.closeSaveAsModal).toHaveBeenCalledTimes(3)
  })

  it('uses Untitled when the model name is empty', function () {
    setup(true, { ...model, metadata: { ...model.metadata, name: '' } })
    render(<SaveAsModal />)
    expect(screen.getByPlaceholderText('Enter filename')).toHaveValue('Untitled')
  })
})
