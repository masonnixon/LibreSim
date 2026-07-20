import { useEffect, useState } from 'react'
import { blockRegistry } from '../blocks'
import { getIsPropertiesFocused } from '../components/Properties/PropertiesPanel'
import { useModelStore } from '../store/modelStore'
import type { BlockDefinition, BlockInstance, Connection } from '../types/block'
import { getDownstreamConnectionIds, getSourceBranchConnectionIds } from '../utils/signalTraversal'
import { deepCopySubsystemContents } from '../utils/subsystemUtils'

interface ClipboardConnection {
  sourceBlockId: string
  sourcePortId: string
  targetBlockId: string
  targetPortId: string
}

export interface EditorClipboard {
  blocks: BlockInstance[]
  connections: ClipboardConnection[]
}

export interface EditorKeyboardShortcutOptions {
  inputFocused: boolean
  selectedBlockIds: string[]
  selectedEdgeId: string | null
  currentBlocks: BlockInstance[]
  currentConnections: Connection[]
  dropBlock: (blockId: string) => void
  dropConnection: (connectionId: string) => void
  selectBlocks: (blockIds: string[]) => void
  addBlock: (definition: BlockDefinition, position: { x: number; y: number }) => string
  addConnection: (connection: ClipboardConnection) => string | null
  spreadBlocks: (factor: number) => void
  rotateSelectedBlocks: () => void
  undo: () => void
  redo: () => void
  pushHistory: () => void
  setSelectedEdgeId: (edgeId: string | null) => void
  setHighlightedConnections: (connectionIds: ReturnType<typeof getSourceBranchConnectionIds>) => void
}

type ClipboardUpdater = EditorClipboard | ((previous: EditorClipboard) => EditorClipboard)

interface KeyboardHandlerOptions extends EditorKeyboardShortcutOptions {
  clipboard: EditorClipboard
  setClipboard: (update: ClipboardUpdater) => void
}

export function createEditorKeyDownHandler(options: KeyboardHandlerOptions) {
  return function handleKeyDown(event: KeyboardEvent) {
    if (options.inputFocused || getIsPropertiesFocused()) return

    const isCtrlOrCmd = event.ctrlKey || event.metaKey
    const isRemovalKey = event.key === 'Delete' || event.key === 'Backspace'

    if (isRemovalKey) {
      event.preventDefault()
      if (options.selectedBlockIds.length > 0 || options.selectedEdgeId) {
        options.pushHistory()
      }
      for (const blockId of options.selectedBlockIds) {
        options.dropBlock(blockId)
      }
      if (options.selectedEdgeId) {
        options.dropConnection(options.selectedEdgeId)
        options.setSelectedEdgeId(null)
      }
    }

    if (isCtrlOrCmd && event.key === 'a') {
      event.preventDefault()
      options.selectBlocks(options.currentBlocks.map(function (block) { return block.id }))
    }

    if (isCtrlOrCmd && event.key === 's') {
      event.preventDefault()
      useModelStore.getState().saveModel()
    }

    if (isCtrlOrCmd && event.key === ']') {
      event.preventDefault()
      options.pushHistory()
      options.spreadBlocks(1.05)
    }

    if (isCtrlOrCmd && event.key === '[') {
      event.preventDefault()
      options.pushHistory()
      options.spreadBlocks(0.95)
    }

    if (isCtrlOrCmd && event.key === 'r') {
      event.preventDefault()
      options.pushHistory()
      options.rotateSelectedBlocks()
    }

    if (isCtrlOrCmd && event.key === 'z' && !event.shiftKey) {
      event.preventDefault()
      options.undo()
    }

    if (isCtrlOrCmd && (event.key === 'y' || (event.key === 'z' && event.shiftKey))) {
      event.preventDefault()
      options.redo()
    }

    if (isCtrlOrCmd && event.shiftKey && options.selectedEdgeId) {
      if (event.key === 'S' || event.key === 's') {
        event.preventDefault()
        const connection = options.currentConnections.find(function (candidate) {
          return candidate.id === options.selectedEdgeId
        })
        if (connection) {
          options.setHighlightedConnections(
            getSourceBranchConnectionIds(connection, options.currentConnections)
          )
        }
      }

      if (event.key === 'D' || event.key === 'd') {
        event.preventDefault()
        const connection = options.currentConnections.find(function (candidate) {
          return candidate.id === options.selectedEdgeId
        })
        if (connection) {
          options.setHighlightedConnections(
            getDownstreamConnectionIds(connection, options.currentConnections)
          )
        }
      }

      if (event.key === 'H' || event.key === 'h') {
        event.preventDefault()
        options.setHighlightedConnections(new globalThis.Set())
      }
    }

    if (isCtrlOrCmd && event.key === 'c') {
      event.preventDefault()
      if (options.selectedBlockIds.length > 0) {
        const blocks = options.currentBlocks.filter(function (block) {
          return options.selectedBlockIds.includes(block.id)
        })
        const connections = options.currentConnections
          .filter(function (connection) {
            return options.selectedBlockIds.includes(connection.sourceBlockId) &&
              options.selectedBlockIds.includes(connection.targetBlockId)
          })
          .map(function (connection) {
            return {
              sourceBlockId: connection.sourceBlockId,
              sourcePortId: connection.sourcePortId,
              targetBlockId: connection.targetBlockId,
              targetPortId: connection.targetPortId,
            }
          })

        options.setClipboard({
          blocks: JSON.parse(JSON.stringify(blocks)),
          connections: JSON.parse(JSON.stringify(connections)),
        })
      }
    }

    if (isCtrlOrCmd && event.key === 'v') {
      event.preventDefault()
      pasteClipboard(options)
    }
  }
}

function pasteClipboard(options: KeyboardHandlerOptions) {
  if (options.clipboard.blocks.length === 0) return

  options.pushHistory()
  const pasteOffset = { x: 50, y: 50 }
  const newBlockIds: string[] = []
  const oldToNewIdMap = new Map<string, string>()
  const oldToNewPortIdMap = new Map<string, string>()

  for (const block of options.clipboard.blocks) {
    const definition = blockRegistry.get(block.type)
    if (!definition) continue

    const newId = options.addBlock(definition, {
      x: block.position.x + pasteOffset.x,
      y: block.position.y + pasteOffset.y,
    })
    if (!newId) continue

    newBlockIds.push(newId)
    oldToNewIdMap.set(block.id, newId)

    block.inputPorts.forEach(function (port, index) {
      oldToNewPortIdMap.set(port.id, `${newId}-in-${index}`)
    })
    block.outputPorts.forEach(function (port, index) {
      oldToNewPortIdMap.set(port.id, `${newId}-out-${index}`)
    })

    if (Object.keys(block.parameters).length > 0) {
      setTimeout(function () {
        useModelStore.getState().updateBlockParameters(newId, block.parameters)
      }, 0)
    }

    if (block.type === 'subsystem' && block.children && block.children.length > 0) {
      const copied = deepCopySubsystemContents(block.children, block.childConnections, newId)
      setTimeout(function () {
        const state = useModelStore.getState()
        const model = state.model
        if (!model) return

        const blockToUpdate = model.blocks.find(function (candidate) { return candidate.id === newId })
        if (!blockToUpdate) return

        blockToUpdate.children = copied.children
        blockToUpdate.childConnections = copied.childConnections
        state.updateBlockParameters(newId, blockToUpdate.parameters)
      }, 0)
    }
  }

  if (options.clipboard.connections.length > 0) {
    setTimeout(function () {
      for (const connection of options.clipboard.connections) {
        const sourceBlockId = oldToNewIdMap.get(connection.sourceBlockId)
        const targetBlockId = oldToNewIdMap.get(connection.targetBlockId)
        const sourcePortId = oldToNewPortIdMap.get(connection.sourcePortId)
        const targetPortId = oldToNewPortIdMap.get(connection.targetPortId)

        if (sourceBlockId && targetBlockId && sourcePortId && targetPortId) {
          options.addConnection({ sourceBlockId, sourcePortId, targetBlockId, targetPortId })
        }
      }
    }, 10)
  }

  if (newBlockIds.length > 0) {
    options.selectBlocks(newBlockIds)
  }

  options.setClipboard(function (previous) {
    return {
      ...previous,
      blocks: previous.blocks.map(function (block) {
        return {
          ...block,
          position: {
            x: block.position.x + pasteOffset.x,
            y: block.position.y + pasteOffset.y,
          },
        }
      }),
    }
  })
}

export function useEditorKeyboardShortcuts(options: EditorKeyboardShortcutOptions) {
  const [clipboard, setClipboard] = useState<EditorClipboard>({ blocks: [], connections: [] })

  useEffect(function () {
    const handleKeyDown = createEditorKeyDownHandler({ ...options, clipboard, setClipboard })
    window.addEventListener('keydown', handleKeyDown)
    return function () {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [options, clipboard])
}
