import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { createElement } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '../../api/client'
import { ExamplesModal, type ExampleInfo } from './ExamplesModal'

vi.mock('../../api/client', function () {
  return { api: { getExamplesReadme: vi.fn() } }
})

const mockedReadme = vi.mocked(api.getExamplesReadme)

const examples: ExampleInfo[] = [
  { id: 'alpha', name: 'Alpha Model', description: 'A beginner walkthrough', category: 'basic' },
  { id: 'beta', name: 'Beta Model', description: 'Another basic example', category: 'basic' },
  { id: 'gamma', name: 'Gamma Controller', description: 'A closed loop', category: 'control' },
  { id: 'delta', name: 'Delta Filter', description: 'Cleans a noisy input', category: 'signal' },
  { id: 'epsilon', name: 'Epsilon Observer', description: 'An estimation example', category: 'advanced' },
]

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason: unknown) => void
  const promise = new Promise<T>(function (resolvePromise, rejectPromise) {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

function setup() {
  const onClose = vi.fn()
  const onLoadExample = vi.fn()
  const onOpenBlockReference = vi.fn()
  const view = render(createElement(ExamplesModal, {
    isOpen: true,
    onClose,
    examples,
    onLoadExample,
    onOpenBlockReference,
  }))
  return { view, onClose, onLoadExample, onOpenBlockReference }
}

describe('ExamplesModal', function () {
  beforeEach(function () {
    vi.clearAllMocks()
  })

  it('renders nothing while closed', function () {
    const view = render(createElement(ExamplesModal, {
      isOpen: false,
      onClose: vi.fn(),
      examples,
      onLoadExample: vi.fn(),
    }))
    expect(view.container).toBeEmptyDOMElement()
  })

  it('filters by category and case-insensitive name or description', function () {
    setup()
    expect(screen.getByRole('heading', { name: /Basic Examples/ })).toBeInTheDocument()
    expect(screen.getByText('2 examples available')).toBeInTheDocument()
    expect(screen.queryByText('Gamma Controller')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /All Examples/ }))
    expect(screen.getByText('5 examples available')).toBeInTheDocument()

    const search = screen.getByPlaceholderText('Search examples...')
    fireEvent.change(search, { target: { value: 'ALPHA' } })
    expect(screen.getByText('Alpha Model')).toBeInTheDocument()
    expect(screen.getByText('1 example available')).toBeInTheDocument()

    fireEvent.change(search, { target: { value: 'noisy' } })
    expect(screen.getByText('Delta Filter')).toBeInTheDocument()
    fireEvent.change(search, { target: { value: 'missing' } })
    expect(screen.getByText('No examples found matching your search.')).toBeInTheDocument()
    expect(screen.getByText('0 examples available')).toBeInTheDocument()

    fireEvent.change(search, { target: { value: '' } })
    fireEvent.click(screen.getByRole('button', { name: /Control Systems/ }))
    expect(screen.getByText('Gamma Controller')).toBeInTheDocument()
    expect(screen.queryByText('Alpha Model')).not.toBeInTheDocument()
    expect(screen.getByText('Feedback control and system analysis examples')).toBeInTheDocument()
  })

  it('loads an example before closing and opens the block reference after closing', function () {
    const callbacks = setup()
    fireEvent.click(screen.getByRole('button', { name: /Alpha Model/ }))
    expect(callbacks.onLoadExample).toHaveBeenCalledWith('alpha')
    expect(callbacks.onLoadExample.mock.invocationCallOrder[0]).toBeLessThan(
      callbacks.onClose.mock.invocationCallOrder[0]
    )

    fireEvent.click(screen.getByRole('button', { name: 'View Block Reference' }))
    expect(callbacks.onOpenBlockReference).toHaveBeenCalledOnce()
    expect(callbacks.onClose.mock.invocationCallOrder[1]).toBeLessThan(
      callbacks.onOpenBlockReference.mock.invocationCallOrder[0]
    )
  })

  it('supports both close controls and omits the optional block reference', function () {
    const onClose = vi.fn()
    const view = render(createElement(ExamplesModal, {
      isOpen: true,
      onClose,
      examples,
      onLoadExample: vi.fn(),
    }))
    expect(screen.queryByRole('button', { name: 'View Block Reference' })).not.toBeInTheDocument()
    const github = screen.getByRole('link', { name: 'View on GitHub' })
    expect(github).toHaveAttribute(
      'href',
      'https://github.com/masonnixon/LibreSim/tree/master/examples'
    )
    expect(github).toHaveAttribute('rel', 'noopener noreferrer')

    const backdrop = view.container.querySelector('.absolute.inset-0') as HTMLElement
    fireEvent.click(backdrop)
    fireEvent.click(screen.getAllByRole('button')[0])
    expect(onClose).toHaveBeenCalledTimes(2)
  })

  it('loads documentation once and reuses it after returning to the examples', async function () {
    const request = deferred<string>()
    mockedReadme.mockReturnValue(request.promise)
    setup()

    fireEvent.click(screen.getByRole('button', { name: 'Documentation' }))
    expect(screen.getByText('Loading documentation...')).toBeInTheDocument()
    request.resolve('# Examples guide\n\nUse the **catalog**.')
    expect(await screen.findByRole('heading', { name: 'Examples guide' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '← Back to Examples' }))
    expect(screen.getByText('Alpha Model')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Documentation' }))
    expect(screen.getByText('catalog')).toBeInTheDocument()
    expect(mockedReadme).toHaveBeenCalledTimes(1)
  })

  it('waits for manual retry after documentation loading fails', async function () {
    const firstRequest = deferred<string>()
    const secondRequest = deferred<string>()
    const consoleError = vi.spyOn(console, 'error').mockImplementation(function () {})
    mockedReadme
      .mockReturnValueOnce(firstRequest.promise)
      .mockReturnValueOnce(secondRequest.promise)
    setup()

    fireEvent.click(screen.getByRole('button', { name: 'Documentation' }))
    firstRequest.reject('offline')
    expect(await screen.findByText('Failed to load documentation. Please try again.')).toBeInTheDocument()
    await waitFor(function () {
      expect(mockedReadme).toHaveBeenCalledTimes(1)
    })

    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(mockedReadme).toHaveBeenCalledTimes(2)
    expect(screen.getByText('Loading documentation...')).toBeInTheDocument()
    secondRequest.resolve('Documentation restored')
    expect(await screen.findByText('Documentation restored')).toBeInTheDocument()
    expect(consoleError).toHaveBeenCalledWith('Failed to load examples documentation:', 'offline')
    consoleError.mockRestore()
  })
})
