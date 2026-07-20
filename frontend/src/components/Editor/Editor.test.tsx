/* eslint-disable @typescript-eslint/no-explicit-any -- ReactFlow callback harness exercises a broad prop surface. */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Editor } from './Editor'

let latestFlowProps: Record<string, any> = {}
let latestMiniMapProps: Record<string, any> = {}
let latestContextProps: Record<string, any> = {}
const nodeChanges = vi.fn()
const edgeChanges = vi.fn()
const flowApi = {
  screenToFlowPosition: vi.fn((point: { x: number; y: number }) => point),
  fitView: vi.fn(),
}

vi.mock('@xyflow/react', async function () {
  const React = await import('react')
  return {
    ReactFlow: function (props: Record<string, any>) {
      latestFlowProps = props
      return React.createElement(
        'div',
        { 'data-testid': 'react-flow' },
        props.children
      )
    },
    ReactFlowProvider: function ({ children }: { children: React.ReactNode }) {
      return children
    },
    Background: function () {
      return React.createElement('div', { 'data-testid': 'background' })
    },
    Controls: function () {
      return React.createElement('div', { 'data-testid': 'controls' })
    },
    Panel: function ({ children }: { children: React.ReactNode }) {
      return React.createElement('div', {}, children)
    },
    MiniMap: function (props: Record<string, any>) {
      latestMiniMapProps = props
      return React.createElement('div', { 'data-testid': 'minimap' })
    },
    useReactFlow: function () {
      return flowApi
    },
    useNodesState: function (initial: any[]) {
      const [nodes, setNodes] = React.useState(initial)
      const onChange = React.useCallback(
        (changes: any[]) => nodeChanges(changes),
        []
      )
      return [nodes, setNodes, onChange]
    },
    useEdgesState: function (initial: any[]) {
      const [edges, setEdges] = React.useState(initial)
      const onChange = React.useCallback(
        (changes: any[]) => edgeChanges(changes),
        []
      )
      return [edges, setEdges, onChange]
    },
  }
})

vi.mock('../../store/modelStore', function () {
  const store = Object.assign(vi.fn(), { getState: vi.fn() })
  return { useModelStore: store }
})
vi.mock('../../store/uiStore', function () {
  return { useUIStore: vi.fn() }
})
vi.mock('../../blocks', function () {
  return { blockRegistry: { get: vi.fn() } }
})
vi.mock('../../utils/smartRouting', function () {
  return { findNearestEdge: vi.fn(), generateSmartWaypoints: vi.fn() }
})
vi.mock('../../utils/signalTraversal', function () {
  return {
    getDownstreamConnectionIds: vi.fn(),
    getSourceBranchConnectionIds: vi.fn(),
  }
})
vi.mock('../Properties/PropertiesPanel', function () {
  return { getIsPropertiesFocused: vi.fn() }
})
vi.mock('../../hooks/useEditorKeyboardShortcuts', function () {
  return { useEditorKeyboardShortcuts: vi.fn() }
})
vi.mock('./ContextMenu', async function () {
  const React = await import('react')
  return {
    EditorContextMenus: function (props: Record<string, any>) {
      latestContextProps = props
      return React.createElement('div', { 'data-testid': 'context-menus' })
    },
  }
})
vi.mock('./BlockNode', function () {
  return {
    BlockNode: function () {
      return null
    },
  }
})
vi.mock('./SubsystemNode', function () {
  return {
    SubsystemNode: function () {
      return null
    },
  }
})
vi.mock('./CustomEdge', function () {
  return {
    CustomEdge: function () {
      return null
    },
  }
})

import { useModelStore } from '../../store/modelStore'
import { useUIStore } from '../../store/uiStore'
import { blockRegistry } from '../../blocks'
import {
  findNearestEdge,
  generateSmartWaypoints,
} from '../../utils/smartRouting'
import {
  getDownstreamConnectionIds,
  getSourceBranchConnectionIds,
} from '../../utils/signalTraversal'
import { getIsPropertiesFocused } from '../Properties/PropertiesPanel'
import { useEditorKeyboardShortcuts } from '../../hooks/useEditorKeyboardShortcuts'

const actions = {
  addBlock: vi.fn(),
  updateBlockPosition: vi.fn(),
  addConnection: vi.fn(),
  addScopeInput: vi.fn(),
  selectBlocks: vi.fn(),
  createSubsystem: vi.fn(),
  expandSubsystem: vi.fn(),
  enterSubsystem: vi.fn(),
  exitSubsystem: vi.fn(),
  navigateToPath: vi.fn(),
  spreadBlocks: vi.fn(),
  rotateSelectedBlocks: vi.fn(),
  undo: vi.fn(),
  redo: vi.fn(),
  pushHistory: vi.fn(),
  removeBlock: vi.fn(),
  removeConnection: vi.fn(),
}
const updateConnectionSignalName = vi.fn()
const updateConnectionWaypoints = vi.fn()
const clearConnectionWaypoints = vi.fn()
const uiActions = { setDraggingBlockType: vi.fn(), openPlotWindow: vi.fn() }

let currentBlocks: any[] = []
let currentConnections: any[] = []
let model: any
let selectedBlockIds: string[] = []
let currentPath: Array<{ id: string; name: string }> = []
let draggingBlockType: string | null = null

const definition = {
  type: 'gain',
  category: 'math',
  name: 'Gain',
  description: '',
  inputs: [],
  outputs: [],
  parameters: [],
  icon: 'G',
}

function block(overrides: Record<string, any> = {}) {
  return {
    id: 'block-1',
    type: 'gain',
    name: 'Gain',
    position: { x: 10, y: 20 },
    parameters: {},
    inputPorts: [{ id: 'in', name: 'in', dataType: 'double', dimensions: [1] }],
    outputPorts: [
      { id: 'out', name: 'out', dataType: 'double', dimensions: [1] },
    ],
    ...overrides,
  }
}

function connection(overrides: Record<string, any> = {}) {
  return {
    id: 'connection-1',
    sourceBlockId: 'source',
    sourcePortId: 'out',
    targetBlockId: 'target',
    targetPortId: 'in',
    ...overrides,
  }
}

function configureStore() {
  model = {
    id: 'model',
    metadata: { name: 'Model' },
    blocks: currentBlocks,
    connections: currentConnections,
    simulationConfig: {},
  }
  vi.mocked(useModelStore).mockReturnValue({
    model,
    ...actions,
    selectedBlockIds,
    currentPath,
    getCurrentBlocks: () => currentBlocks,
    getCurrentConnections: () => currentConnections,
  } as never)
  vi.mocked(useUIStore).mockReturnValue({
    draggingBlockType,
    ...uiActions,
  } as never)
  ;(useModelStore.getState as ReturnType<typeof vi.fn>).mockReturnValue({
    updateConnectionSignalName,
    updateConnectionWaypoints,
    clearConnectionWaypoints,
  })
}

describe('Editor', function () {
  beforeEach(function () {
    vi.clearAllMocks()
    currentBlocks = []
    currentConnections = []
    selectedBlockIds = []
    currentPath = []
    draggingBlockType = JSON.parse('null')
    latestFlowProps = {}
    latestMiniMapProps = {}
    latestContextProps = {}
    Object.defineProperty(window, 'innerWidth', {
      configurable: true,
      writable: true,
      value: 1024,
    })
    vi.mocked(blockRegistry.get).mockReturnValue(definition as never)
    vi.mocked(generateSmartWaypoints).mockReturnValue([])
    vi.mocked(findNearestEdge).mockReturnValue(JSON.parse('null'))
    vi.mocked(getSourceBranchConnectionIds).mockReturnValue(new Set(['source']))
    vi.mocked(getDownstreamConnectionIds).mockReturnValue(
      new Set(['downstream'])
    )
    vi.mocked(getIsPropertiesFocused).mockReturnValue(false)
    configureStore()
  })

  it('renders the empty-model state', function () {
    vi.mocked(useModelStore).mockReturnValue({
      ...(useModelStore() as object),
      model: JSON.parse('null'),
    } as never)
    render(<Editor />)
    expect(screen.getByText('No model loaded')).toBeInTheDocument()
    expect(useEditorKeyboardShortcuts).toHaveBeenCalled()
  })

  it('projects nodes and validates model connections', async function () {
    currentBlocks = [
      block({
        id: 'source',
        size: { width: 120, height: 60 },
        outputPorts: [
          { id: 'out', name: 'out', dataType: 'double', dimensions: [2, 3] },
        ],
      }),
      block({ id: 'target', type: 'subsystem' }),
      block({
        id: 'unknown',
        type: 'mystery',
        name: '',
        inputPorts: [{ id: 'in', name: 'i' }],
        outputPorts: [{ id: 'out', name: 'o' }],
      }),
    ]
    currentConnections = [
      connection(),
      connection({ id: 'no-source', sourceBlockId: 'missing' }),
      connection({ id: 'no-target', targetBlockId: 'missing' }),
      connection({ id: 'no-source-port', sourcePortId: 'missing' }),
      connection({ id: 'no-target-port', targetPortId: 'missing' }),
    ]
    selectedBlockIds = ['source']
    vi.mocked(blockRegistry.get).mockImplementation((type) =>
      type === 'mystery' ? undefined : (definition as never)
    )
    configureStore()
    render(<Editor />)

    await waitFor(() => expect(latestFlowProps.nodes).toHaveLength(3))
    fireEvent(window, new Event('resize'))
    expect(latestMiniMapProps).toBeDefined()
    expect(latestContextProps).toBeDefined()
    expect(latestFlowProps.nodes[0]).toMatchObject({
      id: 'source',
      type: 'blockNode',
      width: 120,
      height: 60,
      selected: true,
    })
    expect(latestFlowProps.nodes[1]).toMatchObject({
      type: 'subsystemNode',
      selected: false,
    })
    expect(latestFlowProps.nodes[2].data.definition).toMatchObject({
      type: 'mystery',
      name: 'mystery',
      icon: '?',
    })
    expect(latestFlowProps.edges).toHaveLength(1)
    expect(latestFlowProps.edges[0]).toMatchObject({
      id: 'connection-1',
      type: 'custom',
      selected: false,
    })
  })

  it('filters ReactFlow changes around focused form controls', async function () {
    currentBlocks = [block()]
    configureStore()
    render(<Editor />)
    await waitFor(() => expect(latestFlowProps.nodes).toHaveLength(1))

    latestFlowProps.onEdgesChange([{ type: 'select' }])
    expect(edgeChanges).toHaveBeenCalledWith([{ type: 'select' }])
    edgeChanges.mockClear()
    latestFlowProps.onEdgesChange([{ type: 'remove', id: 'a' }])
    expect(edgeChanges).not.toHaveBeenCalled()
    latestFlowProps.onEdgesChange([
      { type: 'remove', id: 'a' },
      { type: 'select', id: 'b' },
    ])
    expect(edgeChanges).toHaveBeenCalledWith([{ type: 'select', id: 'b' }])

    latestFlowProps.onNodesChange([{ type: 'select' }])
    expect(nodeChanges).toHaveBeenCalledWith([{ type: 'select' }])
    const input = document.createElement('input')
    document.body.appendChild(input)
    fireEvent.focusIn(input)
    await waitFor(() => expect(latestFlowProps.deleteKeyCode).toBeNull())
    nodeChanges.mockClear()
    latestFlowProps.onNodesChange([{ type: 'select' }, { type: 'position' }])
    expect(nodeChanges).toHaveBeenCalledWith([{ type: 'position' }])
    nodeChanges.mockClear()
    latestFlowProps.onNodesChange([{ type: 'select' }])
    expect(nodeChanges).not.toHaveBeenCalled()
    fireEvent.focusOut(input)
    await waitFor(() =>
      expect(latestFlowProps.deleteKeyCode).toEqual(['Backspace', 'Delete'])
    )
    input.remove()
  })

  it('isolates keyboard events for every form-control type', async function () {
    const view = render(<Editor />)
    await waitFor(() =>
      expect(screen.getByTestId('react-flow')).toBeInTheDocument()
    )

    for (const tag of ['textarea', 'select']) {
      const control = document.createElement(tag)
      document.body.appendChild(control)
      fireEvent.focusIn(control)
      await waitFor(() => expect(latestFlowProps.deleteKeyCode).toBeNull())
      const keyboardEvent = new KeyboardEvent('keydown', { bubbles: true })
      const stopPropagation = vi.spyOn(keyboardEvent, 'stopPropagation')
      control.dispatchEvent(keyboardEvent)
      expect(stopPropagation).toHaveBeenCalled()
      fireEvent.focusOut(control)
      await waitFor(() =>
        expect(latestFlowProps.deleteKeyCode).toEqual(['Backspace', 'Delete'])
      )
      control.remove()
    }

    const div = document.createElement('div')
    document.body.appendChild(div)
    fireEvent.focusIn(div)
    fireEvent.focusOut(div)
    const divEvent = new KeyboardEvent('keydown', { bubbles: true })
    const stopPropagation = vi.spyOn(divEvent, 'stopPropagation')
    div.dispatchEvent(divEvent)
    expect(stopPropagation).not.toHaveBeenCalled()
    div.remove()
    view.unmount()
  })

  it('forwards node, edge, drag, delete, and selection lifecycle actions', async function () {
    currentBlocks = [block()]
    configureStore()
    render(<Editor />)
    await waitFor(() => expect(latestFlowProps.nodes).toHaveLength(1))
    latestFlowProps.onPaneClick()

    latestFlowProps.onNodeDragStart()
    latestFlowProps.onNodeDragStop(
      {},
      { id: 'block-1', position: { x: 40, y: 50 } }
    )
    latestFlowProps.onNodesDelete([{ id: 'a' }, { id: 'b' }])
    latestFlowProps.onEdgesDelete([{ id: 'c' }, { id: 'd' }])
    latestFlowProps.onSelectionChange({
      nodes: [
        { id: 'a', position: { x: 0, y: 0 } },
        { id: 'b', position: { x: 50, y: 60 } },
      ],
    })

    expect(actions.pushHistory).toHaveBeenCalled()
    expect(actions.updateBlockPosition).toHaveBeenCalledWith('block-1', {
      x: 40,
      y: 50,
    })
    expect(actions.removeBlock.mock.calls).toEqual([['a'], ['b']])
    expect(actions.removeConnection.mock.calls).toEqual([['c'], ['d']])
    expect(actions.selectBlocks).toHaveBeenCalledWith(['a', 'b'])
  })

  it('builds complete connections and smart routes while rejecting incomplete requests', async function () {
    currentBlocks = [
      block({
        id: 'source',
        size: { width: 120, height: 80 },
        outputPorts: [
          { id: 'out', name: 'out', dataType: 'double', dimensions: [1] },
        ],
      }),
      block({
        id: 'target',
        position: { x: 300, y: 100 },
        inputPorts: [
          { id: 'in', name: 'in', dataType: 'double', dimensions: [1] },
        ],
      }),
      block({ id: 'default-size' }),
    ]
    configureStore()
    render(<Editor />)
    await waitFor(() => expect(latestFlowProps.nodes).toHaveLength(3))

    latestFlowProps.onConnect({})
    latestFlowProps.onConnect({ source: 'source' })
    latestFlowProps.onConnect({ source: 'source', target: 'target' })
    latestFlowProps.onConnect({
      source: 'source',
      target: 'target',
      sourceHandle: 'out',
    })
    expect(actions.addConnection).not.toHaveBeenCalled()

    latestFlowProps.onConnect({
      source: 'source',
      target: 'target',
      sourceHandle: 'out',
      targetHandle: 'in',
    })
    expect(generateSmartWaypoints).toHaveBeenCalledWith(
      130,
      60,
      300,
      125,
      'source',
      'target',
      currentBlocks,
      currentConnections
    )
    expect(actions.addConnection).toHaveBeenCalledWith({
      sourceBlockId: 'source',
      sourcePortId: 'out',
      targetBlockId: 'target',
      targetPortId: 'in',
      waypoints: undefined,
    })

    vi.mocked(generateSmartWaypoints).mockReturnValue([{ x: 200, y: 70 }])
    latestFlowProps.onConnect({
      source: 'source',
      target: 'target',
      sourceHandle: 'missing',
      targetHandle: 'missing',
    })
    expect(actions.addConnection).toHaveBeenLastCalledWith(
      expect.objectContaining({ waypoints: [{ x: 200, y: 70 }] })
    )

    latestFlowProps.onConnect({
      source: 'missing',
      target: 'target',
      sourceHandle: 'out',
      targetHandle: 'in',
    })
    latestFlowProps.onConnect({
      source: 'source',
      target: 'missing',
      sourceHandle: 'out',
      targetHandle: 'in',
    })
    latestFlowProps.onConnect({
      source: 'default-size',
      target: 'target',
      sourceHandle: 'out',
      targetHandle: 'in',
    })
    expect(actions.addConnection).toHaveBeenCalledTimes(5)
  })

  it('branches from input ports and never falls through to a Scope body', async function () {
    currentBlocks = [
      block({ id: 'input' }),
      block({ id: 'scope', type: 'scope' }),
    ]
    currentConnections = [connection()]
    configureStore()
    render(<Editor />)
    await waitFor(() => expect(latestFlowProps.nodes).toHaveLength(2))

    latestFlowProps.onConnectStart(
      {},
      { nodeId: 'input', handleId: 'in', handleType: 'target' }
    )
    vi.mocked(findNearestEdge).mockReturnValue({
      connection: currentConnections[0],
      distance: 4,
    })
    latestFlowProps.onConnectEnd(
      { clientX: 25, clientY: 35, target: document.body },
      { fromNode: { id: 'input' }, fromHandle: { id: 'in' }, isValid: false }
    )
    expect(actions.addConnection).toHaveBeenCalledWith({
      sourceBlockId: 'source',
      sourcePortId: 'out',
      targetBlockId: 'input',
      targetPortId: 'in',
    })

    actions.addConnection.mockClear()
    vi.mocked(findNearestEdge).mockReturnValue(JSON.parse('null'))
    const scope = document.createElement('div')
    scope.className = 'react-flow__node'
    scope.setAttribute('data-id', 'scope')
    latestFlowProps.onConnectEnd(
      {
        changedTouches: [{ clientX: 50, clientY: 60 }],
        touches: [],
        target: scope,
      },
      { fromNode: { id: 'input' }, fromHandle: { id: 'in' }, isValid: false }
    )
    expect(flowApi.screenToFlowPosition).toHaveBeenLastCalledWith({
      x: 50,
      y: 60,
    })
    expect(actions.addScopeInput).not.toHaveBeenCalled()
    expect(actions.addConnection).not.toHaveBeenCalled()
  })

  it('auto-expands Scope body drops and rejected target ports', async function () {
    vi.useFakeTimers()
    currentBlocks = [
      block({ id: 'source' }),
      block({ id: 'scope', type: 'scope' }),
      block({ id: 'ordinary' }),
    ]
    configureStore()
    actions.addScopeInput.mockReturnValue('new-port')
    render(<Editor />)
    await vi.waitFor(() => expect(latestFlowProps.nodes).toHaveLength(3))

    latestFlowProps.onConnectStart(
      {},
      { nodeId: 'source', handleId: 'out', handleType: 'source' }
    )
    const scope = document.createElement('div')
    scope.className = 'react-flow__node'
    scope.setAttribute('data-id', 'scope')
    latestFlowProps.onConnectEnd(
      { clientX: 10, clientY: 20, target: scope },
      { fromNode: { id: 'source' }, fromHandle: { id: 'out' }, isValid: false }
    )
    vi.runOnlyPendingTimers()
    expect(actions.addConnection).toHaveBeenCalledWith({
      sourceBlockId: 'source',
      sourcePortId: 'out',
      targetBlockId: 'scope',
      targetPortId: 'new-port',
    })

    actions.addConnection.mockClear()
    latestFlowProps.onConnectEnd(
      { clientX: 10, clientY: 20, target: scope },
      {
        fromNode: { id: 'source' },
        fromHandle: { id: 'out' },
        toNode: { id: 'scope' },
        toHandle: { id: 'in' },
        isValid: true,
      }
    )
    vi.runOnlyPendingTimers()
    expect(actions.addScopeInput).toHaveBeenLastCalledWith('scope')
    expect(actions.addConnection).toHaveBeenCalledWith(
      expect.objectContaining({ targetPortId: 'new-port' })
    )
    vi.useRealTimers()
  })

  it('rejects incomplete and ineligible connection-end targets', async function () {
    vi.useFakeTimers()
    currentBlocks = [
      block({ id: 'source' }),
      block({ id: 'scope', type: 'scope' }),
      block({ id: 'ordinary' }),
    ]
    configureStore()
    render(<Editor />)
    await vi.waitFor(() => expect(latestFlowProps.nodes).toHaveLength(3))

    const mouse = { clientX: 10, clientY: 20, target: document.body }
    latestFlowProps.onConnectEnd(mouse, {
      fromHandle: { id: 'out' },
      isValid: false,
    })
    latestFlowProps.onConnectEnd(mouse, {
      fromNode: { id: 'source' },
      isValid: false,
    })
    latestFlowProps.onConnectEnd(
      { changedTouches: [], touches: [], target: document.body },
      { fromNode: { id: 'source' }, fromHandle: { id: 'out' }, isValid: false }
    )
    latestFlowProps.onConnectEnd(
      {
        changedTouches: [],
        touches: [{ clientX: 30, clientY: 40 }],
        target: document.body,
      },
      { fromNode: { id: 'source' }, fromHandle: { id: 'out' }, isValid: false }
    )
    expect(flowApi.screenToFlowPosition).toHaveBeenLastCalledWith({
      x: 30,
      y: 40,
    })

    latestFlowProps.onConnectEnd(
      { clientX: 10, clientY: 20, target: null },
      { fromNode: { id: 'source' }, fromHandle: { id: 'out' }, isValid: false }
    )
    const detached = document.createElement('div')
    latestFlowProps.onConnectEnd(
      { clientX: 10, clientY: 20, target: detached },
      { fromNode: { id: 'source' }, fromHandle: { id: 'out' }, isValid: false }
    )
    const noId = document.createElement('div')
    noId.className = 'react-flow__node'
    latestFlowProps.onConnectEnd(
      { clientX: 10, clientY: 20, target: noId },
      { fromNode: { id: 'source' }, fromHandle: { id: 'out' }, isValid: false }
    )
    const missing = document.createElement('div')
    missing.className = 'react-flow__node'
    missing.setAttribute('data-id', 'missing')
    latestFlowProps.onConnectEnd(
      { clientX: 10, clientY: 20, target: missing },
      { fromNode: { id: 'source' }, fromHandle: { id: 'out' }, isValid: false }
    )
    const ordinary = document.createElement('div')
    ordinary.className = 'react-flow__node'
    ordinary.setAttribute('data-id', 'ordinary')
    latestFlowProps.onConnectEnd(
      { clientX: 10, clientY: 20, target: ordinary },
      { fromNode: { id: 'source' }, fromHandle: { id: 'out' }, isValid: false }
    )
    const scope = document.createElement('div')
    scope.className = 'react-flow__node'
    scope.setAttribute('data-id', 'scope')
    actions.addScopeInput.mockReturnValueOnce(undefined)
    latestFlowProps.onConnectEnd(
      { clientX: 10, clientY: 20, target: scope },
      { fromNode: { id: 'source' }, fromHandle: { id: 'out' }, isValid: false }
    )

    latestFlowProps.onConnectEnd(mouse, {
      fromNode: { id: 'source' },
      fromHandle: { id: 'out' },
      toHandle: { id: 'in' },
      isValid: true,
    })
    latestFlowProps.onConnectEnd(mouse, {
      fromNode: { id: 'source' },
      fromHandle: { id: 'out' },
      toNode: { id: 'scope' },
      isValid: true,
    })
    latestFlowProps.onConnectEnd(mouse, {
      fromNode: { id: 'source' },
      fromHandle: { id: 'out' },
      toNode: { id: 'missing' },
      toHandle: { id: 'in' },
      isValid: true,
    })
    latestFlowProps.onConnectEnd(mouse, {
      fromNode: { id: 'source' },
      fromHandle: { id: 'out' },
      toNode: { id: 'ordinary' },
      toHandle: { id: 'in' },
      isValid: true,
    })

    actions.addScopeInput.mockReturnValueOnce(undefined)
    latestFlowProps.onConnectEnd(mouse, {
      fromNode: { id: 'source' },
      fromHandle: { id: 'out' },
      toNode: { id: 'scope' },
      toHandle: { id: 'in' },
      isValid: true,
    })
    vi.runOnlyPendingTimers()

    actions.addConnection.mockClear()
    currentConnections = [connection({ targetBlockId: 'scope' })]
    latestFlowProps.onConnectEnd(mouse, {
      fromNode: { id: 'source' },
      fromHandle: { id: 'out' },
      toNode: { id: 'scope' },
      toHandle: { id: 'in' },
      isValid: true,
    })
    vi.runOnlyPendingTimers()
    expect(actions.addConnection).not.toHaveBeenCalled()
    vi.useRealTimers()
  })

  it('handles drag-over, absent drops, stale block types, and valid drops', async function () {
    render(<Editor />)
    await waitFor(() =>
      expect(screen.getByTestId('react-flow')).toBeInTheDocument()
    )
    const dragOver = {
      preventDefault: vi.fn(),
      dataTransfer: { dropEffect: 'none' },
    }
    latestFlowProps.onDragOver(dragOver)
    expect(dragOver.preventDefault).toHaveBeenCalled()
    expect(dragOver.dataTransfer.dropEffect).toBe('move')

    latestFlowProps.onDrop({ preventDefault: vi.fn() })
    expect(actions.addBlock).not.toHaveBeenCalled()

    draggingBlockType = 'stale'
    configureStore()
    vi.mocked(blockRegistry.get).mockReturnValue(undefined)
    const stale = render(<Editor />)
    await waitFor(() =>
      expect(screen.getAllByTestId('react-flow')).toHaveLength(2)
    )
    latestFlowProps.onDrop({
      preventDefault: vi.fn(),
      clientX: 30,
      clientY: 40,
    })
    expect(uiActions.setDraggingBlockType).toHaveBeenCalledWith(null)
    stale.unmount()

    draggingBlockType = 'gain'
    configureStore()
    vi.mocked(blockRegistry.get).mockReturnValue(definition as never)
    render(<Editor />)
    latestFlowProps.onDrop({
      preventDefault: vi.fn(),
      clientX: 70,
      clientY: 80,
    })
    expect(flowApi.screenToFlowPosition).toHaveBeenLastCalledWith({
      x: 70,
      y: 80,
    })
    expect(actions.addBlock).toHaveBeenCalledWith(definition, { x: 70, y: 80 })
    expect(actions.pushHistory).toHaveBeenCalled()
    expect(uiActions.setDraggingBlockType).toHaveBeenLastCalledWith(null)
  })

  it('selects edges, shows dimensions, and suppresses propagated pane clicks', async function () {
    currentBlocks = [
      block({
        id: 'source',
        outputPorts: [
          { id: 'out', name: 'out', dataType: 'double', dimensions: [2, 3] },
        ],
      }),
      block({ id: 'target' }),
    ]
    currentConnections = [
      connection({
        waypoints: [{ x: 10, y: 20 }],
        signalName: 'speed',
        labelOffset: { t: 0.2, perpOffset: 3 },
      }),
    ]
    configureStore()
    const now = vi.spyOn(Date, 'now').mockReturnValue(1000)
    render(<Editor />)
    await waitFor(() => expect(latestFlowProps.edges).toHaveLength(1))
    const edge = latestFlowProps.edges[0]
    latestFlowProps.onEdgeClick({}, edge)
    await waitFor(() => expect(latestFlowProps.edges[0].selected).toBe(true))
    expect(latestFlowProps.edges[0]).toMatchObject({
      label: '2×3',
      style: { stroke: '#22d3ee' },
      data: { waypoints: [{ x: 10, y: 20 }], signalName: 'speed' },
    })

    now.mockReturnValue(1200)
    latestFlowProps.onEdgeClick({}, edge)
    latestFlowProps.onPaneClick()
    expect(latestFlowProps.edges[0].selected).toBe(true)
    const event = { stopPropagation: vi.fn(), preventDefault: vi.fn() }
    now.mockReturnValue(2000)
    latestFlowProps.onEdgeDoubleClick(event, edge)
    expect(event.preventDefault).toHaveBeenCalled()
    now.mockReturnValue(2200)
    latestFlowProps.onPaneClick()
    expect(latestFlowProps.edges[0].selected).toBe(true)

    latestFlowProps.edges[0].data.onDragStateChange(true)
    await waitFor(() => expect(latestFlowProps.edges[0].selected).toBe(true))
    now.mockReturnValue(4000)
    latestFlowProps.onPaneClick()
    expect(latestFlowProps.edges[0].selected).toBe(true)
    latestFlowProps.edges[0].data.onDragStateChange(false)
    await waitFor(() => expect(latestFlowProps.edges[0].selected).toBe(true))
    latestFlowProps.onPaneClick()
    await waitFor(() => expect(latestFlowProps.edges[0].selected).toBe(false))
  })

  it('previews branch targets while dragging from an input', async function () {
    currentBlocks = [
      block({ id: 'source', outputPorts: [{ id: 'out', name: 'out' }] }),
      block({ id: 'target' }),
    ]
    currentConnections = [connection()]
    configureStore()
    render(<Editor />)
    await waitFor(() => expect(latestFlowProps.edges).toHaveLength(1))

    act(() => {
      latestFlowProps.onConnectStart(
        {},
        { nodeId: 'target', handleId: 'in', handleType: 'target' }
      )
    })
    vi.mocked(findNearestEdge).mockReturnValue({
      connection: currentConnections[0],
      distance: 2,
    })
    fireEvent.mouseMove(window, { clientX: 12, clientY: 13 })
    await waitFor(() =>
      expect(latestFlowProps.edges[0].style).toEqual({
        stroke: '#22c55e',
        strokeWidth: 3,
      })
    )
    vi.mocked(findNearestEdge).mockReturnValue(JSON.parse('null'))
    fireEvent.mouseMove(window, { clientX: 30, clientY: 40 })
    await waitFor(() => expect(latestFlowProps.edges[0].style).toBeUndefined())
    act(() => latestFlowProps.onEdgeClick({}, latestFlowProps.edges[0]))
    await waitFor(() => expect(latestFlowProps.edges[0].label).toBe('1'))
  })

  it('opens block context actions and creates or enters subsystems', async function () {
    currentBlocks = [block({ id: 'a' }), block({ id: 'b' })]
    selectedBlockIds = ['a', 'b']
    configureStore()
    render(<Editor />)
    await waitFor(() =>
      expect(screen.getByText('2 blocks selected')).toBeInTheDocument()
    )
    const event = { preventDefault: vi.fn(), clientX: 11, clientY: 22 }
    latestFlowProps.onContextMenu(event)
    await waitFor(() =>
      expect(latestContextProps.contextMenu).toEqual({ x: 11, y: 22 })
    )
    latestContextProps.onCreateSubsystem()
    expect(actions.createSubsystem).toHaveBeenCalledWith(['a', 'b'])
    fireEvent.click(screen.getByText('Create Subsystem'))
    expect(actions.createSubsystem).toHaveBeenCalledTimes(2)
    latestContextProps.onEnterSubsystem('a')
    expect(actions.enterSubsystem).toHaveBeenCalledWith('a')
  })

  it('expands a selected subsystem and ignores context menus without a qualifying selection', async function () {
    currentBlocks = [block({ id: 'sub', type: 'subsystem' })]
    selectedBlockIds = ['sub']
    configureStore()
    const view = render(<Editor />)
    await waitFor(() => expect(latestFlowProps.nodes).toHaveLength(1))
    latestFlowProps.onContextMenu({
      preventDefault: vi.fn(),
      clientX: 1,
      clientY: 2,
    })
    await waitFor(() =>
      expect(latestContextProps.selectedSubsystem.id).toBe('sub')
    )
    latestContextProps.onExpandSubsystem()
    expect(actions.expandSubsystem).toHaveBeenCalledWith('sub')
    view.unmount()

    selectedBlockIds = []
    configureStore()
    render(<Editor />)
    latestFlowProps.onContextMenu({
      preventDefault: vi.fn(),
      clientX: 3,
      clientY: 4,
    })
    expect(latestContextProps.contextMenu).toBeNull()
  })

  it('discards and relabels signals', async function () {
    currentBlocks = [block({ id: 'source' }), block({ id: 'target' })]
    currentConnections = [connection()]
    configureStore()
    render(<Editor />)
    await waitFor(() => expect(latestFlowProps.edges).toHaveLength(1))
    const menuEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      clientX: 15,
      clientY: 25,
    }
    latestFlowProps.onEdgeContextMenu(menuEvent, {
      id: 'edge',
      data: { connectionId: 'connection-1' },
    })
    await waitFor(() =>
      expect(latestContextProps.signalContextMenu.connectionId).toBe(
        'connection-1'
      )
    )
    latestContextProps.onSignalDiscard()
    expect(actions.removeConnection).toHaveBeenCalledWith('connection-1')
    latestFlowProps.onEdgeContextMenu(menuEvent, { id: 'fallback-edge' })
    await waitFor(() =>
      expect(latestContextProps.signalContextMenu.connectionId).toBe(
        'fallback-edge'
      )
    )
    latestContextProps.onLabelDiscard()
    expect(updateConnectionSignalName).toHaveBeenCalledWith(
      'fallback-edge',
      undefined
    )
  })

  it('renames and clears signal state', async function () {
    currentBlocks = [block({ id: 'source' }), block({ id: 'target' })]
    currentConnections = [connection()]
    configureStore()
    render(<Editor />)
    await waitFor(() => expect(latestFlowProps.edges).toHaveLength(1))
    const event = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      clientX: 15,
      clientY: 25,
    }
    latestFlowProps.onEdgeContextMenu(event, {
      id: 'edge',
      data: { connectionId: 'connection-1' },
    })
    await waitFor(() =>
      expect(latestContextProps.signalContextMenu).not.toBeNull()
    )
    latestContextProps.onRenameSignal()
    await waitFor(() =>
      expect(latestContextProps.renamingSignal.connectionId).toBe(
        'connection-1'
      )
    )
    latestContextProps.onSaveSignalName('  velocity  ')
    expect(updateConnectionSignalName).toHaveBeenLastCalledWith(
      'connection-1',
      'velocity'
    )
    latestFlowProps.onEdgeContextMenu(event, {
      id: 'edge',
      data: { connectionId: 'connection-1' },
    })
    await waitFor(() =>
      expect(latestContextProps.signalContextMenu).not.toBeNull()
    )
    latestContextProps.onRenameSignal()
    await waitFor(() =>
      expect(latestContextProps.renamingSignal).not.toBeNull()
    )
    latestContextProps.onSaveSignalName('   ')
    expect(updateConnectionSignalName).toHaveBeenLastCalledWith(
      'connection-1',
      undefined
    )
    latestContextProps.onCancelSignalRename()
    latestContextProps.onClearHighlighting()
    fireEvent.click(
      screen.getByTestId('react-flow').parentElement as HTMLElement
    )
  })

  it('auto-routes signals with or without waypoints', async function () {
    currentBlocks = [
      block({ id: 'source' }),
      block({ id: 'target', position: { x: 200, y: 100 } }),
    ]
    currentConnections = [connection({ waypoints: [{ x: 50, y: 50 }] })]
    configureStore()
    render(<Editor />)
    await waitFor(() => expect(latestFlowProps.edges).toHaveLength(1))
    const event = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      clientX: 10,
      clientY: 20,
    }
    latestFlowProps.onEdgeContextMenu(event, {
      id: 'edge',
      data: { connectionId: 'connection-1' },
    })
    await waitFor(() =>
      expect(latestContextProps.signalContextMenu).not.toBeNull()
    )
    vi.mocked(generateSmartWaypoints).mockReturnValue([{ x: 100, y: 50 }])
    latestContextProps.onAutoRouteSignal()
    expect(updateConnectionWaypoints).toHaveBeenCalledWith('connection-1', [
      { x: 100, y: 50 },
    ])
    latestFlowProps.onEdgeContextMenu(event, {
      id: 'edge',
      data: { connectionId: 'connection-1' },
    })
    await waitFor(() =>
      expect(latestContextProps.signalContextMenu).not.toBeNull()
    )
    vi.mocked(generateSmartWaypoints).mockReturnValue([])
    latestContextProps.onAutoRouteSignal()
    expect(clearConnectionWaypoints).toHaveBeenCalledWith('connection-1')
  })

  it('highlights signals toward source and destination', async function () {
    vi.mocked(getSourceBranchConnectionIds).mockReturnValue(
      new Set(['connection-1'])
    )
    currentBlocks = [block({ id: 'source' }), block({ id: 'target' })]
    currentConnections = [connection()]
    configureStore()
    render(<Editor />)
    await waitFor(() => expect(latestFlowProps.edges).toHaveLength(1))
    const event = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      clientX: 10,
      clientY: 20,
    }
    latestFlowProps.onEdgeContextMenu(event, {
      id: 'edge',
      data: { connectionId: 'connection-1' },
    })
    await waitFor(() =>
      expect(latestContextProps.signalContextMenu).not.toBeNull()
    )
    act(() => latestContextProps.onHighlightToSource())
    expect(getSourceBranchConnectionIds).toHaveBeenCalled()
    await waitFor(() =>
      expect(latestFlowProps.edges[0].style).toEqual({
        stroke: '#eab308',
        strokeWidth: 3,
      })
    )
    latestFlowProps.onEdgeContextMenu(event, {
      id: 'edge',
      data: { connectionId: 'connection-1' },
    })
    await waitFor(() =>
      expect(latestContextProps.signalContextMenu).not.toBeNull()
    )
    latestContextProps.onHighlightToDestination()
    expect(getDownstreamConnectionIds).toHaveBeenCalled()
  })

  it('keeps context actions safe when their backing selection is stale', async function () {
    const event = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      clientX: 1,
      clientY: 2,
    }
    const first = render(<Editor />)
    await waitFor(() =>
      expect(screen.getByTestId('react-flow')).toBeInTheDocument()
    )
    latestContextProps.onSignalDiscard()
    latestContextProps.onLabelDiscard()
    latestContextProps.onAutoRouteSignal()
    latestContextProps.onRenameSignal()
    latestContextProps.onSaveSignalName('ignored')
    latestContextProps.onHighlightToSource()
    latestContextProps.onHighlightToDestination()
    latestContextProps.onCreateSubsystem()
    latestContextProps.onExpandSubsystem()
    first.unmount()

    currentBlocks = [block({ id: 'source' }), block({ id: 'target' })]
    currentConnections = [connection()]
    configureStore()
    const second = render(<Editor />)
    latestFlowProps.onEdgeContextMenu(event, { id: 'missing' })
    await waitFor(() =>
      expect(latestContextProps.signalContextMenu).not.toBeNull()
    )
    latestContextProps.onAutoRouteSignal()
    latestFlowProps.onEdgeContextMenu(event, { id: 'missing' })
    await waitFor(() =>
      expect(latestContextProps.signalContextMenu).not.toBeNull()
    )
    latestContextProps.onHighlightToSource()
    latestFlowProps.onEdgeContextMenu(event, { id: 'missing' })
    await waitFor(() =>
      expect(latestContextProps.signalContextMenu).not.toBeNull()
    )
    latestContextProps.onHighlightToDestination()
    second.unmount()

    currentBlocks = [block({ id: 'target' })]
    currentConnections = [connection()]
    configureStore()
    const third = render(<Editor />)
    latestFlowProps.onEdgeContextMenu(event, {
      id: 'edge',
      data: { connectionId: 'connection-1' },
    })
    await waitFor(() =>
      expect(latestContextProps.signalContextMenu).not.toBeNull()
    )
    latestContextProps.onAutoRouteSignal()
    third.unmount()

    currentBlocks = [block({ id: 'source' })]
    configureStore()
    const fourth = render(<Editor />)
    latestFlowProps.onEdgeContextMenu(event, {
      id: 'edge',
      data: { connectionId: 'connection-1' },
    })
    await waitFor(() =>
      expect(latestContextProps.signalContextMenu).not.toBeNull()
    )
    latestContextProps.onAutoRouteSignal()
    fourth.unmount()

    currentBlocks = [block({ id: 'source' }), block({ id: 'target' })]
    currentConnections = [
      connection({ sourcePortId: 'missing', targetPortId: 'missing' }),
    ]
    configureStore()
    render(<Editor />)
    latestFlowProps.onEdgeContextMenu(event, {
      id: 'edge',
      data: { connectionId: 'connection-1' },
    })
    await waitFor(() =>
      expect(latestContextProps.signalContextMenu).not.toBeNull()
    )
    latestContextProps.onAutoRouteSignal()
    expect(clearConnectionWaypoints).toHaveBeenCalledWith('connection-1')
  })

  it('opens subsystem and plotting nodes on double-click', async function () {
    currentBlocks = [
      block({ id: 'sub', type: 'subsystem' }),
      block({ id: 'scope', type: 'scope' }),
      block({ id: 'scope3d', type: 'scope_3d' }),
      block({ id: 'xy', type: 'xy_graph' }),
      block({ id: 'ordinary' }),
    ]
    configureStore()
    render(<Editor />)
    await waitFor(() => expect(latestFlowProps.nodes).toHaveLength(5))
    latestFlowProps.onNodeDoubleClick({}, { id: 'sub', type: 'subsystemNode' })
    for (const id of ['scope', 'scope3d', 'xy', 'ordinary', 'missing']) {
      latestFlowProps.onNodeDoubleClick({}, { id, type: 'blockNode' })
    }
    expect(actions.enterSubsystem).toHaveBeenCalledWith('sub')
    expect(uiActions.openPlotWindow.mock.calls).toEqual([
      ['scope'],
      ['scope3d'],
      ['xy'],
    ])
  })

  it('supports breadcrumbs, keyboard navigation, responsiveness, and MiniMap colors', async function () {
    currentPath = [
      { id: 'outer', name: 'Outer' },
      { id: 'inner', name: 'Inner' },
    ]
    configureStore()
    const view = render(<Editor />)
    await waitFor(() => expect(screen.getByText('Inner')).toBeInTheDocument())
    fireEvent.click(screen.getByText('Model'))
    fireEvent.click(screen.getByText('Outer'))
    fireEvent.click(screen.getByTitle('Exit subsystem (Esc)'))
    expect(actions.navigateToPath.mock.calls).toEqual([[-1], [0]])
    expect(actions.exitSubsystem).toHaveBeenCalled()

    fireEvent.keyDown(window, { key: 'Escape' })
    fireEvent.keyDown(window, { key: ' ' })
    fireEvent.keyDown(window, { key: 'x', code: 'Space' })
    expect(flowApi.fitView).toHaveBeenCalledTimes(2)
    vi.mocked(getIsPropertiesFocused).mockReturnValue(true)
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(actions.exitSubsystem).toHaveBeenCalledTimes(2)
    vi.mocked(getIsPropertiesFocused).mockReturnValue(false)
    Object.defineProperty(window, 'innerWidth', {
      configurable: true,
      writable: true,
      value: 500,
    })
    fireEvent.resize(window)
    await waitFor(() =>
      expect(latestMiniMapProps.style).toEqual({ width: 100, height: 60 })
    )

    const colors = [
      'sources',
      'sinks',
      'continuous',
      'discrete',
      'math',
      'routing',
      'subsystems',
      'other',
    ].map((category) =>
      latestMiniMapProps.nodeColor({ data: { definition: { category } } })
    )
    expect(colors).toEqual([
      '#a6e3a1',
      '#f38ba8',
      '#89b4fa',
      '#fab387',
      '#cba6f7',
      '#f9e2af',
      '#22d3ee',
      '#6c7086',
    ])
    expect(latestMiniMapProps.nodeColor({ data: {} })).toBe('#6c7086')
    expect(latestMiniMapProps.nodeColor({ data: { definition: {} } })).toBe(
      '#6c7086'
    )

    view.unmount()
    configureStore()
    model.metadata.name = ''
    render(<Editor />)
    expect(screen.getByText('Model')).toBeInTheDocument()
  })
})
