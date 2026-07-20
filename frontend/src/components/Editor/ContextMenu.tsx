import { createElement, Fragment, useEffect, useRef } from 'react'
import type { BlockInstance, Connection } from '../../types/block'

export interface MenuPosition {
  x: number
  y: number
}

export interface SignalMenuPosition extends MenuPosition {
  edgeId: string
  connectionId: string
}

export interface SignalRenamePosition extends MenuPosition {
  connectionId: string
}

export interface EditorContextMenusProps {
  contextMenu: MenuPosition | null
  signalContextMenu: SignalMenuPosition | null
  renamingSignal: SignalRenamePosition | null
  selectedBlockCount: number
  selectedSubsystem: BlockInstance | null
  currentConnections: Connection[]
  highlightedConnectionCount: number
  onCreateSubsystem: () => void
  onEnterSubsystem: (subsystemId: string) => void
  onExpandSubsystem: () => void
  onRenameSignal: () => void
  onSignalDiscard: () => void
  onLabelDiscard: () => void
  onHighlightToSource: () => void
  onHighlightToDestination: () => void
  onClearHighlighting: () => void
  onAutoRouteSignal: () => void
  onSaveSignalName: (name: string) => void
  onCancelSignalRename: () => void
}

const menuButtonClass =
  'w-full px-4 py-2 text-left text-sm text-white hover:bg-slate-700 flex items-center gap-2'

function icon(pathData: string) {
  return createElement(
    'svg',
    { className: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' },
    createElement('path', {
      strokeLinecap: 'round',
      strokeLinejoin: 'round',
      strokeWidth: 2,
      d: pathData,
    })
  )
}

function menuButton(label: string, onClick: () => void, pathData: string, shortcut?: string) {
  return createElement(
    'button',
    { className: menuButtonClass, onClick },
    icon(pathData),
    createElement('span', null, label),
    shortcut
      ? createElement('span', { className: 'ml-auto text-slate-400 text-xs' }, shortcut)
      : null
  )
}

function separator() {
  return createElement('div', { className: 'border-t border-slate-600 my-1' })
}

export function EditorContextMenus(props: EditorContextMenusProps) {
  const signalNameInputRef = useRef<HTMLInputElement>(null)

  useEffect(function () {
    if (props.renamingSignal && signalNameInputRef.current) {
      signalNameInputRef.current.focus()
      signalNameInputRef.current.select()
    }
  }, [props.renamingSignal])

  const signalConnection = props.signalContextMenu
    ? props.currentConnections.find(function (connection) {
      return connection.id === props.signalContextMenu?.connectionId
    })
    : undefined

  const renamedConnection = props.renamingSignal
    ? props.currentConnections.find(function (connection) {
      return connection.id === props.renamingSignal?.connectionId
    })
    : undefined

  const createSubsystemButton = props.selectedBlockCount >= 2
    ? createElement(
      'button',
      { className: menuButtonClass, onClick: props.onCreateSubsystem },
      icon('M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z'),
      createElement('span', null, 'Create Subsystem'),
      createElement(
        'span',
        { className: 'ml-auto text-slate-400 text-xs' },
        `${props.selectedBlockCount} blocks`
      )
    )
    : null

  const subsystemButtons = props.selectedSubsystem
    ? createElement(
      Fragment,
      null,
      createElement(
        'button',
        {
          className: menuButtonClass,
          onClick: function () { props.onEnterSubsystem(props.selectedSubsystem!.id) },
        },
        icon('M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1'),
        createElement('span', null, 'Enter Subsystem')
      ),
      createElement(
        'button',
        { className: menuButtonClass, onClick: props.onExpandSubsystem },
        icon('M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4'),
        createElement('span', null, 'Expand Subsystem'),
        createElement(
          'span',
          { className: 'ml-auto text-slate-400 text-xs' },
          `${props.selectedSubsystem.children?.length || 0} blocks`
        )
      )
    )
    : null

  const blockMenu = props.contextMenu
    ? createElement(
      'div',
      {
        'data-testid': 'block-context-menu',
        className: 'absolute z-50 bg-slate-800 border border-slate-600 rounded-lg shadow-xl py-1 min-w-[180px]',
        style: { left: props.contextMenu.x, top: props.contextMenu.y },
      },
      createSubsystemButton,
      subsystemButtons
    )
    : null

  const signalMenu = props.signalContextMenu
    ? createElement(
      'div',
      {
        'data-testid': 'signal-context-menu',
        className: 'absolute z-50 bg-slate-800 border border-slate-600 rounded-lg shadow-xl py-1 min-w-[200px]',
        style: { left: props.signalContextMenu.x, top: props.signalContextMenu.y },
        onClick: function (event) { event.stopPropagation() },
      },
      menuButton('Rename Signal', props.onRenameSignal, 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z'),
      menuButton('Delete', props.onSignalDiscard, 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16', 'Del'),
      signalConnection?.signalName
        ? menuButton('Delete Label', props.onLabelDiscard, 'M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z')
        : null,
      separator(),
      menuButton('Highlight to Source', props.onHighlightToSource, 'M11 19l-7-7 7-7m8 14l-7-7 7-7', 'Ctrl+Shift+S'),
      menuButton('Highlight to Destination', props.onHighlightToDestination, 'M13 5l7 7-7 7M5 5l7 7-7 7', 'Ctrl+Shift+D'),
      props.highlightedConnectionCount > 0
        ? menuButton('Remove Highlighting', props.onClearHighlighting, 'M6 18L18 6M6 6l12 12', 'Ctrl+Shift+H')
        : null,
      separator(),
      menuButton('Auto-route Line', props.onAutoRouteSignal, 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15')
    )
    : null

  const renameInput = props.renamingSignal
    ? createElement(
      'div',
      {
        'data-testid': 'signal-rename-menu',
        className: 'absolute z-50',
        style: { left: props.renamingSignal.x, top: props.renamingSignal.y },
        onClick: function (event) { event.stopPropagation() },
      },
      createElement('input', {
        ref: signalNameInputRef,
        type: 'text',
        defaultValue: renamedConnection?.signalName || '',
        onKeyDown: function (event) {
          event.stopPropagation()
          if (event.key === 'Enter') {
            props.onSaveSignalName(event.currentTarget.value)
          } else if (event.key === 'Escape') {
            props.onCancelSignalRename()
          }
        },
        onBlur: function (event) { props.onSaveSignalName(event.currentTarget.value) },
        className: 'px-2 py-1 text-sm border border-blue-500 rounded bg-slate-800 text-white outline-none min-w-[120px]',
        placeholder: 'Signal name',
      })
    )
    : null

  return createElement(Fragment, null, blockMenu, signalMenu, renameInput)
}
