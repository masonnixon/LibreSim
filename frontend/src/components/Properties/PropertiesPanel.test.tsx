import { fireEvent, render, screen } from '@testing-library/react'
import { createElement } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { blockRegistry } from '../../blocks'
import { useModelStore } from '../../store/modelStore'
import { getIsPropertiesFocused, PropertiesPanel } from './PropertiesPanel'

vi.mock('../../store/modelStore', function () { return { useModelStore: vi.fn() } })
vi.mock('../../blocks', function () {
  return { blockRegistry: { get: vi.fn() } }
})

const mockedModelStore = vi.mocked(useModelStore)
const mockedRegistry = vi.mocked(blockRegistry)

const block = {
  id: 'block-1',
  type: 'configurable',
  name: 'Configurable',
  position: { x: 0, y: 0 },
  parameters: {
    amount: 2,
    label: 'hello',
    active: true,
    mode: 'fast',
    values: [1, 2],
    custom: 'raw',
  },
  inputPorts: [{ id: 'in', name: 'in', dataType: 'double', dimensions: [1] }],
  outputPorts: [{ id: 'out', name: 'out', dataType: 'double', dimensions: [1] }],
}

function setup(options: { model?: unknown; selected?: string[]; blocks?: unknown[] } = {}) {
  const updateBlockParameters = vi.fn()
  const renameBlock = vi.fn()
  mockedModelStore.mockReturnValue({
    model: options.model === undefined ? { blocks: [block] } : options.model,
    selectedBlockIds: options.selected === undefined ? ['block-1'] : options.selected,
    updateBlockParameters,
    renameBlock,
    getCurrentBlocks: vi.fn(function () { return options.blocks === undefined ? [block] : options.blocks }),
  } as never)
  const view = render(createElement(PropertiesPanel))
  return { view, updateBlockParameters, renameBlock }
}

describe('PropertiesPanel', function () {
  beforeEach(function () {
    vi.clearAllMocks()
    mockedRegistry.get.mockReturnValue(undefined)
  })

  it('shows selection guidance for absent models or selections', function () {
    const noModel = setup({ model: null })
    expect(screen.getByText('Select a block to view its properties')).toBeInTheDocument()
    noModel.view.unmount()

    setup({ selected: [] })
    expect(screen.getByText('Select a block to view its properties')).toBeInTheDocument()
  })

  it('summarizes multiple selections and omits stale selected blocks', function () {
    const multiple = setup({ selected: ['one', 'two'] })
    expect(screen.getByText('2 blocks selected')).toBeInTheDocument()
    multiple.view.unmount()

    const stale = setup({ blocks: [] })
    expect(stale.view.container).toBeEmptyDOMElement()
  })

  it('edits every registered parameter type and tracks keyboard focus', function () {
    mockedRegistry.get.mockReturnValue({
      type: 'configurable',
      category: 'math',
      name: 'Configurable',
      description: 'All parameter controls',
      inputs: [],
      outputs: [],
      parameters: [
        { name: 'amount', label: 'Amount', type: 'number', default: 0, min: -5, max: 5, step: 0.5, description: 'Numeric value' },
        { name: 'label', label: 'Label', type: 'string', default: '' },
        { name: 'active', label: 'Active', type: 'boolean', default: false },
        { name: 'mode', label: 'Mode', type: 'select', default: 'fast', options: [{ value: 'fast', label: 'Fast' }, { value: 'slow', label: 'Slow' }] },
        { name: 'values', label: 'Values', type: 'array', default: [] },
        { name: 'custom', label: 'Custom', type: 'custom', default: '' } as never,
      ],
    })
    const stores = setup()
    const textboxes = screen.getAllByRole('textbox')
    fireEvent.change(textboxes[0], { target: { value: 'Renamed' } })
    expect(stores.renameBlock).toHaveBeenCalledWith('block-1', 'Renamed')
    fireEvent.focus(textboxes[0])
    expect(getIsPropertiesFocused()).toBe(true)
    fireEvent.keyDown(textboxes[0], { key: 'Delete' })
    fireEvent.blur(textboxes[0])
    expect(getIsPropertiesFocused()).toBe(false)

    const number = screen.getByRole('spinbutton')
    expect(number).toHaveAttribute('min', '-5')
    expect(number).toHaveAttribute('max', '5')
    expect(number).toHaveAttribute('step', '0.5')
    fireEvent.change(number, { target: { value: '-' } })
    expect(stores.updateBlockParameters).not.toHaveBeenCalled()
    fireEvent.blur(number)
    expect(number).toHaveValue(2)
    fireEvent.change(number, { target: { value: '3.5' } })
    expect(stores.updateBlockParameters).toHaveBeenCalledWith('block-1', { amount: 3.5 })
    fireEvent.blur(number)
    expect(number).toHaveValue(3.5)
    fireEvent.focus(number)
    expect(getIsPropertiesFocused()).toBe(true)
    fireEvent.keyDown(number, { key: 'Backspace' })
    fireEvent.blur(number)

    block.parameters.amount = 4
    stores.view.rerender(createElement(PropertiesPanel))
    expect(number).toHaveValue(4)
    block.parameters.amount = 2

    fireEvent.change(textboxes[1], { target: { value: 'changed' } })
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'slow' } })
    fireEvent.change(textboxes[2], { target: { value: 'invalid json' } })
    fireEvent.change(textboxes[2], { target: { value: '[3,4]' } })
    fireEvent.change(textboxes[3], { target: { value: 'customized' } })

    expect(stores.updateBlockParameters).toHaveBeenCalledWith('block-1', { label: 'changed' })
    expect(stores.updateBlockParameters).toHaveBeenCalledWith('block-1', { active: false })
    expect(stores.updateBlockParameters).toHaveBeenCalledWith('block-1', { mode: 'slow' })
    expect(stores.updateBlockParameters).toHaveBeenCalledWith('block-1', { values: [3, 4] })
    expect(stores.updateBlockParameters).toHaveBeenCalledWith('block-1', { custom: 'customized' })
    expect(screen.getByText('Numeric value')).toBeInTheDocument()
    expect(screen.getByText('Enabled')).toBeInTheDocument()
    expect(screen.getByText('Inputs:')).toBeInTheDocument()
    expect(screen.getByText('Outputs:')).toBeInTheDocument()
  })

  it('builds editable fallback parameters for an unregistered block', function () {
    const unknownBlock = {
      ...block,
      type: 'unknown_type',
      name: '',
      parameters: { camelCase: 2, flag: false, text: 'value' },
      inputPorts: [
        { id: 'in', name: 'in', dataType: '', dimensions: undefined },
        { id: 'in-2', name: 'in 2', dataType: 'single', dimensions: [2] },
      ],
      outputPorts: [
        { id: 'out', name: 'out', dataType: 'single', dimensions: [2] },
        { id: 'out-2', name: 'out 2', dataType: '', dimensions: undefined },
      ],
    }
    const first = setup({ blocks: [unknownBlock] })

    expect(screen.getByText('Block type: unknown_type')).toBeInTheDocument()
    expect(screen.getByText('Camel Case')).toBeInTheDocument()
    expect(screen.getByText('Flag')).toBeInTheDocument()
    expect(screen.getByText('Text')).toBeInTheDocument()
    expect(screen.getByRole('spinbutton')).toHaveAttribute('step', '0.01')
    expect(screen.getByText('Disabled')).toBeInTheDocument()
    first.view.unmount()

    setup({ blocks: [{ ...unknownBlock, parameters: undefined }] })
    expect(screen.getByText('No parameters')).toBeInTheDocument()
  })

  it('renders empty parameter values and definitions without parameters', function () {
    mockedRegistry.get.mockReturnValue({
      type: 'empty-values',
      category: 'math',
      name: 'Empty values',
      description: 'Fallback values',
      inputs: [],
      outputs: [],
      parameters: [
        { name: 'number', label: 'Number', type: 'number', default: 0 },
        { name: 'string', label: 'String', type: 'string', default: '' },
        { name: 'boolean', label: 'Boolean', type: 'boolean', default: false },
        { name: 'select', label: 'Select', type: 'select', default: '' },
        { name: 'array', label: 'Array', type: 'array', default: [] },
        { name: 'other', label: 'Other', type: 'other', default: '' } as never,
      ],
    })
    const emptyBlock = { ...block, type: 'empty-values', parameters: { number: null } }
    const first = setup({ blocks: [emptyBlock] })
    expect(screen.getByRole('spinbutton')).toHaveValue(0)
    expect(screen.getByRole('combobox')).toBeEmptyDOMElement()
    expect(screen.getByPlaceholderText('[1, 2, 3]')).toHaveValue('[]')
    expect(screen.getByText('Disabled')).toBeInTheDocument()
    first.view.unmount()

    mockedRegistry.get.mockReturnValue({
      type: 'plain', category: 'math', name: 'Plain', description: '', inputs: [], outputs: [], parameters: [],
    })
    setup({ blocks: [{ ...block, type: 'plain' }] })
    expect(screen.getByText('No parameters')).toBeInTheDocument()
  })

})
