import { fireEvent, render, screen } from '@testing-library/react'
import { createElement } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { blockRegistry } from '../../blocks'
import type { BlockInstance } from '../../types/block'
import { SubsystemNode } from './SubsystemNode'

const toggleSubsystemExpanded = vi.fn()
vi.mock('../../store/modelStore', function () {
  return {
    useModelStore: vi.fn(function (selector) {
      return selector({ toggleSubsystemExpanded })
    }),
  }
})
vi.mock('../../blocks', function () {
  return { blockRegistry: { get: vi.fn() } }
})
vi.mock('@xyflow/react', async function (importOriginal) {
  const original = await importOriginal<typeof import('@xyflow/react')>()
  return {
    ...original,
    Handle: function (props: { type: string; id: string; title: string; position: unknown; style: unknown }) {
      return createElement('div', {
        'data-testid': `handle-${props.type}-${props.id}`,
        title: props.title,
        'data-position': String(props.position),
        'data-style': JSON.stringify(props.style),
      })
    },
  }
})

const mockedRegistry = vi.mocked(blockRegistry)

type ComparisonProps = {
  selected: boolean
  data: { block: BlockInstance | undefined }
}
const compareProps = (SubsystemNode as unknown as {
  compare: (previous: ComparisonProps, next: ComparisonProps) => boolean
}).compare

const definition = {
  type: 'subsystem', category: 'subsystems', name: 'Subsystem', description: '',
  inputs: [], outputs: [], parameters: [],
}

function createBlock(overrides: Partial<BlockInstance> = {}): BlockInstance {
  return {
    id: 'subsystem-1', type: 'subsystem', name: 'Controller', position: { x: 0, y: 0 },
    parameters: {},
    inputPorts: [{ id: 'in', name: 'input', dataType: 'double', dimensions: [1] }],
    outputPorts: [{ id: 'out', name: 'output', dataType: 'double', dimensions: [1] }],
    children: [], childConnections: [],
    ...overrides,
  }
}

function props(block: BlockInstance, selected = false) {
  return { data: { block, definition }, selected } as never
}

function setup(block = createBlock(), selected = false) {
  return render(createElement(SubsystemNode, props(block, selected)))
}

describe('SubsystemNode', function () {
  beforeEach(function () {
    vi.clearAllMocks()
    mockedRegistry.get.mockReturnValue({ category: 'math' } as never)
  })

  it('renders invalid subsystem data without dereferencing the missing block', function () {
    const missingBlock = { data: { block: undefined, definition }, selected: false } as never
    const first = render(createElement(SubsystemNode, missingBlock))
    expect(screen.getByText('Invalid Subsystem')).toBeInTheDocument()
    first.unmount()

    render(createElement(SubsystemNode, {
      data: { block: createBlock(), definition: undefined }, selected: false,
    } as never))
    expect(screen.getByText('Invalid Subsystem')).toBeInTheDocument()
  })

  it('renders ports, selection, rotation, expansion, and the empty preview', function () {
    const view = setup(createBlock({ rotation: 90, isExpanded: true }), true)
    expect(screen.getByText('Controller')).toBeInTheDocument()
    expect(screen.getByText('[-]')).toBeInTheDocument()
    expect(screen.getByText('Empty')).toBeInTheDocument()
    expect(screen.getByText('input')).toBeInTheDocument()
    expect(screen.getByText('output')).toBeInTheDocument()
    expect(screen.getByTestId('handle-target-in').getAttribute('data-style')).toContain('left')
    expect(view.container.firstElementChild?.className).toContain('ring-2')
    fireEvent.doubleClick(view.container.firstElementChild as HTMLElement)
    expect(toggleSubsystemExpanded).toHaveBeenCalledWith('subsystem-1')

    view.unmount()
    const collapsed = setup(createBlock())
    expect(screen.getByText('[+]')).toBeInTheDocument()
    expect(screen.getByTestId('handle-source-out').getAttribute('data-style')).toContain('top')
    expect(collapsed.container.firstElementChild?.className).not.toContain('ring-2')
    collapsed.unmount()
    setup(createBlock({ children: undefined }))
    expect(screen.getByText('Empty')).toBeInTheDocument()
  })

  it('draws valid child connections and skips missing or interface endpoints', function () {
    const source = createBlock({ id: 'source', type: 'constant', name: 'Short', position: { x: 0, y: 0 } })
    const target = createBlock({ id: 'target', type: 'scope', name: 'LongChildName', position: { x: 100, y: 20 } })
    const inport = createBlock({ id: 'interface', type: 'inport', name: 'Inport', position: { x: -100, y: 0 } })
    mockedRegistry.get.mockImplementation(function (type) {
      if (type === 'constant') return { category: 'sources' } as never
      if (type === 'scope') return { category: 'sinks' } as never
      return undefined
    })
    const view = setup(createBlock({
      children: [source, target, inport],
      childConnections: [
        { id: 'valid', sourceBlockId: 'source', sourcePortId: 'out', targetBlockId: 'target', targetPortId: 'in' },
        { id: 'missing', sourceBlockId: 'source', sourcePortId: 'out', targetBlockId: 'missing', targetPortId: 'in' },
        { id: 'interface-edge', sourceBlockId: 'interface', sourcePortId: 'out', targetBlockId: 'target', targetPortId: 'in' },
      ],
    }))

    expect(screen.getByText('Short')).toBeInTheDocument()
    expect(screen.getByText('LongChi...')).toBeInTheDocument()
    expect(view.container.querySelectorAll('path[stroke="#64748b"]')).toHaveLength(1)

    view.unmount()
    setup(createBlock({ children: [source], childConnections: undefined }))
    expect(screen.getByText('Short')).toBeInTheDocument()
  })

  it('renders interface-only children and every category color', function () {
    const interfaceChildren = [
      createBlock({ id: 'inport', type: 'inport', name: 'Inport' }),
      createBlock({ id: 'outport', type: 'outport', name: 'Outport' }),
    ]
    const first = setup(createBlock({ children: interfaceChildren }))
    expect(screen.getByText('Inport')).toBeInTheDocument()
    expect(screen.getByText('Outport')).toBeInTheDocument()
    first.unmount()

    const categories = [
      'sources', 'sinks', 'continuous', 'discrete', 'math', 'routing', 'subsystems',
      'signal_processing', 'nonlinear', 'observers', 'logic', 'control_analysis',
      'data_types', 'matrix_ops', 'control_design', 'aerospace', 'dsp', 'rf',
      'navigation', 'sensor_fusion', 'unknown',
    ]
    const children = categories.map(function (category, index) {
      return createBlock({
        id: `child-${index}`,
        type: category,
        name: `Child ${index}`,
        position: { x: index * 150, y: index * 75 },
      })
    })
    mockedRegistry.get.mockImplementation(function (type) {
      return type === 'unknown' ? undefined : { category: type } as never
    })
    const view = setup(createBlock({ children }))
    expect(view.container.querySelectorAll('svg g rect')).toHaveLength(categories.length)
    expect(view.container.querySelector('svg text')).not.toBeInTheDocument()
  })

  it('updates the preview when child or connection content changes at the same count', function () {
    const child = createBlock({ id: 'child', name: 'Original' })
    const previous = props(createBlock({
      children: [child],
      childConnections: [{ id: 'edge', sourceBlockId: 'a', sourcePortId: 'out', targetBlockId: 'b', targetPortId: 'in' }],
    })) as ComparisonProps
    const renamedChild = props(createBlock({ children: [{ ...child, name: 'Renamed' }] })) as ComparisonProps
    const changedConnection = props(createBlock({
      children: [child],
      childConnections: [{ id: 'edge-2', sourceBlockId: 'a', sourcePortId: 'out', targetBlockId: 'b', targetPortId: 'in' }],
    })) as ComparisonProps

    expect(compareProps(previous, renamedChild)).toBe(false)
    expect(compareProps(previous, changedConnection)).toBe(false)
  })

  it('compares every render-relevant subsystem property', function () {
    const base = createBlock({ children: [] })
    const previous = props(base) as ComparisonProps
    expect(compareProps(previous, props({ ...base }) as ComparisonProps)).toBe(true)
    expect(compareProps(previous, props(base, true) as ComparisonProps)).toBe(false)

    const changes: BlockInstance[] = [
      { ...base, id: 'changed' },
      { ...base, name: 'Changed' },
      { ...base, isExpanded: true },
      { ...base, rotation: 180 },
      { ...base, parameters: { changed: true } },
      { ...base, inputPorts: [] },
      { ...base, outputPorts: [] },
      { ...base, children: [createBlock({ id: 'child' })] },
      { ...base, childConnections: [{ id: 'new', sourceBlockId: 'a', sourcePortId: 'out', targetBlockId: 'b', targetPortId: 'in' }] },
    ]
    for (const changed of changes) {
      expect(compareProps(previous, props(changed) as ComparisonProps)).toBe(false)
    }

    const missing = { selected: false, data: { block: undefined } }
    expect(compareProps(missing, missing)).toBe(true)
    expect(compareProps(missing, previous)).toBe(false)
    expect(compareProps(previous, missing)).toBe(false)
  })

})
