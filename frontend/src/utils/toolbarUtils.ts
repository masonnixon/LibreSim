import type { BlockInstance } from '../types/block'

export function findAllScopeBlockIds(blocks: BlockInstance[], parentPath = ''): string[] {
  const result: string[] = []
  for (const block of blocks) {
    const flattenedId = parentPath ? `${parentPath}__${block.id}` : block.id
    if (block.type === 'scope' || block.type === 'xy_graph') {
      result.push(flattenedId)
    }
    if (block.type === 'subsystem' && block.children) {
      result.push(...findAllScopeBlockIds(block.children, flattenedId))
    }
  }
  return result
}
