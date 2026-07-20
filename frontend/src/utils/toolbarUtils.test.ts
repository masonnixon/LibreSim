import { describe, expect, it } from 'vitest'
import type { BlockInstance } from '../types/block'
import { findAllScopeBlockIds } from './toolbarUtils'

function block(
  id: string,
  type: string,
  children?: BlockInstance[]
): BlockInstance {
  return {
    id,
    type,
    name: id,
    position: { x: 0, y: 0 },
    parameters: {},
    inputPorts: [],
    outputPorts: [],
    children,
  }
}

describe('findAllScopeBlockIds', function () {
  it('collects root scope and XY graph IDs while ignoring other blocks', function () {
    expect(findAllScopeBlockIds([
      block('scope-1', 'scope'),
      block('xy-1', 'xy_graph'),
      block('gain-1', 'gain'),
    ])).toEqual(['scope-1', 'xy-1'])
  })

  it('flattens nested subsystem IDs using the backend naming convention', function () {
    const blocks = [
      block('outer', 'subsystem', [
        block('inner-scope', 'scope'),
        block('inner', 'subsystem', [block('deep-xy', 'xy_graph')]),
      ]),
      block('empty', 'subsystem'),
    ]
    expect(findAllScopeBlockIds(blocks)).toEqual([
      'outer__inner-scope',
      'outer__inner__deep-xy',
    ])
  })

  it('accepts an existing parent path', function () {
    expect(findAllScopeBlockIds([block('scope-1', 'scope')], 'parent')).toEqual([
      'parent__scope-1',
    ])
  })
})
