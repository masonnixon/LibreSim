import type { Connection } from '../types/block'

export function getSourceBranchConnectionIds(
  connection: Connection,
  connections: Connection[]
) {
  const connectionIds = new Set<string>()
  for (const candidate of connections) {
    if (
      candidate.sourceBlockId === connection.sourceBlockId &&
      candidate.sourcePortId === connection.sourcePortId
    ) {
      connectionIds.add(candidate.id)
    }
  }
  return connectionIds
}

export function getDownstreamConnectionIds(
  connection: Connection,
  connections: Connection[]
) {
  const visitedBlockIds = new Set<string>()
  const blockIdsToVisit = [connection.targetBlockId]
  const connectionIds = new Set<string>([connection.id])

  while (blockIdsToVisit.length > 0) {
    const blockId = blockIdsToVisit.shift()!
    if (visitedBlockIds.has(blockId)) continue
    visitedBlockIds.add(blockId)

    for (const candidate of connections) {
      if (candidate.sourceBlockId === blockId) {
        connectionIds.add(candidate.id)
        blockIdsToVisit.push(candidate.targetBlockId)
      }
    }
  }

  return connectionIds
}
