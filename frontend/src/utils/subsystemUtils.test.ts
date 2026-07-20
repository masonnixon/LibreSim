import { describe, expect, it } from 'vitest'
import type { BlockInstance, Connection } from '../types/block'
import { deepCopySubsystemContents } from './subsystemUtils'

function child(id: string, children?: BlockInstance[]): BlockInstance {
  return {
    id,
    type: children ? 'subsystem' : 'gain',
    name: id,
    position: { x: 10, y: 20 },
    parameters: { gain: 2 },
    inputPorts: [
      { id: `${id}-in-a`, name: 'a', dataType: 'double', dimensions: [1] },
      { id: `${id}-in-b`, name: 'b', dataType: 'double', dimensions: [1] },
    ],
    outputPorts: [
      { id: `${id}-out-a`, name: 'out', dataType: 'double', dimensions: [1] },
    ],
    children,
    childConnections: children ? [] : undefined,
  }
}

describe('deepCopySubsystemContents', function () {
  it('accepts undefined and empty children', function () {
    expect(deepCopySubsystemContents(undefined, undefined, 'parent')).toEqual({
      children: [],
      childConnections: [],
    })
    expect(deepCopySubsystemContents([], [], 'parent')).toEqual({
      children: [],
      childConnections: [],
    })
  })

  it('regenerates nested block, port, and internal connection IDs without mutating input', function () {
    const first = child('first')
    const emptySubsystem = child('empty', [])
    const inner = child('inner')
    const nested = child('nested', [inner])
    nested.childConnections = [{
      id: 'nested-connection',
      sourceBlockId: 'inner',
      sourcePortId: 'inner-out-a',
      targetBlockId: 'inner',
      targetPortId: 'inner-in-a',
    }]

    const originalChildren = [first, emptySubsystem, nested]
    const originalSnapshot = structuredClone(originalChildren)
    const connections: Connection[] = [
      {
        id: 'internal',
        sourceBlockId: 'first',
        sourcePortId: 'first-out-a',
        targetBlockId: 'nested',
        targetPortId: 'nested-in-b',
        waypoints: [{ x: 1, y: 2 }],
      },
      {
        id: 'external',
        sourceBlockId: 'outside-source',
        sourcePortId: 'outside-source-port',
        targetBlockId: 'outside-target',
        targetPortId: 'outside-target-port',
      },
    ]

    const copied = deepCopySubsystemContents(originalChildren, connections, 'parent')
    expect(originalChildren).toEqual(originalSnapshot)
    expect(copied.children).toHaveLength(3)

    const copiedFirst = copied.children[0]
    const copiedNested = copied.children[2]
    expect(copiedFirst.id).toMatch(/^parent__/)
    expect(copiedNested.id).toMatch(/^parent__/)
    expect(new Set(copied.children.map(function (item) { return item.id })).size).toBe(3)
    expect(copiedFirst.inputPorts.map(function (item) { return item.id })).toEqual([
      `${copiedFirst.id}-in-0`,
      `${copiedFirst.id}-in-1`,
    ])
    expect(copiedFirst.outputPorts[0].id).toBe(`${copiedFirst.id}-out-0`)

    const internal = copied.childConnections[0]
    expect(internal).toEqual({
      id: expect.stringMatching(/^parent__conn__/),
      sourceBlockId: copiedFirst.id,
      sourcePortId: copiedFirst.outputPorts[0].id,
      targetBlockId: copiedNested.id,
      targetPortId: copiedNested.inputPorts[1].id,
    })
    expect(internal).not.toHaveProperty('waypoints')
    expect(copied.childConnections[1]).toEqual({
      id: expect.stringMatching(/^parent__conn__/),
      sourceBlockId: 'outside-source',
      sourcePortId: 'outside-source-port',
      targetBlockId: 'outside-target',
      targetPortId: 'outside-target-port',
    })

    const copiedInner = copiedNested.children![0]
    expect(copiedInner.id).toMatch(new RegExp(`^${copiedNested.id}__`))
    expect(copiedNested.childConnections![0]).toEqual({
      id: expect.stringMatching(new RegExp(`^${copiedNested.id}__conn__`)),
      sourceBlockId: copiedInner.id,
      sourcePortId: copiedInner.outputPorts[0].id,
      targetBlockId: copiedInner.id,
      targetPortId: copiedInner.inputPorts[0].id,
    })
  })

  it('treats omitted child connections as empty', function () {
    expect(deepCopySubsystemContents([child('only')], undefined, 'parent').childConnections).toEqual([])
  })
})
