import { nanoid } from 'nanoid'
import type { BlockInstance, Connection } from '../types/block'

export function deepCopySubsystemContents(
  children: BlockInstance[] | undefined,
  childConnections: Connection[] | undefined,
  newParentId: string
): { children: BlockInstance[]; childConnections: Connection[] } {
  if (!children || children.length === 0) {
    return { children: [], childConnections: [] }
  }

  const idMap = new Map<string, string>()
  const portIdMap = new Map<string, string>()
  const newChildren: BlockInstance[] = []

  for (const child of children) {
    const newChildId = `${newParentId}__${nanoid()}`
    idMap.set(child.id, newChildId)

    const newInputPorts = child.inputPorts.map(function (inputPort, index) {
      const newPortId = `${newChildId}-in-${index}`
      portIdMap.set(inputPort.id, newPortId)
      return { ...inputPort, id: newPortId }
    })

    const newOutputPorts = child.outputPorts.map(function (outputPort, index) {
      const newPortId = `${newChildId}-out-${index}`
      portIdMap.set(outputPort.id, newPortId)
      return { ...outputPort, id: newPortId }
    })

    let nestedChildren: BlockInstance[] | undefined
    let nestedConnections: Connection[] | undefined
    if (child.children && child.children.length > 0) {
      const nested = deepCopySubsystemContents(child.children, child.childConnections, newChildId)
      nestedChildren = nested.children
      nestedConnections = nested.childConnections
    }

    newChildren.push({
      ...child,
      id: newChildId,
      inputPorts: newInputPorts,
      outputPorts: newOutputPorts,
      children: nestedChildren,
      childConnections: nestedConnections,
    })
  }

  const newChildConnections: Connection[] = []
  for (const connection of childConnections || []) {
    newChildConnections.push({
      id: `${newParentId}__conn__${nanoid()}`,
      sourceBlockId: idMap.get(connection.sourceBlockId) || connection.sourceBlockId,
      sourcePortId: portIdMap.get(connection.sourcePortId) || connection.sourcePortId,
      targetBlockId: idMap.get(connection.targetBlockId) || connection.targetBlockId,
      targetPortId: portIdMap.get(connection.targetPortId) || connection.targetPortId,
    })
  }

  return { children: newChildren, childConnections: newChildConnections }
}
