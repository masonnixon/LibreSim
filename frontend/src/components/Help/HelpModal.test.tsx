import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '../../api/client'
import { useUIStore } from '../../store/uiStore'
import { HelpModal } from './HelpModal'

vi.mock('../../store/uiStore', function () { return { useUIStore: vi.fn() } })
vi.mock('../../api/client', function () {
  return { api: { getProjectReadme: vi.fn() } }
})

const mockedUIStore = vi.mocked(useUIStore)
const mockedReadme = vi.mocked(api.getProjectReadme)

function setup(
  showHelpModal = true,
  helpModalTab: 'shortcuts' | 'about' | 'blocks' = 'shortcuts'
) {
  const closeHelpModal = vi.fn()
  const openHelpModal = vi.fn()
  mockedUIStore.mockReturnValue({
    showHelpModal,
    helpModalTab,
    closeHelpModal,
    openHelpModal,
  } as never)
  return { closeHelpModal, openHelpModal }
}

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason: unknown) => void
  const promise = new Promise<T>(function (resolvePromise, rejectPromise) {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

describe('HelpModal', function () {
  beforeEach(function () {
    vi.clearAllMocks()
  })

  it('renders nothing while closed', function () {
    setup(false)
    const view = render(<HelpModal />)
    expect(view.container).toBeEmptyDOMElement()
  })

  it('renders all shortcut sections and the external project link', function () {
    setup()
    render(<HelpModal />)

    expect(screen.getByText('General')).toBeInTheDocument()
    expect(screen.getByText('Selection & Editing')).toBeInTheDocument()
    expect(screen.getByText('Signal Lines')).toBeInTheDocument()
    expect(screen.getByText('View & Layout')).toBeInTheDocument()
    expect(screen.getByText('Navigation')).toBeInTheDocument()
    expect(screen.getByText('Ctrl+S')).toBeInTheDocument()
    expect(screen.getByText('Double-click subsystem')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'View on GitHub' })).toHaveAttribute(
      'href',
      'https://github.com/masonnixon/LibreSim'
    )
    expect(screen.getByRole('link', { name: 'View on GitHub' })).toHaveAttribute(
      'rel',
      'noopener noreferrer'
    )
  })

  it('switches tabs, expands block details, and collapses them again', function () {
    const stores = setup()
    render(<HelpModal />)

    fireEvent.click(screen.getByRole('button', { name: 'Blocks' }))
    expect(stores.openHelpModal).toHaveBeenCalledWith('blocks')
    expect(screen.getByText(/LibreSim includes 110/)).toBeInTheDocument()

    const sources = screen.getByRole('button', { name: /Sources/ })
    fireEvent.click(sources)
    expect(screen.getByText('Generate input signals for your model')).toBeInTheDocument()
    expect(screen.getByText('Constant')).toBeInTheDocument()
    expect(screen.getAllByText(/Parameters:/)).not.toHaveLength(0)
    expect(screen.getByText('Clock')).toBeInTheDocument()

    fireEvent.click(sources)
    expect(screen.queryByText('Generate input signals for your model')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Shortcuts' }))
    expect(stores.openHelpModal).toHaveBeenLastCalledWith('shortcuts')
  })

  it('loads and renders the project documentation', async function () {
    const request = deferred<string>()
    mockedReadme.mockReturnValue(request.promise)
    const stores = setup()
    render(<HelpModal />)

    fireEvent.click(screen.getByRole('button', { name: 'About' }))
    expect(stores.openHelpModal).toHaveBeenCalledWith('about')
    expect(screen.getByText('Loading documentation...')).toBeInTheDocument()
    request.resolve('# Project documentation\n\nSee the **guide** for details.')

    expect(await screen.findByRole('heading', { name: 'Project documentation' })).toBeInTheDocument()
    expect(screen.getByText('guide')).toBeInTheDocument()
    expect(mockedReadme).toHaveBeenCalledTimes(1)
  })

  it('waits for manual retry after documentation loading fails', async function () {
    const firstRequest = deferred<string>()
    const secondRequest = deferred<string>()
    const consoleError = vi.spyOn(console, 'error').mockImplementation(function () {})
    mockedReadme
      .mockReturnValueOnce(firstRequest.promise)
      .mockReturnValueOnce(secondRequest.promise)
    setup(true, 'about')
    render(<HelpModal />)

    firstRequest.reject(new Error('offline'))
    expect(await screen.findByText('Failed to load documentation. Please try again.')).toBeInTheDocument()
    await waitFor(function () {
      expect(mockedReadme).toHaveBeenCalledTimes(1)
    })

    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(screen.getByText('Loading documentation...')).toBeInTheDocument()
    expect(mockedReadme).toHaveBeenCalledTimes(2)
    secondRequest.resolve('Documentation restored')
    expect(await screen.findByText('Documentation restored')).toBeInTheDocument()
    expect(consoleError).toHaveBeenCalledWith('Failed to load project README:', expect.any(Error))
    consoleError.mockRestore()
  })

  it('syncs the selected tab when the store tab changes', function () {
    setup()
    const view = render(<HelpModal />)
    expect(screen.getByText('General')).toBeInTheDocument()

    setup(true, 'blocks')
    view.rerender(<HelpModal />)
    expect(screen.getByText(/LibreSim includes 110/)).toBeInTheDocument()
  })

  it('closes from the header, backdrop, and Escape but ignores inner clicks', function () {
    const stores = setup()
    const view = render(<HelpModal />)
    const backdrop = view.container.firstElementChild as HTMLElement
    const panel = backdrop.firstElementChild as HTMLElement

    fireEvent.click(panel)
    fireEvent.keyDown(backdrop, { key: 'Enter' })
    expect(stores.closeHelpModal).not.toHaveBeenCalled()

    fireEvent.click(screen.getAllByRole('button')[3])
    fireEvent.click(backdrop)
    fireEvent.keyDown(backdrop, { key: 'Escape' })
    expect(stores.closeHelpModal).toHaveBeenCalledTimes(3)
  })
})
