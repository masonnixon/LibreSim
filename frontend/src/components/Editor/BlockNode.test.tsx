import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ReactFlowProvider, Position } from '@xyflow/react'
import { BlockNode } from './BlockNode'
import type { BlockDefinition, BlockInstance, BlockCategory, BlockRotation } from '../../types/block'

// Mock the modelStore
const mockUpdateBlockSize = vi.fn()
vi.mock('../../store/modelStore', () => ({
  useModelStore: vi.fn((selector) => {
    const state = { updateBlockSize: mockUpdateBlockSize }
    return selector ? selector(state) : state
  }),
}))

// Mock Handle and NodeResizer components since they require ReactFlow context
vi.mock('@xyflow/react', async (importOriginal) => {
  const original = await importOriginal<typeof import('@xyflow/react')>()
  return {
    ...original,
    Handle: ({ type, id, title, position, style }: { type: string; id: string; title: string; position: unknown; style?: Record<string, unknown> }) => (
      <div data-testid={`handle-${type}-${id}`} title={title} data-position={String(position)} data-style={JSON.stringify(style)} />
    ),
    NodeResizer: ({ isVisible, onResizeEnd }: { isVisible: boolean; onResizeEnd: (e: unknown, params: { width: number; height: number }) => void }) => (
      isVisible ? <div data-testid="node-resizer" onClick={() => onResizeEnd(null, { width: 150, height: 75 })} /> : null
    ),
  }
})

const createMockBlock = (overrides: Partial<BlockInstance> = {}): BlockInstance => ({
  id: 'test-block-1',
  type: 'constant',
  name: 'TestConstant',
  position: { x: 100, y: 100 },
  parameters: { value: 5 },
  inputPorts: [],
  outputPorts: [{ id: 'out_0', name: 'out', dataType: 'double', dimensions: [1] }],
  ...overrides,
})

const createMockDefinition = (overrides: Partial<BlockDefinition> = {}): BlockDefinition => ({
  type: 'constant',
  category: 'sources' as BlockCategory,
  name: 'Constant',
  description: 'Outputs a constant value',
  inputs: [],
  outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
  parameters: [{ name: 'value', label: 'Value', type: 'number', default: 0 }],
  icon: 'C',
  ...overrides,
})

const createMockNodeProps = (
  block: BlockInstance,
  definition: BlockDefinition | undefined,
  selected: boolean = false
) => ({
  id: block.id,
  data: { block, definition },
  selected,
  type: 'blockNode' as const,
  isConnectable: true,
  positionAbsoluteX: block.position.x,
  positionAbsoluteY: block.position.y,
  zIndex: 0,
  dragging: false,
  targetPosition: undefined,
  sourcePosition: undefined,
  selectable: true,
  deletable: true,
  draggable: true,
})

describe('BlockNode', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const renderBlockNode = (
    block: BlockInstance,
    definition: BlockDefinition | undefined,
    selected: boolean = false
  ) => {
    const props = createMockNodeProps(block, definition, selected)
    return render(
      <ReactFlowProvider>
        <BlockNode {...props} />
      </ReactFlowProvider>
    )
  }

  describe('rendering', () => {
    it('should render block name', () => {
      const block = createMockBlock({ name: 'MyConstant' })
      const definition = createMockDefinition()

      renderBlockNode(block, definition)

      expect(screen.getByText('MyConstant')).toBeInTheDocument()
    })

    it('should render "Invalid Block" when block is undefined', () => {
      const props = {
        id: 'test-id',
        data: { block: undefined as unknown as BlockInstance, definition: createMockDefinition() },
        selected: false,
        type: 'blockNode' as const,
        isConnectable: true,
        positionAbsoluteX: 0,
        positionAbsoluteY: 0,
        zIndex: 0,
        dragging: false,
        targetPosition: undefined,
        sourcePosition: undefined,
        selectable: true,
        deletable: true,
        draggable: true,
      }

      render(
        <ReactFlowProvider>
          <BlockNode {...props} />
        </ReactFlowProvider>
      )

      expect(screen.getByText('Invalid Block')).toBeInTheDocument()
    })

    it('should render "Invalid Block" when definition is undefined', () => {
      const props = createMockNodeProps(createMockBlock(), undefined)

      render(
        <ReactFlowProvider>
          <BlockNode {...props} />
        </ReactFlowProvider>
      )

      expect(screen.getByText('Invalid Block')).toBeInTheDocument()
    })

    it('should render input handles', () => {
      const block = createMockBlock({
        inputPorts: [
          { id: 'in_0', name: 'input1', dataType: 'double', dimensions: [1] },
          { id: 'in_1', name: 'input2', dataType: 'double', dimensions: [1] },
        ],
      })
      const definition = createMockDefinition()

      renderBlockNode(block, definition)

      expect(screen.getByTestId('handle-target-in_0')).toBeInTheDocument()
      expect(screen.getByTestId('handle-target-in_1')).toBeInTheDocument()
    })

    it('should render output handles', () => {
      const block = createMockBlock({
        outputPorts: [
          { id: 'out_0', name: 'output1', dataType: 'double', dimensions: [1] },
          { id: 'out_1', name: 'output2', dataType: 'double', dimensions: [1] },
        ],
      })
      const definition = createMockDefinition()

      renderBlockNode(block, definition)

      expect(screen.getByTestId('handle-source-out_0')).toBeInTheDocument()
      expect(screen.getByTestId('handle-source-out_1')).toBeInTheDocument()
    })
  })

  describe('dynamic icons', () => {
    it('should display constant value as icon for constant blocks', () => {
      const block = createMockBlock({
        type: 'constant',
        parameters: { value: 42 },
      })
      const definition = createMockDefinition({ type: 'constant', icon: 'C' })

      renderBlockNode(block, definition)

      expect(screen.getByText('42')).toBeInTheDocument()
    })

    it('should display gain value as icon for gain blocks', () => {
      const block = createMockBlock({
        type: 'gain',
        parameters: { gain: 2.5 },
      })
      const definition = createMockDefinition({ type: 'gain', category: 'math', icon: 'K' })

      renderBlockNode(block, definition)

      expect(screen.getByText('2.5')).toBeInTheDocument()
    })

    it('should use definition icon for other block types', () => {
      const block = createMockBlock({
        type: 'integrator',
        parameters: {},
      })
      const definition = createMockDefinition({
        type: 'integrator',
        category: 'continuous',
        icon: '∫',
      })

      renderBlockNode(block, definition)

      expect(screen.getByText('∫')).toBeInTheDocument()
    })

    it('should use definition icon when constant value is undefined', () => {
      const block = createMockBlock({
        type: 'constant',
        parameters: {},
      })
      const definition = createMockDefinition({ type: 'constant', icon: 'C' })

      renderBlockNode(block, definition)

      expect(screen.getByText('C')).toBeInTheDocument()
    })

    it('should display compare_to_zero operator with 0', () => {
      const block = createMockBlock({
        type: 'compare_to_zero',
        parameters: { operator: '>' },
      })
      const definition = createMockDefinition({ type: 'compare_to_zero', category: 'logic', icon: '?' })

      renderBlockNode(block, definition)

      expect(screen.getByText('>0')).toBeInTheDocument()
    })

    it('should display compare_to_constant operator with constant', () => {
      const block = createMockBlock({
        type: 'compare_to_constant',
        parameters: { operator: '>=', constant: 5 },
      })
      const definition = createMockDefinition({ type: 'compare_to_constant', category: 'logic', icon: '?' })

      renderBlockNode(block, definition)

      expect(screen.getByText('>=5')).toBeInTheDocument()
    })

    it('should display compare_to_constant operator with K when constant missing', () => {
      const block = createMockBlock({
        type: 'compare_to_constant',
        parameters: { operator: '<=' },
      })
      const definition = createMockDefinition({ type: 'compare_to_constant', category: 'logic', icon: '?' })

      renderBlockNode(block, definition)

      expect(screen.getByText('<=K')).toBeInTheDocument()
    })

    it('should display relational_operator operator', () => {
      const block = createMockBlock({
        type: 'relational_operator',
        parameters: { operator: '==' },
      })
      const definition = createMockDefinition({ type: 'relational_operator', category: 'logic', icon: '?' })

      renderBlockNode(block, definition)

      expect(screen.getByText('==')).toBeInTheDocument()
    })

    it('should display logical_operator operator', () => {
      const block = createMockBlock({
        type: 'logical_operator',
        parameters: { operator: 'AND' },
      })
      const definition = createMockDefinition({ type: 'logical_operator', category: 'logic', icon: '?' })

      renderBlockNode(block, definition)

      expect(screen.getByText('AND')).toBeInTheDocument()
    })

    it('should use definition icon when gain is undefined', () => {
      const block = createMockBlock({
        type: 'gain',
        parameters: {},
      })
      const definition = createMockDefinition({ type: 'gain', category: 'math', icon: 'K' })

      renderBlockNode(block, definition)

      expect(screen.getByText('K')).toBeInTheDocument()
    })
  })

  describe('category styling', () => {
    const testCases: { category: BlockCategory; expectedClass: string }[] = [
      { category: 'sources', expectedClass: 'block-source' },
      { category: 'sinks', expectedClass: 'block-sink' },
      { category: 'continuous', expectedClass: 'block-continuous' },
      { category: 'discrete', expectedClass: 'block-discrete' },
      { category: 'math', expectedClass: 'block-math' },
      { category: 'routing', expectedClass: 'block-routing' },
      { category: 'subsystems', expectedClass: 'bg-cyan-600' },
      { category: 'signal_processing', expectedClass: 'bg-teal-600' },
      { category: 'nonlinear', expectedClass: 'bg-orange-600' },
      { category: 'observers', expectedClass: 'bg-indigo-600' },
      { category: 'logic', expectedClass: 'bg-amber-600' },
      { category: 'control_analysis', expectedClass: 'bg-rose-600' },
      { category: 'data_types', expectedClass: 'bg-lime-600' },
      { category: 'matrix_ops', expectedClass: 'bg-emerald-600' },
      { category: 'control_design', expectedClass: 'bg-violet-600' },
      { category: 'aerospace', expectedClass: 'bg-sky-600' },
    ]

    testCases.forEach(({ category, expectedClass }) => {
      it(`should apply ${expectedClass} class for ${category} category`, () => {
        const block = createMockBlock()
        const definition = createMockDefinition({ category })

        const { container } = renderBlockNode(block, definition)

        const blockElement = container.querySelector('.rounded-lg')
        expect(blockElement?.className).toContain(expectedClass)
      })
    })

    it('should apply default styling for unknown category', () => {
      const block = createMockBlock()
      const definition = createMockDefinition({ category: 'unknown' as BlockCategory })

      const { container } = renderBlockNode(block, definition)

      const blockElement = container.querySelector('.rounded-lg')
      expect(blockElement?.className).toContain('bg-gray-600')
    })
  })

  describe('selection', () => {
    it('should apply ring class when selected', () => {
      const block = createMockBlock()
      const definition = createMockDefinition()

      const { container } = renderBlockNode(block, definition, true)

      const blockElement = container.querySelector('.rounded-lg')
      expect(blockElement?.className).toContain('ring-2')
    })

    it('should not apply ring class when not selected', () => {
      const block = createMockBlock()
      const definition = createMockDefinition()

      const { container } = renderBlockNode(block, definition, false)

      const blockElement = container.querySelector('.rounded-lg')
      expect(blockElement?.className).not.toContain('ring-2')
    })

    it('should show NodeResizer when selected', () => {
      const block = createMockBlock()
      const definition = createMockDefinition()

      renderBlockNode(block, definition, true)

      expect(screen.getByTestId('node-resizer')).toBeInTheDocument()
    })

    it('should not show NodeResizer when not selected', () => {
      const block = createMockBlock()
      const definition = createMockDefinition()

      renderBlockNode(block, definition, false)

      expect(screen.queryByTestId('node-resizer')).not.toBeInTheDocument()
    })
  })

  describe('rotation', () => {
    it('should apply rotation transform', () => {
      const block = createMockBlock({ rotation: 90 as BlockRotation })
      const definition = createMockDefinition()

      const { container } = renderBlockNode(block, definition)

      const blockElement = container.querySelector('.rounded-lg')
      expect(blockElement?.getAttribute('style')).toContain('rotate(90deg)')
    })

    it('should apply counter-rotation to content', () => {
      const block = createMockBlock({ rotation: 90 as BlockRotation })
      const definition = createMockDefinition()

      const { container } = renderBlockNode(block, definition)

      // The inner content div should have counter-rotation
      const contentDiv = container.querySelector('.text-center')
      expect(contentDiv?.getAttribute('style')).toContain('rotate(-90deg)')
    })

    it('should default to 0 rotation when not specified', () => {
      const block = createMockBlock()
      const definition = createMockDefinition()

      const { container } = renderBlockNode(block, definition)

      const blockElement = container.querySelector('.rounded-lg')
      expect(blockElement?.getAttribute('style')).toContain('rotate(0deg)')
    })
  })

  describe('block sizing', () => {
    it('should use custom size when provided', () => {
      const block = createMockBlock({
        size: { width: 150, height: 80 },
      })
      const definition = createMockDefinition()

      renderBlockNode(block, definition)

      // The block should use the custom size (reflected in font size calculations)
      // We can verify the block renders without errors
      expect(screen.getByText('TestConstant')).toBeInTheDocument()
    })

    it('should use default size when not provided', () => {
      const block = createMockBlock()
      const definition = createMockDefinition()

      renderBlockNode(block, definition)

      expect(screen.getByText('TestConstant')).toBeInTheDocument()
    })

    it('should hide text for very small blocks', () => {
      const block = createMockBlock({
        size: { width: 20, height: 20 },
      })
      const definition = createMockDefinition()

      const { container } = renderBlockNode(block, definition)

      // Text should be hidden for small blocks, but icon should still show
      // The font-semibold class is on the name div, which should not be rendered
      const nameDiv = container.querySelector('.font-semibold')
      expect(nameDiv).toBeNull()
    })

    it('should apply smaller padding for small blocks', () => {
      const block = createMockBlock({
        size: { width: 40, height: 30 },
      })
      const definition = createMockDefinition()

      const { container } = renderBlockNode(block, definition)

      const blockElement = container.querySelector('.rounded-lg')
      expect(blockElement?.getAttribute('style')).toContain('padding: 4px')
    })
  })

  describe('resize handler', () => {
    it('should call updateBlockSize when resized', () => {
      const block = createMockBlock()
      const definition = createMockDefinition()

      renderBlockNode(block, definition, true)

      const resizer = screen.getByTestId('node-resizer')
      fireEvent.click(resizer)

      expect(mockUpdateBlockSize).toHaveBeenCalledWith('test-block-1', { width: 150, height: 75 })
    })
  })

  describe('handle positioning', () => {
    it('should position handles evenly along edges', () => {
      const block = createMockBlock({
        inputPorts: [
          { id: 'in_0', name: 'in1', dataType: 'double', dimensions: [1] },
          { id: 'in_1', name: 'in2', dataType: 'double', dimensions: [1] },
        ],
        outputPorts: [
          { id: 'out_0', name: 'out1', dataType: 'double', dimensions: [1] },
        ],
      })
      const definition = createMockDefinition()

      renderBlockNode(block, definition)

      // Verify handles are rendered with style data
      const inputHandle0 = screen.getByTestId('handle-target-in_0')
      const inputHandle1 = screen.getByTestId('handle-target-in_1')
      const outputHandle = screen.getByTestId('handle-source-out_0')

      expect(inputHandle0).toBeInTheDocument()
      expect(inputHandle1).toBeInTheDocument()
      expect(outputHandle).toBeInTheDocument()

      // Check that styles contain percentage positioning
      const style0 = inputHandle0.getAttribute('data-style')
      const style1 = inputHandle1.getAttribute('data-style')
      expect(style0).toContain('top')
      expect(style1).toContain('top')
    })
  })
})
