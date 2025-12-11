import type { BlockDefinition, BlockCategory } from '../types/block'
import { sourceBlocks } from './sources'
import { sinkBlocks } from './sinks'
import { continuousBlocks } from './continuous'
import { discreteBlocks } from './discrete'
import { mathBlocks } from './math'
import { routingBlocks } from './routing'
import { subsystemBlocks } from './subsystems'
import { signalProcessingBlocks } from './signal_processing'
import { nonlinearBlocks } from './nonlinear'
import { observerBlocks } from './observers'

// All block definitions
const allBlocks: BlockDefinition[] = [
  ...sourceBlocks,
  ...sinkBlocks,
  ...continuousBlocks,
  ...discreteBlocks,
  ...mathBlocks,
  ...routingBlocks,
  ...subsystemBlocks,
  ...signalProcessingBlocks,
  ...nonlinearBlocks,
  ...observerBlocks,
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
  'signal_processing',
  'nonlinear',
  'observers',
]

export { sourceBlocks } from './sources'
export { sinkBlocks } from './sinks'
export { continuousBlocks } from './continuous'
export { discreteBlocks } from './discrete'
export { mathBlocks } from './math'
export { routingBlocks } from './routing'
export { subsystemBlocks } from './subsystems'
export { signalProcessingBlocks } from './signal_processing'
export { nonlinearBlocks } from './nonlinear'
export { observerBlocks } from './observers'
