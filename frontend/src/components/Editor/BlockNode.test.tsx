import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ReactFlowProvider } from '@xyflow/react'
import { BlockNode } from './BlockNode'
import type { BlockDefinition, BlockInstance, BlockCategory } from '../../types/block'

// Mock Handle component since it requires ReactFlow context
vi.mock('@xyflow/react', async (importOriginal) => {
  const original = await importOriginal<typeof import('@xyflow/react')>()
  return {
    ...original,
    Handle: ({ type, id, title }: { type: string; id: string; title: string }) => (
      <div data-testid={`handle-${type}-${id}`} title={title} />
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
  })
})
