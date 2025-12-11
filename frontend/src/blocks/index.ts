import type { BlockDefinition, BlockCategory } from '../types/block'
import { sourceBlocks } from './sources'
import { sinkBlocks } from './sinks'
import { continuousBlocks } from './continuous'
import { discreteBlocks } from './discrete'
import { mathBlocks } from './math'
import { routingBlocks } from './routing'
import { subsystemBlocks } from './subsystems'

// All block definitions
const allBlocks: BlockDefinition[] = [
  ...sourceBlocks,
  ...sinkBlocks,
  ...continuousBlocks,
  ...discreteBlocks,
  ...mathBlocks,
  ...routingBlocks,
  ...subsystemBlocks,
]

// Block registry for quick lookup
class BlockRegistry {
  private blocks: Map<string, BlockDefinition>

  constructor(definitions: BlockDefinition[]) {
    this.blocks = new Map()
    definitions.forEach((def) => {
      this.blocks.set(def.type, def)
    })
  }

  get(type: string): BlockDefinition | undefined {
    return this.blocks.get(type)
  }

  getAll(): BlockDefinition[] {
    return Array.from(this.blocks.values())
  }

  getByCategory(category: BlockCategory): BlockDefinition[] {
    return this.getAll().filter((def) => def.category === category)
  }

  has(type: string): boolean {
    return this.blocks.has(type)
  }
}

export const blockRegistry = new BlockRegistry(allBlocks)

export const blockCategories: BlockCategory[] = [
  'sources',
  'sinks',
  'continuous',
  'discrete',
  'math',
  'routing',
  'subsystems',
]

export { sourceBlocks } from './sources'
export { sinkBlocks } from './sinks'
export { continuousBlocks } from './continuous'
export { discreteBlocks } from './discrete'
export { mathBlocks } from './math'
export { routingBlocks } from './routing'
export { subsystemBlocks } from './subsystems'
