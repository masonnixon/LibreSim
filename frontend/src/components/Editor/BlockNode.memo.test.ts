import { describe, it } from 'vitest'
import { expect } from 'vitest'
import type { BlockInstance } from '../../types/block'
import { BlockNode } from './BlockNode'

type ComparisonProps = {
  selected: boolean
  data: { block: BlockInstance | undefined }
}

const arePropsEqual = (BlockNode as unknown as {
  compare: (previous: ComparisonProps, next: ComparisonProps) => boolean
}).compare

const baseBlock = {
  id: 'block-1',
  type: 'constant',
  name: 'Constant',
  position: { x: 0, y: 0 },
  size: { width: 100, height: 50 },
  parameters: { value: 1 },
  inputPorts: [],
  outputPorts: [{ id: 'out', name: 'out', dataType: 'double', dimensions: [1] }],
} as BlockInstance

function nodeProps(block: BlockInstance, selected = false) {
  return { selected, data: { block } }
}

describe('BlockNode memoization', function () {
  it('updates when a port changes without changing the array length', function () {
    const next = {
      ...baseBlock,
      outputPorts: [{ ...baseBlock.outputPorts[0], name: 'renamed output' }],
    }
    expect(arePropsEqual(nodeProps(baseBlock), nodeProps(next))).toBe(false)
  })

  it('compares every render-relevant block property', function () {
    const previous = nodeProps(baseBlock)
    expect(arePropsEqual(previous, nodeProps({ ...baseBlock }))).toBe(true)
    expect(arePropsEqual(previous, nodeProps(baseBlock, true))).toBe(false)

    const changes: BlockInstance[] = [
      { ...baseBlock, id: 'changed-id' },
      { ...baseBlock, name: 'Changed name' },
      { ...baseBlock, type: 'gain' },
      { ...baseBlock, rotation: 90 },
      { ...baseBlock, size: { width: 101, height: 50 } },
      { ...baseBlock, size: { width: 100, height: 51 } },
      { ...baseBlock, parameters: { value: 99 } },
      { ...baseBlock, inputPorts: [{ id: 'in', name: 'in', dataType: 'double', dimensions: [1] }] },
      { ...baseBlock, outputPorts: [] },
    ]
    for (const changed of changes) {
      expect(arePropsEqual(previous, nodeProps(changed))).toBe(false)
    }

    const withoutSize = { ...baseBlock, size: undefined }
    expect(arePropsEqual(nodeProps(withoutSize), nodeProps({ ...withoutSize }))).toBe(true)
  })

  it('handles missing block data consistently', function () {
    const valid = nodeProps(baseBlock)
    const missing = { ...valid, data: { block: undefined } }
    expect(arePropsEqual(missing, missing)).toBe(true)
    expect(arePropsEqual(missing, valid)).toBe(false)
    expect(arePropsEqual(valid, missing)).toBe(false)
  })

})
