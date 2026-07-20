import { createElement } from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { BlockInstance, Connection } from '../../types/block'
import { EditorContextMenus, type EditorContextMenusProps } from './ContextMenu'

type Props = EditorContextMenusProps

function block(id: string, children?: BlockInstance[]): BlockInstance {
  return {
    id,
    type: 'subsystem',
    name: id,
    position: { x: 0, y: 0 },
    parameters: {},
    inputPorts: [],
    outputPorts: [],
    children,
  }
}

function connection(signalName?: string): Connection {
  return {
    id: 'connection-1',
    sourceBlockId: 'source',
    sourcePortId: 'source-out',
    targetBlockId: 'target',
    targetPortId: 'target-in',
    signalName,
  }
}

function props(overrides: Partial<Props> = {}): Props {
  return {
    contextMenu: null,
    signalContextMenu: null,
    renamingSignal: null,
    selectedBlockCount: 0,
    selectedSubsystem: null,
    currentConnections: [],
    highlightedConnectionCount: 0,
    onCreateSubsystem: vi.fn(),
    onEnterSubsystem: vi.fn(),
    onExpandSubsystem: vi.fn(),
    onRenameSignal: vi.fn(),
    onSignalDiscard: vi.fn(),
    onLabelDiscard: vi.fn(),
    onHighlightToSource: vi.fn(),
    onHighlightToDestination: vi.fn(),
    onClearHighlighting: vi.fn(),
    onAutoRouteSignal: vi.fn(),
    onSaveSignalName: vi.fn(),
    onCancelSignalRename: vi.fn(),
    ...overrides,
  }
}

describe('EditorContextMenus', function () {
  it('renders no menu without a menu position', function () {
    const view = render(createElement(EditorContextMenus, props()))
    expect(view.container).toBeEmptyDOMElement()
  })

  it('renders the multi-selection menu and creates a subsystem', function () {
    const options = props({
      contextMenu: { x: 12, y: 34 },
      selectedBlockCount: 3,
    })
    render(createElement(EditorContextMenus, options))

    const menu = screen.getByTestId('block-context-menu')
    expect(menu).toHaveStyle({ left: '12px', top: '34px' })
    fireEvent.click(screen.getByRole('button', { name: /Create Subsystem/ }))
    expect(options.onCreateSubsystem).toHaveBeenCalledOnce()
  })

  it('enters and expands a selected subsystem and reports its child count', function () {
    const subsystem = block('subsystem-1', [block('child')])
    const options = props({
      contextMenu: { x: 0, y: 0 },
      selectedBlockCount: 1,
      selectedSubsystem: subsystem,
    })
    const view = render(createElement(EditorContextMenus, options))

    expect(screen.getByText('1 blocks')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Enter Subsystem' }))
    fireEvent.click(screen.getByRole('button', { name: /Expand Subsystem/ }))
    expect(options.onEnterSubsystem).toHaveBeenCalledWith('subsystem-1')
    expect(options.onExpandSubsystem).toHaveBeenCalledOnce()

    view.rerender(createElement(EditorContextMenus, {
      ...options,
      selectedSubsystem: block('empty-subsystem'),
    }))
    expect(screen.getByText('0 blocks')).toBeInTheDocument()
  })

  it('renders every signal action and stops clicks from reaching the canvas', function () {
    const parentClick = vi.fn()
    const options = props({
      signalContextMenu: { x: 20, y: 40, edgeId: 'edge-1', connectionId: 'connection-1' },
      currentConnections: [connection('named signal')],
      highlightedConnectionCount: 2,
    })
    render(createElement(
      'div',
      { onClick: parentClick },
      createElement(EditorContextMenus, options)
    ))

    const menu = screen.getByTestId('signal-context-menu')
    expect(menu).toHaveStyle({ left: '20px', top: '40px' })
    fireEvent.click(menu)
    fireEvent.click(screen.getByRole('button', { name: 'Rename Signal' }))
    fireEvent.click(screen.getByRole('button', { name: /Del.*Del/ }))
    fireEvent.click(screen.getByRole('button', { name: /Label/ }))
    fireEvent.click(screen.getByRole('button', { name: /Highlight to Source/ }))
    fireEvent.click(screen.getByRole('button', { name: /Highlight to Destination/ }))
    fireEvent.click(screen.getByRole('button', { name: /Remove Highlighting/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Auto-route Line' }))

    expect(parentClick).not.toHaveBeenCalled()
    expect(options.onRenameSignal).toHaveBeenCalledOnce()
    expect(options.onSignalDiscard).toHaveBeenCalledOnce()
    expect(options.onLabelDiscard).toHaveBeenCalledOnce()
    expect(options.onHighlightToSource).toHaveBeenCalledOnce()
    expect(options.onHighlightToDestination).toHaveBeenCalledOnce()
    expect(options.onClearHighlighting).toHaveBeenCalledOnce()
    expect(options.onAutoRouteSignal).toHaveBeenCalledOnce()
  })

  it('hides conditional signal actions when no name or highlighting exists', function () {
    const options = props({
      signalContextMenu: { x: 0, y: 0, edgeId: 'edge-1', connectionId: 'missing' },
    })
    render(createElement(EditorContextMenus, options))
    expect(screen.queryByRole('button', { name: /Label/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Remove Highlighting/ })).not.toBeInTheDocument()
  })

  it('focuses the rename input and saves with Enter or blur', function () {
    const parentClick = vi.fn()
    const selectInput = vi.spyOn(HTMLInputElement.prototype, 'select')
    const options = props({
      renamingSignal: { x: 5, y: 6, connectionId: 'connection-1' },
      currentConnections: [connection('existing name')],
    })
    render(createElement(
      'div',
      { onClick: parentClick },
      createElement(EditorContextMenus, options)
    ))

    const input = screen.getByPlaceholderText('Signal name') as HTMLInputElement
    expect(input).toHaveFocus()
    expect(input).toHaveValue('existing name')
    expect(selectInput).toHaveBeenCalledOnce()

    fireEvent.click(screen.getByTestId('signal-rename-menu'))
    fireEvent.change(input, { target: { value: 'new name' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    fireEvent.blur(input)

    expect(parentClick).not.toHaveBeenCalled()
    expect(options.onSaveSignalName).toHaveBeenNthCalledWith(1, 'new name')
    expect(options.onSaveSignalName).toHaveBeenNthCalledWith(2, 'new name')
    selectInput.mockRestore()
  })

  it('cancels with Escape and ignores other rename keys', function () {
    const options = props({
      renamingSignal: { x: 0, y: 0, connectionId: 'missing' },
    })
    render(createElement(EditorContextMenus, options))
    const input = screen.getByPlaceholderText('Signal name')

    expect(input).toHaveValue('')
    fireEvent.keyDown(input, { key: 'x' })
    expect(options.onCancelSignalRename).not.toHaveBeenCalled()
    fireEvent.keyDown(input, { key: 'Escape' })
    expect(options.onCancelSignalRename).toHaveBeenCalledOnce()
  })
})
