import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { blockRegistry } from '../blocks'
import { useModelStore } from '../store/modelStore'
import type { BlockDefinition, BlockInstance, Connection } from '../types/block'
import {
  createEditorKeyDownHandler,
  useEditorKeyboardShortcuts,
  type EditorClipboard,
  type EditorKeyboardShortcutOptions,
} from './useEditorKeyboardShortcuts'

const propertyFocus = vi.hoisted(function () {
  return vi.fn(function () { return false })
})

vi.mock('../components/Properties/PropertiesPanel', function () {
  return { getIsPropertiesFocused: propertyFocus }
})

const definition: BlockDefinition = {
  type: 'constant',
  category: 'sources',
  name: 'Constant',
  description: 'test',
  inputs: [],
  outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
  parameters: [],
}

function makeBlock(id: string, overrides: Partial<BlockInstance> = {}): BlockInstance {
  return {
    id,
    type: 'constant',
    name: id,
    position: { x: 10, y: 20 },
    parameters: {},
    inputPorts: [],
    outputPorts: [{ id: `${id}-out`, name: 'out', dataType: 'double', dimensions: [1] }],
    ...overrides,
  }
}

function makeConnection(id: string, source = 'a', target = 'b'): Connection {
  return {
    id,
    sourceBlockId: source,
    sourcePortId: `${source}-out`,
    targetBlockId: target,
    targetPortId: `${target}-in`,
  }
}

function makeOptions(
  overrides: Partial<EditorKeyboardShortcutOptions> = {}
): EditorKeyboardShortcutOptions {
  return {
    inputFocused: false,
    selectedBlockIds: [],
    selectedEdgeId: null,
    currentBlocks: [],
    currentConnections: [],
    dropBlock: vi.fn(),
    dropConnection: vi.fn(),
    selectBlocks: vi.fn(),
    addBlock: vi.fn(function () { return 'new-block' }),
    addConnection: vi.fn(function () { return 'new-connection' }),
    spreadBlocks: vi.fn(),
    rotateSelectedBlocks: vi.fn(),
    undo: vi.fn(),
    redo: vi.fn(),
    pushHistory: vi.fn(),
    setSelectedEdgeId: vi.fn(),
    setHighlightedConnections: vi.fn(),
    ...overrides,
  }
}

function makeHandler(
  options: EditorKeyboardShortcutOptions,
  clipboard: EditorClipboard = { blocks: [], connections: [] },
  onClipboard = vi.fn()
) {
  return createEditorKeyDownHandler({
    ...options,
    clipboard,
    setClipboard: onClipboard,
  })
}

function keyEvent(key: string, init: KeyboardEventInit = {}) {
  return new KeyboardEvent('keydown', { key, cancelable: true, ...init })
}

describe('createEditorKeyDownHandler', function () {
  beforeEach(function () {
    propertyFocus.mockReturnValue(false)
    useModelStore.getState().createNewModel('Shortcut test')
  })

  afterEach(function () {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('ignores shortcuts while an editor or properties input has focus', function () {
    const focusedOptions = makeOptions({ inputFocused: true })
    makeHandler(focusedOptions)(keyEvent('a', { ctrlKey: true }))
    expect(focusedOptions.selectBlocks).not.toHaveBeenCalled()

    propertyFocus.mockReturnValue(true)
    const propertyOptions = makeOptions()
    makeHandler(propertyOptions)(keyEvent('a', { ctrlKey: true }))
    expect(propertyOptions.selectBlocks).not.toHaveBeenCalled()
  })

  it('removes selected blocks and an edge with one history entry', function () {
    const options = makeOptions({
      selectedBlockIds: ['a', 'b'],
      selectedEdgeId: 'edge-1',
    })
    const event = keyEvent('Delete')

    makeHandler(options)(event)

    expect(event.defaultPrevented).toBe(true)
    expect(options.pushHistory).toHaveBeenCalledOnce()
    expect(options.dropBlock).toHaveBeenCalledTimes(2)
    expect(options.dropBlock).toHaveBeenNthCalledWith(1, 'a')
    expect(options.dropConnection).toHaveBeenCalledWith('edge-1')
    expect(options.setSelectedEdgeId).toHaveBeenCalledWith(null)
  })

  it('handles removal keys when there is nothing selected', function () {
    const options = makeOptions()
    makeHandler(options)(keyEvent('Backspace'))
    expect(options.pushHistory).not.toHaveBeenCalled()
    expect(options.dropBlock).not.toHaveBeenCalled()
    expect(options.dropConnection).not.toHaveBeenCalled()
  })

  it('handles selection, save, layout, rotation, undo, and redo commands', function () {
    const blocks = [makeBlock('a'), makeBlock('b')]
    const options = makeOptions({ currentBlocks: blocks })
    const saveModel = vi.spyOn(useModelStore.getState(), 'saveModel')
    const handler = makeHandler(options)

    handler(keyEvent('a', { metaKey: true }))
    handler(keyEvent('s', { ctrlKey: true }))
    handler(keyEvent(']', { ctrlKey: true }))
    handler(keyEvent('[', { ctrlKey: true }))
    handler(keyEvent('r', { ctrlKey: true }))
    handler(keyEvent('z', { ctrlKey: true }))
    handler(keyEvent('y', { ctrlKey: true }))
    handler(keyEvent('z', { ctrlKey: true, shiftKey: true }))

    expect(options.selectBlocks).toHaveBeenCalledWith(['a', 'b'])
    expect(saveModel).toHaveBeenCalledOnce()
    expect(options.spreadBlocks).toHaveBeenNthCalledWith(1, 1.05)
    expect(options.spreadBlocks).toHaveBeenNthCalledWith(2, 0.95)
    expect(options.rotateSelectedBlocks).toHaveBeenCalledOnce()
    expect(options.undo).toHaveBeenCalledOnce()
    expect(options.redo).toHaveBeenCalledTimes(2)
    expect(options.pushHistory).toHaveBeenCalledTimes(3)
  })

  it('handles source, destination, and clear highlighting commands', function () {
    const selected = makeConnection('selected', 'b', 'c')
    const sibling = makeConnection('sibling', 'b', 'other')
    const downstream = makeConnection('downstream', 'c', 'd')
    const options = makeOptions({
      selectedEdgeId: selected.id,
      currentConnections: [sibling, selected, downstream],
    })
    const handler = makeHandler(options)

    handler(keyEvent('s', { ctrlKey: true, shiftKey: true }))
    handler(keyEvent('D', { metaKey: true, shiftKey: true }))
    handler(keyEvent('h', { ctrlKey: true, shiftKey: true }))

    expect(options.setHighlightedConnections).toHaveBeenCalledTimes(3)
    expect(options.setHighlightedConnections).toHaveBeenNthCalledWith(
      1,
      new globalThis.Set(['sibling', 'selected'])
    )
    expect(options.setHighlightedConnections).toHaveBeenNthCalledWith(
      2,
      new globalThis.Set(['selected', 'downstream'])
    )
    expect(options.setHighlightedConnections).toHaveBeenNthCalledWith(3, new globalThis.Set())
  })

  it('does not highlight when the selected connection is stale', function () {
    const options = makeOptions({ selectedEdgeId: 'missing' })
    const handler = makeHandler(options)
    handler(keyEvent('S', { ctrlKey: true, shiftKey: true }))
    handler(keyEvent('d', { ctrlKey: true, shiftKey: true }))
    expect(options.setHighlightedConnections).not.toHaveBeenCalled()
  })

  it('copies selected blocks and only their internal connections', function () {
    const a = makeBlock('a')
    const b = makeBlock('b', {
      inputPorts: [{ id: 'b-in', name: 'in', dataType: 'double', dimensions: [1] }],
    })
    const internal = makeConnection('internal')
    const external = makeConnection('external', 'b', 'outside')
    const setClipboard = vi.fn()
    const options = makeOptions({
      selectedBlockIds: ['a', 'b'],
      currentBlocks: [a, b],
      currentConnections: [internal, external],
    })

    makeHandler(options, undefined, setClipboard)(keyEvent('c', { ctrlKey: true }))

    expect(setClipboard).toHaveBeenCalledWith({
      blocks: [a, b],
      connections: [{
        sourceBlockId: 'a',
        sourcePortId: 'a-out',
        targetBlockId: 'b',
        targetPortId: 'b-in',
      }],
    })
    expect(setClipboard.mock.calls[0][0].blocks[0]).not.toBe(a)
  })

  it('leaves the clipboard unchanged when copying an empty selection', function () {
    const setClipboard = vi.fn()
    makeHandler(makeOptions(), undefined, setClipboard)(keyEvent('c', { metaKey: true }))
    expect(setClipboard).not.toHaveBeenCalled()
  })

  it('pastes blocks, restores parameters, reconnects ports, and advances the clipboard', function () {
    vi.useFakeTimers()
    vi.spyOn(blockRegistry, 'get').mockReturnValue(definition)
    const updateParameters = vi.spyOn(useModelStore.getState(), 'updateBlockParameters')
    const a = makeBlock('a', { parameters: { value: 7 } })
    const b = makeBlock('b', {
      inputPorts: [{ id: 'b-in', name: 'in', dataType: 'double', dimensions: [1] }],
    })
    const clipboard: EditorClipboard = {
      blocks: [a, b],
      connections: [{
        sourceBlockId: 'a',
        sourcePortId: 'a-out',
        targetBlockId: 'b',
        targetPortId: 'b-in',
      }],
    }
    const addBlock = vi.fn()
      .mockReturnValueOnce('new-a')
      .mockReturnValueOnce('new-b')
    const setClipboard = vi.fn()
    const options = makeOptions({ addBlock })

    makeHandler(options, clipboard, setClipboard)(keyEvent('v', { ctrlKey: true }))
    vi.runAllTimers()

    expect(options.pushHistory).toHaveBeenCalledOnce()
    expect(addBlock).toHaveBeenNthCalledWith(1, definition, { x: 60, y: 70 })
    expect(updateParameters).toHaveBeenCalledWith('new-a', { value: 7 })
    expect(options.addConnection).toHaveBeenCalledWith({
      sourceBlockId: 'new-a',
      sourcePortId: 'new-a-out-0',
      targetBlockId: 'new-b',
      targetPortId: 'new-b-in-0',
    })
    expect(options.selectBlocks).toHaveBeenCalledWith(['new-a', 'new-b'])

    const updater = setClipboard.mock.calls[0][0]
    expect(updater(clipboard).blocks.map(function (block: BlockInstance) { return block.position })).toEqual([
      { x: 60, y: 70 },
      { x: 60, y: 70 },
    ])
  })

  it('does nothing when paste is requested with an empty clipboard', function () {
    const options = makeOptions()
    makeHandler(options)(keyEvent('v', { metaKey: true }))
    expect(options.pushHistory).not.toHaveBeenCalled()
    expect(options.addBlock).not.toHaveBeenCalled()
  })

  it('skips unknown blocks, failed additions, and incomplete connections', function () {
    vi.useFakeTimers()
    const unknown = makeBlock('unknown', { type: 'not-registered' })
    const failed = makeBlock('failed')
    vi.spyOn(blockRegistry, 'get').mockImplementation(function (type) {
      return type === 'not-registered' ? undefined : definition
    })
    const options = makeOptions({ addBlock: vi.fn(function () { return '' }) })
    const clipboard: EditorClipboard = {
      blocks: [unknown, failed],
      connections: [{
        sourceBlockId: 'unknown',
        sourcePortId: 'unknown-out',
        targetBlockId: 'failed',
        targetPortId: 'failed-in',
      }],
    }

    makeHandler(options, clipboard)(keyEvent('v', { ctrlKey: true }))
    vi.runAllTimers()

    expect(options.addBlock).toHaveBeenCalledOnce()
    expect(options.addConnection).not.toHaveBeenCalled()
    expect(options.selectBlocks).not.toHaveBeenCalled()
  })

  it('restores copied subsystem contents when the delayed target is available', function () {
    vi.useFakeTimers()
    const subsystemDefinition = { ...definition, type: 'subsystem' }
    vi.spyOn(blockRegistry, 'get').mockReturnValue(subsystemDefinition)
    const child = makeBlock('child')
    const subsystem = makeBlock('source-subsystem', {
      type: 'subsystem',
      children: [child],
      childConnections: [],
    })
    const target = makeBlock('new-subsystem', { type: 'subsystem' })
    const options = makeOptions({ addBlock: vi.fn(function () { return target.id }) })
    const clipboard = { blocks: [subsystem], connections: [] }

    useModelStore.setState({ model: null })
    makeHandler(options, clipboard)(keyEvent('v', { ctrlKey: true }))
    vi.runAllTimers()

    useModelStore.getState().createNewModel('Missing target')
    makeHandler(options, clipboard)(keyEvent('v', { ctrlKey: true }))
    vi.runAllTimers()

    const model = useModelStore.getState().model
    expect(model).not.toBeNull()
    useModelStore.setState({ model: { ...model!, blocks: [target] } })
    const updateParameters = vi.spyOn(useModelStore.getState(), 'updateBlockParameters')
    makeHandler(options, clipboard)(keyEvent('v', { ctrlKey: true }))
    vi.runAllTimers()

    const pasted = useModelStore.getState().model!.blocks[0]
    expect(pasted.children).toHaveLength(1)
    expect(pasted.children![0].id).not.toBe(child.id)
    expect(updateParameters).toHaveBeenCalledWith(target.id, target.parameters)
  })
})

describe('useEditorKeyboardShortcuts', function () {
  it('registers the window listener and cleans it up on unmount', function () {
    const options = makeOptions({ currentBlocks: [makeBlock('a')] })
    const hook = renderHook(function () {
      useEditorKeyboardShortcuts(options)
    })

    act(function () {
      window.dispatchEvent(keyEvent('a', { ctrlKey: true }))
    })
    expect(options.selectBlocks).toHaveBeenCalledOnce()

    hook.unmount()
    window.dispatchEvent(keyEvent('a', { ctrlKey: true }))
    expect(options.selectBlocks).toHaveBeenCalledOnce()
  })
})
