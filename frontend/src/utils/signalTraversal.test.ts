import { describe, expect, it } from 'vitest'
import type { Connection } from '../types/block'
import { getDownstreamConnectionIds, getSourceBranchConnectionIds } from './signalTraversal'

function edge(
  id: string,
  sourceBlockId: string,
  sourcePortId: string,
  targetBlockId: string
): Connection {
  return {
    id,
    sourceBlockId,
    sourcePortId,
    targetBlockId,
    targetPortId: `${targetBlockId}-in`,
  }
}

describe('getSourceBranchConnectionIds', function () {
  it('matches only connections from the same source block and port', function () {
    const selected = edge('selected', 'source', 'out-1', 'first')
    const sibling = edge('sibling', 'source', 'out-1', 'second')
    const otherPort = edge('other-port', 'source', 'out-2', 'third')
    const otherBlock = edge('other-block', 'different', 'out-1', 'fourth')

    expect(getSourceBranchConnectionIds(selected, [selected, sibling, otherPort, otherBlock])).toEqual(
      new Set(['selected', 'sibling'])
    )
  })

  it('returns an empty set when the selected connection is absent from an unrelated list', function () {
    const selected = edge('selected', 'source', 'out-1', 'first')
    expect(getSourceBranchConnectionIds(selected, [edge('other', 'different', 'out-2', 'last')])).toEqual(new Set())
  })
})

describe('getDownstreamConnectionIds', function () {
  it('walks linear chains and every fan-out from reached blocks', function () {
    const selected = edge('selected', 'source', 'out', 'a')
    const aToB = edge('a-b', 'a', 'out-1', 'b')
    const aToC = edge('a-c', 'a', 'out-2', 'c')
    const bToD = edge('b-d', 'b', 'out', 'd')
    const unrelated = edge('unrelated', 'x', 'out', 'y')

    expect(getDownstreamConnectionIds(selected, [selected, aToB, aToC, bToD, unrelated])).toEqual(
      new Set(['selected', 'a-b', 'a-c', 'b-d'])
    )
  })

  it('terminates cycles and includes fan-in edges reached from different paths', function () {
    const selected = edge('selected', 'source', 'out', 'a')
    const aToB = edge('a-b', 'a', 'out', 'b')
    const aToC = edge('a-c', 'a', 'out-2', 'c')
    const cToB = edge('c-b', 'c', 'out', 'b')
    const bToA = edge('b-a', 'b', 'out', 'a')

    expect(getDownstreamConnectionIds(selected, [selected, aToB, aToC, cToB, bToA])).toEqual(
      new Set(['selected', 'a-b', 'a-c', 'c-b', 'b-a'])
    )
  })

  it('returns only the selected connection for a terminal target', function () {
    const selected = edge('selected', 'source', 'out', 'terminal')
    expect(getDownstreamConnectionIds(selected, [])).toEqual(new Set(['selected']))
  })
})
